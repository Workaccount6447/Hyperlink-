#Jai Shree Ganesha 
#Jai Shree Krishna 
#Jai Shree Ram 

#This repo was made by - @RoyalityBots of telegram .

import os
import uuid
import httpx
from datetime import datetime

from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from sqlalchemy import (
    create_engine,
    Column,
    String,
    BigInteger,
    DateTime,
)
from sqlalchemy.orm import sessionmaker, declarative_base

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse


# =========================
# CONFIG
#This repo was made by - @RoyalityBots of telegram .
# =========================

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
APP_BASE_URL = os.getenv("APP_BASE_URL", "").rstrip("/")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")

if not DATABASE_URL:
    raise RuntimeError("Missing DATABASE_URL")

# =========================
# DATABASE
# =========================
#This repo was made by - @RoyalityBots of telegram .
Base = declarative_base()
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

class FileMeta(Base):
    __tablename__ = "files"

    file_id = Column(String, primary_key=True, index=True)
    filename = Column(String)
    content_type = Column(String)
    size = Column(BigInteger)
    telegram_file_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# =========================
# APP
# =========================
#This repo was made by - @RoyalityBots of telegram .

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

app.mount("/static", StaticFiles(directory="static"), name="static")

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
#This repo was made by - @RoyalityBots of telegram .

from fastapi import UploadFile, File, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
import uuid
import httpx

# =========================
# HOST PAGES
# =========================

@app.get("/host")
def host():
    return FileResponse("static/ab.html", media_type="text/html")


@app.get("/pw")
def preview_home():
    return FileResponse("static/pw.html", media_type="text/html")


# =========================
# PREVIEW PAGE (IMAGE + VIDEO)
# =========================


# =========================
# UPLOAD
# =========================

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    size = len(content)

    if size > MAX_FILE_SIZE:
        raise HTTPException(400, "File exceeds 50MB limit")

    file_id = uuid.uuid4().hex

    file.file.seek(0)
    telegram_file_id = await send_to_telegram(file)

    db = SessionLocal()
    try:
        meta = FileMeta(
            file_id=file_id,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            size=size,
            telegram_file_id=telegram_file_id,
        )
        db.add(meta)
        db.commit()
    finally:
        db.close()

    return {
        "id": file_id,
        "url": f"/pw/{file_id}",
        "filename": file.filename,
        "size": size,
        "content_type": file.content_type,
    }


# =========================
# FILE REDIRECT (TELEGRAM)
# =========================

@app.get("/pw/{file_id}")
def preview_file(file_id: str):
    db = SessionLocal()
    try:
        meta = db.query(FileMeta).filter_by(file_id=file_id).first()
    finally:
        db.close()

    if not meta:
        raise HTTPException(404, "File not found")

    allowed_types = (
        "image/jpeg",
        "image/png",
        "video/mp4",
        "video/webm",
        "video/ogg",
        "video/quicktime",
    )

    if meta.content_type not in allowed_types:
        raise HTTPException(
            400,
            "Invalid format. Only JPG, PNG and video files are allowed"
        )

    # Frontend loads media via /f/{file_id}
    return FileResponse("static/pw.html", media_type="text/html")



@app.get("/f/{file_id}")
async def get_file(file_id: str):
    db = SessionLocal()
    try:
        meta = db.query(FileMeta).filter_by(file_id=file_id).first()
    finally:
        db.close()

    if not meta:
        raise HTTPException(404, "File not found")

    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile"

    async with httpx.AsyncClient() as client:
        r = await client.get(tg_url, params={"file_id": meta.telegram_file_id})

    if r.status_code != 200 or not r.json().get("ok"):
        raise HTTPException(500, "Telegram lookup failed")

    file_path = r.json()["result"]["file_path"]
    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"

    return RedirectResponse(download_url)


# =========================
# METADATA
# =========================

@app.get("/meta/{file_id}")
async def meta(file_id: str):
    db = SessionLocal()
    try:
        meta = db.query(FileMeta).filter_by(file_id=file_id).first()
    finally:
        db.close()

    if not meta:
        raise HTTPException(404, "Not found")

    return JSONResponse({
        "file_id": meta.file_id,
        "filename": meta.filename,
        "content_type": meta.content_type,
        "size": meta.size,
        "telegram_file_id": meta.telegram_file_id,
        "created_at": meta.created_at.isoformat(),
    })

from fastapi.responses import HTMLResponse

@app.get("/pre/{file_id}", response_class=HTMLResponse)
async def preview_file(file_id: str):
    db = SessionLocal()
    try:
        meta = db.query(FileMeta).filter_by(file_id=file_id).first()
    finally:
        db.close()

    if not meta:
        raise HTTPException(404, "File not found")

    ctype = meta.content_type or ""

    # IMAGE PREVIEW
    if ctype.startswith("image/"):
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Preview</title>
            <style>
                body {{
                    margin: 0;
                    background: #000;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                }}
                img {{
                    max-width: 100%;
                    max-height: 100%;
                }}
            </style>
        </head>
        <body>
            <img src="/f/{file_id}">
        </body>
        </html>
        """

    # VIDEO PREVIEW
    if ctype.startswith("video/"):
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Preview</title>
            <style>
                body {{
                    margin: 0;
                    background: #000;
                }}
                video {{
                    width: 100%;
                    height: 100vh;
                }}
            </style>
        </head>
        <body>
            <video controls autoplay>
                <source src="/f/{file_id}" type="{ctype}">
            </video>
        </body>
        </html>
        """

    # OTHER FILE TYPES
    raise HTTPException(
        400,
        "Preview not supported for this file type"
    )
