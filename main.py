import os
import uuid
import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ================== CONFIG ==================
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise RuntimeError("Telegram env vars missing")

# simple in-memory db (replace with postgres later)
DATABASE = {}

# ================== APP ==================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== HELPERS ==================
async def send_to_telegram(file: UploadFile):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    data = {
        "chat_id": TELEGRAM_CHAT_ID
    }

    files = {
        "document": (file.filename, await file.read(), file.content_type)
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(url, data=data, files=files)

    if r.status_code != 200 or not r.json().get("ok"):
        raise Exception("Telegram upload failed")

    return r.json()["result"]["document"]["file_id"]


# ================== ROUTES ==================
@app.get("/host", response_class=HTMLResponse)
def host_page():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>kust-host</title></head>
    <body>
        <script>location.href="/static/ab.html"</script>
    </body>
    </html>
    """


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    data = await file.read()
    size = len(data)

    if size > MAX_FILE_SIZE:
        raise HTTPException(400, "File exceeds 50MB limit")

    file_id = uuid.uuid4().hex

    file.file.seek(0)
    telegram_file_id = await send_to_telegram(file)

    DATABASE[file_id] = {
        "file_id": file_id,
        "filename": file.filename,
        "content_type": file.content_type or "application/octet-stream",
        "size": size,
        "telegram_file_id": telegram_file_id,
    }

    return {
        "id": file_id,
        "url": f"/f/{file_id}",
        "filename": file.filename,
        "size": size,
        "content_type": file.content_type,
    }


@app.get("/f/{file_id}")
async def download_file(file_id: str):
    meta = DATABASE.get(file_id)
    if not meta:
        raise HTTPException(404, "File not found")

    tg = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile"

    async with httpx.AsyncClient() as client:
        r = await client.get(tg, params={"file_id": meta["telegram_file_id"]})

    file_path = r.json()["result"]["file_path"]
    return RedirectResponse(
        f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    )


@app.get("/meta/{file_id}")
async def metadata(file_id: str):
    meta = DATABASE.get(file_id)
    if not meta:
        raise HTTPException(404, "Not found")
    return JSONResponse(meta)
