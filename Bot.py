import telebot
from telebot import types
import requests
import os

# ==================== НАСТРОЙКИ ====================
TOKEN = os.environ.get('BOT_TOKEN', '8294451648:AAFV-vMPVo4wHbkjjnN6W5_5Q39BxcTwCpg')
CHANNEL_VIP = "-1003906026623"
CHAT_VIP = "https://t.me/+aSbD7SmXaf8yNGIy"
TELEGRAM_CHANNEL = "https://t.me/voiceinsideglxy"
BACKEND_URL = "https://voiceinside-backend.onrender.com"

# Тарифы
TARIFFS = {
    "1_month": {"name": "1 месяц", "price": 1, "days": 30},
    "3_months": {"name": "3 месяца", "price": 700, "days": 90},
    "6_months": {"name": "6 месяцев", "price": 1500, "days": 180},
    "1_year": {"name": "1 год", "price": 3500, "days": 365}
}

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# ==================== ГЛАВНОЕ МЕНЮ ====================
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("Telegram канал", url=TELEGRAM_CHANNEL))
    markup.add(types.InlineKeyboardButton("Voice Inside Galaxy +", callback_data="vip"))
    bot.send_message(message.chat.id, "Voice Inside Galaxy", reply_markup=markup)

# ==================== ОБРАБОТКА КНОПОК ====================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "vip":
        show_tariffs(call)
    elif call.data.startswith("tariff_"):
        select_tariff(call)
    elif call.data == "check_vip":
        check_vip(call)
    elif call.data == "back_to_vip":
        show_tariffs(call)


def show_tariffs(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("1 месяц — 300р", callback_data="tariff_1_month"))
    markup.add(types.InlineKeyboardButton("3 месяца — 700р", callback_data="tariff_3_months"))
    markup.add(types.InlineKeyboardButton("6 месяцев — 1500р", callback_data="tariff_6_months"))
    markup.add(types.InlineKeyboardButton("1 год — 3500р", callback_data="tariff_1_year"))
    markup.add(types.InlineKeyboardButton("Проверить доступ", callback_data="check_vip"))

    bot.edit_message_text(
        "Voice Inside Galaxy +\n\nВыберите срок подписки:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )


def select_tariff(call):
    tariff_key = call.data.replace("tariff_", "")
    tariff = TARIFFS.get(tariff_key)

    if not tariff:
        bot.answer_callback_query(call.id, "Тариф не найден")
        return

    user_id = call.from_user.id

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/bot/create-payment",
            json={
                "userId": user_id,
                "price": tariff["price"],
                "days": tariff["days"],
                "description": f"Подписка {tariff['name']} — {tariff['price']}р"
            },
            timeout=10
        )
        data = response.json()

        if data.get("success"):
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("Перейти к оплате", url=data["confirmationUrl"]))
            markup.add(types.InlineKeyboardButton("Проверить доступ", callback_data="check_vip"))
            markup.add(types.InlineKeyboardButton("Назад", callback_data="back_to_vip"))

            bot.edit_message_text(
                f"Voice Inside Galaxy +\n\n"
                f"Тариф: {tariff['name']}\n"
                f"Сумма: {tariff['price']}р\n\n"
                f"1. Нажмите «Перейти к оплате»\n"
                f"2. Оплатите\n"
                f"3. Вернитесь и нажмите «Проверить доступ»",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        else:
            bot.answer_callback_query(call.id, "Ошибка создания платежа")
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.answer_callback_query(call.id, "Сервис временно недоступен")


def check_vip(call):
    user_id = call.from_user.id

    try:
        response = requests.get(
            f"{BACKEND_URL}/api/bot/subscription",
            params={"user_id": user_id},
            timeout=10
        )
        data = response.json()

        if data.get("active"):
            bot.edit_message_text(
                f"Подписка активна.\n"
                f"Действует до: {data['expire_date']}\n"
                f"Осталось дней: {data['days_left']}\n\n"
                f"Доступ к чату: {CHAT_VIP}",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("1 месяц — 300р", callback_data="tariff_1_month"))
            markup.add(types.InlineKeyboardButton("3 месяца — 700р", callback_data="tariff_3_months"))
            markup.add(types.InlineKeyboardButton("6 месяцев — 1500р", callback_data="tariff_6_months"))
            markup.add(types.InlineKeyboardButton("1 год — 3500р", callback_data="tariff_1_year"))

            bot.edit_message_text(
                "Подписка не найдена или истекла.\n\nВыберите срок подписки:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
    except Exception as e:
        print(f"Ошибка проверки: {e}")
        bot.answer_callback_query(call.id, "Сервис временно недоступен")


if __name__ == "__main__":
    print("Бот запущен!")
    bot.polling(none_stop=True)