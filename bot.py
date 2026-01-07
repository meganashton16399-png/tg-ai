import os
import time
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
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Check if Key is missing
        if not GROQ_API_KEY:
            bot.reply_to(message, "CRITICAL ERROR: GROQ_API_KEY is missing in Render Settings!")
            return

        bot.send_chat_action(message.chat.id, 'typing')

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": message.text}
            ],
            model="llama3-8b-8192",
        )

        bot_reply = chat_completion.choices[0].message.content
        bot.reply_to(message, bot_reply)

    except Exception as e:
        # THIS IS THE IMPORTANT PART: Send the specific error to Telegram
        error_msg = f"⚠️ SYSTEM ERROR:\n{str(e)}"
        bot.reply_to(message, error_msg)

if __name__ == '__main__':
    Thread(target=run_flask).start()
    bot.infinity_polling()
