import telebot
import os
import time

TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    print("BOT_TOKEN не найден!")
    exit(1)

bot = telebot.TeleBot(TOKEN)
print("Bot started!")

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Voice Inside Galaxy
Bothost 24/7 ONLINE!
Готов к работе!")

@bot.message_handler(commands=['ping'])
def ping(message):
    bot.reply_to(message, "PONG! Bot работает!")

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.reply_to(message, "Получено: " + message.text)

print("Polling started...")
bot.polling(none_stop=True)
