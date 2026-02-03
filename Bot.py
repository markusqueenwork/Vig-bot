import telebot
from telebot import types
import os

TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_FREE = "-1001524100665"
CHANNEL_VIP = "-1003727929609"
CHAT_FREE = "https://t.me/vigcomm"
CHAT_VIP = "https://t.me/+UZ2GwssR5so3MzVi"
TRIBUTE_URL = "https://t.me/tribute/app?startapp=sN2w"
YOUR_USERNAME = "@Fullllmooooooooooooo"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("💬 Бесплатный чат", callback_data="free"))
    markup.add(types.InlineKeyboardButton("💎 VIP 100р/мес", callback_data="vip"))
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
        markup.add(types.InlineKeyboardButton("💳 Оплатить 100р", url=TRIBUTE_URL))
        markup.add(types.InlineKeyboardButton("✅ Проверить VIP", callback_data="check_vip"))
        bot.edit_message_text("💎 VIP канал
100р/мес • Эксклюзив
Оплати → добавлю!", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "services":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("📝 Написать нам", url="https://t.me/Fullllmooooooooooooo"))
        markup.add(types.InlineKeyboardButton("💰 Полный прайс", callback_data="prices"))
        bot.edit_message_text("🎛️ Сведение/Мастеринг

Нажми для подробностей:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "prices":
        text = """🌾 Здравствуйте, команда "Voice Inside Galaxy"

Услуги:
1️⃣ Сведение+мастеринг: 10000р
2️⃣ Коррекция вокала: 5000р
3️⃣ Текст песни: 3500р
4️⃣ Аранжировка: от 5000р
5️⃣ Сведение бита: от 3000р
6️⃣ Мастеринг: 3000р

Оплата:
1. Сбербанк
2. Крипта Telegram (-10%)
3. USDC/USDT

Реклама: Markusqueenwork@gmail.com

⚠️ Важно:
Полная предоплата
3 правки на проект
{} для заказа""".format(YOUR_USERNAME)
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✉️ Заказать услугу", url="https://t.me/Fullllmooooooooooooo"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
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
                markup.add(types.InlineKeyboardButton("💳 Оплатить 100р", url=TRIBUTE_URL))
                bot.edit_message_text("❌ Оплати VIP!", call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            bot.answer_callback_query(call.id, "Бот не админ VIP!")

if __name__ == "__main__":
    print("🚀 Бот запущен!")
    bot.polling(none_stop=True)
