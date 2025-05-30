from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def summarise_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Please provide a YouTube link.\nExample: /summarise https://youtube.com/watch?v=XXXX")
        return

    url = args[0]
    await update.message.reply_text(f"Summarizing video from: {url}\n(This is a placeholder)")