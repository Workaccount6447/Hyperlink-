from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from selenium import webdriver
from PIL import Image
import os
import re
import asyncio

# Define the owner ID and bot token
OWNER_ID = 7588665244  # Replace with your Telegram user ID
BOT_TOKEN = "7864703583:AAGqZInSK2tp8Jykwpte7Ng0iunmYLlRwms"  # Replace with your bot token

# Set to store authorized user IDs
AUTHORIZED_USERS = {OWNER_ID}

# Dictionary to track user activity
user_activity = {}

async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    await update.message.reply_text("Welcome! You can send me links, and I'll take a screenshot for you.")
    user_activity[user_id] = user_activity.get(user_id, 0) + 1

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    user_message = update.message.text
    await update.message.reply_text("Processing your message...")

    link_pattern = r'(https?://[^\s]+|www\.[^\s]+)'
    match = re.search(link_pattern, user_message)

    if match:
        user_link = match.group(0)
        await update.message.reply_text(f"Found link: {user_link}")

        try:
            driver = webdriver.Chrome()  # Make sure ChromeDriver is installed and in PATH
            driver.get(user_link)

            screenshot_path = "screenshot.png"
            driver.save_screenshot(screenshot_path)
            driver.quit()

            image = Image.open(screenshot_path)

            # Crop box coordinates
            left = 516
            top = 272
            right = left + 270
            bottom = top + 183

            cropped_image = image.crop((left, top, right, bottom))
            cropped_image_path = "cropped_image.png"
            cropped_image.save(cropped_image_path)

            caption_text = f"Here is your screenshot:\n\nOriginal message:\n{user_message}"
            await update.message.reply_photo(photo=open(cropped_image_path, 'rb'), caption=caption_text)

        except Exception as e:
            await update.message.reply_text(f"An error occurred: {str(e)}")
        finally:
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            if os.path.exists(cropped_image_path):
                os.remove(cropped_image_path)
    else:
        await update.message.reply_text("No valid link found in your message.")

async def add_user(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You are not authorized to perform this action.")
        return

    if context.args:
        new_user_id = int(context.args[0])
        if new_user_id in AUTHORIZED_USERS:
            await update.message.reply_text(f"User {new_user_id} is already an authorized user.")
        else:
            AUTHORIZED_USERS.add(new_user_id)
            await update.message.reply_text(f"User {new_user_id} has been added to the authorized users.")
    else:
        await update.message.reply_text("Please provide a user ID to add.")

async def remove_user(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You are not authorized to perform this action.")
        return

    if context.args:
        user_id_to_remove = int(context.args[0])
        if user_id_to_remove in AUTHORIZED_USERS:
            AUTHORIZED_USERS.remove(user_id_to_remove)
            await update.message.reply_text(f"User {user_id_to_remove} has been removed from authorized users.")
        else:
            await update.message.reply_text(f"User {user_id_to_remove} is not an authorized user.")
    else:
        await update.message.reply_text("Please provide a user ID to remove.")

# Run the bot
if __name__ == '__main__':
    async def main():
        application = ApplicationBuilder().token(BOT_TOKEN).build()  # Use your bot token

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("adduser", add_user))
        application.add_handler(CommandHandler("removeuser", remove_user))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Run the bot without asyncio.run()
        await application.run_polling()

    # Instead of using asyncio.run(), directly run the event loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
        
        
  
