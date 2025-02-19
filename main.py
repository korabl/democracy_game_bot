from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from user_interaction import start, start_game, start_character_creation, receive_character_details
from user_interaction import start, start_game, start_character_creation


# Ваш API ключ для Telegram
API_KEY = "7889681920:AAG1uIXd9jUfyqrNGViBYc_Qug6gGnpn03o"  # ПРОД
#API_KEY = ""   #ТЕСТ

def main():
    # Создаем приложение с API ключом
    application = Application.builder().token(API_KEY).build()

    # Добавляем обработчики команд и нажатий на кнопки
    application.add_handler(CommandHandler("start", start))  # Обработчик для команды /start
    application.add_handler(CallbackQueryHandler(start_game, pattern='start_game'))  # Обработчик для кнопки "Начать игру"
    application.add_handler(CallbackQueryHandler(start_character_creation, pattern='start_character_creation'))  # Обработчик для кнопки "Создать персонажа"
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_character_details))  # Обработчик для получения описания персонажа

    application.run_polling()

if __name__ == "__main__":
    main()
