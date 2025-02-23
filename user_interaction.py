import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from game_world import generate_world_from_gpt, generate_world_metrics, generate_character, generate_world_news, generate_world_changes
from database import save_world_to_db, create_user, save_world_metrics_to_db, save_chatacters_to_db, get_user_id_by_telegram_id, get_world_description_by_id, get_world_metrics_by_id, save_world_news_to_db
from dotenv import load_dotenv
from states import WAITING_FOR_CHARACTER_DETAILS, WAITING_FOR_INITIATIVE  # Импортируем состояния
import os
import random

logger = logging.getLogger(__name__)

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


### ОСНОВНОЙ ФУНКЦИОНАЛ ###

# Команда /start для бота
async def start(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id
    username = update.message.from_user.username
    logger.info(f"Команда /start от пользователя {update.message.from_user.username}")

    # Получаем user_id из базы данных по telegram_id
    user_id = get_user_id_by_telegram_id(telegram_id)

    # Сохраняем user_id в контексте, чтобы передать на следующем шаге
    context.user_data['user_id'] = user_id

    # Создаем пользователя при запуске бота
    create_user(telegram_id, username)

    # Отправляем приветственное сообщение
    intro_text = (
        "Добро пожаловать в мир, который мы будем строить! Нажмите 'Начать', чтобы начать игру и узнать, какие проблемы ждут вас."
    )

    # Создаем кнопку "Начать историю"
    keyboard = [
        [InlineKeyboardButton("Начать историю", callback_data='start_game')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(intro_text, reply_markup=reply_markup)

# Обработчик нажатия на кнопку "Начать историю"
async def start_game(update: Update, context: CallbackContext):
    logger.info("Обработка нажатия кнопки 'Начать историю'...")
    
    try:
        # Генерация мира через GPT
        logger.info("Попытка вызвать генерацию мира через GPT...")
        
        # Генерируем случайный год от -10 000 (первые общины) до 2025 (наши дни)
        game_year = random.randint(-10000, 2025)

        # Сохраняем world_id в контексте, чтобы передать на следующем шаге
        context.user_data['game_year'] = game_year

        world_data = await generate_world_from_gpt(game_year)  # Получаем описание мира

        # Записываем описание мира в базу данных
        world_id = save_world_to_db(game_year, world_data)  # Вставка в таблицу worlds

        if not world_id:
            await update.callback_query.message.edit_text("Ошибка при записи мира в базу данных.")
            return

        # Сохраняем world_id в контексте, чтобы передать на следующем шаге
        context.user_data['world_id'] = world_id

        # Логируем успешный вызов
        logger.info(f"Мир с ID {world_id} успешно записан в базу данных.")

        # Выводим описания мира пользователю без ожидания генерации метрик
        await update.callback_query.message.edit_text(f"{world_data}")

        # Второе сообщение с текстом "Давай сделаем персонажа"
        intro_text = "Давай теперь создадим персонажа!"

        keyboard = [
            [InlineKeyboardButton("Создать персонажа", callback_data='start_character_creation')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем сообщение о создании персонажа
        await update.callback_query.message.reply_text(intro_text, reply_markup=reply_markup)

        # Генерация метрик для мира
        logger.info("Попытка вызвать генерацию метрик для мира...")
        metrics_data = await generate_world_metrics(world_data)  # Генерация метрик от GPT

        if not metrics_data:
            await update.callback_query.message.edit_text("Ошибка при генерации метрик для мира.")
            return

        # Записываем метрики мира в базу данных
        metric_id = save_world_metrics_to_db(world_id, metrics_data)  # Вставка в таблицу world_metrics
        logger.info(f"Метрики мира с ID мира {world_id} успешно записаны в базу данных.")

    except Exception as e:
        await update.callback_query.message.edit_text("Произошла ошибка при генерации мира в обработчике нажатия кнопки 'Начать'.")
        logger.error(f"Ошибка при генерации мира: {e}")
    

# Обработчик для создания персонажа
async def start_character_creation(update: Update, context: CallbackContext):
    logger.info("Начинаем создание персонажа...")

    # Запрашиваем у пользователя имя персонажа
    await update.callback_query.message.edit_text("Расскажите о имя своём персонаже! Можешь поделиться любыми деталями, которыми захочется!\nНаример, имя, возрат, пофессия, харакетер.\nА если не хочется никого придумывать, просто напиши 'Любой'!")

    return WAITING_FOR_CHARACTER_DETAILS

# Эта функция срабатывает, когда пользователь отправляет описание своего персонажа
async def receive_character_details(update: Update, context: CallbackContext):
    character_details = update.message.text  # Получаем текст от пользователя
    logger.info("Получили описание персонажа от пользователя...")

    # Сохраняем данные в context, чтобы использовать их для генерации персонажа
    context.user_data['character_details'] = character_details

    # Получаем world_id и user_id из context
    world_id = context.user_data.get('world_id')
    user_id = context.user_data.get('user_id')  

    # Отправляем подтверждение пользователю
    await update.message.reply_text(f"Спасибо! Ты выбрал: {character_details}. Теперь я создам персонажа.")

    # Генерация персонажа с помощью GPT
    world_data = get_world_description_by_id(world_id)
    context.user_data['world_data'] = world_data  # Сохраняем описание мира в context
    character_description = await generate_character(world_data, character_details)
    context.user_data['character_description'] = character_description  # Сохраняем описание персонажа в context

    # Сохраняем персонажа в базу данных
    save_chatacters_to_db(world_id, user_id, character_description)  # Вставка в таблицу characters

    # Отправляем сгенерированное описание персонажа
    await update.message.reply_text(f"Вот твой персонаж: {character_description}")

    # Выводим дайджест актуальных новостей
    intro_text = "Вот твоя подборка актуальных новостей!"

    # Отправляем сообщение пользователю
    await update.message.reply_text(intro_text)

    # Подготавливаем дайджест новостей для пользователя
    logger.info("Попытка вызвать генерацию новостей для мира...")
    world_data = context.user_data.get('world_data')    # Получаем world_data из context
    world_id = context.user_data.get('world_id')        # Получаем world_id из context
    world_metrics = get_world_metrics_by_id(world_id)   # Получаем метрики мира из базы данных

    # Генерация новостей через GPT
    game_year = context.user_data.get('game_year')      # Получаем game_year из context
    world_news = await generate_world_news(game_year, world_data, world_metrics)  # Генерация новостей с использованием await
    logger.info(f"Генерация новостей завершена: {world_news}")

    # Отправляем новости пользователю
    if world_news:
        await update.message.reply_text(world_news)

        # Сохраняем новости в базу данных
        save_world_news_to_db(world_id, world_news)  # Вставка в таблицу world_new

    else:
        await update.message.reply_text("Не удалось получить новости. Попробуй позже.")

    # Отправляем сообщение с текстом "Давай внесём инициативу!"
    intro_text = "Давай теперь внесём инициативу!"

    # Создаем клавиатуру с кнопкой
    keyboard = [
        [InlineKeyboardButton("Внести инициативу", callback_data='start_initiation')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с кнопкой
    await update.message.reply_text(intro_text, reply_markup=reply_markup)

    return WAITING_FOR_INITIATIVE

# Обработчик для внесения инициативы (когда пользователь нажимает на кнопку)
async def start_initiation(update: Update, context: CallbackContext):
    logger.info("Начинаем внесение инициативы...")

    # Ответ на нажатие кнопки
    await update.callback_query.message.edit_text(
        "Опиши свою инициативу! Можешь поделиться любыми деталями, которыми захочется!\nНаример, какие проблемы ты видишь в мире, какие изменения хочешь внести, какие идеи у тебя есть.\nА если не хочется ничего придумывать, просто напиши 'Любой'!"
    )
    # Подтверждаем, что callback_query обработан
    await update.callback_query.answer()

    return WAITING_FOR_INITIATIVE  # Ожидаем текст инициативы

# Эта функция срабатывает, когда пользователь отправляет текст инициативы
async def receive_initiative_details(update: Update, context: CallbackContext):
    # Получаем текст инициативы от пользователя
    initiation_details = update.message.text

    # Сохраняем данные в context
    context.user_data['initiation_details'] = initiation_details

    # Отправляем подтверждение пользователю
    await update.message.reply_text(f"Спасибо! Твоя инициатива: {initiation_details}.")

    # Генерация изменений мира на основе инициативы от GPT
    next_game_year = context.user_data.get('game_year') + 1   # Получаем game_year из context
    context.user_data['game_year'] = next_game_year    # Перезаписываем next_game_year в context
    logger.info(f"Следующий год: {next_game_year}")

    world_data = context.user_data.get('world_data')    # Получаем world_data из context
    сharacter_description = context.user_data.get('character_description')  # Получаем character_description из context
    initiate_result = await generate_world_changes(сharacter_description, next_game_year, world_data, initiation_details)

    # Отправляем сгенерированное изменение мира
    await update.message.reply_text(f"Вот твой результат: {initiate_result}")

    # Выводим дайджест актуальных новостей
    intro_text = "Вот твоя подборка актуальных новостей спустя год!"

    # Отправляем сообщение пользователю
    await update.message.reply_text(intro_text)

    # Подготавливаем дайджест новостей для пользователя
    logger.info("Попытка вызвать генерацию новостей для мира...")
    world_id = context.user_data.get('world_id')        # Получаем world_id из context
    world_metrics = get_world_metrics_by_id(world_id)   # Получаем метрики мира из базы данных

    # Генерация метрик нового мира
    world_metrics = await generate_world_metrics(initiate_result)  # Генерация метрик от GPT

    # Генерация новостей через GPT
    world_news = await generate_world_news(next_game_year, initiate_result, world_metrics)  # Генерация новостей с использованием await
    logger.info(f"Генерация новостей завершена: {world_news}")

    # Отправляем новости пользователю
    if world_news:
        await update.message.reply_text(world_news)

        # Сохраняем новости в базу данных
        # save_world_news_to_db(world_id, world_news)  # Вставка в таблицу world_new

    else:
        await update.message.reply_text("Не удалось получить новости. Попробуй позже.")

    # Отправляем сообщение с текстом "Давай внесём инициативу!"
    intro_text = "Давай теперь внесём инициативу!"

    # Создаем клавиатуру с кнопкой
    keyboard = [
        [InlineKeyboardButton("Внести инициативу", callback_data='start_initiation')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с кнопкой
    await update.message.reply_text(intro_text, reply_markup=reply_markup)

    return WAITING_FOR_INITIATIVE  # Ожидаем следующий ввод инициативы

