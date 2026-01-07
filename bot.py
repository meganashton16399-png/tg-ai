import os
import logging
import time
from threading import Thread
from flask import Flask
import telebot # This is pyTelegramBotAPI
from groq import Groq

# --- CONFIGURATION ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Check if keys are loaded
if not GROQ_API_KEY or not TELEGRAM_TOKEN:
    print("CRITICAL ERROR: API Keys are missing in Environment Variables!")

# Setup Groq
client = Groq(api_key=GROQ_API_KEY)

# Setup Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- FLASK SERVER (To keep Render awake) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# --- BOT LOGIC ---
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        user_text = message.text
        print(f"User said: {user_text}") # Log to Render console

        # Send 'Typing...' status
        bot.send_chat_action(message.chat.id, 'typing')

        # 1. Ask Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a specialized Class 12 Commerce Tutor. You help with Accounts, Eco, B.St, Hindi, and English. Be concise. If solving a numerical, show steps."
                },
                {
                    "role": "user",
                    "content": user_text,
                }
            ],
            model="llama3-8b-8192",
        )

        # 2. Get Answer
        bot_reply = chat_completion.choices[0].message.content

        # 3. Reply to User
        bot.reply_to(message, bot_reply)

    except Exception as e:
        # This will print the ACTUAL error to your Render logs so you can see what's wrong
        print(f"ERROR DETAILS: {e}")
        bot.reply_to(message, "Error. Developer, check Render logs.")

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    # Start Flask in background thread
    t = Thread(target=run_flask)
    t.start()

    # Start Bot (Infinity Polling)
    print("Bot started...")
    try:
        bot.remove_webhook() # Resets connection to ensure clean start
        time.sleep(1)
        bot.infinity_polling()
    except Exception as e:
        print(f"Polling Error: {e}")
