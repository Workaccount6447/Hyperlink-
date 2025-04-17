import logging
import requests
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, filters
from PIL import Image
from io import BytesIO
import os
import re
import asyncio

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
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_access.get(user_id, False):  # Check if user has access
        user_message = update.message.text

        # Find the first valid URL in the message
        url_match = re.search(r'(https?://\S+)', user_message)

        if url_match:
            extracted_url = url_match.group(0)
            remaining_text = user_message.replace(extracted_url, '', 1).strip() # Remove the URL and any extra whitespace

            # Send the link to www.example.com
            response = requests.post("https://mypricehistory.com/product/boat-airdopes-91-45hrs-battery-50ms-low-latency-enx-tech-fast-charge-ipx4-iwp-tech-v5-3-bluetooth-earbuds-tws-ear-buds-wireless-earphones-with-mic-active-black-P0TSB8H8ORHN", data={'link': extracted_url})

            # Check if the request was successful
            if response.status_code == 200:
                reply_text = "Link sent successfully!"
                if remaining_text:
                    reply_text += f"\n\nAdditional text: {remaining_text}"
                await update.message.reply_text(reply_text)
            else:
                await update.message.reply_text("Failed to send the link.")
        else:
            await update.message.reply_text("Please send a valid link.")
    else:
        await update.message.reply_text("You are not Authorised to access this bot .Firstly Paid ₹100 to the owner of the bot and send proof to @Toolsforaffilatesupportbot and wait for the response when our owner comes online it will gives access to you and notifies you . Kindly Be Patient. We Respect Your Patinent .")

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
async def main() -> None:
    # Replace 'YOUR_TOKEN' with your bot's token
    application = ApplicationBuilder().token("7864703583:AAGqZInSK2tp8Jykwpte7Ng0iunmYLlRwms").build()

    # Register handlers directly to the application
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("grant_access", grant_access))
    application.add_handler(CommandHandler("block_user", block_user))
    application.add_handler(CommandHandler("list_users", list_users))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo)) # Add handler for photos

    # Start the Bot
    await application.run_polling()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())l
