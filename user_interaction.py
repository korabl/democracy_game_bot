import logging
import os
import random
from typing import Dict

from dotenv import load_dotenv
# Импорты из библиотеки Telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext
)

from actions.receive_character_details import generate_character_description, generate_news
from actions.receive_initiative_details import generate_initiative_result_and_resources, \
    get_current_money, update_metrics
from actions.start import create_telegram_user
from database import save_world_metrics_to_db, save_world_resources_to_db
# Импорты из базы данных
from database.worlds import World
# Импорты игровых функций
from game_world import (
    generate_world_news, generate_world_from_gpt, generate_world_metrics, generate_world_resources
)
# Импорты состояний для бота
from states import WAITING_FOR_CHARACTER_DETAILS, WAITING_FOR_INITIATIVE

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

# Создаем экземпляр класса, будем обращаться к этому экземпляру при операциях с данными мира
world_storage = World()

### ОСНОВНОЙ ФУНКЦИОНАЛ ###

# Команда /start для бота
async def start(update: Update, context: CallbackContext):
    logger.info(f"Команда /start от пользователя {update.message.from_user.username}")
    user_id = update.message.from_user.id

    create_telegram_user(user_id, update.message.from_user.username)
    # Сохраняем user_id в контексте, чтобы передать на следующем шаге
    context.user_data['user_id'] = user_id

    # Отправляем приветственное сообщение
    intro_text =  "Добро пожаловать в мир, который мы будем строить! Нажмите 'Начать', чтобы начать игру и узнать, какие проблемы ждут вас."

    # Создаем кнопку "Начать историю"
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Начать историю", callback_data='start_game')]
    ])

    await update.message.reply_text(intro_text, reply_markup=reply_markup)

# Обработчик нажатия на кнопку "Начать историю"
async def start_game(update: Update, context: CallbackContext):
    logger.info("Обработка нажатия кнопки 'Начать историю'...")

    # Генерация мира через GPT
    logger.info("Попытка вызвать генерацию мира через GPT...")
    # Генерируем случайный год от -10 000 (первые общины) до 2025 (наши дни)
    game_year = random.randint(-2000, 2025)

    try:
        world_data = await generate_world_from_gpt(game_year)  # Получаем описание мира
        # Записываем описание мира в базу данных
        world_id = world_storage.save(game_year, world_data)  # Вставка в таблицу worlds
        # Логируем успешный вызов
        logger.info(f"Мир с ID {world_id} успешно записан в базу данных.")
    except Exception as e:
        logger.error("Ошибка при генерации мира", e)
        await update.callback_query.message.edit_text("Ошибка при генерации мира.")
        return

    context.user_data['game_year'] = game_year  # Сохраняем world_id в контексте, чтобы передать на следующем шаге
    context.user_data['world_id'] = world_id  # Сохраняем world_id в контексте, чтобы передать на следующем шаге
    context.user_data['world_data'] = world_data  # Сохраняем описание мира в контексте

    # Выводим описания мира пользователю без ожидания генерации метрик
    await update.callback_query.message.edit_text(f"{world_data}")

    # Второе сообщение с текстом "Давай сделаем персонажа"
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Создать персонажа", callback_data='start_character_creation')]
    ])
    # Отправляем сообщение о создании персонажа
    await update.callback_query.message.reply_text("Давай теперь создадим персонажа!", reply_markup=reply_markup)

    try:
        world_data = context.user_data.get('world_data')
        world_id = context.user_data.get('world_id')

        metrics_dict = await generate_world_metrics(world_data)
        context.user_data['metrics_dict'] = metrics_dict  # Сохраняем описание мира в контексте
        logger.info(f"Метрики мира: {metrics_dict}")
        save_world_metrics_to_db(world_id, metrics_dict)  # Вставка в таблицу world_metrics
        logger.info(f"Метрики мира с ID мира {world_id} успешно записаны в базу данных.")

        # Генерация ресурсов для мира
        logger.info("Попытка вызвать генерацию ресурсов для мира...")
        resources_dict = await generate_world_resources(metrics_dict, world_data)  # Генерация ресурсов от GPT
        context.user_data['resources_dict'] = resources_dict  # Сохраняем ресурсы мира в контексте
        logger.info(f"Ресурсы мира: {resources_dict}")

        # Записываем ресурсы мира в базу данных
        save_world_resources_to_db(world_id, resources_dict)  # Вставка в таблицу world_metrics
        logger.info(f"Ресурсы мира с ID мира {world_id} успешно записаны в базу данных.")

    except Exception as e:
        logger.error(f"Ошибка генерации метрик и ресурсов", e)

# Обработчик для создания персонажа
async def start_character_creation(update: Update, context: CallbackContext):
    logger.info("Начинаем создание персонажа...")

    # Запрашиваем у пользователя имя персонажа
    await update.callback_query.message.edit_text("Расскажите о имя своём персонаже! Можешь поделиться любыми деталями, которыми захочется!\nНаример, имя, возрат, пофессия, харакетер.\nА если не хочется никого придумывать, просто напиши 'Любой'!")

    return WAITING_FOR_CHARACTER_DETAILS

# Эта функция срабатывает, когда пользователь отправляет описание своего персонажа
async def receive_character_details(update: Update, context: CallbackContext):
    logger.info("Получили описание персонажа от пользователя...")
    # Сохраняем данные в context, чтобы использовать их для генерации персонажа
    character_details = update.message.text
    context.user_data['character_details'] = character_details
    world_data = context.user_data.get('world_data')  # Получаем world_data из context
    character_details = context.user_data['character_details']
    # Получаем world_id и user_id из context
    world_id = context.user_data.get('world_id')
    user_id = context.user_data.get('user_id')
    world_metrics = context.user_data.get('metrics_dict')  # Получаем актуальные метрики мира из контекста
    game_year = context.user_data.get('game_year')  # Получаем game_year из context


    logger.info("Получили описание персонажа от пользователя...")

    # Отправляем подтверждение пользователю
    await update.message.reply_text(f"Спасибо! Ты выбрал: {character_details}. Теперь я создам персонажа.")

    character_description = await generate_character_description(user_id, world_id, world_data, character_details)
    context.user_data['character_description'] = character_description  # Сохраняем описание персонажа в context

    # Отправляем сгенерированное описание персонажа
    await update.message.reply_text(f"Вот твой персонаж: {character_description}")
    # Выводим дайджест актуальных новостей
    await update.message.reply_text("Вот твоя подборка актуальных новостей!")

    # Подготавливаем дайджест новостей для пользователя
    world_news = await generate_news(world_id, world_data, world_metrics, game_year)

    # Отправляем новости пользователю
    if world_news:
        await update.message.reply_text(world_news)
    else:
        await update.message.reply_text("Не удалось получить новости. Попробуй позже.")

    # Создаем клавиатуру с кнопкой
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Внести инициативу", callback_data='start_initiation')]
    ])

    # Отправляем сообщение с кнопкой
    await update.message.reply_text("Давай теперь внесём инициативу!", reply_markup=reply_markup)

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
    context.user_data['initiation_details'] = initiation_details
    # Получаем данные из telegram context
    world_id = context.user_data.get('world_id')  # Получаем world_id из context
    character_description = context.user_data.get('character_description')  # Получаем character_description из context
    next_game_year = context.user_data.get('game_year') + 1  # Получаем game_year из context
    world_data = context.user_data.get('world_data')  # Получаем world_data из context
    world_metrics = context.user_data.get('metrics_dict')  # Получаем актуальные метрики мира из контекста

    logger.info(f"Текущий ID мира {world_id}")

    # Отправляем подтверждение пользователю
    await update.message.reply_text(f"Спасибо! Твоя инициатива: {initiation_details}.")

    initiate_result = await generate_initiative_result_and_resources(world_id, character_description, next_game_year, world_data, initiation_details)

    # Отправляем сгенерированное изменение мира
    await update.message.reply_text(f"{initiate_result}")

    # Отправляем сгенерированное изменение мира
    current_money = get_current_money(world_id)
    await update.message.reply_text(f"Казна на конец года: {current_money}")

    updated_metrics = await update_metrics(world_id, world_data, world_metrics, initiation_details)
    context.user_data['metrics_dict'] = updated_metrics  # Сохраняем описание метрик в context
    logger.info(f"Обновленные метрики: {updated_metrics}")

    # Выводим дайджест актуальных новостей
    await update.message.reply_text("Вот твоя подборка актуальных новостей спустя год!")

    # Генерация новостей через GPT
    world_news = await generate_world_news(next_game_year, initiate_result, updated_metrics)  # Генерация новостей с использованием await
    logger.info(f"Генерация новостей завершена: {world_news}")

    # Отправляем новости пользователю
    if world_news:
        await update.message.reply_text(world_news)
    else:
        await update.message.reply_text("Не удалось получить новости. Попробуй позже.")

    # Обновляем контекст и заносим в краткосрочную память
    context.user_data['world_data'] += f"\n\n Год: {next_game_year}\n Инициатива игрока: {initiation_details}\n Изменения: {initiate_result}"
    context.user_data['initiation_details'] = initiation_details
    context.user_data['game_year'] = next_game_year  # Перезаписываем next_game_year в context

    # Отправляем сообщение с текстом "Давай внесём инициативу!"
    # Создаем клавиатуру с кнопкой
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Внести инициативу", callback_data='start_initiation')]
    ])

    # Отправляем сообщение с кнопкой
    await update.message.reply_text("Давай теперь внесём инициативу!", reply_markup=reply_markup)

    return WAITING_FOR_INITIATIVE  # Ожидаем следующий ввод инициативы

async def get_resources_report(game_year: int, resources_dict: Dict[str, int]) -> str:
    # Форматируем год для отображения "до или после нашей эры"
    if game_year < 0:
        era = "до н.э."
        year = abs(game_year)
    else:
        era = "н.э."
        year = game_year

    # Создаём отчет
    report_text = f"📊 *Отчет за {year} год {era}*\n\n"
    report_text += "💰 *Ресурсы:*\n"

    # Переносим единицы в конец для каждого ресурса
    for key, value in resources_dict.items():
        if key == "Деньги":
            report_text += f"  🔹 {key}: *{value}* монет\n"
        elif key == "Население":
            report_text += f"  🔹 {key}: *{value}* людей\n"
        else:
            report_text += f"  🔹 {key}: *{value}* единиц\n"

    return report_text
