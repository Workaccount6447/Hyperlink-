import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler, filters
import datetime
import json

# === CONFIG ===
BOT_TOKEN = "8009237833:AAH93dARRAJXkqoS0l3iHfMn3pFPDWL2kYY"
OWNER_ID = 7588665244
DB_URL = "https://kvdb.io/BPkErVJ1RUwQA1brf928qK"
API_URL = "https://managing-pippy-fhfhcd-af2e08fb.koyeb.app/api?api=deepak&link="
# ==============

# Database
def db_set(key, value):
    requests.post(f"{DB_URL}/{key}", data=json.dumps(value))

def db_get(key):
    r = requests.get(f"{DB_URL}/{key}")
    if r.status_code == 200 and r.text.strip():
        return json.loads(r.text)
    return None

def is_premium(uid):
    data = db_get(f"user_{uid}")
    if not data:
        return False
    exp = datetime.datetime.fromisoformat(data["expiry"])
    return datetime.datetime.now() < exp

# Commands
async def start(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    if not is_premium(uid):
        await update.message.reply_text(
            "You are not authorised to use the bot.\nContact admin: @AmazonLinkShortnerRobot"
        )
        return
    data = db_get(f"user_{uid}")
    if not data.get("setup_done", False):
        kb = [
            [InlineKeyboardButton("Set Amazon Tag", callback_data="set_tag")],
            [InlineKeyboardButton("Channel Setup", callback_data="set_channel")],
            [InlineKeyboardButton("Add Your Private Bot", callback_data="set_token")]
        ]
        await update.message.reply_text("Setup Panel", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text("Welcome back! Send me an Amazon link.")

async def add(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        return
    try:
        uid = int(context.args[0])
        days = int(context.args[1])
    except:
        await update.message.reply_text("Usage: /add <user_id> <days>")
        return
    exp = datetime.datetime.now() + datetime.timedelta(days=days)
    db_set(f"user_{uid}", {"expiry": exp.isoformat(), "setup_done": False})
    await context.bot.send_message(uid, f"You can now use this bot.\nExpires in {days} days.")
    await update.message.reply_text(f"User {uid} added for {days} days.")

async def button_handler(update: Update, context: CallbackContext):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if q.data == "set_tag":
        db_set(f"user_{uid}_step", {"step": "tag"})
        await q.edit_message_text("Send your Amazon tag (e.g., mytag-21)")
    elif q.data == "set_channel":
        db_set(f"user_{uid}_step", {"step": "channel"})
        await q.edit_message_text("Send your channel ID")
    elif q.data == "set_token":
        db_set(f"user_{uid}_step", {"step": "token"})
        await q.edit_message_text("Send your bot token")

async def text_handler(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    step = db_get(f"user_{uid}_step")
    msg = update.message.text.strip()

    if step:
        user_data = db_get(f"user_{uid}") or {}
        if step["step"] == "tag":
            user_data["tag"] = msg
            await update.message.reply_text("Tag saved.")
        elif step["step"] == "channel":
            user_data["channel_id"] = msg
            await update.message.reply_text("Channel saved.")
        elif step["step"] == "token":
            user_data["bot_token"] = msg
            await update.message.reply_text("Token saved. Setup complete!")
            user_data["setup_done"] = True
        db_set(f"user_{uid}", user_data)
        db_set(f"user_{uid}_step", {})
        return

    if "amazon" in msg.lower():
        user_data = db_get(f"user_{uid}")
        if not user_data or "tag" not in user_data:
            await update.message.reply_text("Setup first.")
            return
        link = msg.split("?")[0] + f"?tag={user_data['tag']}"
        short = requests.get(API_URL + link).text.strip()
        await update.message.reply_text(short)
        if "channel_id" in user_data:
            await context.bot.send_message(user_data["channel_id"], short)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling()
