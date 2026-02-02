import telebot
from telebot import types

TOKEN = "8294451648:AAFV-vMPVo4wHbkjjnN6W5_5Q39BxcTwCpg"
CHANNEL_ID = "-1001524100665"
CHAT_INVITE = "https://t.me/vigcomm"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("📢 Подписаться", url="https://t.me/voiceinsideglxy")
    btn2 = types.InlineKeyboardButton("✅ Проверить", callback_data="check")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "🎵 Voice Inside Galaxy. Подпишись и проверь!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "check":
        try:
            status = bot.get_chat_member(CHANNEL_ID, call.from_user.id).status
            if status in ['member', 'administrator', 'creator']:
                bot.edit_message_text("✅ Чат: " + CHAT_INVITE, call.message.chat.id, call.message.message_id)
            else:
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton("📢 Подписаться", url="https://t.me/voiceinsideglxy")
                btn2 = types.InlineKeyboardButton("🔄 Проверить", callback_data="check")
                markup.add(btn1, btn2)
                bot.edit_message_text("❌ Подпишись сначала!", call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            bot.answer_callback_query(call.id, "❌ Бот не админ!")

if __name__ == '__main__':
    print("🚀 Бот запущен!")
    bot.polling(none_stop=True)
