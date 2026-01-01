import os
import uuid
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import asyncpg
import httpx

# =========================
# Config
# =========================

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

APP_BASE_URL = os.getenv("APP_BASE_URL", "")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_LOG_CHANNEL_ID = os.getenv("TELEGRAM_LOG_CHANNEL_ID")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN missing")

if not TELEGRAM_LOG_CHANNEL_ID:
    raise RuntimeError("TELEGRAM_LOG_CHANNEL_ID missing")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL missing")

# =========================
# App
# =========================

app = FastAPI(title="Telegram File Host")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# =========================
# Database helpers
# =========================

async def get_db():
    return await asyncpg.connect(DATABASE_URL)


async def save_metadata(file_id, filename, content_type, size, telegram_file_id):
    conn = await get_db()
    await conn.execute(
        """
        INSERT INTO files (id, filename, content_type, size, telegram_file_id)
        VALUES ($1, $2, $3, $4, $5)
        """,
        file_id,
        filename,
        content_type,
        size,
        telegram_file_id,
    )
    await conn.close()


async def load_metadata(file_id) -> Optional[dict]:
    conn = await get_db()
    row = await conn.fetchrow(
        "SELECT * FROM files WHERE id=$1",
        file_id,
    )
    await conn.close()
    return dict(row) if row else None

# =========================
# Telegram helpers
# =========================

async def send_to_telegram(file: UploadFile) -> str:
    file.file.seek(0)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            url,
            data={"chat_id": TELEGRAM_LOG_CHANNEL_ID},
            files={
                "document": (
                    file.filename,
                    await file.read(),
                    file.content_type or "application/octet-stream",
                )
            },
        )

    if resp.status_code != 200:
        raise RuntimeError("Failed to upload to Telegram")

    data = resp.json()
    return data["result"]["document"]["file_id"]

# =========================
# Routes
# =========================
@app.get("/host")
def host():
    return FileResponse("static/ab.html")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    size = len(contents)

    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 50MB limit")

    file_id = uuid.uuid4().hex

    try:
        telegram_file_id = await send_to_telegram(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        await save_metadata(
            file_id=file_id,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            size=size,
            telegram_file_id=telegram_file_id,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    file_url = f"{APP_BASE_URL}/f/{file_id}" if APP_BASE_URL else f"/f/{file_id}"

    return {
        "id": file_id,
        "url": file_url,
        "filename": file.filename,
        "size": size,
    }


@app.get("/f/{file_id}")
async def get_file(file_id: str):
    meta = await load_metadata(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")

    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile"

    async with httpx.AsyncClient() as client:
        r = await client.get(
            tg_url,
            params={"file_id": meta["telegram_file_id"]},
        )

    if r.status_code != 200:
        raise HTTPException(status_code=500, detail="Telegram lookup failed")

    file_path = r.json()["result"]["file_path"]
    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"

    return RedirectResponse(download_url)


@app.get("/meta/{file_id}")
async def metadata(file_id: str):
    meta = await load_metadata(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Not found")
    return JSONResponse(meta)


# =========================
# Local run
# =========================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
