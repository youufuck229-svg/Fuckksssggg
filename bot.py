import os
import telebot
import requests
from flask import Flask, request

# 🔴 Direct credentials daal diye (testing ke liye)
BOT_TOKEN = "8804895685:AAGF9vdkKm3zALWagVJDinUIvzX1yy0IgQQ"
TWILIO_SID = "AC2163cc7ccb0eef66a85f946de829e929"
TWILIO_AUTH = "7f6206005a73184fea24641f31ec4929"

# Railway domain (agar Railway pe host kar rahe ho)
RAILWAY_DOMAIN = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
WEBHOOK_URL = f"https://{RAILWAY_DOMAIN}/webhook" if RAILWAY_DOMAIN else None

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

user_data = {}

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "Bot ready!\n/set_sender <name>\n/set_number <+91...>\n/set_message <text>\n/send")

@bot.message_handler(commands=['set_sender'])
def set_sender(msg):
    sender = msg.text.replace('/set_sender', '').strip()
    user_data.setdefault(msg.chat.id, {})['sender'] = sender
    bot.reply_to(msg, f"Sender ID set: {sender}")

@bot.message_handler(commands=['set_number'])
def set_number(msg):
    number = msg.text.replace('/set_number', '').strip()
    user_data.setdefault(msg.chat.id, {})['number'] = number
    bot.reply_to(msg, f"Number set: {number}")

@bot.message_handler(commands=['set_message'])
def set_message(msg):
    text = msg.text.replace('/set_message', '').strip()
    user_data.setdefault(msg.chat.id, {})['message'] = text
    bot.reply_to(msg, f"Message set: {text}")

@bot.message_handler(commands=['send'])
def send(msg):
    data = user_data.get(msg.chat.id, {})
    if not all(k in data for k in ('sender', 'number', 'message')):
        bot.reply_to(msg, "Pehle /set_sender, /set_number, /set_message karo")
        return

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    payload = {
        'From': data['sender'],
        'To': data['number'],
        'Body': data['message']
    }

    try:
        res = requests.post(url, data=payload, auth=(TWILIO_SID, TWILIO_AUTH))
        if res.status_code == 201:
            bot.reply_to(msg, "Message bhej diya!")
        else:
            bot.reply_to(msg, f"Twilio Error: {res.json().get('message')}")
    except Exception as e:
        bot.reply_to(msg, f"Error: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return '', 403

@app.route('/healthz')
def health():
    return "OK", 200

if __name__ == "__main__":
    if WEBHOOK_URL:
        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)