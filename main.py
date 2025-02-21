from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from user_interaction import start, start_game, start_character_creation, receive_character_details, receive_initiative_details, start_initiation
from dotenv import load_dotenv
from states import WAITING_FOR_CHARACTER_DETAILS, WAITING_FOR_INITIATIVE
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

# Настройка ConversationHandler
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_character_creation, pattern='start_character_creation')],  # Начинаем с нажатия кнопки
    states={
        WAITING_FOR_CHARACTER_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_character_details)],  # Сбор описания персонажа
        WAITING_FOR_INITIATIVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_initiative_details)]  # Сбор инициативы
    },
    fallbacks=[CommandHandler('cancel', lambda update, context: ConversationHandler.END)]  # Обработчик отмены
    )

def main():
    # Создаем приложение с API ключом
    application = Application.builder().token(TELEGRAM_API_KEY).build()

    # Добавляем обработчики команд и нажатий на кнопки
    application.add_handler(CommandHandler("start", start))  # Обработчик для команды /start
    application.add_handler(CallbackQueryHandler(start_game, pattern='start_game'))  # Обработчик для кнопки "Начать игру"
    #application.add_handler(CallbackQueryHandler(start_character_creation, pattern='start_character_creation'))  # Обработчик для кнопки "Создать персонажа"
    application.add_handler(CallbackQueryHandler(start_initiation, pattern='start_initiation'))  # Обработчик для кнопки "Внести инициативу"
        
    # Регистрация обработчиков
    application.add_handler(conv_handler)

    # Запуск приложения
    application.run_polling()

if __name__ == "__main__":
    main()
