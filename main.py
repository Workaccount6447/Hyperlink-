import os
import uuid
import httpx

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# =========================
# CONFIG
# =========================

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
APP_BASE_URL = os.getenv("APP_BASE_URL", "").rstrip("/")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")

# =========================
# APP
# =========================

app = FastAPI(title="File Host")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# STATIC FILES
# =========================

# IMPORTANT: ab.html must be inside ./static/
app.mount("/static", StaticFiles(directory="static"), name="static")

# =========================
# IN-MEMORY STORAGE
# =========================

FILES = {}

# =========================
# HELPERS
# =========================

async def send_to_telegram(file: UploadFile) -> str:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    data = {"chat_id": TELEGRAM_CHAT_ID}
    files = {
        "document": (
            file.filename,
            await file.read(),
            file.content_type or "application/octet-stream",
        )
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(url, data=data, files=files)

    if r.status_code != 200 or not r.json().get("ok"):
        raise HTTPException(500, "Telegram upload failed")

    return r.json()["result"]["document"]["file_id"]

# =========================
# ROUTES
# =========================

@app.get("/host", response_class=HTMLResponse)
def host():
    return """
    <!DOCTYPE html>
    <html>
      <head>
        <title>File Host</title>
        <meta charset="utf-8">
      </head>
      <body>
        <h2>File Host</h2>
        <a href="/static/ab.html">Open uploader</a>
      </body>
    </html>
    """

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    size = len(content)

    if size > MAX_FILE_SIZE:
        raise HTTPException(400, "File exceeds 50MB limit")

    file_id = uuid.uuid4().hex

    # reset pointer before sending to telegram
    file.file.seek(0)
    telegram_file_id = await send_to_telegram(file)

    FILES[file_id] = {
        "file_id": file_id,
        "filename": file.filename,
        "content_type": file.content_type or "application/octet-stream",
        "size": size,
        "telegram_file_id": telegram_file_id,
    }

    file_url = (
        f"{APP_BASE_URL}/f/{file_id}"
        if APP_BASE_URL
        else f"/f/{file_id}"
    )

    return {
        "id": file_id,
        "url": file_url,
        "filename": file.filename,
        "size": size,
        "content_type": file.content_type,
    }

@app.get("/f/{file_id}")
async def get_file(file_id: str):
    meta = FILES.get(file_id)
    if not meta:
        raise HTTPException(404, "File not found")

    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile"

    async with httpx.AsyncClient() as client:
        r = await client.get(tg_url, params={"file_id": meta["telegram_file_id"]})

    if r.status_code != 200 or not r.json().get("ok"):
        raise HTTPException(500, "Telegram lookup failed")

    file_path = r.json()["result"]["file_path"]
    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"

    return RedirectResponse(download_url)

@app.get("/meta/{file_id}")
async def meta(file_id: str):
    meta = FILES.get(file_id)
    if not meta:
        raise HTTPException(404, "Not found")
    return JSONResponse(meta)
