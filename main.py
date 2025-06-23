
import logging
import re
import requests
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHANNEL_API_MAPPING = {
    "C1": {
        "channels": ["https://t.me/sampleoftest", "@dealsduniyaloot"],
        "sankmo": "SANKMO_API_KEY",
        "earnkaro": "EARNKARO_API_KEY"
    },
    "C2": {
        "channels": ["@freedeals143", "@loot_deals143"],
        "sankmo": "SANKMO_API_KEY_C2",
        "earnkaro": "EARNKARO_API_KEY_C2"
    }
}

def convert_link(link: str, api_key: str) -> str:
    if "sank" in link:
        url = f"https://link.sankmo.com/api?api={api_key}&url={link}"
    elif "earn" in link:
        url = f"https://earnkaro.com/api?api={api_key}&url={link}"
    else:
        return link

    try:
        response = requests.get(url)
        data = response.json()
        return data.get("shortenedUrl", link)
    except Exception as e:
        logger.error(f"Error converting link: {e}")
        return link

def extract_affiliate_link(text: str) -> str:
    match = re.search(r'(https?://\S+)', text)
    return match.group(0) if match else ""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    user = message.from_user.username
    text = message.text
    chat_id = message.chat.id

    logger.info(f"Received message from {user}: {text}")

    target_config = None
    for config in CHANNEL_API_MAPPING.values():
        if f"@{user}" in config["channels"] or f"https://t.me/{user}" in config["channels"]:
            target_config = config
            break

    if not target_config:
        await message.reply_text("Unauthorized user or channel.")
        return

    aff_link = extract_affiliate_link(text)
    if not aff_link:
        await message.reply_text("No affiliate link found.")
        return

    api_key = target_config["sankmo"] if "sank" in aff_link else target_config["earnkaro"]
    converted_link = convert_link(aff_link, api_key)

    new_message = text.replace(aff_link, converted_link)
    for channel in target_config["channels"]:
        try:
            await context.bot.send_message(chat_id=channel, text=new_message)
        except Exception as e:
            logger.error(f"Failed to send message to {channel}: {e}")

def start_scheduler(application):
    scheduler = BackgroundScheduler()
    scheduler.start()

if __name__ == "__main__":
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    start_scheduler(application)
    application.run_polling()
