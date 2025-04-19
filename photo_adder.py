import logging
import re
import asyncio
import json
import time
import traceback

from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, filters
from PIL import Image
from io import BytesIO
import nest_asyncio  # for environments with running event loops

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

OWNER_ID = 7588665244  # Replace with your own Telegram user ID
ACCESS_FILE = "access.json"

# Load access control list
def load_access():
    try:
        with open(ACCESS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save access control list
def save_access(access_data):
    with open(ACCESS_FILE, "w") as f:
        json.dump(access_data, f)

user_access = load_access()

# Bot start command
async def start(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    if user_id not in user_access:
        user_access[user_id] = {"access": False}
        save_access(user_access)
    await update.message.reply_text("Welcome! Please wait for access to be granted.")

# Grant access command
async def grant_access(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /grant_access <user_id>")
        return
    user_id = context.args[0]
    user_access[user_id] = {"access": True}
    save_access(user_access)
    await update.message.reply_text(f"Access granted to {user_id}")

# Block user command
async def block_user(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /block_user <user_id>")
        return
    user_id = context.args[0]
    if user_id in user_access:
        user_access[user_id]["access"] = False
        save_access(user_access)
        await update.message.reply_text(f"User {user_id} blocked.")

# List users command
async def list_users(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        return
    msg = "Users:\n"
    for uid, info in user_access.items():
        msg += f"{uid} - {'Access' if info.get('access') else 'Blocked'}\n"
    await update.message.reply_text(msg)

# Handle URL messages
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    if user_id not in user_access or not user_access[user_id].get("access"):
        await update.message.reply_text("Access denied.")
        return

    url = update.message.text.strip()
    if not re.match(r'^https?://', url):
        await update.message.reply_text("Please send a valid URL.")
        return

    await update.message.reply_text("Taking screenshot...")

    try:
        # Crop rectangle (X=272, Y=516, Width=270, Height=183) => (left, upper, right, lower)
        screenshot = await take_screenshot_and_crop(url, (272, 516, 542, 699))
        if screenshot:
            await update.message.reply_photo(photo=InputFile(screenshot, filename="screenshot.jpg"))
        else:
            await update.message.reply_text("Failed to take screenshot.")
    except Exception as e:
        logger.error(traceback.format_exc())
        await update.message.reply_text("Error occurred during processing.")

# Dummy photo handler
async def handle_photo(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("This bot only handles text URLs.")

# Cropping function
def crop_image(image: Image, crop_dimensions: tuple) -> Image:
    return image.crop(crop_dimensions)

# Screenshot and crop
async def take_screenshot_and_crop(url: str, crop_dimensions: tuple) -> BytesIO | None:
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1280,1024")

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(15)
        driver.get(url)
        time.sleep(3)

        screenshot = driver.get_screenshot_as_png()
        driver.quit()

        image = Image.open(BytesIO(screenshot)).convert("RGB")
        cropped = crop_image(image, crop_dimensions)

        output = BytesIO()
        cropped.save(output, format="JPEG", quality=90)
        output.seek(0)

        return output

    except (WebDriverException, TimeoutException) as e:
        logger.error(f"WebDriver error: {e}")
        return None

# Run bot
async def main(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("grant_access", grant_access))
    application.add_handler(CommandHandler("block_user", block_user))
    application.add_handler(CommandHandler("list_users", list_users))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    await application.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()  # Fix for running inside environments with running event loop

    application = ApplicationBuilder().token("7864703583:AAGqZInSK2tp8Jykwpte7Ng0iunmYLlRwms").build()
    user_access = load_access()

    asyncio.run(main(application))
    
