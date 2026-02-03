import telebot
import os
import time
import logging

# Логирование для Bothost
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен из Bothost переменных
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    logger.error("❌ BOT_TOKEN не найден в переменных Bothost!")
    exit(1)

try:
    bot = telebot.TeleBot(TOKEN)
    logger.info(f"🚀 Bot инициализирован: {TOKEN[:20]}...")
except Exception as e:
    logger.error(f"❌ Ошибка инициализации бота: {e}")
    exit(1)

@bot.message_handler(commands=['start'])
def start_handler(message):
    logger.info(f"📨 /start от {message.from_user.id}")
    try:
        bot.reply_to(message, 
            "🎉 *Voice Inside Galaxy*

"
            "✅ Bothost 24/7 ONLINE!
"
            "🔄 Бесконечный цикл работает
"
            "🚀 Готов к работе!")
    except Exception as e:
        logger.error(f"Ошибка /start: {e}")

@bot.message_handler(commands=['help'])
def help_handler(message):
    help_text = """
🤖 *Voice Galaxy Bot*

/start - Запуск бота
/help - Помощь
/ping - Проверка связи

📡 Все сообщения эхом
    """
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['ping'])
def ping_handler(message):
    bot.reply_to(message, "🏓 PONG! Bothost работает!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    logger.info(f"📨 Сообщение от {message.from_user.id}: {message.text[:50]}")
    try:
        bot.reply_to(message, f"📱 Получено: `{message.text}`

"
                             f"👤 ID: `{message.from_user.id}`")
    except Exception as e:
        logger.error(f"Ошибка echo: {e}")

@bot.message_handler(content_types=['voice', 'audio', 'photo', 'document'])
def media_handler(message):
    bot.reply_to(message, "📎 Файл получен! (голос/аудио/фото/документ)")

if __name__ == '__main__':
    logger.info("🔄 Запуск polling...")
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            logger.error(f"❌ Polling упал: {e}. Перезапуск через 5 сек...")
            time.sleep(5)
