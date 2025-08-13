# bot.py
import threading
import requests
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes
import server

# --- BOT CONFIG ---
BOT_TOKEN = "8009237833:AAH93dARRAJXkqoS0l3iHfMn3pFPDWL2kYY"
OWNER_ID = 7588665244
KVDB_URL = "https://kvdb.io/BPkErVJ1RUwQA1brf928qK/"
API_URL = "https://managing-pippy-fhfhcd-af2e08fb.koyeb.app/api?api=deepak&link="

# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running!")

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    try:
        uid = int(context.args[0])
        days = int(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /add_user <user_id> <days>")
        return
    
    # Store user in KVDB
    requests.post(f"{KVDB_URL}{uid}", data=str(days))
    await context.bot.send_message(uid, f"✅ You can now use this bot for {days} days.")
    await update.message.reply_text(f"✅ User {uid} added for {days} days.")

async def forward_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    days_left = requests.get(f"{KVDB_URL}{user_id}").text.strip()

    if not days_left or days_left == "null":
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /link <amazon_link>")
        return

    amazon_link = context.args[0]
    final_url = f"{API_URL}{amazon_link}"
    r = requests.get(final_url)
    await update.message.reply_text(f"Here’s your link: {r.text}")

# --- THREAD RUNNERS ---
def run_flask():
    server.app.run(host="0.0.0.0", port=5000)

def run_telegram():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_user", add_user))
    app.add_handler(CommandHandler("link", forward_link))
    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_telegram()
