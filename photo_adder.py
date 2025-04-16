
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
OWNER_ID = 7588665244  # Replace with your Telegram user ID

# Store user access
user_access = {}

# Define a function to handle messages
def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_access.get(user_id, False):  # Check if user has access
        user_message = update.message.text
        if user_message.startswith("http://") or user_message.startswith("https://"):
            # Send the link to www.example.com
            response = requests.post("https://mypricehistory.com/product/boat-airdopes-91-45hrs-battery-50ms-low-latency-enx-tech-fast-charge-ipx4-iwp-tech-v5-3-bluetooth-earbuds-tws-ear-buds-wireless-earphones-with-mic-active-black-P0TSB8H8ORHN", data={'link': user_message})
            
            # Check if the request was successful
            if response.status_code == 200:
                update.message.reply_text("Link sent successfully!")
            else:
                update.message.reply_text("Failed to send the link.")
        else:
            update.message.reply_text("Please send a valid link.")
    else:
        update.message.reply_text("You are not Authorised to access this bot .Firstly Paid ₹100 to the owner of the bot and send proof to @Toolsforaffilatesupportbot and wait for the response when our owner comes online it will gives access to you and notifies you . Kindly Be Patient. We Respect Your Patinent .")

# Define a function to start the bot
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_access.get(user_id, False):
        update.message.reply_text("Send me a link and I'll send it to www.example.com!")
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
        update.message.reply_text(f"User  {user_id} has been blocked.")
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
    updater = Updater("7864703583:AAGqZInSK2tp8Jykwpte7Ng0iunmYLlRwms")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("grant_access", grant_access))
    dispatcher.add_handler(CommandHandler("block_user", block_user))
    dispatcher.add_handler(Command    
        
  
