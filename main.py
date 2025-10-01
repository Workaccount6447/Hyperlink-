hiimport os
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import yt_dlp

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")  # from Render environment variable
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))  # your Telegram ID
FORCE_CHANNEL = os.getenv("FORCE_CHANNEL", "")      # leave empty "" if not required
DB_GROUP_ID = int(os.getenv("DB_GROUP_ID", "-1001234567890"))

os.makedirs("downloads", exist_ok=True)

# --- Download audio ---
def download_audio(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=True)
        filename = ydl.prepare_filename(info['entries'][0])
        mp3_file = os.path.splitext(filename)[0] + ".mp3"
        duration = str(info['entries'][0].get("duration", "Unknown")) + " sec"
        return mp3_file, info['entries'][0]['title'], duration

# --- Force channel check ---
def is_subscribed(bot, user_id):
    if not FORCE_CHANNEL:
        return True
    try:
        member = bot.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# --- Start ---
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    first_name = user.first_name

    if FORCE_CHANNEL and not is_subscribed(context.bot, user.id):
        update.message.reply_text(
            f"🚨 To use this bot, please join our channel first:\n{FORCE_CHANNEL}"
        )
        return

    # Log user to DB group
    try:
        context.bot.send_message(DB_GROUP_ID, f"New user: `{user.id}`", parse_mode="Markdown")
    except:
        pass

    start_message = f"""
🔥 Welcome to Music Bot, {first_name}! 🔥  

🎶 Unlimited music downloads,  
⚡ Super-fast & free,  
❤️ Always available for you.  

Just send a song name or I will directly send your favourite song to you within seconds.  

🥰 Made with love by Hanuman
"""
    update.message.reply_text(start_message)

# --- Handle requests ---
def handle_message(update: Update, context: CallbackContext):
    user = update.effective_user

    if FORCE_CHANNEL and not is_subscribed(context.bot, user.id):
        update.message.reply_text(
            f"🚨 To use this bot, please join our channel first:\n{FORCE_CHANNEL}"
        )
        return

    query = update.message.text
    msg = update.message.reply_text("⏳ Searching and downloading...")

    try:
        file_path, title, duration = download_audio(query)

        # Send audio
        context.bot.send_audio(
            chat_id=update.effective_chat.id,
            audio=open(file_path, 'rb'),
            title=title
        )
        os.remove(file_path)

        # Custom message
        if update.effective_chat.type == "private":
            message_text = f"""
━━━━━━━━━━━━━━━━━━
🎵 Title : {title} 
⏱ Duration : {duration}
━━━━━━━━━━━━━━━━━━━

🥰 Made with love by Hanuman

Enjoy !!❤️
"""
        else:
            user_mention = update.effective_user.mention_html()
            message_text = f"""
━━━━━━━━━━━━━━━━━━
🎵 Title : {title}
⏱ Duration : {duration}

💥Downloaded by {user_mention}
━━━━━━━━━━━━━━━━━━━
🥰 Made with love by Hanuman

Enjoy !!❤️
"""
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text,
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        msg.edit_text(f"❌ Error: {str(e)}")
    else:
        msg.delete()

# --- Broadcast ---
def broadcast(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        update.message.reply_text("❌ You are not allowed to use this command.")
        return

    if not context.args:
        update.message.reply_text("⚠️ Usage: /broadcast <message>")
        return

    text = " ".join(context.args)

    # Send broadcast to DB group users
    try:
        history = context.bot.get_chat(DB_GROUP_ID)  # log group info
        context.bot.send_message(DB_GROUP_ID, f"📢 Owner broadcast started:\n{text}")
    except:
        update.message.reply_text("⚠️ Cannot access DB group.")
        return

    update.message.reply_text("✅ Broadcast command acknowledged (DB group will have logs).")

# --- Main ---
if __name__ == "__main__":
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("broadcast", broadcast))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()
