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

# Данные ЮKassa
YOOKASSA_SHOP_ID = "1319443"
YOOKASSA_SECRET_KEY = "live_oERkhR1uKbbSskCwVY_SzaLbXH1O5P4egEL-toqLPJA"

# Ссылка на ваш закрытый чат (постоянная, для fallback)
INVITE_LINK = "https://t.me/+aSbD7SmXaf8yNGIy"

# ID чата — нужно получить вручную
CHAT_ID = None  # ← замените на ID, когда получите (например, -1001234567890)

# Настройки подписки
PRICE = 300
DAYS = 30

# Username бота
BOT_USERNAME = "voiceinsideglxy"

# ==================== НАСТРОЙКА ЮKASSA ====================
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

# Временное хранилище платежей
pending_payments = {}

# ==================== БОТ ====================
bot = telebot.TeleBot(BOT_TOKEN)
bot.remove_webhook()

# ==================== КОМАНДЫ ====================

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("🔒 Получить доступ (300 руб./30 дн.)", callback_data="pay"),
        types.InlineKeyboardButton("📋 Моя подписка", callback_data="my_sub")
    )
    bot.send_message(
        message.chat.id,
        "Voice Inside Galaxy\n\nДоступ в закрытый чат — 300 руб./30 дней.",
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "pay":
        pay(call)
    elif call.data == "check_payment":
        check_payment(call)
    elif call.data == "my_sub":
        my_sub(call)
    elif call.data == "back_to_start":
        back_to_start(call)


def pay(call):
    """Создание платежа"""
    user_id = call.from_user.id
    user_name = call.from_user.first_name

    # Создаём платёж в ЮKassa
    idempotency_key = str(uuid.uuid4())
    payment = yookassa.Payment.create({
        "amount": {
            "value": str(PRICE),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"https://t.me/{BOT_USERNAME}"
        },
        "capture": True,
        "description": f"Доступ в закрытый чат на {DAYS} дн.",
        "metadata": {
            "telegram_user_id": str(user_id)
        }
    }, idempotency_key)

    pending_payments[user_id] = payment.id

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("💳 Перейти к оплате", url=payment.confirmation.confirmation_url),
        types.InlineKeyboardButton("✅ Я оплатил", callback_data="check_payment"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")
    )

    bot.edit_message_text(
        f"💰 Доступ в закрытый чат\n\n"
        f"Срок: {DAYS} дней\n"
        f"Цена: {PRICE} руб.\n\n"
        f"1. Нажмите «Перейти к оплате»\n"
        f"2. Оплатите\n"
        f"3. Вернитесь и нажмите «Я оплатил»",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


def check_payment(call):
    """Проверка статуса платежа"""
    user_id = call.from_user.id
    payment_id = pending_payments.get(user_id)

    if not payment_id:
        bot.edit_message_text(
            "❌ Нет активного платежа. Нажмите /start.",
            call.message.chat.id,
            call.message.message_id
        )
        return

    try:
        payment = yookassa.Payment.find_one(payment_id)

        if payment.status == "succeeded":
            del pending_payments[user_id]

            # Сохраняем в базу
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

            # Создаём ссылку на чат
            if CHAT_ID:
                try:
                    invite_link = bot.create_chat_invite_link(
                        chat_id=CHAT_ID,
                        member_limit=1
                    )
                    link = invite_link.invite_link
                except Exception as e:
                    print(f"Ошибка создания ссылки: {e}")
                    link = "⚠️ Не удалось создать ссылку.\nВот постоянная ссылка: " + INVITE_LINK
            else:
                link = INVITE_LINK

            bot.edit_message_text(
                f"✅ Оплата прошла!\n"
                f"Подписка до: {new_expire.strftime('%d.%m.%Y')}\n\n"
                f"🔗 {link}\n\n"
                f"Ссылка одноразовая (если сгенерирована). /start — главное меню.",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            bot.edit_message_text(
                "⏳ Платёж не найден.\n\n"
                "Если оплатили — подождите пару минут.\n"
                "Нажмите /start чтобы проверить снова.",
                call.message.chat.id,
                call.message.message_id
            )
    except Exception as e:
        print(f"Ошибка проверки платежа: {e}")
        bot.edit_message_text(
            "⏳ Платёж не найден.\nПопробуйте позже.",
            call.message.chat.id,
            call.message.message_id
        )


def my_sub(call):
    """Проверка статуса подписки"""
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
                f"✅ Подписка активна\n"
                f"Осталось дней: {days_left}\n"
                f"Действует до: {expire_date.strftime('%d.%m.%Y')}",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            bot.edit_message_text(
                "❌ Подписка истекла. Нажмите /start чтобы продлить.",
                call.message.chat.id,
                call.message.message_id
            )
    else:
        bot.edit_message_text(
            "У вас нет активной подписки. Нажмите /start чтобы оформить.",
            call.message.chat.id,
            call.message.message_id
        )


def back_to_start(call):
    """Возврат в главное меню"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("🔒 Получить доступ (300 руб./30 дн.)", callback_data="pay"),
        types.InlineKeyboardButton("📋 Моя подписка", callback_data="my_sub")
    )
    bot.edit_message_text(
        "Voice Inside Galaxy\n\nДоступ в закрытый чат — 300 руб./30 дней.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )


# ==================== ПРОВЕРКА ПОДПИСОК ====================

def check_subscriptions():
    """Ежедневная проверка подписок"""
    if not CHAT_ID:
        print("❌ CHAT_ID не задан. Пропускаю проверку.")
        return

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    today = date.today()

    # Кикаем просроченных
    cursor.execute("SELECT user_id FROM subscriptions WHERE expire_date < ?", (today,))
    to_kick = cursor.fetchall()

    for (user_id,) in to_kick:
        try:
            bot.ban_chat_member(chat_id=CHAT_ID, user_id=user_id)
            bot.unban_chat_member(chat_id=CHAT_ID, user_id=user_id)
            bot.send_message(user_id, "❌ Подписка истекла. Доступ в чат закрыт.\nНажмите /start чтобы продлить.")
        except Exception as e:
            print(f"Не удалось кикнуть {user_id}: {e}")
        cursor.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))

    # Напоминаем за 3 дня
    remind_date = today + timedelta(days=3)
    cursor.execute("""
        SELECT user_id FROM subscriptions
        WHERE expire_date = ? AND is_reminded = 0
    """, (remind_date,))
    to_remind = cursor.fetchall()

    for (user_id,) in to_remind:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("💳 Продлить подписку", callback_data="pay"))
        try:
            bot.send_message(
                user_id,
                "⚠️ Подписка закончится через 3 дня.\nПродлите, чтобы не потерять доступ.",
                reply_markup=keyboard
            )
            cursor.execute("UPDATE subscriptions SET is_reminded = 1 WHERE user_id = ?", (user_id,))
        except Exception as e:
            print(f"Не удалось напомнить {user_id}: {e}")

    conn.commit()
    conn.close()


# Запуск планировщика в отдельном потоке
def run_scheduler():
    schedule.every().day.at("10:00").do(check_subscriptions)
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

# ==================== ЗАПУСК ====================

print("Бот запущен!")
bot.polling(none_stop=True)