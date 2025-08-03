import os
import json
import logging
import re
import requests
from datetime import datetime, timedelta

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OWNER_ID = 7588665244  # Replace with your actual Telegram user ID
DATA_FILE = "users.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        await update.message.reply_text(
            "You are not authorised to use this bot.\nKindly consult our team.\nSupport: @amazonlinkshortnerrobot"
        )
        return

    user = data[user_id]
    if datetime.now() > datetime.fromisoformat(user["expiry"]):
        await update.message.reply_text("Your subscription has expired. Contact support.")
        return

    keyboard = [
        [InlineKeyboardButton("Set Amazon Tag", callback_data="set_tag")],
        [InlineKeyboardButton("Set Channel", callback_data="set_channel")]
    ]
    await update.message.reply_text("Setup Panel Of Amazon Link Shortener", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    context.user_data["awaiting"] = query.data
    if query.data == "set_tag":
        await query.edit_message_text("Send your Amazon tag (e.g., tagname-21)")
    elif query.data == "set_channel":
        await query.edit_message_text("Forward a message from your channel (where bot is admin).")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        return

    if "awaiting" in context.user_data:
        key = context.user_data.pop("awaiting")
        if key == "set_tag":
            data[user_id]["tag"] = update.message.text.strip()
            await update.message.reply_text("Amazon tag set successfully.")
        elif key == "set_channel":
            if update.message.forward_from_chat:
                data[user_id]["channel"] = update.message.forward_from_chat.id
                await update.message.reply_text("Channel saved successfully.")
        save_data(data)
        return

    # Process Amazon link
    urls = re.findall(r'(https?://\S+)', update.message.text)
    for url in urls:
        expanded = expand_link(url)
        if is_amazon_link(expanded):
            user = data[user_id]
            tag = user.get("tag", "defaulttag-21")
            new_url = replace_tag(expanded, tag)
            short = shorten_amazon(new_url)
            if short:
                text = update.message.text.replace(url, short)
                if "channel" in user:
                    await context.bot.send_message(user["channel"], text)
                await update.message.reply_text("Link processed.")
                return

    await update.message.reply_text("No valid Amazon link found.")

def expand_link(link):
    try:
        r = requests.head(link, allow_redirects=True, timeout=5)
        return r.url
    except:
        return link

def is_amazon_link(url):
    return "amazon." in url

def replace_tag(url, new_tag):
    return re.sub(r'tag=[^&]+', f'tag={new_tag}', url) if 'tag=' in url else f"{url}&tag={new_tag}"

def shorten_amazon(link):
    api_url = f"https://individual-nanci-fhfhcd-8054f73b.koyeb.app/api?api=amazon&link={link}"
    try:
        r = requests.get(api_url)
        return r.text.strip()
    except:
        return None

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    try:
        user_id = context.args[0]
        days = int(context.args[1])
        data = load_data()
        expiry = datetime.now() + timedelta(days=days)
        data[user_id] = {
            "expiry": expiry.isoformat()
        }
        save_data(data)
        await update.message.reply_text(f"User {user_id} added. Valid for {days} days.")
        await context.bot.send_message(
            chat_id=int(user_id),
            text=f"You are now authorised. Time Period - {days} days.\nSend /start again."
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    data = load_data()
    now = datetime.now()
    this_month = [u for u in data.values() if datetime.fromisoformat(u['expiry']).month == now.month]
    total = len(data)
    new_this_month = len(this_month)
    growth = (new_this_month / total) * 100 if total else 0

    await update.message.reply_text(
        f"📊 Stats:\nTotal Users: {total}\nNew This Month: {new_this_month}\nLinks Converted: (counting skipped)\nGrowth: {growth:.2f}%"
    )

async def details_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    data = load_data()
    text = ""
    for uid, d in data.items():
        channel = d.get("channel", "N/A")
        tag = d.get("tag", "N/A")
        expiry = d.get("expiry", "N/A")
        text += f"👤 ID: {uid}\n📺 Channel: {channel}\n🏷️ Tag: {tag}\n⏳ Expiry: {expiry}\n\n"

    await update.message.reply_text(text or "No users found.")

async def reminder_check(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    now = datetime.now()
    for user_id, u in data.items():
        expiry = datetime.fromisoformat(u["expiry"])
        if 0 < (expiry - now).days <= 5:
            try:
                await context.bot.send_message(
                    chat_id=int(user_id),
                    text=f"⚠️ Your subscription expires in {(expiry - now).days} days. Please renew soon."
                )
            except:
                continue

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable not set.")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adduser", add_user))
    app.add_handler(CommandHandler("statistics", statistics))
    app.add_handler(CommandHandler("detailsuser", details_user))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Set up reminder job
    app.job_queue.run_repeating(reminder_check, interval=86400, first=10)

    app.run_polling()

if __name__ == "__main__":
    main()
        
