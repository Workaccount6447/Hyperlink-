from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from model_selector import user_current_model

async def mode_selector_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "mode_menu":
        keyboard = [
            [InlineKeyboardButton("🧠 Deep Reasoning", callback_data="mode_qwen_reasoning")],
            [InlineKeyboardButton("💬 Dialogue and Chat", callback_data="mode_llama_chat")],
            [InlineKeyboardButton("🧑‍💻 Coding", callback_data="mode_qwen_coder")],
            [InlineKeyboardButton("📊 Business and Analysis", callback_data="mode_llama_biz")],
        ]
        await query.edit_message_text("Select a mode:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    mode_map = {
        "mode_qwen_reasoning": "qwen/qwen-2-72b-instruct",
        "mode_llama_chat": "meta-llama/llama-3-70b-instruct",
        "mode_qwen_coder": "openrouter/quen-2.5-coder-32b",
        "mode_llama_biz": "meta-llama/llama-3-70b-instruct",
    }
    selected_model = mode_map.get(query.data)
    if selected_model:
        user_current_model[query.from_user.id] = selected_model
        label = query.data.split("_", 1)[1].replace("_", " ").title()
        await query.edit_message_text(f"You selected “{label}” for Chatting.\nIf you have or face any problem, contact us on @Smartautomationsuppport_bot")