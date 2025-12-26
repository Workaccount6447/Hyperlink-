import os
import threading
import uuid
import zipfile
import shutil
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
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://Cahnnel:Xu52ciUXinailOAX@cluster0.02ez6dm.mongodb.net/?appName=Cluster0")
translator = Translator()
BOT_NAME = "royalitybot"  # for About Me inline info
UPDATES_CHANNEL = "https://t.me/RoyalityBots"

# ================= DATABASE =================

client = MongoClient(MONGO_URL)
db = client["royality_bot"]
users_col = db["users"]
banned_col = db["banned"]

def add_user(uid, name=None):
    users_col.update_one(
        {"uid": uid},
        {"$setOnInsert": {"uid": uid, "name": name}},
        upsert=True
    )

def ban_user(uid):
    banned_col.update_one(
        {"uid": uid},
        {"$setOnInsert": {"uid": uid}},
        upsert=True
    )

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
    if os.path.exists(path):
        os.remove(path)

def generate_qr(text):
    img = qrcode.make(text)
    path = os.path.join(TMP, f"{uuid.uuid4().hex}_qr.png")
    img.save(path)
    return path

# ================= TELEGRAM COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name
    add_user(uid, name)
    
    welcome_text = f"""Welcome , {name}

𝖨 𝖼𝖺𝗇 𝖺𝗎𝗍𝗈𝗆𝖺𝗍𝗂𝖼𝖺𝗅𝗅𝗒 𝖺𝗉𝗉𝗋𝗈𝗏𝖾 𝗇𝖾𝗐 𝖺𝗌 𝗐𝖾𝗅𝗅 𝖺𝗌 𝗉𝖾𝗇𝖽𝗂𝗇𝗀 𝗃𝗈𝗂𝗇 𝗋𝖾𝗊𝗎𝖾𝗌𝗍 𝗂𝗇 𝗒𝗈𝗎𝗋 𝖼𝗁𝖺𝗇𝗇𝖾𝗅𝗌 𝗈𝗋 𝗀𝗋𝗈𝗎𝗉𝗌.

𝖩𝗎𝗌𝗍 𝖺𝖽𝖽 𝗆𝖾 𝗂𝗇 𝗒𝗈𝗎𝗋 𝖼𝗁𝖺𝗇𝗇𝖾𝗅𝗌 𝖺𝗇𝖽 𝗀𝗋𝗈𝗎𝗉𝗌 𝗐𝗂𝗍𝗁 𝗉𝖾𝗋𝗆𝗂𝗌𝗌𝗂𝗈𝗇 𝗍𝗈 𝖺𝖽𝖽 𝗇𝖾𝗐 𝗆𝖾𝗆𝖻𝖾𝗋𝗌.

‣ ᴍᴀɪɴᴛᴀɪɴᴇᴅ ʙʏ : [RoyalityBots]({UPDATES_CHANNEL})
"""
    keyboard = [
        [InlineKeyboardButton("Help Menu", callback_data="help")],
        [InlineKeyboardButton("About Me / Updates Channel", url=UPDATES_CHANNEL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        cmds = """
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
/math <equation> - Solve math
/id <user/channel> - Get ID
/tr <lang> <text> - Translate
/pdf <file> - Convert to PDF
/docx <file> - Convert to DOCX
/zip <file> - Compress
/unzip <file> - Unzip
/time <country> - Show time
"""
        await query.edit_message_text(cmds)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)  # reuse start for welcome & buttons

# ================= YT-DLP DOWNLOAD =================

async def ytdlp_download(update: Update, context: ContextTypes.DEFAULT_TYPE, url=None, audio=False):
    if not url and not context.args:
        return await update.message.reply_text("❌ No URL provided")
    if not url:
        url = context.args[0]
    out_path = os.path.join(TMP, "%(title)s.%(ext)s")
    opts = {"outtmpl": out_path}
    if audio:
        opts.update({"format":"bestaudio","postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":"mp3"}]})
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        info = yt_dlp.YoutubeDL({}).extract_info(url, download=False)
        file = yt_dlp.YoutubeDL(opts).prepare_filename(info)
        await update.message.reply_document(open(file, "rb"))
    except Exception as e:
        await update.message.reply_text(f"❌ Download failed: {e}")
    finally:
        cleanup(file)

# Short command wrappers
async def yt(update, context): await ytdlp_download(update, context)
async def ytc(update, context): await ytdlp_download(update, context)
async def mp3(update, context): await ytdlp_download(update, context, audio=True)
async def fa(update, context): await ytdlp_download(update, context)
async def tw(update, context): await ytdlp_download(update, context)
async def tk(update, context): await ytdlp_download(update, context)
async def tch(update, context): await ytdlp_download(update, context)
async def ig(update, context): await ytdlp_download(update, context)
async def igp(update, context): await ytdlp_download(update, context)
async def git(update, context): await ytdlp_download(update, context)

async def qr_cmd(update, context):
    if not context.args:
        return await update.message.reply_text("❌ No text provided")
    path = generate_qr(" ".join(context.args))
    await update.message.reply_photo(open(path,"rb"))
    cleanup(path)

async def math_cmd(update, context):
    try:
        eq = " ".join(context.args)
        result = sympify(eq)
        await update.message.reply_text(f"🧮 {eq} = {result}")
    except:
        await update.message.reply_text("❌ Invalid equation")

async def tr_cmd(update, context):
    try:
        lang = context.args[0]
        text = " ".join(context.args[1:])
        trans = translator.translate(text, dest=lang)
        await update.message.reply_text(f"🌐 {trans.text}")
    except:
        await update.message.reply_text("❌ Invalid usage")

async def id_cmd(update, context):
    if context.args:
        await update.message.reply_text(f"ID: {context.args[0]}")
    else:
        await update.message.reply_text(f"Your ID: {update.effective_user.id}")

async def time_cmd(update, context):
    if not context.args:
        return await update.message.reply_text("❌ Usage: /time <timezone>")
    tzname = context.args[0]
    try:
        tz = pytz.timezone(tzname)
        t = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        await update.message.reply_text(f"Time in {tzname}: {t}")
    except:
        await update.message.reply_text("❌ Invalid timezone")

# ================= OWNER COMMANDS =================

async def broadcast(update, context):
    if not owner_only(update.effective_user.id):
        return await update.message.reply_text("❌ Owner only.")
    msg = " ".join(context.args)
    for u in get_all_users():
        try:
            await context.bot.send_message(u, msg)
        except:
            pass
    await update.message.reply_text("✅ Broadcast sent.")

async def ban(update, context):
    if not owner_only(update.effective_user.id):
        return await update.message.reply_text("❌ Owner only.")
    try:
        user_to_ban = int(context.args[0])
        ban_user(user_to_ban)
        await update.message.reply_text(f"✅ Banned {user_to_ban}")
    except:
        await update.message.reply_text("❌ Invalid user ID")

async def unban(update, context):
    if not owner_only(update.effective_user.id):
        return await update.message.reply_text("❌ Owner only.")
    try:
        user_to_unban = int(context.args[0])
        unban_user(user_to_unban)
        await update.message.reply_text(f"✅ Unbanned {user_to_unban}")
    except:
        await update.message.reply_text("❌ Invalid user ID")

async def stats(update, context):
    if not owner_only(update.effective_user.id):
        return await update.message.reply_text("❌ Owner only.")
    await update.message.reply_text(f"✅ Total users: {count_users()}\n❌ Banned: {count_banned()}")

# ================= FLASK =================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

# ================= RUN BOT =================

def run_bot():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

    handlers = [  
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
        CommandHandler("broadcast", broadcast),
        CommandHandler("ban", ban),
        CommandHandler("unban", unban),
        CommandHandler("stats", stats),
        CallbackQueryHandler(button_callback),
    ]  
    
    for h in handlers:  
        app_bot.add_handler(h)  
    
    print("Bot running...")  
    app_bot.run_polling()

# ================= MAIN =================

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=5000)
