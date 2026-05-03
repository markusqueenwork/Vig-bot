import asyncio
import logging
import sqlite3
import uuid
from datetime import date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import yookassa
import os

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8294451648:AAFV-vMPVo4wHbkjjnN6W5_5Q39BxcTwCpg')

# Данные ЮKassa
YOOKASSA_SHOP_ID = "1319443"
YOOKASSA_SECRET_KEY = "live_oERkhR1uKbbSskCwVY_SzaLbXH1O5P4egEL-toqLPJA"

# Ссылка на ваш закрытый чат
INVITE_LINK = "https://t.me/+aSbD7SmXaf8yNGIy"

# ID чата — вычислится автоматически
CHAT_ID = None

# Настройки подписки
PRICE = 300  # рублей
DAYS = 30

# Username бота
BOT_USERNAME = "voiceinsideglxy"

# ==================== НАСТРОЙКА ====================
yookassa.Configuration.account_id = YOOKASSA_SHOP_ID
yookassa.Configuration.secret_key = YOOKASSA_SECRET_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

pending_payments = {}

# ==================== ПОЛУЧЕНИЕ ID ЧАТА ====================
async def get_chat_id(app: Application):
    global CHAT_ID
    try:
        invite = await app.bot.get_chat(INVITE_LINK)
        CHAT_ID = invite.id
        logger.info(f"✅ ID чата: {CHAT_ID}")
    except Exception as e:
        logger.error(f"❌ Не удалось получить ID чата: {e}")

# ==================== КОМАНДЫ ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔒 Получить доступ (300 руб./30 дн.)", callback_data="pay")],
        [InlineKeyboardButton("📋 Моя подписка", callback_data="my_sub")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Voice Inside Galaxy\n\n"
        "Доступ в закрытый чат — 300 руб./30 дней.",
        reply_markup=reply_markup
    )


async def my_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
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
            await query.edit_message_text(
                f"✅ Подписка активна\n"
                f"Осталось дней: {days_left}\n"
                f"Действует до: {expire_date.strftime('%d.%m.%Y')}"
            )
        else:
            await query.edit_message_text("❌ Подписка истекла. Нажмите /start чтобы продлить.")
    else:
        await query.edit_message_text("У вас нет активной подписки. Нажмите /start чтобы оформить.")


async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

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

    keyboard = [
        [InlineKeyboardButton("💳 Перейти к оплате", url=payment.confirmation.confirmation_url)],
        [InlineKeyboardButton("✅ Я оплатил", callback_data="check_payment")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"💰 Доступ в закрытый чат\n\n"
        f"Срок: {DAYS} дней\n"
        f"Цена: {PRICE} руб.\n\n"
        f"1. Нажмите «Перейти к оплате»\n"
        f"2. Оплатите\n"
        f"3. Вернитесь и нажмите «Я оплатил»",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    payment_id = pending_payments.get(user_id)

    if not payment_id:
        await query.edit_message_text("❌ Нет активного платежа. Нажмите /start.")
        return

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
                invite_link = await context.bot.create_chat_invite_link(
                    chat_id=CHAT_ID,
                    member_limit=1
                )
                link = invite_link.invite_link
            except Exception as e:
                logger.error(f"Ошибка создания ссылки: {e}")
                link = "⚠️ Не удалось создать ссылку. Обратитесь в поддержку."
        else:
            link = INVITE_LINK

        await query.edit_message_text(
            f"✅ Оплата прошла!\n"
            f"Подписка до: {new_expire.strftime('%d.%m.%Y')}\n\n"
            f"🔗 {link}\n\n"
            f"Ссылка одноразовая. /start — главное меню."
        )
    else:
        await query.edit_message_text(
            "⏳ Платёж не найден.\n\n"
            "Если оплатили — подождите пару минут.\n"
            "Нажмите /start чтобы проверить снова."
        )


async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🔒 Получить доступ (300 руб./30 дн.)", callback_data="pay")],
        [InlineKeyboardButton("📋 Моя подписка", callback_data="my_sub")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "Voice Inside Galaxy\n\n"
        "Доступ в закрытый чат — 300 руб./30 дней.",
        reply_markup=reply_markup
    )


# ==================== ПРОВЕРКА ПОДПИСОК ====================

async def check_subscriptions(context: ContextTypes.DEFAULT_TYPE):
    """
    Эта функция запускается раз в день (в 10:00 утра).
    Проверяет всех пользователей в базе:
    - У кого срок истёк → кикает из чата и удаляет из базы
    - У кого срок истекает через 3 дня → отправляет напоминание
    """
    if not CHAT_ID:
        logger.warning("❌ Невозможно проверить подписки: ID чата неизвестен")
        return

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    today = date.today()

    # 1. КИКАЕМ ПРОСРОЧЕННЫХ — у кого expire_date < сегодня
    cursor.execute("SELECT user_id FROM subscriptions WHERE expire_date < ?", (today,))
    to_kick = cursor.fetchall()

    for (user_id,) in to_kick:
        try:
            # Баним (выгоняем из чата)
            await context.bot.ban_chat_member(chat_id=CHAT_ID, user_id=user_id)
            # Сразу разбаниваем — чтобы мог вернуться, если заплатит снова
            await context.bot.unban_chat_member(chat_id=CHAT_ID, user_id=user_id)
            # Уведомляем
            await context.bot.send_message(
                user_id,
                "❌ Подписка истекла. Доступ в чат закрыт.\nНажмите /start чтобы продлить."
            )
        except Exception as e:
            logger.warning(f"Не удалось кикнуть {user_id}: {e}")
        # Удаляем запись из базы
        cursor.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))

    # 2. НАПОМИНАЕМ ТЕМ, У КОГО ОСТАЛОСЬ 3 ДНЯ
    remind_date = today + timedelta(days=3)
    cursor.execute("""
        SELECT user_id FROM subscriptions
        WHERE expire_date = ? AND is_reminded = 0
    """, (remind_date,))
    to_remind = cursor.fetchall()

    for (user_id,) in to_remind:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("💳 Продлить подписку", callback_data="pay")
        ]])
        try:
            await context.bot.send_message(
                user_id,
                "⚠️ Подписка закончится через 3 дня.\nПродлите, чтобы не потерять доступ.",
                reply_markup=keyboard
            )
            # Помечаем, что напомнили — чтобы не спамить каждый день
            cursor.execute("UPDATE subscriptions SET is_reminded = 1 WHERE user_id = ?", (user_id,))
        except Exception as e:
            logger.warning(f"Не удалось напомнить {user_id}: {e}")

    conn.commit()
    conn.close()


# ==================== ОБРАБОТЧИКИ ====================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "pay":
        await pay(update, context)
    elif data == "check_payment":
        await check_payment(update, context)
    elif data == "my_sub":
        await my_sub(update, context)
    elif data == "back_to_start":
        await back_to_start(update, context)


# ==================== ЗАПУСК ====================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # При старте получаем ID чата
    app.job_queue.run_once(lambda ctx: asyncio.create_task(get_chat_id(app)), when=1)

    # Планировщик — проверка раз в день в 10:00
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_subscriptions, 'cron', hour=10, minute=0, args=[app])
    scheduler.start()

    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    init_db()
    main()