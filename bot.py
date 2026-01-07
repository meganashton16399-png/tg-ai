import os
import logging
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from groq import Groq

# --- CONFIGURATION ---
# We use os.environ.get to read keys from Render's Environment Variables
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Setup Groq Client
client = Groq(api_key=GROQ_API_KEY)

# Setup Logging (Helps debug on Render)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- FLASK SERVER (For Render Health Check) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    # Render assigns a port automatically in the PORT env var
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# --- BOT LOGIC ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    # Send a "typing..." action so the user knows it's working
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # 1. Send query to Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful Class 12 Commerce tutor (India). Answer questions on Accounts, Business Studies, Economics, Hindi, and English concisely. If a user asks for a solution, provide steps."
                },
                {
                    "role": "user",
                    "content": user_text,
                }
            ],
            model="llama3-8b-8192", # Very fast and free model
        )

        # 2. Get the answer
        bot_reply = chat_completion.choices[0].message.content

        # 3. Send answer back to Telegram
        await context.bot.send_message(chat_id=chat_id, text=bot_reply)

    except Exception as e:
        print(f"Error: {e}")
        await context.bot.send_message(chat_id=chat_id, text="Sorry, I faced an error processing that.")

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    # Start Flask in a separate thread so it doesn't block the bot
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Start the Telegram Bot
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found!")
    else:
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        # Handle all text messages
        echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
        application.add_handler(echo_handler)
        
        print("Bot is polling...")
        application.run_polling()
