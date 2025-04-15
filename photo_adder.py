import telebot
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import re  # For finding links in text

# --- 1. Bot Token and Owner ID ---
BOT_TOKEN = "7864703583:AAGqZInSK2tp8Jykwpte7Ng0iunmYLlRwms"  # Replace with your actual bot token
OWNER_ID = 7588665244  # Replace with your Telegram user ID (as an integer)

# --- 2. Authorized Users (Initially Empty) ---
authorized_users = set()

# --- 3. Support Bot Username ---
SUPPORT_BOT_USERNAME = "@supportbot"

# --- 4. Payment Information ---
PAYMENT_AMOUNT = 100
PAYMENT_INSTRUCTIONS = "consult to the owner and send proof to [@Toolsforaffilatesupportbot]"

# --- 5. Initialize the Telegram Bot ---
bot = telebot.TeleBot(BOT_TOKEN)

# --- 6. Function to Check if a User is Authorized ---
def is_authorized(user_id):
    return user_id == OWNER_ID or user_id in authorized_users

# --- 7. Function to Capture and Crop Screenshot ---
def capture_and_crop_screenshot(url):
    try:
        # Set up Chrome WebDriver (you might need to adjust this based on your setup)
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)

        driver.set_window_size(1024, 768)  # Set an initial window size
        driver.get(url)

        # Give the page a moment to load (adjust as needed)
        driver.implicitly_wait(5)

        # Take a screenshot
        driver.save_screenshot("screenshot.png")

        # Crop the image
        img = Image.open("screenshot.png")
        cropped_img = img.crop((272, 516, 272 + 270, 516 + 183))  # (left, top, right, bottom)
        cropped_img.save("cropped_screenshot.png")

        driver.quit()
        return "cropped_screenshot.png"
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None

# --- 8. Function to Find a Link in Text ---
def find_link(text):
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    match = url_pattern.search(text)
    if match:
        url = match.group(0)
        # Add 'https://' if it's just 'www'
        if not url.startswith("http"):
            url = "https://" + url
        return url
    return None

# --- 9. Handler for the /start Command ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"You are not authorised to access the bot. Do payment of ₹{PAYMENT_AMOUNT} or {PAYMENT_INSTRUCTIONS}. After that the owner will give you access after he verified.\n\nPlease be patient.")

# --- 10. Handler for the /authorize Command (Owner Only) ---
@bot.message_handler(commands=['authorize'])
def authorize_user(message):
    if message.from_user.id == OWNER_ID:
        if len(message.text.split()) == 2:
            try:
                user_id_to_authorize = int(message.text.split()[1])
                authorized_users.add(user_id_to_authorize)
                bot.reply_to(message, f"User ID {user_id_to_authorize} has been authorized.")
            except ValueError:
                bot.reply_to(message, "Invalid user ID. Please use /authorize <user_id>.")
        else:
            bot.reply_to(message, "Please provide the user ID to authorize. Usage: /authorize <user_id>")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# --- 11. Handler for the /remove Command (Owner Only) ---
@bot.message_handler(commands=['remove'])
def remove_user(message):
    if message.from_user.id == OWNER_ID:
        if len(message.text.split()) == 2:
            try:
                user_id_to_remove = int(message.text.split()[1])
                if user_id_to_remove in authorized_users:
                    authorized_users.remove(user_id_to_remove)
                    bot.reply_to(message, f"User ID {user_id_to_remove} has been removed.")
                else:
                    bot.reply_to(message, f"User ID {user_id_to_remove} is not authorized.")
            except ValueError:
                bot.reply_to(message, "Invalid user ID. Please use /remove <user_id>.")
        else:
            bot.reply_to(message, "Please provide the user ID to remove. Usage: /remove <user_id>")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# --- 12. Handler for Text Messages (Link Processing) ---
@bot.message_handler(func=lambda message: True)
def process_message(message):
    user_id = message.from_user.id
    if is_authorized(user_id):
        link = find_link(message.text)
        if link:
            bot.reply_to(message, f"Processing link: {link}")
            screenshot_path = capture_and_crop_screenshot(link)
            if screenshot_path:
                with open(screenshot_path, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, caption=message.text)
            else:
                bot.reply_to(message, "Failed to capture or process the screenshot.")
        else:
            bot.reply_to(message, "No valid link found in your message.")
    else:
        bot.reply_to(message, f"You are not authorised to access the bot. Do payment of ₹{PAYMENT_AMOUNT} or {PAYMENT_INSTRUCTIONS}. After that the owner will give you access after he verified.\n\nPlease be patient.")

# --- 13. Start Listening for Messages ---
if __name__ == '__main__':
    print("Bot is running...")
    bot.polling(none_stop=True)
        
        
  
