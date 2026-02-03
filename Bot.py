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
    markup.add(types.InlineKeyboardButton("Besplatny chat", callback_data="free"))
    markup.add(types.InlineKeyboardButton("VIP 100rub/mes", callback_data="vip"))
    markup.add(types.InlineKeyboardButton("Uslugi", callback_data="services"))
    bot.send_message(message.chat.id, "Voice Inside Galaxy", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "free":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Podpischis", url="https://t.me/voiceinsideglxy"))
        markup.add(types.InlineKeyboardButton("Proverit", callback_data="check_free"))
        bot.edit_message_text("Besplatny chat. Podpischis na kanal!", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "vip":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Oplatit 100rub", url=TRIBUTE_URL))
        markup.add(types.InlineKeyboardButton("Proverit VIP", callback_data="check_vip"))
        bot.edit_message_text("VIP kanal 100rub/mes. Oplati dobavlyu!", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "services":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("Napisat nam", url="https://t.me/Fullllmooooooooooooo"))
        markup.add(types.InlineKeyboardButton("Prais", callback_data="prices"))
        bot.edit_message_text("Svedenie Mastering. Nai mi podrobnosti!", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "prices":
        text = """Zdravstvuyte! Voice Inside Galaxy

Uslugi:
1. Svedenie + mastering: 10000rub
2. Korekciya vokala: 5000rub
3. Tekst pesni: 3500rub
4. Aranzhirovka ot 5000rub
5. Svedenie bita ot 3000rub
6. Mastering 3000rub

Oплата:
1. Sberbank
2. Kripta Telegram -10%
3. USDC base USDT ton

Reklama: Markusqueenwork@gmail.com

Vazhno:
1. Polnaa predoplata
2. Oплата ne otmeniaetsa
3. 3 pravki na proekt
4. Chestnaa rabota
5. Mahinacii = blok

{} dla zaказа""".format(YOUR_USERNAME)
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Zakazat", url="https://t.me/Fullllmooooooooooooo"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "check_free":
        try:
            status = bot.get_chat_member(CHANNEL_FREE, call.from_user.id).status
            if status in ['member','administrator','creator']:
                bot.edit_message_text("Dostup k chatu: " + CHAT_FREE, call.message.chat.id, call.message.message_id)
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Podpischis", url="https://t.me/voiceinsideglxy"))
                markup.add(types.InlineKeyboardButton("Proverit", callback_data="check_free"))
                bot.edit_message_text("Podpischis snachala!", call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            bot.answer_callback_query(call.id, "Bot ne admin kanala!")
    
    elif call.data == "check_vip":
        try:
            status = bot.get_chat_member(CHANNEL_VIP, call.from_user.id).status
            if status in ['member','administrator','creator']:
                bot.edit_message_text("VIP dostup: " + CHAT_VIP, call.message.chat.id, call.message.message_id)
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Oplatit 100rub", url=TRIBUTE_URL))
                bot.edit_message_text("Oplati VIP!", call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            bot.answer_callback_query(call.id, "Bot ne admin VIP!")

if __name__ == "__main__":
    print("Bot zapuschen!")
    bot.polling(none_stop=True)
