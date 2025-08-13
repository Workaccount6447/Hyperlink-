import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import datetime
import json

# ==== CONFIG ====
BOT_TOKEN = "8009237833:AAH93dARRAJXkqoS0l3iHfMn3pFPDWL2kYY"
OWNER_ID = 7588665244
DB_URL = "https://kvdb.io/BPkErVJ1RUwQA1brf928qK"
API_URL = "https://managing-pippy-fhfhcd-af2e08fb.koyeb.app/api?api=deepak&link="
# ================

# Database helper
def db_set(key, value):
    requests.post(f"{DB_URL}/{key}", data=json.dumps(value))

def db_get(key):
    res = requests.get(f"{DB_URL}/{key}")
    if res.status_code == 200 and res.text.strip():
        return json.loads(res.text)
    return None

def is_premium(user_id):
    data = db_get(f"user_{user_id}")
    if not data:
        return False
    expiry = datetime.datetime.fromisoformat(data["expiry"])
    return datetime.datetime.now() < expiry

# Commands
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_premium(user_id):
        await update.message.reply_text("You are not authorised to use the bot.\nContact admin: @AmazonLinkShortnerRobot")
        return
    
    user_data = db_get(f"user_{user_id}")
    if not user_data.get("setup_done", False):
        keyboard = [
            [InlineKeyboardButton("Set Amazon Tag", callback_data="set_tag")],
            [InlineKeyboardButton("Channel Setup", callback_data="set_channel")],
            [InlineKeyboardButton("Add Your Private Bot", callback_data="set_token")]
        ]
        await update.message.reply_text(
            "Setup Panel",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("Welcome back! Send me an Amazon link.")

async def add_user(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        return
    try:
        user_id = int(context.args[0])
        days = int(context.args[1])
    except:
        await update.message.reply_text("Usage: /add <user_id> <days>")
        return
    
    expiry = datetime.datetime.now() + datetime.timedelta(days=days)
    db_set(f"user_{user_id}", {"expiry": expiry.isoformat(), "setup_done": False})
    await context.bot.send_message(
        chat_id=user_id,
        text=f"You are now able to use this bot.\nTutorial - Coming Soon\nExpires After {days} days"
    )
    await update.message.reply_text(f"User {user_id} added for {days} days.")

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "set_tag":
        await query.edit_message_text("Please send your Amazon tag (e.g., Prashant75-21).")
        db_set(f"user_{user_id}_step", {"step": "tag"})
    elif data == "set_channel":
        await query.edit_message_text("Send me your channel ID.\nUse @username_to_id_bot to get it.")
        db_set(f"user_{user_id}_step", {"step": "channel"})
    elif data == "set_token":
        await query.edit_message_text("Send me your bot token.")
        db_set(f"user_{user_id}_step", {"step": "token"})

async def text_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    step_data = db_get(f"user_{user_id}_step")
    msg = update.message.text.strip()

    if step_data:
        step = step_data["step"]
        if step == "tag":
            user_data = db_get(f"user_{user_id}") or {}
            user_data["tag"] = msg
            db_set(f"user_{user_id}", user_data)
            await update.message.reply_text("Amazon tag saved.")
        elif step == "channel":
            user_data = db_get(f"user_{user_id}") or {}
            user_data["channel_id"] = msg
            db_set(f"user_{user_id}", user_data)
            await update.message.reply_text("Channel ID saved.")
        elif step == "token":
            user_data = db_get(f"user_{user_id}") or {}
            user_data["bot_token"] = msg
            db_set(f"user_{user_id}", user_data)
            await update.message.reply_text("Bot token saved.\nSetup complete!")
            user_data["setup_done"] = True
            db_set(f"user_{user_id}", user_data)
        db_set(f"user_{user_id}_step", {})  # clear step
        return
    
    # Process Amazon link
    if "amazon" in msg.lower():
        user_data = db_get(f"user_{user_id}")
        if not user_data or "tag" not in user_data:
            await update.message.reply_text("Please complete setup first.")
            return
        # Replace tag and shorten
        modified_link = msg.split("?")[0] + f"?tag={user_data['tag']}"
        short_link = requests.get(API_URL + modified_link).text.strip()
        await update.message.reply_text(short_link)
        if "channel_id" in user_data:
            await context.bot.send_message(chat_id=user_data["channel_id"], text=short_link)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_user))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app.run_polling()
