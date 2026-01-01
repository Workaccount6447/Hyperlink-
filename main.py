import os
import uuid
import asyncpg
import httpx

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# ================= CONFIG =================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_LOG_CHANNEL_ID = os.getenv("TELEGRAM_LOG_CHANNEL_ID")
DATABASE_URL = os.getenv("DATABASE_URL")

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_LOG_CHANNEL_ID, DATABASE_URL]):
    raise RuntimeError("Missing env variables")

# ================= APP =================

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

db: asyncpg.Pool | None = None


@app.on_event("startup")
async def startup():
    global db
    db = await asyncpg.create_pool(DATABASE_URL)


@app.on_event("shutdown")
async def shutdown():
    await db.close()


# ================= HELPERS =================

async def send_to_telegram(filename: str, content_type: str, data: bytes) -> str:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            url,
            data={"chat_id": TELEGRAM_LOG_CHANNEL_ID},
            files={
                "document": (
                    filename,
                    data,
                    content_type or "application/octet-stream",
                )
            },
        )

    if r.status_code != 200:
        raise RuntimeError(r.text)

    return r.json()["result"]["document"]["file_id"]


async def save_metadata(file_id, filename, content_type, size, tg_file_id):
    await db.execute(
        """
        INSERT INTO files (file_id, filename, content_type, size, telegram_file_id)
        VALUES ($1, $2, $3, $4, $5)
        """,
        file_id,
        filename,
        content_type,
        size,
        tg_file_id,
    )


async def load_metadata(file_id):
    return await db.fetchrow(
        "SELECT * FROM files WHERE file_id=$1", file_id
    )


# ================= ROUTES =================

@app.get("/host", response_class=HTMLResponse)
async def host():
    with open("static/ab.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    data = await file.read()
    size = len(data)

    if size > MAX_FILE_SIZE:
        raise HTTPException(400, "File exceeds 50MB")

    file_id = uuid.uuid4().hex

    tg_id = await send_to_telegram(
        file.filename, file.content_type, data
    )

    await save_metadata(
        file_id,
        file.filename,
        file.content_type or "application/octet-stream",
        size,
        tg_id,
    )

    return {
        "id": file_id,
        "filename": file.filename,
        "size": size,
        "content_type": file.content_type,
        "url": f"/f/{file_id}",
    }


@app.get("/f/{file_id}")
async def download(file_id: str):
    meta = await load_metadata(file_id)
    if not meta:
        raise HTTPException(404, "Not found")

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile",
            params={"file_id": meta["telegram_file_id"]},
        )

    path = r.json()["result"]["file_path"]
    return RedirectResponse(
        f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{path}"
    )


@app.get("/meta/{file_id}")
async def meta(file_id: str):
    meta = await load_metadata(file_id)
    if not meta:
        raise HTTPException(404, "Not found")

    return JSONResponse(dict(meta))
