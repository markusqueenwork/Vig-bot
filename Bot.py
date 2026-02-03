import telebot
from telebot import types
import os

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("💬 Бесплатный чат", callback_data="free"))
    markup.add(types.InlineKeyboardButton("💎 VIP 100₽/мес", callback_data="vip"))
    markup.add(types.InlineKeyboardButton("🎛️ Услуги", callback_data="services"))
    bot.send_message(message.chat.id, "🎵 Voice Inside Galaxy", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "free":
        bot.answer_callback_query(call.id, "💬 Бесплатный чат")
("Подпишись на канал!")
    elif call.data == "vip":
        bot.answer_callback_query(call.id, "💎 VIP 100₽/мес
Оплати для доступа!")
    elif call.data == "services":
        bot.answer_callback_query(call.id, "🎛️ Сведение/Мастеринг
💰 Прайс: /prices")

bot.polling(none_stop=True)
