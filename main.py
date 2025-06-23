import os
import re
import json
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, Filters, MessageHandler, CallbackContext, CallbackQueryHandler
logging.basicConfig(level=logging.INFO) logger = logging.getLogger(name)

CHANNELS = { 'C1': { 'chat': '@Dealsduniyalimited', 'sankmo': '66e62d6c3d06a67d606147fe0c774539', 'ekaro': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2N2JmMTY4Zjc2N2RiN2IzOWY3ZDNmZTIiLCJlYXJua2FybyI6IjQyMTg5MDkiLCJpYXQiOjE3NTA2NTU3OTB9.TjksUyuVLeVgXvIRbzFK1byHMNdcCrqr5CAAjrIzAeQ' }, 'C2': { 'chat': '@dealsduniyaloot', 'sankmo': '66e62d6c3d06a67d606147fe0c774539', 'ekaro': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2N2JmMTY4Zjc2N2RiN2IzOWY3ZDNmZTIiLCJlYXJua2FybyI6IjQyMTg5MDkiLCJpYXQiOjE3NTA2NTU3OTB9.TjksUyuVLeVgXvIRbzFK1byHMNdcCrqr5CAAjrIzAeQ' }, 'C3': { 'chat': '@dealsofferslooters', 'sankmo': '66e62d6c3d06a67d606147fe0c774539', 'ekaro': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2N2JmMTY4Zjc2N2RiN2IzOWY3ZDNmZTIiLCJlYXJua2FybyI6IjQyMTg5MDkiLCJpYXQiOjE3NTA2NTU4Mzd9.R7F6GE06Kifl7VExLq9nBxO-zGbpa_ocCRKembcBBsc' }, 'C4': { 'chat': '@dealsofferslooters2', 'sankmo': '66e62d6c3d06a67d606147fe0c774539', 'ekaro': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2N2JmMTY4Zjc2N2RiN2IzOWY3ZDNmZTIiLCJlYXJua2FybyI6IjQyMTg5MDkiLCJpYXQiOjE3NTA2NTU4Mzd9.R7F6GE06Kifl7VExLq9nBxO-zGbpa_ocCRKembcBBsc' } }

BOT_OWNER = int(os.getenv('BOT_OWNER', '0')) BOT_TOKEN = os.getenv('BOT_TOKEN')

EKARO_URL = 'https://ekaro-api.affiliaters.in/api/converter/public'

def extract_urls(text): return re.findall(r'https?://[^\s]+', text)

def convert_sankmo(api_key, text): urls = extract_urls(text) for u in urls: if 'amazon.' in u: r = requests.get(f"https://api.sankmo.com/convert?api_key={api_key}&url={u}") try: new = r.json().get('converted_url', u) text = text.replace(u, new) except: pass return text

def convert_ekaro(token, text): headers = { 'Authorization': f'Bearer {token}', 'Content-Type': 'application/json' } payload = json.dumps({"deal": text, "convert_option": "convert_only"}) try: r = requests.post(EKARO_URL, headers=headers, data=payload) if r.status_code == 200: return r.json().get('converted_deal', text) except: pass return text

def convert_text(code, text): conf = CHANNELS[code] text = convert_sankmo(conf['sankmo'], text) text = convert_ekaro(conf['ekaro'], text) return text

def ask_code(update): btns = [[InlineKeyboardButton(f"Channel {i}", callback_data=f"C{i}")] for i in range(1, 5)] update.message.reply_text("Which channel to post to?", reply_markup=InlineKeyboardMarkup(btns))

def handle_message(update: Update, context: CallbackContext): msg = update.message user = msg.from_user.id chat = msg.chat

if chat.type == 'private' and user != BOT_OWNER:
    return

text = msg.caption or msg.text or ''
code = next((c for c in CHANNELS if c in text), None)

if not code:
    context.user_data['pending'] = {'text': text, 'photos': msg.photo}
    ask_code(update)
    return

post_and_reply(update, context, code, text, msg.photo)

def button_handler(update: Update, context: CallbackContext): query = update.callback_query code = query.data query.answer() data = context.user_data.pop('pending', {}) post_and_reply(query, context, code, data.get('text', ''), data.get('photos'))

def post_and_reply(update_or_query, context: CallbackContext, code, text, photos): text = re.sub(r'\b' + code + r'\b', '', text).strip() converted = convert_text(code, text) target = CHANNELS[code]['chat']

if photos:
    photo_id = photos[-1].file_id
    context.bot.send_photo(chat_id=target, photo=photo_id, caption=converted)
else:
    context.bot.send_message(chat_id=target, text=converted)

response = f"✅ Deal posted to {target}\n\n{converted}"

if hasattr(update_or_query, 'message'):
    update_or_query.message.reply_text(response)
elif hasattr(update_or_query, 'edit_message_text'):
    update_or_query.edit_message_text(response)

def main(): updater = Updater(BOT_TOKEN) dp = updater.dispatcher dp.add_handler(MessageHandler(Filters.text | Filters.photo, handle_message)) dp.add_handler(CallbackQueryHandler(button_handler)) updater.start_polling() updater.idle()

if name == 'main': main()

