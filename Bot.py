import telebot
from telebot import types
import sqlite3
import uuid
import os
from datetime import date, timedelta, time
import threading
import schedule
import yookassa

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8294451648:AAFV-vMPVo4wHbkjjnN6W5_5Q39BxcTwCpg')

YOOKASSA_SHOP_ID = "1319443"
YOOKASSA_SECRET_KEY = "live_oERkhR1uKbbSskCwVY_SzaLbXH1O5P4egEL-toqLPJA"

INVITE_LINK = "https://t.me/+aSbD7SmXaf8yNGIy"
TELEGRAM_CHANNEL = "https://t.me/voiceinsideglxy"
CHAT_ID = None
PRICE = 300
DAYS = 30
BOT_USERNAME = "voiceinsideglxy"

yookassa.Configuration.account_id = YOOKASSA_SHOP_ID
yookassa.Configuration.secret_key = YOOKASSA_SECRET_KEY

# ==================== БАЗА ДАННЫХ ====================
def init_db():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER PRIMARY KEY,
            expire_date TEXT NOT NULL,
            is_reminded INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()
pending_payments = {}

# ==================== БОТ ====================
bot = telebot.TeleBot(BOT_TOKEN)
bot.remove_webhook()

# ==================== ГЛАВНОЕ МЕНЮ ====================
@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("Telegram канал", url=TELEGRAM_CHANNEL),
        types.InlineKeyboardButton("Voice Inside Galaxy +", callback_data="pay_info")
    )
    bot.send_message(
        message.chat.id,
        "Voice Inside Galaxy\n\nВыберите действие:",
        reply_markup=keyboard
    )

# ==================== ОБРАБОТКА КНОПОК ====================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "pay_info":
        pay_info(call)
    elif call.data == "pay":
        pay(call)
    elif call.data == "check_payment":
        check_payment(call)
    elif call.data == "my_sub":
        my_sub(call)
    elif call.data == "back_to_start":
        back_to_start(call)

def pay_info(call):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("Оплатить", callback_data="pay"),
        types.InlineKeyboardButton("Проверить оплату", callback_data="check_payment"),
        types.InlineKeyboardButton("Моя подписка", callback_data="my_sub"),
        types.InlineKeyboardButton("Назад", callback_data="back_to_start")
    )
    bot.edit_message_text(
        "Voice Inside Galaxy +\n\n"
        "Закрытое сообщество с уникальным контентом.\n\n"
        "Нажмите «Оплатить» для оформления подписки.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

def pay(call):
    user_id = call.from_user.id
    idempotency_key = str(uuid.uuid4())
    payment = yookassa.Payment.create({
        "amount": {"value": str(PRICE), "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": f"https://t.me/{BOT_USERNAME}"},
        "capture": True,
        "description": f"Подписка на {DAYS} дн.",
        "metadata": {"telegram_user_id": str(user_id)}
    }, idempotency_key)

    pending_payments[user_id] = payment.id

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("Перейти к оплате", url=payment.confirmation.confirmation_url),
        types.InlineKeyboardButton("Я оплатил", callback_data="check_payment"),
        types.InlineKeyboardButton("Назад", callback_data="pay_info")
    )
    bot.edit_message_text(
        "Оформление подписки\n\n"
        "1. Нажмите «Перейти к оплате»\n"
        "2. Оплатите\n"
        "3. Вернитесь и нажмите «Я оплатил»",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

def check_payment(call):
    user_id = call.from_user.id
    payment_id = pending_payments.get(user_id)

    if not payment_id:
        bot.edit_message_text("Нет активного платежа.", call.message.chat.id, call.message.message_id)
        return

    try:
        payment = yookassa.Payment.find_one(payment_id)
        if payment.status == "succeeded":
            del pending_payments[user_id]
            conn = sqlite3.connect("bot.db")
            cursor = conn.cursor()
            new_expire = date.today() + timedelta(days=DAYS)
            cursor.execute("""
                INSERT INTO subscriptions (user_id, expire_date, is_reminded)
                VALUES (?, ?, 0)
                ON CONFLICT(user_id) DO UPDATE SET expire_date = ?, is_reminded = 0
            """, (user_id, new_expire, new_expire))
            conn.commit()
            conn.close()

            if CHAT_ID:
                try:
                    invite_link = bot.create_chat_invite_link(chat_id=CHAT_ID, member_limit=1)
                    link = invite_link.invite_link
                except:
                    link = INVITE_LINK
            else:
                link = INVITE_LINK

            bot.edit_message_text(
                f"Оплата прошла.\n\n"
                f"Подписка до: {new_expire.strftime('%d.%m.%Y')}\n\n"
                f"Ссылка на чат:\n{link}\n\n"
                f"Ссылка одноразовая.",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            bot.edit_message_text(
                "Платёж не найден. Если оплатили — подождите пару минут.",
                call.message.chat.id,
                call.message.message_id
            )
    except:
        bot.edit_message_text("Платёж пока не найден.", call.message.chat.id, call.message.message_id)

def my_sub(call):
    user_id = call.from_user.id
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT expire_date FROM subscriptions WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        expire_date = date.fromisoformat(row[0])
        today = date.today()
        if expire_date >= today:
            days_left = (expire_date - today).days
            bot.edit_message_text(
                f"Подписка активна\nОсталось дней: {days_left}\nДействует до: {expire_date.strftime('%d.%m.%Y')}",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            bot.edit_message_text("Подписка истекла.", call.message.chat.id, call.message.message_id)
    else:
        bot.edit_message_text("У вас нет активной подписки.", call.message.chat.id, call.message.message_id)

def back_to_start(call):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("Telegram канал", url=TELEGRAM_CHANNEL),
        types.InlineKeyboardButton("Voice Inside Galaxy +", callback_data="pay_info")
    )
    bot.edit_message_text(
        "Voice Inside Galaxy\n\nВыберите действие:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

# ==================== ПРОВЕРКА ПОДПИСОК ====================
def check_subscriptions():
    if not CHAT_ID:
        return
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    today = date.today()

    cursor.execute("SELECT user_id FROM subscriptions WHERE expire_date < ?", (today,))
    for (user_id,) in cursor.fetchall():
        try:
            bot.ban_chat_member(chat_id=CHAT_ID, user_id=user_id)
            bot.unban_chat_member(chat_id=CHAT_ID, user_id=user_id)
            bot.send_message(user_id, "Подписка истекла. Доступ в чат закрыт.")
        except:
            pass
        cursor.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))

    remind_date = today + timedelta(days=3)
    cursor.execute("SELECT user_id FROM subscriptions WHERE expire_date = ? AND is_reminded = 0", (remind_date,))
    for (user_id,) in cursor.fetchall():
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Продлить подписку", callback_data="pay"))
        try:
            bot.send_message(user_id, "Подписка закончится через 3 дня.", reply_markup=keyboard)
            cursor.execute("UPDATE subscriptions SET is_reminded = 1 WHERE user_id = ?", (user_id,))
        except:
            pass

    conn.commit()
    conn.close()

def run_scheduler():
    schedule.every().day.at("10:00").do(check_subscriptions)
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

print("Бот запущен!")
bot.polling(none_stop=True)