import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from start import start
from summarise import summarise_command
from model_selector import model_selector_handler
from mode_selector import mode_selector_handler
from chat_handler import chat_handler

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

logging.basicConfig(level=logging.INFO)
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("summarise", summarise_command))
app.add_handler(CallbackQueryHandler(model_selector_handler, pattern="^model_"))
app.add_handler(CallbackQueryHandler(mode_selector_handler, pattern="^mode_"))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_handler))

app.run_polling()

@bot.message_handler(commands=["announce"])
def announce_command(message):
    if message.from_user.id != 7588665244:
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    msg = bot.reply_to(message, "Please send the announcement text:")
    bot.register_next_step_handler(msg, process_announcement)

def process_announcement(message):
    announcement_text = message.text
    count = 0
    failed = 0

    # Load user IDs from database or file
    try:
        with open("users.txt", "r") as f:
            user_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
    except FileNotFoundError:
        bot.reply_to(message, "No users found.")
        return

    for user_id in user_ids:
        try:
            bot.send_message(user_id, f"**Announcement:**\n{announcement_text}", parse_mode="Markdown")
            count += 1
        except Exception:
            failed += 1

    bot.reply_to(message, f"Announcement sent to {count} users. Failed to send to {failed} users.")
