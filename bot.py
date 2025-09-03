import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ---------------- CONFIG ----------------
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
OWNER_ID = 123456789  # your Telegram ID
FORCE_CHANNEL = "@AdvanceRobots"   # leave "" if you don’t want force join


# ---------------- YT-DLP ----------------
def download_song(song_name):
    search_query = f"ytsearch1:{song_name}"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=True)
        filename = ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"
    return filename, info


# ---------------- HELPERS ----------------
async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is a member of FORCE_CHANNEL."""
    if not FORCE_CHANNEL:
        return True

    try:
        member = await context.bot.get_chat_member(FORCE_CHANNEL, update.effective_user.id)
        if member.status in ["left", "kicked"]:
            raise Exception("Not joined")
    except Exception:
        # Send join button
        button = InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{FORCE_CHANNEL.replace('@','')}")
        markup = InlineKeyboardMarkup([[button]])
        await update.message.reply_text(
            "🚨 To use me, you must join our update channel first!",
            reply_markup=markup
        )
        return False

    return True


# ---------------- HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_force_join(update, context):
        return

    user = update.effective_user
    name = user.first_name

    buttons = [
        [InlineKeyboardButton("🔥 Deals Channel", url="https://t.me/dealsduniyalimited")],
        [InlineKeyboardButton("🚀 Update Channel", url="https://t.me/AdvanceRobots")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    text = (
        f"Hello 👋 {name}\n\n"
        "I'm a Music 🎶 Downloader Bot\n\n"
        "Send me a name of a song and I'll send you the song in the highest quality.\n\n"
        "Enjoy your song ❤️\n"
        "Made with love by @AdvanceRobots"
    )

    await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_force_join(update, context):
        return

    song_name = update.message.text
    status = await update.message.reply_text("🎉 Downloading...")

    try:
        file_path, info = download_song(song_name)

        caption = (
            f"🎶 Title: {info.get('title', 'Unknown')}\n"
            f"👁 Views: {info.get('view_count', 0)}\n"
            f"⏱ Duration: {int(info.get('duration', 0) // 60)}:{int(info.get('duration', 0) % 60):02d}"
        )

        await update.message.reply_audio(audio=open(file_path, "rb"), caption=caption)

        os.remove(file_path)  # delete file after sending
        await status.edit_text("✅ Song sent successfully!")

    except Exception as e:
        await status.edit_text(f"❌ Error: {e}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # You can either keep the file locally (help_video.mp4) or use a direct URL
    video_path = "help_video.mp4"   # replace with your file name or direct link
    await update.message.reply_video(video=video_path, caption="📹 Here’s how to use me!")


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_song))

    print("✅ Bot is running…")
    app.run_polling()


if __name__ == "__main__":
    main()
