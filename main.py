import os
import logging
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Updater, Filters, MessageHandler, CallbackContext, CallbackQueryHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHANNEL_API_MAPPING = {
    "C1": {
        "channels": ["@Dealsduniyalimited", "@dealsduniyaloot"],
        "sankmo": "66e62d6c3d06a67d606147fe0c774539",
        "earnkaro": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2N2JmMTY4Zjc2N2RiN2IzOWY3ZDNmZTIiLCJlYXJua2FybyI6IjQyMTg5MDkiLCJpYXQiOjE3NTA2NTU3OTB9.TjksUyuVLeVgXvIRbzFK1byHMNdcCrqr5CAAjrIzAeQ"
    },
    "C2": {
        "channels": ["@dealsofferslooters", "@dealsofferslooters2"],
        "sankmo": "66e62d6c3d06a67d606147fe0c774539",
        "earnkaro": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2N2JmMTY4Zjc2N2RiN2IzOWY3ZDNmZTIiLCJlYXJua2FybyI6IjQyMTg5MDkiLCJpYXQiOjE3NTA2NTU4Mzd9.R7F6GE06Kifl7VExLq9nBxO-zGbpa_ocCRKembcBBsc"
    }
}

def convert_link(link, sankmo_api, earnkaro_api):
    if "camerawale" in link.lower():
        url = "https://sankmo-api-url.com/convert"
        headers = {'Authorization': sankmo_api, 'Content-Type': 'application/json'}
    else:
        url = "https://ekaro-api.affiliaters.in/api/converter/public"
        headers = {'Authorization': f'Bearer {earnkaro_api}', 'Content-Type': 'application/json'}

    payload = json.dumps({"deal": link, "convert_option": "convert_only"})
    response = requests.post(url, headers=headers, data=payload)
    
    try:
        data = response.json()
        return data.get("converted_deal") or link
    except Exception:
        return link

def handle_message(update: Update, context: CallbackContext):
    user = update.effective_user
    message = update.message
    text = message.caption or message.text or ""

    matched_code = None
    for code in CHANNEL_API_MAPPING:
        if code in text:
            matched_code = code
            text = text.replace(code, "").strip()
            break

    if matched_code:
        mapping = CHANNEL_API_MAPPING[matched_code]
        sankmo_api = mapping["sankmo"]
        earnkaro_api = mapping["earnkaro"]
        new_text = convert_link(text, sankmo_api, earnkaro_api)

        if message.photo:
            photo = message.photo[-1].file_id
            for channel in mapping["channels"]:
                context.bot.send_photo(chat_id=channel, photo=photo, caption=new_text)
        else:
            for channel in mapping["channels"]:
                context.bot.send_message(chat_id=channel, text=new_text)

        message.reply_text("✅ Deal sent to respective channels.")

    else:
        keyboard = [[InlineKeyboardButton("C1", callback_data='C1'),
                     InlineKeyboardButton("C2", callback_data='C2')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message.reply_text("Select where to send the deal:", reply_markup=reply_markup)

def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_data = context.user_data
    query.answer()

    selected_code = query.data
    user_data['code'] = selected_code

    message = query.message
    if message.caption:
        text = message.caption
    else:
        text = message.text or ""

    mapping = CHANNEL_API_MAPPING[selected_code]
    sankmo_api = mapping["sankmo"]
    earnkaro_api = mapping["earnkaro"]
    new_text = convert_link(text, sankmo_api, earnkaro_api)

    if message.photo:
        photo = message.photo[-1].file_id
        for channel in mapping["channels"]:
            context.bot.send_photo(chat_id=channel, photo=photo, caption=new_text)
    else:
        for channel in mapping["channels"]:
            context.bot.send_message(chat_id=channel, text=new_text)

    query.edit_message_text("✅ Deal forwarded.")

def main():
    from telegram.ext import Updater
    TOKEN = os.getenv("BOT_TOKEN")
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text | Filters.caption, handle_message))
    dp.add_handler(CallbackQueryHandler(button_callback))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
