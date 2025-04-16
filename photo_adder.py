import logging
import requests
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from PIL import Image
from io import BytesIO
import os

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Set your bot's owner ID (replace with your actual Telegram user ID)
OWNER_ID = 123456789  # Replace with your Telegram user ID

# Store user access
user_access = {}

# Define cropping dimensions
CROP_DIMENSIONS = (516, 272, 786, 455)  # (left, upper, right, lower)

# Define a function to handle messages
def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_access.get(user_id, False):  # Check if user has access
        user_message = update.message.text
        if user_message.startswith("http://") or user_message.startswith("https://"):
            # Take a screenshot and crop it
            cropped_image = take_screenshot_and_crop(user_message, CROP_DIMENSIONS)
            update.message.reply_photo(photo=cropped_image)
        else:
            update.message.reply_text("Please send a valid link.")
    else:
        update.message.reply_text("You do not have access to use this bot.")

# Define a function to start the bot
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_access.get(user_id, False):
        update.message.reply_text("Send me a link and I'll send you a cropped screenshot!")
    else:
        update.message.reply_text("You do not have access to use this bot.")

# Owner commands
def grant_access(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == OWNER_ID:
        user_id = int(context.args[0])
        user_access[user_id] = True
        update.message.reply_text(f"Access granted to user {user_id}.")
    else:
        update.message.reply_text("You are not authorized to use this command.")

def block_user(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == OWNER_ID:
        user_id = int(context.args[0])
        user_access[user_id] = False
        update.message.reply_text(f"User {user_id} has been blocked.")
        # Notify the user about the payment requirement
        context.bot.send_message(chat_id=user_id, text="Do payment of ₹100 to use this again and send proof on @Toolsforaffilatesupportbot.")
    else:
        update.message.reply_text("You are not authorized to use this command.")

def list_users(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id == OWNER_ID:
        users = [user_id for user_id, access in user_access.items() if access]
        update.message.reply_text(f"Users with access: {users}")
    else:
        update.message.reply_text("You are not authorized to use this command.")

# Function to crop an image
def crop_image(image: Image, crop_dimensions: tuple) -> Image:
    return image.crop(crop_dimensions)

# Function to take a screenshot and crop it
def take_screenshot_and_crop(url: str, crop_dimensions: tuple) -> BytesIO:
    # Here you would implement the screenshot logic (e.g., using Selenium or another library)
    # For demonstration, let's assume we have a screenshot image
    screenshot_image = Image.new('RGB', (800, 600), color='blue')  # Placeholder for the screenshot

    # Crop the image
    cropped_image = crop_image(screenshot_image, crop_dimensions)
    
    # Save to BytesIO
    img_byte_arr = BytesIO()
    cropped_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

# Define the main function to run the bot
def main() -> None:
    # Replace 'YOUR_TOKEN' with your bot's token
    updater = Updater("YOUR_TOKEN")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("grant_access", grant_access))
    dispatcher.add_handler(CommandHandler("block_user", block_user
        
        
  
