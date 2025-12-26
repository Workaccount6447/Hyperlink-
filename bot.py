import os
import threading
import uuid
import zipfile
import shutil
import urllib.parse
from datetime import datetime
from PIL import Image
import qrcode
import yt_dlp
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from sympy import sympify
from googletrans import Translator
from PyPDF2 import PdfReader, PdfWriter
from docx import Document
import pytz
from pymongo import MongoClient

# ================= CONFIG =================

BOT_TOKEN = "8569119575:AAFts4CJWhVfdL0lKk_RUllaU8_rHo1HLWA"
OWNER_ID = 8420494874
TMP = "/tmp"
# Hardcoded URI with stability parameters for Render
MONGO_URL = "mongodb+srv://Cahnnel:Xu52ciUXinailOAX@cluster0.02ez6dm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

translator = Translator()
UPDATES_CHANNEL = "https://t.me/RoyalityBots"

# ================= DATABASE =================

# Added connection fixes for DNS resolution errors
client = MongoClient(
    MONGO_URL,
    tlsAllowInvalidCertificates=True,
    connectTimeoutMS=30000,
    socketTimeoutMS=None,
    connect=False
)

db = client["royality_bot"]
users_col = db["users"]
banned_col = db["banned"]

def add_user(uid, name=None):
    try:
        users_col.update_one({"uid": uid}, {"$set": {"uid": uid, "name": name}}, upsert=True)
    except: pass

def ban_user(uid):
    banned_col.update_one({"uid": uid}, {"$set": {"uid": uid}}, upsert=True)

def unban_user(uid):
    banned_col.delete_one({"uid": uid})

def is_banned(uid):
    return banned_col.find_one({"uid": uid}) is not None

def get_all_users():
    return [u["uid"] for u in users_col.find({}, {"uid": 1})]

def count_users():
    return users_col.count_documents({})

def count_banned():
    return banned_col.count_documents({})

# ================= HELPERS =================

def owner_only(uid):
    return uid == OWNER_ID

def cleanup(path):
    if path and os.path.exists(path):
        if os.path.isdir(path): shutil.rmtree(path)
        else: os.remove(path)

def generate_qr(text):
    img = qrcode.make(text)
    path = os.path.join(TMP, f"{uuid.uuid4().hex}_qr.png")
    img.save(path)
    return path

# ================= TELEGRAM COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_banned(uid): return
    name = update.effective_user.first_name
    add_user(uid, name)
    
    welcome_text = f"Welcome, {name}\n\nI can automate requests and provide tools.\n\nMaintained by: RoyalityBots"
    keyboard = [
        [InlineKeyboardButton("Help Menu", callback_data="help")],
        [InlineKeyboardButton("Updates Channel", url=UPDATES_CHANNEL)]
    ]
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "help":
        cmds = """
/yt <url> - YT Video
/ytc <url> - YT Clip
/mp3 <url> - YT Audio
/fa <url> - FB Video
/tw <url> - Twitter
/tk <url> - TikTok
/tch <url> - Twitch
/ig <url> - Insta Video
/igp <url> - Insta Photo
/git <url> - GitHub Zip
/qr <text> - QR Code
/math <eq> - Solve Math
/id - Get ID
/tr <lang> <text> - Translate
/time <tz> - Current Time
"""
        await query.edit_message_text(cmds)

# ================= TOOLS =================

async def downloader(update, context, audio=False):
    if not context.args: return await update.message.reply_text("❌ Send URL")
    url = context.args[0]
    m = await update.message.reply_text("⏳ Processing...")
    try:
        opts = {'outtmpl': f'{TMP}/%(title)s.%(ext)s'}
        if audio: opts.update({'format': 'bestaudio', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]})
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            if audio: path = path.rsplit('.', 1)[0] + ".mp3"
            await update.message.reply_document(open(path, 'rb'))
            cleanup(path)
    except Exception as e: await update.message.reply_text(f"❌ Error: {e}")
    finally: await m.delete()

async def qr_cmd(update, context):
    if not context.args: return
    path = generate_qr(" ".join(context.args))
    await update.message.reply_photo(open(path, "rb"))
    cleanup(path)

async def math_cmd(update, context):
    try:
        res = sympify(" ".join(context.args))
        await update.message.reply_text(f"🧮 Result: {res}")
    except: await update.message.reply_text("❌ Invalid Equation")

async def tr_cmd(update, context):
    try:
        dest, text = context.args[0], " ".join(context.args[1:])
        res = translator.translate(text, dest=dest)
        await update.message.reply_text(f"🌐 {res.text}")
    except: await update.message.reply_text("❌ Usage: /tr en Hello")

async def id_cmd(update, context):
    target = context.args[0] if context.args else update.effective_user.id
    await update.message.reply_text(f"🆔 ID: `{target}`", parse_mode="Markdown")

async def time_cmd(update, context):
    try:
        tz = pytz.timezone(context.args[0])
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        await update.message.reply_text(f"🕒 {context.args[0]}: {now}")
    except: await update.message.reply_text("❌ Invalid Timezone (e.g. Asia/Kolkata)")

# ================= OWNER COMMANDS =================

async def broadcast(update, context):
    if not owner_only(update.effective_user.id): return
    msg = " ".join(context.args)
    count = 0
    for u in get_all_users():
        try:
            await context.bot.send_message(u, msg)
            count += 1
        except: pass
    await update.message.reply_text(f"✅ Sent to {count} users.")

async def ban(update, context):
    if owner_only(update.effective_user.id):
        ban_user(int(context.args[0]))
        await update.message.reply_text("🚫 Banned.")

async def unban(update, context):
    if owner_only(update.effective_user.id):
        unban_user(int(context.args[0]))
        await update.message.reply_text("✅ Unbanned.")

async def stats(update, context):
    if owner_only(update.effective_user.id):
        await update.message.reply_text(f"📊 Total: {count_users()}\n🚫 Banned: {count_banned()}")

# ================= RUNNER =================

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Active"

def run_bot():
    bot = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Register All Commands
    cmd_list = [
        ("start", start), ("help", start), ("qr", qr_cmd), ("math", math_cmd),
        ("tr", tr_cmd), ("id", id_cmd), ("time", time_cmd), ("stats", stats),
        ("broadcast", broadcast), ("ban", ban), ("unban", unban),
        ("yt", lambda u, c: downloader(u, c)),
        ("ytc", lambda u, c: downloader(u, c)),
        ("mp3", lambda u, c: downloader(u, c, audio=True)),
        ("fa", lambda u, c: downloader(u, c)),
        ("tw", lambda u, c: downloader(u, c)),
        ("tk", lambda u, c: downloader(u, c)),
        ("tch", lambda u, c: downloader(u, c)),
        ("ig", lambda u, c: downloader(u, c)),
        ("igp", lambda u, c: downloader(u, c)),
        ("git", lambda u, c: downloader(u, c))
    ]
    
    for name, func in cmd_list:
        bot.add_handler(CommandHandler(name, func))
    
    bot.add_handler(CallbackQueryHandler(button_callback))
    bot.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
