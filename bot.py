import os
import logging
import time
import sys
from threading import Thread
from flask import Flask
import telebot 
from telebot import apihelper
from groq import Groq

# --- CONFIGURATION ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Basic check
if not GROQ_API_KEY or not TELEGRAM_TOKEN:
    print("CRITICAL: Keys missing. Check Environment Variables.")
    sys.exit(1)

# Setup Groq
client = Groq(api_key=GROQ_API_KEY)

# Setup Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- FLASK SERVER (Keeps Render Awake) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running efficiently!"

def run_flask():
    # Render assigns PORT, default to 5000 if missing
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# --- BOT LOGIC ---
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        user_text = message.text
        chat_id = message.chat.id
        print(f"Query from {chat_id}: {user_text}")

        # Send 'Typing...' action
        bot.send_chat_action(chat_id, 'typing')

        # 1. Ask Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful Class 12 Commerce Tutor (India). Concise answers for Accounts, Eco, B.St, Hindi, English."
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

        # 3. Reply
        bot.reply_to(message, bot_reply)

    except Exception as e:
        print(f"Error processing message: {e}")
        bot.send_message(message.chat.id, "Bot is waking up. Ask again in 10 seconds!")

# --- MAIN EXECUTION WITH RESTART LOGIC ---
if __name__ == '__main__':
    # Start Flask
    t = Thread(target=run_flask)
    t.start()

    print("--- STARTING BOT ---")
    
    # 1. Force kill any old webhooks (Fixes Conflict issues)
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception as e:
        print(f"Webhook removal warning: {e}")

    # 2. Infinite Restart Loop
    while True:
        try:
            print("Bot is polling (Listening for messages)...")
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        
        except Exception as e:
            # If 409 Conflict happens, this catches it
            print(f"CRASH: {e}")
            print("Restarting in 5 seconds...")
            time.sleep(5)
