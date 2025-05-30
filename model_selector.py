from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

user_current_model = {}

async def model_selector_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "model_menu":
        keyboard = [
            [InlineKeyboardButton("Gemini 2.5 Flash", callback_data="model_gemini")],
            [InlineKeyboardButton("ChatGPT", callback_data="model_llama")],
        ]
        await query.edit_message_text("Select a model:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    model_map = {
        "model_gemini": "google/gemini-pro-2.5-flash",
        "model_llama": "meta-llama/llama-3-70b-instruct",
    }
    selected_model = model_map.get(query.data)
    if selected_model:
        user_current_model[query.from_user.id] = selected_model
        label = query.data.replace("model_", "").capitalize()
        await query.edit_message_text(f"You selected “{label}” for Chatting.\nIf you have or face any problem, contact us on @Smartautomationsuppport_bot")