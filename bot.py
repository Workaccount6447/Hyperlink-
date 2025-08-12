import asyncio, datetime, re, json
import aiohttp
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# --- CONFIG ---
MAIN_BOT_TOKEN = "8009237833:AAH93dARRAJXkqoS0l3iHfMn3pFPDWL2kYY"
OWNER_ID = "7588665244"  # Replace with your Telegram ID
KVDB_BUCKET = "BPkErVJ1RUwQA1brf928qK"
KVDB_BASE = f"https://kvdb.io/{KVDB_BUCKET}"
SHORTENER_API = "https://managing-pippy-fhfhcd-af2e08fb.koyeb.app/api?api=deepak&link="
URL_RE = re.compile(r"https?://[^\s]+")

# --- HELPER FUNCTIONS ---
async def kv_get(session, key):
    async with session.get(f"{KVDB_BASE}/{key}") as resp:
        if resp.status == 200:
            return await resp.text()
    return None

async def kv_set(session, key, value):
    async with session.post(f"{KVDB_BASE}/{key}", data=value) as resp:
        return resp.status == 200

def now():
    return datetime.datetime.utcnow()

def parse_user(data_str):
    return json.loads(data_str) if data_str else {}

def dump_user(data_dict):
    return json.dumps(data_dict)

async def is_premium(session, user_id):
    data_str = await kv_get(session, f"user:{user_id}")
    if not data_str:
        return False, None
    user_data = parse_user(data_str)
    expiry = datetime.datetime.fromisoformat(user_data.get("expiry"))
    return expiry > now(), user_data

# --- COMMANDS ---
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != OWNER_ID:
        await update.message.reply_text("You are not authorised to use this command.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /add <user_id> <days>")
        return
    uid = context.args[0]
    days = int(context.args[1])
    expiry = now() + datetime.timedelta(days=days)
    user_data = {"expiry": expiry.isoformat()}
    async with aiohttp.ClientSession() as session:
        await kv_set(session, f"user:{uid}", dump_user(user_data))
    try:
        await context.bot.send_message(
            chat_id=uid,
            text=f"You are now able to use this bot.\nTutorial - Coming Soon\nExpires After {days} days ({expiry.date()})"
        )
    except:
        pass
    await update.message.reply_text(f"User {uid} added with {days} days premium.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiohttp.ClientSession() as session:
        premium, _ = await is_premium(session, update.effective_user.id)
    if not premium:
        await update.message.reply_text(
            "You are not authorised to use the bot.\n"
            "To authorise to use this bot contact our admin team @AmazonLinkShortnerRobot"
        )
        return

    keyboard = [
        [InlineKeyboardButton("Set Amazon Tag", callback_data="set_tag")],
        [InlineKeyboardButton("Channel Setup", callback_data="set_channel")],
        [InlineKeyboardButton("Add your private Bot", callback_data="set_bot_token")]
    ]
    await update.message.reply_text("Setup Panel", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    async with aiohttp.ClientSession() as session:
        user_data_str = await kv_get(session, f"user:{uid}")
        user_data = parse_user(user_data_str)
        user_data["setup_step"] = query.data
        await kv_set(session, f"user:{uid}", dump_user(user_data))

    if query.data == "set_tag":
        await query.message.reply_text("Please send your Amazon tag (e.g., Prashant75-21).")
    elif query.data == "set_channel":
        await query.message.reply_text("Send me your channel ID. Use @username_to_id_bot to get it.")
    elif query.data == "set_bot_token":
        await query.message.reply_text("Send your bot token:")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    async with aiohttp.ClientSession() as session:
        premium, user_data = await is_premium(session, uid)
        if not premium:
            return
        step = user_data.get("setup_step")
        if step == "set_tag":
            user_data["amazon_tag"] = update.message.text.strip()
            user_data.pop("setup_step", None)
            await kv_set(session, f"user:{uid}", dump_user(user_data))
            await update.message.reply_text("Amazon tag saved.")
        elif step == "set_channel":
            user_data["channel_id"] = update.message.text.strip()
            user_data.pop("setup_step", None)
            await kv_set(session, f"user:{uid}", dump_user(user_data))
            await update.message.reply_text("Channel ID saved.")
        elif step == "set_bot_token":
            token = update.message.text.strip()
            try:
                test_bot = Application.builder().token(token).build().bot
                await test_bot.get_me()
                user_data["bot_token"] = token
                user_data.pop("setup_step", None)
                await kv_set(session, f"user:{uid}", dump_user(user_data))
                await update.message.reply_text("Bot token saved. Setup complete.")
            except:
                await update.message.reply_text("Invalid Bot token.")
        else:
            await process_message(update, context, user_data)

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE, user_data):
    text = update.message.text or ""
    urls = URL_RE.findall(text)
    if not urls:
        return
    for url in urls:
        if "amazon." not in url:
            continue
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        qs["tag"] = [user_data.get("amazon_tag", "")]
        new_query = urlencode(qs, doseq=True)
        new_url = urlunparse(parsed._replace(query=new_query))

        async with aiohttp.ClientSession() as session:
            async with session.get(SHORTENER_API + new_url) as resp:
                short_link = await resp.text()

        text = text.replace(url, short_link)

    await update.message.reply_text(text)

async def main():
    app = Application.builder().token(MAIN_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_user))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
