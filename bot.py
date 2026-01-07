import os
import time
import sys
from threading import Thread
from flask import Flask
import telebot 
from groq import Groq

# --- CONFIGURATION ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is active"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Send 'typing' action
        bot.send_chat_action(message.chat.id, 'typing')

        # ASK GROQ (Updated Model Name)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful Class 12 Commerce Tutor (India). Answer questions on Accounts, Eco, B.St, Hindi, English. Be concise."
                },
                {
                    "role": "user",
                    "content": message.text
                }
            ],
            # vvvv THIS IS THE FIX vvvv
            model="llama-3.3-70b-versatile", 
            # ^^^^ THIS IS THE FIX ^^^^
        )

        bot_reply = chat_completion.choices[0].message.content
        bot.reply_to(message, bot_reply)

    except Exception as e:
        error_msg = f"⚠️ Error: {str(e)}"
        bot.reply_to(message, error_msg)

if __name__ == '__main__':
    # 1. Start Flask
    Thread(target=run_flask).start()

    # 2. CLEAR GHOST CONNECTIONS
    print("Clearing previous webhooks...")
    try:
        bot.remove_webhook()
        time.sleep(2) # Wait for Telegram to register the removal
    except Exception as e:
        print(e)

    # 3. Start Polling
    print("Bot started polling...")
    bot.infinity_polling()
