import telebot
from telebot import types
import requests
import os
import sqlite3
from datetime import datetime

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_VIP = "-1003906026623"
CHAT_VIP = "https://t.me/+aSbD7SmXaf8yNGIy"
TELEGRAM_CHANNEL = "https://t.me/voiceinsideglxy"
BACKEND_URL = "https://backend-voiceinsidegalaxy.amvera.io"

SONGS_CHAT_ID = -1003703009385
CHANNEL_USERNAME = "@voiceinsideglxy"

TARIFFS = {
    "1_month": {"name": "1 месяц", "price": 200, "days": 30},
    "3_months": {"name": "3 месяца", "price": 490, "days": 90},
    "6_months": {"name": "6 месяцев", "price": 990, "days": 180},
    "1_year": {"name": "1 год", "price": 1990, "days": 365}
}

bot = telebot.TeleBot(BOT_TOKEN)
bot.remove_webhook()

pending_payments = {}

# ==================== БАЗА ДАННЫХ ====================
def init_warnings_db():
    conn = sqlite3.connect("warnings.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warnings (
            user_id INTEGER PRIMARY KEY,
            message_id INTEGER,
            warned_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_warnings_db()

# ==================== ПРОВЕРКА ПОДПИСКИ НА КАНАЛ ====================
@bot.message_handler(
    func=lambda message: message.chat.id == SONGS_CHAT_ID,
    content_types=['text', 'audio', 'voice', 'document', 'video', 'video_note',
                   'photo', 'sticker', 'animation', 'contact', 'location',
                   'venue', 'poll', 'dice']
)
def check_channel_subscription(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"

    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        if status in ['member', 'administrator', 'creator']:
            return
    except:
        return

    sent = bot.reply_to(
        message,
        f"@{username}, вы не подписаны на {CHANNEL_USERNAME}"
    )

    conn = sqlite3.connect("warnings.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO warnings (user_id, message_id, warned_at)
        VALUES (?, ?, ?)
    """, (user_id, sent.message_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ==================== ПРОВЕРКА КТО ПОДПИСАЛСЯ ====================
def check_who_subscribed():
    conn = sqlite3.connect("warnings.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, message_id FROM warnings")
    rows = cursor.fetchall()

    for user_id, message_id in rows:
        try:
            status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
            if status in ['member', 'administrator', 'creator']:
                username = f"user_{user_id}"
                try:
                    user = bot.get_chat(user_id)
                    if user.username:
                        username = user.username
                except:
                    pass

                cursor.execute("DELETE FROM warnings WHERE user_id = ?", (user_id,))

                try:
                    bot.send_message(
                        SONGS_CHAT_ID,
                        f"@{username} подписался на канал",
                        reply_to_message_id=message_id
                    )
                except:
                    pass
        except:
            pass

    conn.commit()
    conn.close()

import threading
import time

def run_periodic_check():
    while True:
        time.sleep(60)
        try:
            check_who_subscribed()
        except:
            pass

threading.Thread(target=run_periodic_check, daemon=True).start()

# ==================== ГЛАВНОЕ МЕНЮ ====================
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("Telegram канал", url=TELEGRAM_CHANNEL))
    markup.add(types.InlineKeyboardButton("Voice Inside Galaxy +", callback_data="vip"))
    bot.send_message(message.chat.id, "Voice Inside Galaxy", reply_markup=markup)

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
            payment_id = data.get("paymentId")
            pending_payments[user_id] = payment_id

            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("Перейти к оплате", url=data["confirmationUrl"]))
            markup.add(types.InlineKeyboardButton("Я оплатил", callback_data="check_vip"))
            markup.add(types.InlineKeyboardButton("Назад", callback_data="back_to_vip"))

            bot.edit_message_text(
                f"Voice Inside Galaxy +\n\n"
                f"Тариф: {tariff['name']}\n"
                f"Сумма: {tariff['price']}р\n\n"
                f"1. Нажмите «Перейти к оплате»\n"
                f"2. Оплатите\n"
                f"3. Вернитесь и нажмите «Я оплатил»",
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
    payment_id = pending_payments.get(user_id)

    if not payment_id:
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/bot/subscription",
                params={"user_id": user_id},
                timeout=10
            )
            data = response.json()

            if data.get("active"):
                bot.edit_message_text(
                    f"Подписка активна\n"
                    f"Действует до: {data['expire_date']}\n"
                    f"Осталось дней: {data['days_left']}\n\n"
                    f"Доступ к чату: {CHAT_VIP}",
                    call.message.chat.id,
                    call.message.message_id
                )
            else:
                show_tariffs(call)
        except:
            bot.answer_callback_query(call.id, "Сервис временно недоступен")
        return

    try:
        response = requests.get(
            f"{BACKEND_URL}/api/payment/{payment_id}",
            timeout=10
        )
        data = response.json()

        if data.get("status") == "succeeded":
            del pending_payments[user_id]

            try:
                requests.post(
                    f"{BACKEND_URL}/api/bot/confirm-payment",
                    json={
                        "paymentId": payment_id,
                        "userId": user_id
                    },
                    timeout=10
                )
            except:
                pass

            bot.edit_message_text(
                f"Оплата прошла\n\n"
                f"Доступ к чату: {CHAT_VIP}\n\n"
                f"Если ссылка не работает, обратитесь в поддержку",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            bot.edit_message_text(
                "Оплата ещё не прошла\n\n"
                f"Если вы оплатили — подождите минуту и нажмите кнопку снова",
                call.message.chat.id,
                call.message.message_id
            )
    except Exception as e:
        print(f"Ошибка проверки: {e}")
        bot.answer_callback_query(call.id, "Сервис временно недоступен")

if __name__ == "__main__":
    print("Бот запущен!")
    bot.polling(none_stop=True)