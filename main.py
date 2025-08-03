import logging
import json
import os
import re
import requests
from datetime import datetime, timedelta
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# --- Configuration ---
BOT_TOKEN = "YOUR_BOT_TOKEN"
OWNER_ID = 123456789  # Replace with your actual Telegram user ID
DATA_FILE = "data.json"

# --- Logging setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Functions ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "logs": {"links": 0}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def is_authorized(user_id):
    data = load_data()
    user = data["users"].get(str(user_id))
    if user:
        return datetime.now() < datetime.fromisoformat(user["expires"])
    return False

def shorten_link(original_link, tag):
    # Replace tag in the link
    if "tag=" in original_link:
        new_link = re.sub(r'tag=[^&]+', f'tag={tag}', original_link)
    else:
        separator = '&' if '?' in original_link else '?'
        new_link = f"{original_link}{separator}tag={tag}"

    api_link = f"https://individual-nanci-fhfhcd-8054f73b.koyeb.app/api?api=amazon&link={new_link}"
    try:
        response = requests.get(api_link, timeout=10)
        return response.text.strip()
    except:
        return "❌ Failed to process link."

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if not is_authorized(user_id):
        await update.message.reply_text(
            "❌ You are not authorised to use this bot.\n"
            "Kindly consult our team to start using this bot.\n"
            "Team Support - @amazonlinkshortnerrobot"
        )
        return

    user = data["users"].setdefault(user_id, {})
    if not user.get("tag") or not user.get("channel"):
        buttons = [
            [InlineKeyboardButton("Set Amazon Tag", callback_data="set_tag")],
            [InlineKeyboardButton("Set Channel", callback_data="set_channel")]
        ]
        await update.message.reply_text(
            "🛠 Setup Panel Of Amazon Link Shortner",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await update.message.reply_text("✅ You are ready to send links!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = load_data()
    user = data["users"].setdefault(user_id, {})

    await query.answer()
    if query.data == "set_tag":
        await query.message.reply_text("Please send your Amazon tag (e.g., mytag-21):")
        context.user_data["awaiting"] = "tag"
    elif query.data == "set_channel":
        await query.message.reply_text("Please forward a message from your channel.")
        context.user_data["awaiting"] = "channel"

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    user = data["users"].setdefault(user_id, {})

    if not is_authorized(user_id):
        return

    if context.user_data.get("awaiting") == "tag":
        user["tag"] = update.message.text.strip()
        await update.message.reply_text("✅ Amazon tag saved.")
        context.user_data.clear()
        save_data(data)
        return

    if context.user_data.get("awaiting") == "channel":
        if update.message.forward_from_chat:
            user["channel"] = update.message.forward_from_chat.id
            await update.message.reply_text("✅ Channel saved.")
            context.user_data.clear()
            save_data(data)
            return

    # Process Amazon links
    urls = re.findall(r'https?://[^\s]+', update.message.text or "")
    amazon_links = [url for url in urls if "amazon" in url]
    if not amazon_links:
        return

    if not user.get("tag") or not user.get("channel"):
        await update.message.reply_text("⚠️ Please complete setup first.")
        return

    modified_links = []
    for link in amazon_links:
        short = shorten_link(link, user["tag"])
        modified_links.append(short)
        data["logs"]["links"] += 1

    save_data(data)
    msg = update.message.text
    for old, new in zip(amazon_links, modified_links):
        msg = msg.replace(old, new)

    if update.message.photo:
        await context.bot.send_photo(chat_id=user["channel"], photo=update.message.photo[-1].file_id, caption=msg)
    else:
        await context.bot.send_message(chat_id=user["channel"], text=msg)

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /adduser <id> <days>")
        return

    uid, days = args
    data = load_data()
    expires = (datetime.now() + timedelta(days=int(days))).isoformat()
    data["users"][uid] = {
        "expires": expires,
        "joined": datetime.now().isoformat()
    }
    save_data(data)

    try:
        await context.bot.send_message(chat_id=int(uid), text=f"✅ You are now authorised.\nTime Period: {days} days.\nSend /start again.")
    except:
        await update.message.reply_text("User added but could not notify.")

    await update.message.reply_text(f"User {uid} added.")

async def reminder_job(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    for uid, info in data["users"].items():
        exp = datetime.fromisoformat(info["expires"])
        delta = (exp - datetime.now()).days
        if delta in [5, 3, 1]:
            try:
                await context.bot.send_message(chat_id=int(uid), text=f"⏳ Reminder: Your plan expires in {delta} days.")
            except:
                continue

async def statics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    data = load_data()
    total = len(data["users"])
    month = datetime.now().month
    new_this_month = sum(1 for u in data["users"].values()
                         if datetime.fromisoformat(u["joined"]).month == month)
    links = data["logs"]["links"]
    growth = round((new_this_month / total) * 100, 2) if total else 0

    await update.message.reply_text(
        f"📊 Statics:\n"
        f"Total Users This Month: {total}\n"
        f"New Users This Month: {new_this_month}\n"
        f"Links Converted: {links}\n"
        f"Growth Rate: {growth}%"
    )

async def details_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    data = load_data()
    msg = ""
    for uid, info in data["users"].items():
        msg += f"👤 {uid} → Channel: {info.get('channel', '❌')}\n"
    await update.message.reply_text(msg or "No users found.")

# --- Main App ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adduser", add_user))
    app.add_handler(CommandHandler("statics", statics))
    app.add_handler(CommandHandler("detailsuser", details_user))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL, message_handler))

    app.job_queue.run_repeating(reminder_job, interval=86400, first=5)

    app.run_polling()

if __name__ == "__main__":
    main()
