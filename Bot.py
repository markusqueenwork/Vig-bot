import telebot
from telebot import types

TOKEN = "8294451648:AAFV-vMPVo4wHbkjjnN6W5_5Q39BxcTwCpg"
CHANNEL_FREE = "-1001524100665"
CHANNEL_VIP = "-1003727929609"
CHAT_FREE = "https://t.me/vigcomm"
CHAT_VIP = "https://t.me/+UZ2GwssR5so3MzVi"
TRIBUTE_URL = "https://t.me/tribute/app?startapp=sN2w"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

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
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Подписаться", url="https://t.me/voiceinsideglxy"))
        markup.add(types.InlineKeyboardButton("✅ Проверить", callback_data="check_free"))
        bot.edit_message_text("💬 Бесплатный чат
Подпишись → получи доступ:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "vip":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Оплатить 100₽", url=TRIBUTE_URL))
        markup.add(types.InlineKeyboardButton("✅ Проверить VIP", callback_data="check_vip"))
        bot.edit_message_text("💎 VIP канал
100₽/мес • Эксклюзив
Оплати → добавлю!", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "services":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 @Fullllmooooooooooooo", url="https://t.me/Fullllmooooooooooooo"))
        bot.edit_message_text("🎛️ Услуги:
Сведение от 3000₽
Мастеринг 3000₽
Полный пакет 10000₽", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "check_free":
        try:
            status = bot.get_chat_member(CHANNEL_FREE, call.from_user.id).status
            if status in ['member','administrator','creator']:
                bot.edit_message_text("✅ Доступ к чату:
" + CHAT_FREE, call.message.chat.id, call.message.message_id)
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("📢 Подписаться", url="https://t.me/voiceinsideglxy"))
                markup.add(types.InlineKeyboardButton("🔄 Проверить", callback_data="check_free"))
                bot.edit_message_text("❌ Подпишись сначала!", call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            bot.answer_callback_query(call.id, "Бот не админ канала!")
    
    elif call.data == "check_vip":
        try:
            status = bot.get_chat_member(CHANNEL_VIP, call.from_user.id).status
            if status in ['member','administrator','creator']:
                bot.edit_message_text("✅ VIP доступ:
" + CHAT_VIP, call.message.chat.id, call.message.message_id)
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("💳 Оплатить 100₽", url=TRIBUTE_URL))
                bot.edit_message_text("❌ Оплати VIP!", call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            bot.answer_callback_query(call.id, "Бот не админ VIP!")

if __name__ == "__main__":
    print("🚀 Бот запущен!")
    bot.polling(none_stop=True)
