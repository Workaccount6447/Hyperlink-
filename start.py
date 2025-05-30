from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from model_selector import user_current_model

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_current_model[user.id] = None

    keyboard = [
        [InlineKeyboardButton("Model", callback_data="model_menu")],
        [InlineKeyboardButton("Mode", callback_data="mode_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = f"""🎉 Welcome {user.first_name}! 🎉

✨ I'm your personal AI assistant ✨

🤖 How can I assist you today?

🔥 Features: ✅ 100% Free & Unlimited ✅ Instant Responses ✅ Memory Across Chats

📝 Quick Commands:
/start – Begin interacting with the bot, new chat.
/summarise – Get a summary of a YouTube video via AI.
/privacypolicy – View our data handling and privacy policy.
/help – Show help message.

⚡ Features • Unlimited • 3x Faster Responses • 32K Context Memory

⚒ Support: @Smartautomationsuppport_bot

🚀 Powered by: @smartautomations
"""
    await update.message.reply_text(message, reply_markup=reply_markup)