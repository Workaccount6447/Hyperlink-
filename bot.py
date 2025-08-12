import os
import re
import requests
import json
import time
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# ENV Variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "8009237833:AAH93dARRAJXkqoS0l3iHfMn3pFPDWL2kYY")
OWNER_ID = int(os.getenv("OWNER_ID", 7588665244))  # Replace with your Telegram ID
KVDB_BUCKET = "https://kvdb.io/BPkErVJ1RUwQA1brf928qK/"
API_URL = "https://managing-pippy-fhfhcd-af2e08fb.koyeb.app/api?api=deepak&link="

# ---------------- DATABASE HELPERS ---------------- #
def db_set(key, value):
    return requests.post(KVDB_BUCKET + key, data=json.dumps(value))

def db_get(key):
    r = requests.get(KVDB_BUCKET + key)
    if r.status_code == 200 and r.text:
        try:
            return json.loads(r.text)
        except:
            return r.text
    return None

def db_delete(key):
    return requests.delete(KVDB_BUCKET + key)

# ---------------- COMMANDS ---------------- #
async def start(update, context):
    user_id = update.effective_user.id
    user_data = db_get(f"user_{user_id}")

    if not user_data:
        await update.message.reply_text(
            "You are not authorised to use the bot.\n"
            "To authorise to use this bot contact our admin team @AmazonLinkShortnerRobot"
        )
        return

    # Check expiration
    expiry = datetime.fromtimestamp(user_data["expiry"])
    if datetime.now() > expiry:
        db_delete(f"user_{user_id}")
        await update.message.reply_text(
            "Your premium plan has expired.\nContact @AmazonLinkShortnerRobot to renew."
        )
        return

    # First time after becoming premium → Show setup panel
    if not user_data.get("setup_done", False):
        keyboard = [
            [InlineKeyboardButton("Set Amazon Tag", callback_data="set_tag")],
            [InlineKeyboardButton("Channel Setup", callback_data="set_channel")],
            [InlineKeyboardButton("Add Your Private Bot", callback_data="set_bot")]
        ]
        await update.message.reply_text(
            "Setup Panel:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("Welcome back! Send me your Amazon link.")

async def add_user(update, context):
    if update.effective_user.id != OWNER_ID:
        return

    try:
        target_id = int(context.args[0])
        days = int(context.args[1])
    except:
        await update.message.reply_text("Usage: /add <user_id> <days>")
        return

    expiry = datetime.now() + timedelta(days=days)
    db_set(f"user_{target_id}", {"expiry": expiry.timestamp(), "setup_done": False})

    await update.message.reply_text(f"User {target_id} added for {days} days.")
    await context.bot.send_message(
        chat_id=target_id,
        text=(
            "You are now able to use this bot.\n"
            "Tutorial - Coming Soon\n"
            f"Expires After {days} days"
        )
    )

async def button_handler(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    user_data = db_get(f"user_{user_id}")

    if query.data == "set_tag":
        await query.message.reply_text("Please send your Amazon tag (e.g., Prashant75-21).")
        context.user_data["awaiting_tag"] = True

    elif query.data == "set_channel":
        await query.message.reply_text(
            "Send me your channel ID.\nUse @username_to_id_bot to get your channel ID."
        )
        context.user_data["awaiting_channel"] = True

    elif query.data == "set_bot":
        await query.message.reply_text("Please send your bot token.")
        context.user_data["awaiting_bot"] = True

async def text_handler(update, context):
    user_id = update.effective_user.id
    text = update.message.text
    user_data = db_get(f"user_{user_id}")

    if not user_data:
        return

    # Capture setup inputs
    if context.user_data.get("awaiting_tag"):
        user_data["tag"] = text.strip()
        context.user_data["awaiting_tag"] = False
        db_set(f"user_{user_id}", user_data)
        await update.message.reply_text("Amazon tag saved.")

    elif context.user_data.get("awaiting_channel"):
        user_data["channel_id"] = text.strip()
        context.user_data["awaiting_channel"] = False
        db_set(f"user_{user_id}", user_data)
        await update.message.reply_text("Channel ID saved.")

    elif context.user_data.get("awaiting_bot"):
        token = text.strip()
        # Validate token
        try:
            test_bot = Application.builder().token(token).build()
            # Assume token is valid for simplicity
            user_data["bot_token"] = token
            user_data["setup_done"] = True
            db_set(f"user_{user_id}", user_data)
            await update.message.reply_text(
                "Your Setup Panel is completed. You can now use this bot.\n"
                "Don't forget to renew your plan."
            )
        except:
            await update.message.reply_text("Invalid Bot Token.")

    else:
        # Handle Amazon link replacement
        amazon_pattern = r"(https?://[^\s]+)"
        links = re.findall(amazon_pattern, text)
        if not links:
            return

        new_text = text
        for link in links:
            if "amazon." not in link:
                continue
            # Replace tag
            link = re.sub(r"tag=[^&]+", f"tag={user_data.get('tag', '')}", link)
            # Shorten via API
            r = requests.get(API_URL + link)
            if r.status_code == 200:
                short_link = r.text.strip()
                new_text = new_text.replace(link, short_link)

        await update.message.reply_text(new_text)
        # Send to user's channel via their bot
        if user_data.get("channel_id") and user_data.get("bot_token"):
            try:
                requests.post(
                    f"https://api.telegram.org/bot{user_data['bot_token']}/sendMessage",
                    data={"chat_id": user_data["channel_id"], "text": new_text}
                )
            except:
                pass

# ---------------- MAIN ---------------- #
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_user))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
