import telebot
from telebot import types
import os

TOKEN = os.environ.get('BOT_TOKEN', '8294451648:AAFV-vMPVo4wHbkjjnN6W5_5Q39BxcTwCpg')
CHANNEL_VIP = "-1003906026623"
CHAT_VIP = "https://t.me/+aSbD7SmXaf8yNGIy"
TRIBUTE_URL = "https://t.me/tribute/app?startapp=sUh7"
TELEGRAM_CHANNEL = "https://t.me/voiceinsideglxy"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("Telegram канал", url=TELEGRAM_CHANNEL))
    markup.add(types.InlineKeyboardButton("Voice Inside Galaxy +", callback_data="vip"))
    bot.send_message(message.chat.id, "Voice Inside Galaxy", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "vip":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Оплатить 300р", url=TRIBUTE_URL))
        markup.add(types.InlineKeyboardButton("Проверить доступ", callback_data="check_vip"))
        bot.edit_message_text(
            "Voice Inside Galaxy +\n\nЗакрытый чат. Оплати и получи доступ!",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    elif call.data == "check_vip":
        try:
            status = bot.get_chat_member(CHANNEL_VIP, call.from_user.id).status
            if status in ['member', 'administrator', 'creator']:
                bot.edit_message_text(
                    "Доступ к чату: " + CHAT_VIP,
                    call.message.chat.id,
                    call.message.message_id
                )
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Оплатить 300р", url=TRIBUTE_URL))
                bot.edit_message_text(
                    "Оплати подписку!",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup
                )
        except:
            bot.answer_callback_query(call.id, "Бот не админ чата!")

if __name__ == "__main__":
    print("Бот запущен!")
    bot.polling(none_stop=True)