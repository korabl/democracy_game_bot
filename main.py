from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from user_interaction import start, start_game, start_character_creation, receive_character_details
from user_interaction import start, start_game, start_character_creation
from dotenv import load_dotenv
import os

# Загружаем переменные из .env
load_dotenv()

# Читаем переменную окружения для определения текущего окружения
ENV = os.getenv("ENV")  # Получаем 'development' или 'production'

# Читаем API ключи для теста и продакшн
TELEGRAM_API_KEY_TEST = os.getenv("TELEGRAM_API_KEY_TEST")
TELEGRAM_API_KEY_PROD = os.getenv("TELEGRAM_API_KEY_PROD")

# В зависимости от окружения выбираем нужный API ключ
if ENV == "production":
    TELEGRAM_API_KEY = TELEGRAM_API_KEY_PROD
else:
    TELEGRAM_API_KEY = TELEGRAM_API_KEY_TEST

print(f"Using bot API: {TELEGRAM_API_KEY}")  # Для проверки, какой ключ используется


def main():
    # Создаем приложение с API ключом
    application = Application.builder().token(TELEGRAM_API_KEY).build()

    # Добавляем обработчики команд и нажатий на кнопки
    application.add_handler(CommandHandler("start", start))  # Обработчик для команды /start
    application.add_handler(CallbackQueryHandler(start_game, pattern='start_game'))  # Обработчик для кнопки "Начать игру"
    application.add_handler(CallbackQueryHandler(start_character_creation, pattern='start_character_creation'))  # Обработчик для кнопки "Создать персонажа"
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_character_details))  # Обработчик для получения описания персонажа

    application.run_polling()

if __name__ == "__main__":
    main()