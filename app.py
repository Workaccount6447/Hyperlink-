import os
import re
import requests
from bs4 import BeautifulSoup
import yt_dlp
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from youtubesearchpython import VideosSearch
from flask import Flask
import threading

# --- Config ---
BOT_TOKEN = "8416104849:AAEV2neML_bs7L47zuymWHnnv6zWBsbtEd8"
OWNER_ID = 7588665244  # only owner can broadcast
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Store user interactions
search_results = {}
users = set()

# --- Spotify Metadata Extractor ---
def extract_metadata_from_spotify(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.find("meta", property="og:title")
    artist = soup.find("meta", property="music:musician")

    song_title = title["content"] if title else None
    artist_name = artist["content"] if artist else None

    if not song_title:
        raise Exception("Could not extract metadata from Spotify link.")
    
    return f"{song_title} {artist_name if artist_name else ''}"

# --- YouTube Downloader ---
def download_song(url_or_query, search_mode=False):
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "outtmpl": "%(title).40s.%(ext)s",
        "socket_timeout": 20,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "64"
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if search_mode:
            info = ydl.extract_info(f"ytsearch1:{url_or_query}", download=True)
            info = info["entries"][0]
        else:
            info = ydl.extract_info(url_or_query, download=True)

        filename = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
    return filename, info.get("title", "Unknown"), info.get("duration")

# --- YouTube Fast Search ---
def search_songs(query):
    videosSearch = VideosSearch(query, limit=5)
    results = videosSearch.result()["result"]
    return [{"title": r["title"], "url": r["link"], "duration": r.get("duration")} for r in results]

# --- /start ---
@bot.message_handler(commands=["start"])
def start(msg):
    users.add(msg.chat.id)  # track users for broadcast

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ Add Me", url="http://t.me/SongsDownload_Robot?startgroup=true"))
    kb.add(InlineKeyboardButton("💬 Support", url="http://t.me/Smarttgsupportbot"))
    kb.add(InlineKeyboardButton("📣 Updates", url="https://t.me/SmartTgBots"))
    kb.add(InlineKeyboardButton("❓ Help", callback_data="help"))

    text = ("🎵 I'm a Music Downloader Bot!\n"
            "I can help you download songs.\n\n"
            "Just send me the name of the song you want to download.\n"
            "Example: royalty\n\n"
            "I can also download songs from Spotify.\n\n"
            "You can also use me in any chat by typing:\n"
            "@SongsDownload_Robot song_name\n\n"
            "Made with love by - [Smart Tg Bots](https://t.me/SmartTgBots)")

    bot.send_message(msg.chat.id, text, reply_markup=kb)

# --- Broadcast (Owner only) ---
@bot.message_handler(commands=["broadcast"])
def broadcast(msg):
    if msg.from_user.id != OWNER_ID:
        bot.reply_to(msg, "❌ You are not authorized.")
        return
    text = msg.text.replace("/broadcast", "").strip()
    if not text:
        bot.reply_to(msg, "Usage: /broadcast Your message")
        return
    count = 0
    for uid in users:
        try:
            bot.send_message(uid, f"📢 Broadcast:\n\n{text}")
            count += 1
        except:
            pass
    bot.reply_to(msg, f"✅ Broadcast sent to {count} users.")

# --- Handle all text ---
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    users.add(message.chat.id)  # save user

    query = message.text.strip()

    # --- If Spotify link ---
    if "open.spotify.com/track/" in query:
        try:
            q = extract_metadata_from_spotify(query)
            wait_msg = bot.reply_to(message, "⬇️ Downloading your song 🎵 please wait.")
            file_path, title, duration = download_song(q, search_mode=True)

            with open(file_path, "rb") as audio:
                caption = (f"(Music)\n"
                           f"🎵 Title : {title}\n"
                           "━━━━━━━━━━━━━━━━━━━\n"
                           f"🔗 Url : {query}\n"
                           f"⏱ Duration : {duration//60}:{duration%60:02d}\n"
                           "━━━━━━━━━━━━━━━━━━━")
                bot.send_audio(message.chat.id, audio, title=title, caption=caption)

            os.remove(file_path)
            bot.delete_message(message.chat.id, wait_msg.message_id)
        except:
            bot.send_message(message.chat.id, "⚠️ Something went wrong. Please try again later.")

    # --- If song name (YouTube search) ---
    else:
        wait_msg = bot.reply_to(message, "🔎 Searching songs... please wait.")
        try:
            results = search_songs(query)
            if not results:
                bot.send_message(message.chat.id, "❌ No results found.")
                return

            search_results[message.chat.id] = results
            kb = InlineKeyboardMarkup()
            for idx, r in enumerate(results):
                kb.add(InlineKeyboardButton(f"{idx+1}. {r['title']}", callback_data=str(idx)))
            bot.send_message(message.chat.id, "Choose your song:", reply_markup=kb)

            bot.delete_message(message.chat.id, wait_msg.message_id)
        except:
            bot.send_message(message.chat.id, "⚠️ Something went wrong. Please try again later.")

# --- Callback for YouTube choices ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    try:
        index = int(call.data)
        result = search_results[chat_id][index]

        downloading_msg = bot.send_message(chat_id, f"⬇️ Downloading: {result['title']} Please wait...")

        file_path, title, duration = download_song(result["url"], search_mode=False)

        with open(file_path, "rb") as audio:
            if call.message.chat.type == "private":
                caption = (f"(Music)\n"
                           f"🎵 Title : {title}\n"
                           "━━━━━━━━━━━━━━━━━━━\n"
                           f"⏱ Duration : {duration//60}:{duration%60:02d}\n"
                           "━━━━━━━━━━━━━━━━━━━")
            else:
                user = call.from_user
                username = f"[{user.first_name}](tg://user?id={user.id})"
                caption = (f"(Music)\n"
                           f"🎵 Title : {title}\n"
                           "━━━━━━━━━━━━━━━━━━━\n"
                           f"⏱ Duration : {duration//60}:{duration%60:02d}\n"
                           "━━━━━━━━━━━━━━━━━━━\n"
                           f"Downloaded by : {username}\n\n"
                           "Made with love by [Smart Tg Bots](https://t.me/SmartTgBots)")

            bot.send_audio(chat_id, audio, title=title, caption=caption)

        os.remove(file_path)
        bot.delete_message(chat_id, downloading_msg.message_id)
        bot.delete_message(chat_id, call.message.message_id)  # remove choices

    except:
        bot.send_message(chat_id, "⚠️ Something went wrong. Please try again later.")

# --- Dummy Flask server for Koyeb ---
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_bot():
    bot.infinity_polling(skip_pending=True, timeout=20)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
