import os
import logging
from flask import Flask, request
import telebot 
from groq import Groq

# --- CONFIGURATION ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# --- SETUP ---
# Enable logging to see errors in Render logs
logging.basicConfig(level=logging.INFO)

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# --- WEBHOOK LOGIC (The Permanent Fix) ---
@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def getMessage():
    """
    Telegram sends messages to this URL. 
    We pass them to the bot library to handle.
    """
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    """
    This endpoint sets the webhook. 
    Render calls this automatically when the server starts.
    """
    bot.remove_webhook()
    
    # Set the new webhook URL so Telegram knows where to send messages
    bot.set_webhook(url=WEBHOOK_URL + "/" + TELEGRAM_TOKEN)
    return f"Webhook set to {WEBHOOK_URL}!", 200

# --- BOT ANSWER LOGIC ---
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Ask Groq (Using the NEW working model)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful Class 12 Commerce Tutor. Answer concisely."
                },
                {
                    "role": "user",
                    "content": message.text
                }
            ],
            model="llama-3.3-70b-versatile", # <--- UPDATED MODEL
        )

        bot_reply = chat_completion.choices[0].message.content
        bot.reply_to(message, bot_reply)

    except Exception as e:
        print(f"Error: {e}")
        # Don't send error to user, just log it.
        # If Groq fails, we don't want to crash the webhook.

if __name__ == "__main__":
    # Standard Render setup
    port = int(os.environ.get('PORT', 5000))
    
    # In Webhook mode, we DO NOT use bot.polling()
    # We only run the Flask server.
    
    # Run setup first
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + "/" + TELEGRAM_TOKEN)
    
    print(f"Server starting on port {port} with Webhook...")
    app.run(host="0.0.0.0", port=port)
