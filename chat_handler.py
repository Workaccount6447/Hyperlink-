import requests
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from model_selector import user_current_model

OPENROUTER_API_KEY = "your_openrouter_api_key_here"

def call_openrouter(model_id, user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": user_message}],
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    model_id = user_current_model.get(user_id)
    if not model_id:
        await update.message.reply_text("Please select a model or mode first.")
        return

    user_message = update.message.text
    try:
        reply = call_openrouter(model_id, user_message)
        if "coder" in model_id.lower():
            reply = f"```python\n{reply}\n```"
            await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("An error occurred while processing your request.")