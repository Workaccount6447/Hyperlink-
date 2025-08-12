import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
import time
import requests

# ==== HARDCODED CONFIG ====
BOT_TOKEN = "8009237833:AAH93dARRAJXkqoS0l3iHfMn3pFPDWL2kYY"
OWNER_ID = 7588665244
KVDB_BUCKET = "BPkErVJ1RUwQA1brf928qK"
SHORT_API = "https://managing-pippy-fhfhcd-af2e08fb.koyeb.app/api?api=deepak&link="
KVDB_BASE = f"https://kvdb.io/{KVDB_BUCKET}"

# ==== DATABASE HELPERS ====
def kvdb_set(key, value):
    requests.post(f"{KVDB_BASE}/{key}", data=str(value))

def kvdb_get(key):
    r = requests.get(f"{KVDB_BASE}/{key}")
    return r.text if r.status_code == 200 else None

# ==== BOT HANDLERS ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    expiry = kvdb_get(f"user:{user_id}:expiry")

    if not expiry:
        await update.message.reply_text(
            "🚫 You are not authorised to use the bot.\n"
            "To authorise, contact our admin team @AmazonLinkShortnerRobot"
        )
        return

    if int(expiry) < int(time.time()):
        await update.message.reply_text("⏳ Your premium plan has expired.")
        return

    await update.message.reply_text(
        "⚙️ Setup Panel",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Set Amazon Tag", callback_data="set_tag")],
            [InlineKeyboardButton("Channel Setup", callback_data="set_channel")],
            [InlineKeyboardButton("Add your private Bot", callback_data="set_bot")]
        ])
    )

async def add_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /add <user_id> <days>")
        return
    uid = context.args[0]
    days = int(context.args[1])
    expiry = int(time.time()) + days * 86400
    kvdb_set(f"user:{uid}:expiry", expiry)
    await context.bot.send_message(
        uid,
        f"✅ You are now able to use this bot.\nTutorial - Coming Soon\nExpires After {days} days"
    )
    await update.message.reply_text(f"User {uid} added for {days} days.")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "set_tag":
        await query.edit_message_text("Please send your Amazon tag (e.g., Prashant75-21).")
        context.user_data["awaiting"] = "tag"

    elif query.data == "set_channel":
        await query.edit_message_text(
            "Send me your channel ID.\nUse @username_to_id_bot to get it."
        )
        context.user_data["awaiting"] = "channel"

    elif query.data == "set_bot":
        await query.edit_message_text("Send your bot token.")
        context.user_data["awaiting"] = "bot"

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    expiry = kvdb_get(f"user:{user_id}:expiry")
    if not expiry or int(expiry) < int(time.time()):
        return

    awaiting = context.user_data.get("awaiting")

    if awaiting == "tag":
        kvdb_set(f"user:{user_id}:tag", update.message.text.strip())
        await update.message.reply_text("✅ Amazon tag saved.")
        context.user_data.pop("awaiting")

    elif awaiting == "channel":
        kvdb_set(f"user:{user_id}:channel", update.message.text.strip())
        await update.message.reply_text("✅ Channel saved.")
        context.user_data.pop("awaiting")

    elif awaiting == "bot":
        token = update.message.text.strip()
        kvdb_set(f"user:{user_id}:bottoken", token)
        await update.message.reply_text("✅ Bot token saved. Setup completed.")
        context.user_data.pop("awaiting")

    else:
        # Replace Amazon tag in links
        text = update.message.text
        tag = kvdb_get(f"user:{user_id}:tag")
        if tag:
            amazon_link = extract_amazon_link(text)
            if amazon_link:
                new_link = replace_tag_and_shorten(amazon_link, tag)
                if new_link:
                    text = text.replace(amazon_link, new_link)
        await update.message.reply_text(text)

def extract_amazon_link(text):
    match = re.search(r"(https?://[^\s]+amazon\.[^\s]+)", text)
    return match.group(1) if match else None

def replace_tag_and_shorten(link, new_tag):
    # Replace tag
    link = re.sub(r"tag=[^&]+", f"tag={new_tag}", link)
    # Shorten
    try:
        resp = requests.get(SHORT_API + link)
        if resp.status_code == 200:
            return resp.text.strip()
    except:
        pass
    return link

# ==== FLASK APP ====
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Bot is running."

# ==== START BOT THREAD ====
def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_premium))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
