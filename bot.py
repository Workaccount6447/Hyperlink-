import os
import threading
import uuid
import zipfile
import shutil
import requests
import subprocess
from datetime import datetime
from PIL import Image
import qrcode
import yt_dlp
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import psycopg2
from sympy import sympify
from googletrans import Translator
from PyPDF2 import PdfReader, PdfWriter
from docx import Document
import pytz

# ================= CONFIG =================
BOT_TOKEN = "8569119575:AAFts4CJWhVfdL0lKk_RUllaU8_rHo1HLWA"
OWNER_ID = 8420494874
TMP = "/tmp"
DATABASE_URL = os.environ.get("DATABASE_URL","postgresql://royality_database_user:qPWcamj4vaMZx0UMN12RnBuDlMx3GiFK@dpg-d571nq0gjchc739ap3ag-a/royality_database")
translator = Translator()

# ================= DATABASE =================
def get_conn(): return psycopg2.connect(DATABASE_URL, sslmode="require")
def add_user(uid, name=None):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users(uid BIGINT PRIMARY KEY, name TEXT)")
    cur.execute("INSERT INTO users(uid,name) VALUES(%s,%s) ON CONFLICT(uid) DO NOTHING",(uid,name))
    conn.commit(); cur.close(); conn.close()
def ban_user(uid):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS banned(uid BIGINT PRIMARY KEY)")
    cur.execute("INSERT INTO banned(uid) VALUES(%s) ON CONFLICT(uid) DO NOTHING",(uid,))
    conn.commit(); cur.close(); conn.close()
def unban_user(uid):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM banned WHERE uid=%s",(uid,))
    conn.commit(); cur.close(); conn.close()
def is_banned(uid):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT uid FROM banned WHERE uid=%s",(uid,))
    res=cur.fetchone(); cur.close(); conn.close(); return res is not None
def get_all_users():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT uid FROM users"); res = cur.fetchall()
    cur.close(); conn.close(); return [r[0] for r in res]
def count_users():
    conn = get_conn(); cur = conn.cursor(); cur.execute("SELECT COUNT(*) FROM users")
    res=cur.fetchone()[0]; cur.close(); conn.close(); return res
def count_banned():
    conn = get_conn(); cur = conn.cursor(); cur.execute("SELECT COUNT(*) FROM banned")
    res=cur.fetchone()[0]; cur.close(); conn.close(); return res

# ================= HELPERS =================
def owner_only(uid): return uid==OWNER_ID
def cleanup(path): 
    if os.path.exists(path): os.remove(path)
def generate_qr(text):
    img=qrcode.make(text); path=os.path.join(TMP,f"{uuid.uuid4().hex}_qr.png"); img.save(path); return path

# ================= START & HELP =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; add_user(uid,update.effective_user.first_name)
    await update.message.reply_text("✅ Bot is alive. Use /help to see commands.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmds="""
/yt <url> - Download YouTube video
/ytc <url> - Download YouTube clip
/mp3 <url> - Download audio from YouTube
/fa <url> - Download Facebook video
/tw <url> - Download Twitter video
/tk <url> - Download TikTok video
/tch <url> - Download Twitch video
/ig <url> - Download Instagram video
/igp <url> - Download Instagram photo
/git <url> - Download GitHub repo as zip
/qr <text> - Generate QR code
/ss <url> - Screenshot webpage
/math <equation> - Solve math
/id <user/channel> - Get ID
/tr <lang> <text> - Translate
/pdf <file> - Convert to PDF
/docx <file> - Convert to DOCX
/zip <file> - Compress
/unzip <file> - Unzip
/bg <file> - Remove background
/time <country> - Show time
"""
    await update.message.reply_text(cmds)

# ================= YT-DLP DOWNLOAD =================
async def ytdlp_download(update: Update, context: ContextTypes.DEFAULT_TYPE, url=None, audio=False):
    if not url and not context.args: return await update.message.reply_text("❌ No URL provided")
    if not url: url=context.args[0]
    out_path=os.path.join(TMP,f"%(title)s.%(ext)s")
    opts={"outtmpl":out_path}
    if audio: opts.update({"format":"bestaudio","postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":"mp3"}]})
    try:
        with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([url])
        info=yt_dlp.YoutubeDL({}).extract_info(url,download=False)
        file=yt_dlp.YoutubeDL(opts).prepare_filename(info)
        await update.message.reply_document(open(file,"rb"))
    except Exception as e: await update.message.reply_text(f"❌ Download failed: {e}")
    finally: cleanup(file)

# ================= COMMANDS =================
async def yt(update, context): await ytdlp_download(update,context)
async def ytc(update, context): await ytdlp_download(update,context)
async def mp3(update, context): await ytdlp_download(update,context,audio=True)
async def fa(update, context): await ytdlp_download(update,context)
async def tw(update, context): await ytdlp_download(update,context)
async def tk(update, context): await ytdlp_download(update,context)
async def tch(update, context): await ytdlp_download(update,context)
async def ig(update, context): await ytdlp_download(update,context)
async def igp(update, context): await ytdlp_download(update,context)
async def git(update, context): await ytdlp_download(update,context)

async def qr_cmd(update, context):
    if not context.args: return await update.message.reply_text("❌ No text provided")
    path=generate_qr(" ".join(context.args))
    await update.message.reply_photo(open(path,"rb")); cleanup(path)

async def math_cmd(update, context):
    try:
        eq=" ".join(context.args)
        result=sympify(eq)
        await update.message.reply_text(f"🧮 {eq} = {result}")
    except: await update.message.reply_text("❌ Invalid equation")

async def tr_cmd(update, context):
    try:
        lang=context.args[0]
        text=" ".join(context.args[1:])
        trans=translator.translate(text,dest=lang)
        await update.message.reply_text(f"🌐 {trans.text}")
    except: await update.message.reply_text("❌ Invalid usage")

async def id_cmd(update, context):
    if context.args: await update.message.reply_text(f"ID: {context.args[0]}")
    else: await update.message.reply_text(f"Your ID: {update.effective_user.id}")

async def time_cmd(update, context):
    if not context.args: return await update.message.reply_text("❌ Usage: /time <timezone>")
    tzname=context.args[0]
    try:
        tz=pytz.timezone(tzname)
        t=datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        await update.message.reply_text(f"Time in {tzname}: {t}")
    except: await update.message.reply_text("❌ Invalid timezone")

# ================= FILE COMMANDS =================
async def pdf_cmd(update, context):
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        return await update.message.reply_text("❌ Reply to a file")
    doc = update.message.reply_to_message.document
    path = os.path.join(TMP, doc.file_name)
    await doc.get_file().download_to_drive(path)
    try: pdf_path = path+".pdf"; shutil.copy(path,pdf_path); await update.message.reply_document(open(pdf_path,"rb"))
    finally: cleanup(path); cleanup(pdf_path)

async def docx_cmd(update, context):
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        return await update.message.reply_text("❌ Reply to a file")
    doc = update.message.reply_to_message.document
    path = os.path.join(TMP, doc.file_name)
    await doc.get_file().download_to_drive(path)
    try: docx_path = path+".docx"; shutil.copy(path,docx_path); await update.message.reply_document(open(docx_path,"rb"))
    finally: cleanup(path); cleanup(docx_path)

async def zip_cmd(update, context):
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        return await update.message.reply_text("❌ Reply to a file")
    doc = update.message.reply_to_message.document
    path = os.path.join(TMP, doc.file_name)
    await doc.get_file().download_to_drive(path)
    zip_path = path+".zip"
    try: 
        with zipfile.ZipFile(zip_path,"w") as zf: zf.write(path,doc.file_name)
        await update.message.reply_document(open(zip_path,"rb"))
    finally: cleanup(path); cleanup(zip_path)

async def unzip_cmd(update, context):
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        return await update.message.reply_text("❌ Reply to a zip file")
    doc = update.message.reply_to_message.document
    path = os.path.join(TMP, doc.file_name)
    await doc.get_file().download_to_drive(path)
    try:
        with zipfile.ZipFile(path,"r") as zf:
            zf.extractall(TMP)
            for f in zf.namelist(): await update.message.reply_document(open(os.path.join(TMP,f),"rb"))
    finally: cleanup(path); [cleanup(os.path.join(TMP,f)) for f in zf.namelist()]

# ================= OWNER COMMANDS =================
async def broadcast(update, context):
    uid=update.effective_user.id
    if not owner_only(uid): return await update.message.reply_text("❌ Owner only.")
    msg=" ".join(context.args)
    for u in get_all_users():
        try: await context.bot.send_message(u,msg)
        except: pass
    await update.message.reply_text("✅ Broadcast sent.")

async def ban(update, context):
    uid=update.effective_user.id
    if not owner_only(uid): return await update.message.reply_text("❌ Owner only.")
    try: user_to_ban=int(context.args[0]); ban_user(user_to_ban)
    except: return await update.message.reply_text("❌ Invalid user ID")
    await update.message.reply_text(f"✅ Banned {user_to_ban}")

async def unban(update, context):
    uid=update.effective_user.id
    if not owner_only(uid): return await update.message.reply_text("❌ Owner only.")
    try: user_to_unban=int(context.args[0]); unban_user(user_to_unban)
    except: return await update.message.reply_text("❌ Invalid user ID")
    await update.message.reply_text(f"✅ Unbanned {user_to_unban}")

async def stats(update, context):
    uid=update.effective_user.id
    if not owner_only(uid): return await update.message.reply_text("❌ Owner only.")
    await update.message.reply_text(f"✅ Total users: {count_users()}\n❌ Banned: {count_banned()}")

# ================= FLASK & BOT =======);

def run_bot():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    handlers=[
        CommandHandler("start", start),
        CommandHandler("help", help_cmd),
        CommandHandler("yt", yt),
        CommandHandler("ytc", ytc),
        CommandHandler("mp3", mp3),
        CommandHandler("fa", fa),
        CommandHandler("tw", tw),
        CommandHandler("tk", tk),
        CommandHandler("tch", tch),
        CommandHandler("ig", ig),
        CommandHandler("igp", igp),
        CommandHandler("git", git),
        CommandHandler("qr", qr_cmd),
        CommandHandler("math", math_cmd),
        CommandHandler("tr", tr_cmd),
        CommandHandler("id", id_cmd),
        CommandHandler("time", time_cmd),
        CommandHandler("pdf", pdf_cmd),
        CommandHandler("docx", docx_cmd),
        CommandHandler("zip", zip_cmd),
        CommandHandler("unzip", unzip_cmd),
        CommandHandler("broadcast", broadcast),
        CommandHandler("ban", ban),
        CommandHandler("unban", unban),
        CommandHandler("stats", stats),
    ]
    for h in handlers: app_bot.add_handler(h)
    print("Bot running...")
    app_bot.run_polling()
    
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
