import logging
import requests
import re
import asyncio
import json
import time
import traceback

from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, filters
from PIL import Image
from io import BytesIO

# Selenium imports (for screenshotting)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Set your bot's owner ID (replace with your actual Telegram user ID)
OWNER_ID = 7588665244  # Replace with your Telegram user ID

# File to store user access data
ACCESS_FILE = "access.json"

# Load user access from file
def load_access():
    try:
        with open(ACCESS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save user access to file
def save_access(access_data):
    with open(ACCESS_FILE, "w") as f:
        json.dump(access_data, f)

# Global variable to store user access
user_access = load_access()

# Define a function to handle messages
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_access.get(user_id, False):  # Check if user has access
        user_message = update.message.text

        # Find the first valid URL in the message
        url_match = re.search(r'(https?://\S+)', user_message)

        if url_match:
            extracted_url = url_match.group(0)
            remaining_text = user_message.replace(extracted_url, '', 1).strip() # Remove the URL and any extra whitespace

            await update.message.reply_text("Processing the link...")

            try:
                # Example: Send the link to a website (replace with your actual website)
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.post("https://mypricehistory.com/product/boat-airdopes-91-45hrs-battery-50ms-low-latency-enx-tech-fast-charge-ipx4-iwp-tech-v5-3-bluetooth-earbuds-tws-ear-buds-wireless-earphones-with-mic-active-black-P0TSB8H8ORHN", data={'link': extracted_url}, headers=headers, timeout=10) # Add timeout

                # Check if the request was successful
                if response.status_code == 200:
                    reply_text = "Link sent successfully!"
                    if remaining_text:
                        reply_text += f"\n\nAdditional text: {remaining_text}"

                    # Take a screenshot
                    img_byte_arr = await take_screenshot_and_crop(extracted_url, (0, 0, 800, 600)) # Example crop
                    if img_byte_arr:
                        await context.bot.send_photo(chat_id=update.message.chat_id, photo=InputFile(img_byte_arr, filename="screenshot.png"), caption=reply_text)
                    else:
                         await update.message.reply_text(f"Link sent. {reply_text}. But screenshot Failed!")

                else:
                    await update.message.reply_text(f"Failed to send the link. Status code: {response.status_code}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}\n{traceback.format_exc()}")
                await update.message.reply_text(f"Error: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}\n{traceback.format_exc()}")
                await update.message.reply_text("An unexpected error occurred.")

        else:
            await update.message.reply_text("Please send a valid link.")
    else:
        await update.message.reply_text("You are not authorized to access this bot. Firstly Paid ₹100 to the owner of the bot and send proof to @Toolsforaffilatesupportbot and wait for the response when our owner comes online it will gives access to you and notifies you . Kindly Be Patient. We Respect Your Patinent .")

# Define a function to start the bot
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_access.get(user_id, False):
        await update.message.reply_text("Send me a link (you can add some text before or after) and I'll process the link!")
    else:
        await update.message.reply_text("You do not have access to use this bot.")

# Owner commands
async def grant_access(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == OWNER_ID:
        if context.args:
            try:
                user_id = int(context.args[0])
                user_access[user_id] = True
                save_access(user_access)  # Save to file
                await update.message.reply_text(f"Access granted to user {user_id}.")
            except ValueError:
                await update.message.reply_text("Please provide a valid user ID.")
        else:
            await update.message.reply_text("Please provide a user ID to grant access.")
    else:
        await update.message.reply_text("You are not authorized to use this command.")

async def block_user(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == OWNER_ID:
        if context.args:
            try:
                user_id = int(context.args[0])
                user_access[user_id] = False
                save_access(user_access)  # Save to file
                await update.message.reply_text(f"User {user_id} has been blocked.")
            except ValueError:
                await update.message.reply_text("Please provide a valid user ID.")
        else:
            await update.message.reply_text("Please provide a user ID to block.")
    else:
        await update.message.reply_text("You are not authorized to use this command.")

async def list_users(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == OWNER_ID:
        access_granted_users = [user_id for user_id, access in user_access.items() if access]
        await update.message.reply_text(f"Users with access: {access_granted_users}")
    else:
        await update.message.reply_text("You are not authorized to use this command.")

# Function to crop an image
def crop_image(image: Image, crop_dimensions: tuple) -> Image:
    try:
        return image.crop(crop_dimensions)
    except Exception as e:
        logger.error(f"Error cropping image: {e}")
        return image

# Function to take a screenshot and crop it
async def take_screenshot_and_crop(url: str, crop_dimensions: tuple) -> BytesIO | None:
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run Chrome in headless mode (no GUI)
        chrome_options.add_argument("--no-sandbox")  # Required for running in some environments (e.g., Docker)
        chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems

        driver = webdriver.Chrome(options=chrome_options)

        driver.set_page_load_timeout(10)  # Timeout for page load
        driver.set_script_timeout(10) # Timeout for Javascript

        try:
            driver.get(url)
            driver.set_window_size(1280, 1024)  # Set an appropriate window size
            # Wait a bit for the page to load (adjust the time as needed)
            await asyncio.sleep(3)

            # Take the screenshot
            img_byte_arr = BytesIO(driver.get_screenshot_as_png())
            img_byte_arr.seek(0)

            image = Image.open(img_byte_arr)
            cropped_image = crop_image(image, crop_dimensions)
            img_byte_arr = BytesIO() # Reset BytesIO for storing the cropped image.
            cropped_image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            return img_byte_arr

        except TimeoutException as e:
            logger.error(f"Timeout Exception taking screenshot of {url}: {e}\n{traceback.format_exc()}")
            return None

        finally:
            driver.quit() # Close the browser
    except WebDriverException as e:
        logger.error(f"WebDriverException taking screenshot of {url}: {e}\n{traceback.format_exc()}")
        return None
    except Exception as e:
        logger.error(f"Error taking screenshot of {url}: {e}\n{traceback.format_exc()}")
        return None

# Define a handler for sending a photo with the original link and text
async def handle_photo(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_access.get(user_id, False):
        if update.message.caption:
            caption_text = update.message.caption
            url_match = re.search(r'(https?://\S+)', caption_text)
            if url_match:
                extracted_url = url_match.group(0)
                remaining_text = caption_text.replace(extracted_url, '', 1).strip()

                # For demonstration, we'll just reply with the caption and extracted URL
                reply_text = f"Received a photo with the following information:\nLink: {extracted_url}"
                if remaining_text:
                    reply_text += f"\nAdditional text: {remaining_text}"
                await update.message.reply_text(reply_text)
                # In a real scenario, you might want to process the photo and the link.
            else:
                await update.message.reply_text("Received a photo, but no valid link was found in the caption.")
        else:
            await update.message.reply_text("Received a photo without a caption containing a link.")
    else:
        await update.message.reply_text("You are not authorized to access this bot.")


# Define the main function to run the bot
async def main(application: ApplicationBuilder) -> None:
    # Replace 'YOUR_TOKEN' with your bot's token
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("grant_access", grant_access))
    application.add_handler(CommandHandler("block_user", block_user))
    application.add_handler(CommandHandler("list_users", list_users))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo)) # Add handler for photos

    # Start polling
    try:
        await application.run_polling()
    finally:
        await application.shutdown()
        save_access(user_access) # Save user access when closing


if __name__
 == '__main__':
    application = ApplicationBuilder().token("7864703583:AAGqZInSK2tp8Jykwpte7Ng0iunmYLlRwms").build() # Replace with your bot token
    user_access = load_access() # Load user access from json
    asyncio.run(main(application)) # Call main to start the bot
