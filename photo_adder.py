import logging
import requests
import re
import json
import asyncio
import traceback

from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, filters
from PIL import Image
from io import BytesIO
from aiohttp import web  # For Koyeb health check

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- Configuration ---
OWNER_ID = 7588665244
BOT_TOKEN = "7903608399:AAGxBNWuFGKHUv3J0poHKR8-vd-IIC--odU"
ACCESS_FILE = "access.json"
HEALTH_PORT = 8000

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Access Control ---
def load_access():
    try:
        with open(ACCESS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_access(data):
    with open(ACCESS_FILE, "w") as f:
        json.dump(data, f)

user_access = load_access()

# --- Command Handlers ---
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_access.get(str(user_id), False):
        await update.message.reply_text("Send a product link, and I'll process it with a screenshot!")
    else:
        await update.message.reply_text("You are not authorized. Pay ₹100 and send proof to @Toolsforaffilatesupportbot.")

async def grant_access(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == OWNER_ID:
        if context.args:
            user_id = context.args[0]
            user_access[str(user_id)] = True
            save_access(user_access)
            await update.message.reply_text(f"Access granted to user {user_id}.")
        else:
            await update.message.reply_text("Usage: /grant_access <user_id>")
    else:
        await update.message.reply_text("You are not authorized.")

async def block_user(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == OWNER_ID:
        if context.args:
            user_id = context.args[0]
            user_access[str(user_id)] = False
            save_access(user_access)
            await update.message.reply_text(f"User {user_id} has been blocked.")
        else:
            await update.message.reply_text("Usage: /block_user <user_id>")
    else:
        await update.message.reply_text("You are not authorized.")

async def list_users(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == OWNER_ID:
        allowed = [uid for uid, v in user_access.items() if v]
        await update.message.reply_text(f"Allowed users: {allowed}")
    else:
        await update.message.reply_text("You are not authorized.")

# --- Message Handlers ---
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if not user_access.get(str(user_id), False):
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    user_message = update.message.text
    url_match = re.search(r'(https?://\S+)', user_message)

    if not url_match:
        await update.message.reply_text("Please send a valid product link.")
        return

    extracted_url = url_match.group(0)
    remaining_text = user_message.replace(extracted_url, '', 1).strip()
    await update.message.reply_text("Processing your link...")

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.post(
            "https://mypricehistory.com/product/boat-airdopes-91-45hrs-battery-50ms-low-latency-enx-tech-fast-charge-ipx4-iwp-tech-v5-3-bluetooth-earbuds-tws-ear-buds-wireless-earphones-with-mic-active-black-P0TSB8H8ORHN",
            data={'link': extracted_url}, headers=headers, timeout=10)

        if response.status_code == 200:
            reply_text = "Link sent successfully!"
            if remaining_text:
                reply_text += f"\n\nNote: {remaining_text}"

            img = await take_screenshot_and_crop(extracted_url, (272, 516, 272 + 270, 516 + 183))
            if img:
                await context.bot.send_photo(chat_id=update.message.chat_id, photo=InputFile(img, filename="screenshot.png"), caption=reply_text)
            else:
                await update.message.reply_text(reply_text + "\nBut screenshot failed.")
        else:
            await update.message.reply_text(f"Failed to process link. Status: {response.status_code}")
    except Exception as e:
        logger.error(f"Processing error: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"Error occurred: {str(e)}")

async def handle_photo(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if not user_access.get(str(user_id), False):
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    photo = update.message.photo[-1]
    photo_file = await photo.get_file()
    photo_bytes = await photo_file.download_as_bytearray()

    try:
        img = Image.open(BytesIO(photo_bytes)).convert("RGB")
        output = BytesIO()
        img.save(output, format="PNG")
        output.seek(0)

        await context.bot.send_document(
            chat_id=update.message.chat_id,
            document=InputFile(output, filename="converted_image.png"),
            caption="Here is your image converted to PNG."
        )
    except Exception as e:
        logger.error(f"Image conversion error: {e}")
        await update.message.reply_text("Failed to convert the image.")

# --- Screenshot Utility ---
def crop_image(image: Image, dimensions: tuple) -> Image:
    return image.crop(dimensions)

async def take_screenshot_and_crop(url: str, crop_dimensions: tuple) -> BytesIO | None:
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(10)

        try:
            driver.get(url)
            driver.set_window_size(1280, 1024)
            await asyncio.sleep(3)

            png = BytesIO(driver.get_screenshot_as_png())
            image = Image.open(png)
            cropped = crop_image(image, crop_dimensions)
            result = BytesIO()
            cropped.save(result, format='PNG')
            result.seek(0)
            return result
        finally:
            driver.quit()
    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        return None

# --- Koyeb Health Check ---
async def healthcheck(request):
    return web.Response(text="Bot is alive!")

async def start_health_server():
    app = web.Application()
    app.router.add_get("/", healthcheck)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=HEALTH_PORT)
    await site.start()
    logger.info(f"Health check running on port {HEALTH_PORT}")

# --- Main Entry ---
async def main():
    import nest_asyncio
    nest_asyncio.apply()

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("grant_access", grant_access))
    application.add_handler(CommandHandler("block_user", block_user))
    application.add_handler(CommandHandler("list_users", list_users))

    # Message Handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    await start_health_server()

    await application.run_polling()

if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    try:
        loop.create_task(main())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

    
