import re
import aiohttp
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

BOT_TOKEN = "8009237833:AAHpVo798Sk5qtKRGHpDQYKSIxD2NEGLEfw"
OWNER_ID = 7588665244
KVDB_URL = "https://kvdb.io/BPkErVJ1RUwQA1brf928qK/"
API_URL = "https://managing-pippy-fhfhcd-af2e08fb.koyeb.app/api?api=deepak&link="

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ---------------------- Helper Functions ----------------------
async def kvdb_get(key):
    async with aiohttp.ClientSession() as session:
        async with session.get(KVDB_URL + key) as resp:
            if resp.status == 200:
                try:
                    return await resp.json()
                except:
                    return {}
            return {}

async def kvdb_set(key, data):
    async with aiohttp.ClientSession() as session:
        await session.post(KVDB_URL + key, json=data)

async def is_premium(user_id):
    users = await kvdb_get("premium_users")
    if str(user_id) in users:
        expiry = datetime.fromisoformat(users[str(user_id)]["expiry"])
        if datetime.now() <= expiry:
            return True
        else:
            del users[str(user_id)]
            await kvdb_set("premium_users", users)
    return False

async def get_user_settings(user_id):
    settings = await kvdb_get("user_settings")
    return settings.get(str(user_id), {})

# ---------------------- Command Handlers ----------------------
@dp.message_handler(commands=["add"])
async def add_premium(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        _, uid, days = message.text.split()
        uid = int(uid)
        days = int(days)
    except:
        return await message.reply("Usage: /add <user_id> <days>")

    users = await kvdb_get("premium_users")
    expiry = datetime.now() + timedelta(days=days)
    users[str(uid)] = {"expiry": expiry.isoformat(), "first_time": True}
    await kvdb_set("premium_users", users)

    try:
        await bot.send_message(uid, f"You are now able to use this bot.\nTutorial - Coming Soon\nExpires After {days} days")
    except:
        pass
    await message.reply(f"User {uid} added for {days} days.")

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    premium = await is_premium(message.from_user.id)
    if not premium:
        return await message.reply("You are not authorised to use the bot. To authorise to use this bot contact our admin team @AmazonLinkShortnerRobot")

    users = await kvdb_get("premium_users")
    user_data = users[str(message.from_user.id)]
    if user_data["first_time"]:
        users[str(message.from_user.id)]["first_time"] = False
        await kvdb_set("premium_users", users)

        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Set Amazon Tag", callback_data="set_tag"),
            InlineKeyboardButton("Channel Setup", callback_data="set_channel"),
            InlineKeyboardButton("Add Your Private Bot", callback_data="set_bot")
        )
        return await message.reply("Setup Panel", reply_markup=kb)

    await message.reply("Welcome back! Your bot is ready to use.")

# ---------------------- Callback Queries ----------------------
@dp.callback_query_handler(lambda c: c.data == "set_tag")
async def cb_set_tag(callback: types.CallbackQuery):
    await callback.message.answer("Please send your Amazon tag (e.g., Prashant75-21).")
    dp.register_message_handler(save_tag, content_types=types.ContentTypes.TEXT, state=None)

async def save_tag(message: types.Message):
    settings = await kvdb_get("user_settings")
    s = settings.get(str(message.from_user.id), {})
    s["amazon_tag"] = message.text.strip()
    settings[str(message.from_user.id)] = s
    await kvdb_set("user_settings", settings)
    await message.reply("Amazon tag saved.")
    dp.unregister_message_handler(save_tag)

@dp.callback_query_handler(lambda c: c.data == "set_channel")
async def cb_set_channel(callback: types.CallbackQuery):
    await callback.message.answer("Send me your channel id. Use @username_to_id_bot to get it.")
    dp.register_message_handler(save_channel, content_types=types.ContentTypes.TEXT, state=None)

async def save_channel(message: types.Message):
    settings = await kvdb_get("user_settings")
    s = settings.get(str(message.from_user.id), {})
    s["channel_id"] = message.text.strip()
    settings[str(message.from_user.id)] = s
    await kvdb_set("user_settings", settings)
    await message.reply("Channel ID saved.")
    dp.unregister_message_handler(save_channel)

@dp.callback_query_handler(lambda c: c.data == "set_bot")
async def cb_set_bot(callback: types.CallbackQuery):
    await callback.message.answer("Send me your private bot token.")
    dp.register_message_handler(save_bot, content_types=types.ContentTypes.TEXT, state=None)

async def save_bot(message: types.Message):
    token = message.text.strip()
    try:
        test_bot = Bot(token=token)
        me = await test_bot.get_me()
    except:
        return await message.reply("Invalid Bot token")

    settings = await kvdb_get("user_settings")
    s = settings.get(str(message.from_user.id), {})
    s["bot_token"] = token
    settings[str(message.from_user.id)] = s
    await kvdb_set("user_settings", settings)
    await message.reply("Bot token saved. Setup completed.")
    dp.unregister_message_handler(save_bot)

# ---------------------- Amazon Link Processing ----------------------
@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def process_links(message: types.Message):
    premium = await is_premium(message.from_user.id)
    if not premium:
        return

    urls = re.findall(r"https?://\\S+", message.text)
    if not urls:
        return

    user_settings = await get_user_settings(message.from_user.id)
    if "amazon_tag" not in user_settings:
        return await message.reply("Please set your Amazon tag first.")

    for url in urls:
        if "amazon" not in url:
            continue
        new_url = re.sub(r"tag=[^&]+", f"tag={user_settings['amazon_tag']}", url)
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL + new_url) as resp:
                short_link = await resp.text()
        await message.reply(short_link)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
