import os
import requests
import fitz
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
        from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup

# Define your reply_markup if needed
reply_markup = InlineKeyboardMarkup([
    [InlineKeyboardButton("Support", url="https://t.me/Smartautomationsuppport_bot")]
])

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
    reply = await ask_deepseek(user_histories[user_id])
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
        "Kindly send me the **name of your language** in English.\n\n"
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
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        translated_text = ''.join([seg[0] for seg in response.json()[0] if seg[0]])

        await update.message.reply_text(
            f"🌐 *Translated to {language_name}:*\n\n{translated_text}",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        await update.message.reply_text(
            "⚠️ *Invalid Language Name*\n\n"
            "Please send the **correct English name** of your language.\n\n"
            "Examples:\n"
            "• `Spanish` (not 'es')\n"
            "• `Russian` (not 'ru')\n"
            "• `Chinese` (not 'zh')",
            parse_mode=ParseMode.MARKDOWN
        )
    finally:
        if user_id in translation_requests:
            del translation_requests[user_id]

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file = update.message.document

    if file.mime_type not in ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        await update.message.reply_text("⚠️ Unsupported file type. Please send a .txt, .pdf, or .docx file.")
        return

    file_path = f"{file.file_unique_id}_{file.file_name}"
    new_file = await file.get_file()
    await new_file.download_to_drive(file_path)

    try:
        if file.mime_type == "text/plain":
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif file.mime_type == "application/pdf":
            content = await extract_text_from_pdf(file_path)
        elif file.mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            content = await extract_text_from_docx(file_path)
    except:
        await update.message.reply_text("⚠️ Failed to read the file.")
        os.remove(file_path)
        return

    os.remove(file_path)
    if len(content) > 4000:
        content = content[:4000]

    user_histories[user_id] = [{"role": "user", "content": f"Please summarize or explain this:\n\n{content}"}]
    msg = await update.message.reply_text("📂 Reading your file...\n🔍 Smart AI is thinking 🤔...")
    reply = await ask_deepseek(user_histories[user_id])
    keyboard = [[InlineKeyboardButton("🌐 Translate", callback_data="translate")]]
    await msg.edit_text(reply, reply_markup=InlineKeyboardMarkup(keyboard))

async def extract_text_from_pdf(path):
    content = ""
    doc = fitz.open(path)
    for page in doc:
        text = page.get_text()
        if text.strip():
            content += text
        else:
            img = page.get_pixmap()
            img_path = "page.png"
            img.save(img_path)
            content += pytesseract.image_to_string(Image.open(img_path))
            os.remove(img_path)
    doc.close()
    return content

async def extract_text_from_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)
    

health_app = Flask(__name__)

@health_app.route('/')
def index():
    return 'OK'

def run_health_server():
    health_app.run(host='0.0.0.0', port=8000)

# Start Flask health check server in a background thread
Thread(target=run_health_server).start()


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("privacypolicy", privacy_policy))
    app.add_handler(CommandHandler("announcementbyowner", announcement_by_owner))
    app.add_handler(CallbackQueryHandler(handle_translation_button, pattern="translate"))
    app.add_handler(CallbackQueryHandler(help_command, pattern="help"))
    app.add_handler(CallbackQueryHandler(new, pattern="new"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_language_input))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot is running...")
    app.run_polling()
    

    


