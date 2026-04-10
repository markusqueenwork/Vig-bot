import telebot
from telebot import types
import os

TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_FREE = "-1001524100665"
CHAT_FREE = "https://t.me/vigcomm"
TELEGRAM_URL = "https://t.me/voiceinsideglxy"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("Бесплатный чат", callback_data="free"))
    markup.add(types.InlineKeyboardButton("Telegram канал", callback_data="telegram"))
    bot.send_message(message.chat.id, "Voice Inside Galaxy", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "free":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Подписаться", url="https://t.me/voiceinsideglxy"))
        markup.add(types.InlineKeyboardButton("Проверить", callback_data="check_free"))
        bot.edit_message_text("Бесплатный чат. Подпишись на канал!", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "telegram":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Подписаться", url=TELEGRAM_URL))
        bot.edit_message_text("Подпишись на Telegram!", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "check_free":
        try:
            status = bot.get_chat_member(CHANNEL_FREE, call.from_user.id).status
            if status in ['member','administrator','creator']:
                bot.edit_message_text("Доступ к чату: " + CHAT_FREE, call.message.chat.id, call.message.message_id)
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Подписаться", url="https://t.me/voiceinsideglxy"))
                markup.add(types.InlineKeyboardButton("Проверить", callback_data="check_free"))
                bot.edit_message_text("Подпишись сначала!", call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            bot.answer_callback_query(call.id, "Бот не админ канала!")

if __name__ == "__main__":
    print("Бот запущен!")
    bot.polling(none_stop=True)