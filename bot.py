from dotenv import load_dotenv
load_dotenv()
import os
import requests
from docx import Document
from PIL import Image
import pytesseract
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
import tempfile
from threading import Thread
from flask import Flask

# Configuration
MODEL = "google/gemma-9b-it"
API_KEY = os.getenv("OPENROUTER_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID"))
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://t.me/smartautomations_bot"
}

user_histories = {}
translation_requests = {}

async def ask_gemma(history):
    payload = {
        "model": MODEL,
        "messages": history
    }
    try:
        response = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=60)
        return response.json()["choices"][0]["message"]["content"]
    except Exception:
        return "⚠️ Error connecting to AI."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("📢 Main Channel", url="https://t.me/smartautomations")],
        [InlineKeyboardButton("🆘 Help", callback_data="help"),
         InlineKeyboardButton("🔄 New Chat", callback_data="new")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎉 *Welcome {user.first_name}!* 🎉  \n\n"
        "✨ *I'm your personal AI assistant* ✨  \n\n"
        "🤖 How can I assist you today?  \n\n"
        "🔥 *Features*:  \n"
        "✅ 100% Free & Unlimited  \n"
        "✅ Instant Responses  \n"
        "✅ Memory Across Chats  \n"
        "✅ File Supports \n\n"
        "📝 *Quick Commands*:  \n"
        "🔄 /new - Fresh start  \n"
        "ℹ️ /help - Show this menu  \n\n"
        "⚡ *Try asking*:  \n"
        "\"Explain like I'm 5 🧒\"  \n"
        "\"Give me 3 ideas 💡\"  \n\n"
        "🛠️ Support: @Smartautomationsuppport_bot  \n"
        "🚀 Powered by: @smartautomations",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text(
        "🔄 *Memory Cleared!* 🧹\n\n"
        "Ask me anything new! 💭\n\n"
        "*Try these*:\n"
        "• \"Tell me a fun fact 🎲\"\n"
        "• \"Help me brainstorm 💡\"", 
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆘 *@smartautomations_bot Help* 🆘\n────────────────────\n"
        "💬 *How to chat*:\nJust type messages like:\n"
        "• \"Explain quantum physics ⚛️\"\n• \"Write a haiku about cats 🐱\"\n\n"
        "🌍 *Translation*:\nClick 'Translate' button then send language name\n\n"
        "⚙️ *Commands*:\n🔄 /new - Reset conversation\nℹ️ /help - This message\n\n"
        "📏 *Limits*:\n4000 chars/message\n\n"
        "🔋 *Status*: Operational ✅",
        parse_mode=ParseMode.MARKDOWN
    )

async def privacy_policy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ Privacy Policy 🛡️\n\n"
        "We're committed to protecting your data and follow all data protection laws! Here's how we handle your information:\n\n"
        "*1. 💾 Data Collection and Storage 💾*\n"
        "• 🔍 Only necessary data is collected\n"
        "• 👤 Info like username and Telegram ID only\n"
        "• 🙅‍♀️ No extra personal data is stored\n\n"
        "*2. 🤖 Use of Data 🤖*\n"
        "• 🚀 Used only to improve bot performance\n"
        "• 💬 Message history stored temporarily for better conversation\n"
        "• ⚙️ Mode, balance, and settings retained for smooth experience\n\n"
        "*3. 🔒 Data Protection 🔒*\n"
        "• 💪 Strong security measures in place\n"
        "• 🛡️ Secure servers and limited access\n\n"
        "*4. 🗑️ Data Deletion 🗑️*\n"
        "• 🧹 Reset deletes all previous messages\n"
        "• 🙋‍♀️ Request data deletion anytime\n\n"
        "*5. 🤝 Data Sharing 🤝*\n"
        "• 🚫 Never shared or sold to anyone\n\n"
        "*6. 🔄 Changes to Privacy Policy 🔄*\n"
        "• ✍️ We may update this policy\n"
        "• 🔔 We’ll notify of major changes\n\n"
        "By using our bot, you agree to this privacy policy.\n\n"
        "If you have any questions or concerns, please reach out! 📧 We're here to help. 😊",
        parse_mode=ParseMode.MARKDOWN
    )

async def announcement_by_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("🚫 This command is restricted to the bot owner only.")
        return
    if not context.args:
        await update.message.reply_text("ℹ️ Usage: /announcementbyowner Your announcement text here")
        return

    announcement_text = " ".join(context.args)
    active_users = list(user_histories.keys())
    await update.message.reply_text(f"📢 Starting broadcast to {len(active_users)} users...")

    success = 0
    fail = 0
    for chat_id in active_users:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📢 *Owner Announcement*\n\n{announcement_text}\n\n- Bot Owner",
                parse_mode=ParseMode.MARKDOWN
            )
            success += 1
        except:
            fail += 1

    await update.message.reply_text(f"✅ Broadcast completed!\n\n• Successfully sent: {success}\n• Failed to send: {fail}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip().lower()

    # Custom hardcoded replies
    if any(q in text for q in ["who are you", "what are you", "your name"]):
        await update.message.reply_text("🤖 I am ChatGPT, your AI assistant!")
        return
    if any(q in text for q in ["can i create you", "did i create you", "did i made you"]):
        await update.message.reply_text("🙅‍♂️ No, you didn’t create me.")
        return
    if "who created you" in text:
        await update.message.reply_text("👨‍🔬 I was created by OpenAI.")
        return

    if user_id not in user_histories:
        user_histories[user_id] = []

    msg = await update.message.reply_text(
        "🔍 Smart AI is thinking 🤔...\n\n"
        "✨ We respect your patience\n\n"
        "Total Expected Duration:\n"
        "✅ Simple queries: 3–8 seconds\n"
        "⚠️ Complex queries: 8–15 seconds"
    )

    user_histories[user_id].append({"role": "user", "content": update.message.text})
    reply = await ask_gemma(user_histories[user_id])
    keyboard = [[InlineKeyboardButton("🌐 Translate", callback_data="translate")]]
    await msg.edit_text(reply, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_translation_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    translation_requests[update.effective_user.id] = {
        'text': query.message.text,
        'state': 'awaiting_language'
    }

    await query.message.reply_text(
        "🌍 *Translation Requested*\n\n"
        "Please send me the **name of the language** in English.\n\n"
        "Examples:\n"
        "• `French`\n"
        "• `Arabic`\n"
        "• `Hindi`\n"
        "• `Japanese`",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_language_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in translation_requests:
        return

    language_name = update.message.text.strip().title()
    original_text = translation_requests[user_id]['text']
    try:
        url = (
            f"https://translate.googleapis.com/translate_a/single?"
            f"client=gtx&sl=auto&tl={language_name.lower()}&dt=t&q={requests.utils.quote(original_text)}"
        )
        response = requests.get(url)
        translated_text = response.json()[0][0][0]
        await update.message.reply_text(f"🌍 Translation to {language_name}:\n\n{translated_text}")
    except:
        await update.message.reply_text("⚠️ Sorry, I couldn't translate that. Please try again.")

# Set up command handlers
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("new", new))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("privacy", privacy_policy))
app.add_handler(CommandHandler("announcementbyowner", announcement_by_owner))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_translation_button, pattern="translate"))
app.add_handler(MessageHandler(filters.TEXT, handle_language_input))

# Run the bot
if __name__ == "__main__":
    app.run_polling()
