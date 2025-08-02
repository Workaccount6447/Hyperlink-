import json, logging, re, requests
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

OWNER_ID = 123456789  # 🔁 Replace with your Telegram ID
SUPPORT_BOT = '@amazonlinkshortnerrobot'
SHORT_API = 'https://individual-nanci-fhfhcd-8054f73b.koyeb.app/api?api=amazon&link='

DATA_FILE = 'users.json'
LINK_LOG = 'log.txt'
users = {}
converted_links = []

# Load users
try:
    with open(DATA_FILE) as f: users = json.load(f)
except: users = {}

def save(): open(DATA_FILE, 'w').write(json.dumps(users))

def is_premium(uid): return uid in users and datetime.strptime(users[uid]["expires"], "%Y-%m-%d") > datetime.utcnow()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in users:
        await update.message.reply_text(f"You are not authorised to use this bot.\nKindly consult our team.\nSupport: {SUPPORT_BOT}")
        return
    if not is_premium(uid):
        await update.message.reply_text("⛔ Your premium plan has expired. Contact support.")
        return
    btn = [
        [InlineKeyboardButton("🧾 Amazon Tag", callback_data='tag')],
        [InlineKeyboardButton("📣 Channel", callback_data='channel')]
    ]
    await update.message.reply_text("🔧 Setup Panel Of Amazon Link Shortener", reply_markup=InlineKeyboardMarkup(btn))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()
    if query.data == 'tag':
        users[str(uid)]["step"] = "waiting_tag"
        save()
        await query.message.reply_text("🔖 Send your Amazon Affiliate Tag:")
    elif query.data == 'channel':
        users[str(uid)]["step"] = "waiting_channel"
        save()
        await query.message.reply_text("📩 Forward a message from your channel where the bot is admin.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg = update.message
    text = msg.text or ''
    user = users.get(str(uid), {})
    step = user.get("step")

    if step == "waiting_tag":
        users[str(uid)]["tag"] = text.strip()
        users[str(uid)]["step"] = None
        save()
        await msg.reply_text("✅ Amazon tag configured.")
    elif step == "waiting_channel" and msg.forward_from_chat:
        chat = msg.forward_from_chat
        chat_id = chat.id
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if bot_member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            users[str(uid)]["channel"] = chat_id
            users[str(uid)]["step"] = None
            save()
            await msg.reply_text("✅ Channel verified and saved.")
        else:
            await msg.reply_text("⚠️ Bot must be admin in the channel.")
    elif "amazon." in text or "amzn.to" in text:
        await process_link(update, context)

async def process_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg = update.message
    text = msg.text
    if not is_premium(uid): return

    tag = users[str(uid)].get("tag")
    channel = users[str(uid)].get("channel")

    found = re.findall(r'(https?://[^\s]+)', text)
    new_text = text
    for link in found:
        full = unshorten(link)
        new = replace_tag(full, tag)
        final = requests.get(SHORT_API + new).text.strip()
        new_text = new_text.replace(link, final)
        converted_links.append({"uid": uid, "time": datetime.utcnow().isoformat()})

    if msg.photo:
        await context.bot.send_photo(chat_id=channel, photo=msg.photo[-1].file_id, caption=new_text)
        await msg.reply_photo(photo=msg.photo[-1].file_id, caption=new_text)
    else:
        await context.bot.send_message(chat_id=channel, text=new_text)
        await msg.reply_text(new_text)

def unshorten(link):
    try:
        res = requests.head(link, allow_redirects=True)
        return res.url
    except:
        return link

def replace_tag(url, tag):
    parts = urlparse(url)
    query = parse_qs(parts.query)
    query['tag'] = [tag]
    return urlunparse(parts._replace(query=urlencode(query, doseq=True)))

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    try:
        uid = int(context.args[0])
        days = int(context.args[1])
        expiry = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")
        users[str(uid)] = {"tag": "", "channel": "", "expires": expiry, "step": None}
        save()
        await update.message.reply_text(f"✅ User {uid} added for {days} days.")
        await context.bot.send_message(chat_id=uid, text=f"✅ You are now authorised to use this bot.\nSend /start again to begin.\n🕐 Time Period – {days} days")
    except:
        await update.message.reply_text("❌ Usage: /adduser <id> <days>")

async def statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    now = datetime.utcnow()
    this_month = now.strftime("%Y-%m")
    total_users = sum(1 for u in users.values() if u.get("expires", "").startswith(this_month))
    new_users = sum(1 for u in users.values() if "added" in u and u["added"].startswith(this_month))
    converted = len([l for l in converted_links if l["time"].startswith(this_month)])
    growth = (new_users / total_users * 100) if total_users else 0
    await update.message.reply_text(f"""📊 Bot Statistics:
Total Users This Month: {total_users}
New Users This Month: {new_users}
Links Converted: {converted}
📈 Growth Rate: {growth:.2f}%""")

async def detailsuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    msg = \"\\n\".join([f\"User: {uid} | Channel: {d.get('channel', '-')}`\" for uid, d in users.items()])
    await update.message.reply_text(f\"👥 User Details:\\n{msg}\")

def remind_expiring():
    for uid, data in users.items():
        if \"expires\" in data:
            exp = datetime.strptime(data[\"expires\"], \"%Y-%m-%d\")
            if (exp - datetime.utcnow()).days in [5, 1]:
                try:
                    context.bot.send_message(chat_id=int(uid), text=\"⏳ Your premium plan expires soon. Kindly renew.\")
                except: pass

app = ApplicationBuilder().token(\"YOUR_BOT_TOKEN\").build()
app.add_handler(CommandHandler(\"start\", start))
app.add_handler(CommandHandler(\"adduser\", adduser))
app.add_handler(CommandHandler(\"statistics\", statistics))
app.add_handler(CommandHandler(\"detailsuser\", detailsuser))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.ALL, handle_message))
app.run_polling()
