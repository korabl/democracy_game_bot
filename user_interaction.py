import os
import json
import random
import re
import logging

from dotenv import load_dotenv
from decimal import Decimal
from typing import Dict

# Импорты из библиотеки Telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackContext, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)

# Импорты из базы данных
from database import (
    create_user, save_world_metrics_to_db, save_chatacters_to_db, get_db_connection,
    get_user_id_by_telegram_id, save_world_news_to_db,
    get_latest_world_metrics, save_world_resources_to_db, get_current_money_from_db,
    get_current_money_multiplier_from_db, save_new_money_to_db, save_new_money_multiplier_to_db
)

from database.worlds import World

# Импорты игровых функций
from game_world import (
    generate_world_from_gpt, generate_world_metrics, generate_character,
    generate_world_news, generate_world_changes, update_world_metrics,
    generate_world_resources
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

# Получаем соединение c БД
conn = get_db_connection()

# Создаем экземпляр класса, будем обращаться к этому экземпляру при операциях с данными мира
world_storage = World()

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
        game_year = random.randint(-2000, 2025)

        # Сохраняем world_id в контексте, чтобы передать на следующем шаге
        context.user_data['game_year'] = game_year

        world_data = await generate_world_from_gpt(game_year)  # Получаем описание мира

        # Записываем описание мира в базу данных
        world_id = world_storage.save(game_year, world_data)  # Вставка в таблицу worlds

        if not world_id:
            await update.callback_query.message.edit_text("Ошибка при записи мира в базу данных.")
            return

        context.user_data['world_id'] = world_id    # Сохраняем world_id в контексте, чтобы передать на следующем шаге
        context.user_data['world_data'] = world_data  # Сохраняем описание мира в контексте

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
        gpt_response = await generate_world_metrics(world_data)  # Генерация метрик от GPT
        print(f"Метрики мира: {gpt_response}")

        if not gpt_response:
            await update.callback_query.message.edit_text("Ошибка при генерации метрик для мира.")
            return

        # Распаршеваем ответ от ГПТ
        gpt_response_cleaned = re.sub(r"```python|```", "", gpt_response).strip()   # Убираем кодовый блок и излишние пробелы/символы

        # Преобразуем строку в словарь
        try:
            metrics_dict = json.loads(gpt_response_cleaned)
            print("Метрики успешно распарсены:", metrics_dict)
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON: {e}")

        # Записываем метрики мира в базу данных
        save_world_metrics_to_db(world_id, metrics_dict)  # Вставка в таблицу world_metrics
        context.user_data['metrics_dict'] = metrics_dict  # Сохраняем описание мира в контексте
        logger.info(f"Метрики мира с ID мира {world_id} успешно записаны в базу данных.")

        # Генерация ресурсов для мира
        logger.info("Попытка вызвать генерацию ресурсов для мира...")
        gpt_response = await generate_world_resources(metrics_dict, world_data)  # Генерация ресурсов от GPT
        print(f"Ресурсы мира: {gpt_response}")

        if not gpt_response:
            await update.callback_query.message.edit_text("Ошибка при генерации ресурсов для мира.")
            return

        # Распаршеваем ответ от ГПТ
        gpt_response_cleaned = re.sub(r"```python|```", "", gpt_response).strip()   # Убираем кодовый блок и излишние пробелы/символы

        # Преобразуем строку в словарь
        try:
            resources_dict = json.loads(gpt_response_cleaned)
            print("Ресурсы успешно распарсены:", resources_dict)
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON: {e}")

        # Записываем ресурсы мира в базу данных
        save_world_resources_to_db(world_id, resources_dict)  # Вставка в таблицу world_metrics
        context.user_data['resources_dict'] = resources_dict  # Сохраняем ресурсы мира в контексте
        logger.info(f"Ресурсы мира с ID мира {world_id} успешно записаны в базу данных.")

    except Exception as e:
        await update.callback_query.message.edit_text("Произошла ошибка при генерации мира в обработчике нажатия кнопки 'Начать историю'.")
        logger.error(f"Ошибка при генерации мира: {e}")

    return WAITING_FOR_CHARACTER_DETAILS

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
    world_data = context.user_data.get('world_data')    # Получаем world_data из context
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
    world_metrics = context.user_data.get('metrics_dict')  # Получаем актуальные метрики мира из контекста

    # Генерация новостей через GPT
    game_year = context.user_data.get('game_year')      # Получаем game_year из context
    world_news = await generate_world_news(game_year, world_data, world_metrics)  # Генерация новостей с использованием await
    logger.info(f"Генерация новостей завершена: {world_news}")

    # Отправляем новости пользователю
    if world_news:
        await update.message.reply_text(world_news)

        # Сохраняем новости в базу данных
        save_world_news_to_db(world_id, world_news)  # Вставка в таблицу world_news

    else:
        await update.message.reply_text("Не удалось получить новости. Попробуй позже.")

    # Отправляем отчёт на текущий год пользователю
    resources_dict = context.user_data.get('resources_dict', {})
    report_text = await get_resources_report(game_year, resources_dict)
    await update.message.reply_text(report_text, parse_mode="Markdown")

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

    # Получаем данные из telegram context
    world_id = context.user_data.get('world_id')  # Получаем world_id из context
    world_id = context.user_data.get('world_id')  # Получаем world_data из context
    next_game_year = context.user_data.get('game_year') + 1  # Получаем game_year из context
    world_data = context.user_data.get('world_data')  # Получаем world_data из context
    world_metrics = context.user_data.get('metrics_dict')  # Получаем актуальные метрики мира из контекста
    # world_resources = context.user_data.get('resources_dict')    # Получаем ресурсы из context

    # Отправляем подтверждение пользователю
    await update.message.reply_text(f"Спасибо! Твоя инициатива: {initiation_details}.")

    # Генерация изменений мира на основе инициативы от GPT

    print(f"Текущий айди мира {world_id}")
    character_description = context.user_data.get('character_description')  # Получаем character_description из context
    initiate_result = await generate_initiative_result_and_resources(
        world_id,
        world_data,
        character_description,
        next_game_year,
        initiation_details
    )

    # Отправляем сгенерированное изменение мира
    await update.message.reply_text(f"{initiate_result}")

    # Отправляем сгенерированное изменение мира
    current_money = get_current_money_from_db(conn, world_id)
    await update.message.reply_text(f"Казна на конец года: {current_money}")

    # Апдейт метрик для мира после инициативы пользователя
    logger.info("Попытка вызвать обновление метрик для мира...")
    gpt_response = await update_world_metrics(world_data, initiation_details)  # Генерация метрик от GPT
    print(f"Изменения метрик нового мира: {gpt_response}")

    if not gpt_response:
        await update.callback_query.message.edit_text("Ошибка при генерации обновления метрик для мира.")
        return

    # Удаляем ```json и ``` с помощью регулярного выражения
    cleaned_response = re.sub(r"```json|```", "", gpt_response).strip()
    print(f"Ответ GPT после очистки: {cleaned_response}")  # Логируем после очистки

    # Преобразуем строку в словарь
    try:
        metrics_dict = json.loads(cleaned_response)
        print("Изменения метрик успешно распарсены:", metrics_dict)
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")

    # Определяем, какие изменения вносим в метрики(суммируем старые и новые значения)
    updated_metrics = {}

    # Преобразуем строковые значения "+" и "-" в числа (1 и -1 соответственно)
    for key in world_metrics:
        if metrics_dict[key] == "+":
            updated_metrics[key] = world_metrics[key] + 1
        elif metrics_dict[key] == "-":
            updated_metrics[key] = world_metrics[key] - 1
        elif metrics_dict[key] == "0":
            updated_metrics[key] = world_metrics[key]
        else:
            # Если пришло число, просто складываем
            updated_metrics[key] = world_metrics[key] + int(metrics_dict.get(key, 0))

    print(f"Обновленные метрики: {updated_metrics}")

    # Обновляем метрики в БД
    context.user_data['metrics_dict'] = updated_metrics  # Сохраняем описание метрик в context
    save_world_metrics_to_db(world_id, updated_metrics)

    print(f"✅ Метрики обновлены для мира {world_id}: {updated_metrics}")

    # Выводим дайджест актуальных новостей
    intro_text = "Вот твоя подборка актуальных новостей спустя год!"

    # Отправляем сообщение пользователю
    await update.message.reply_text(intro_text)

    # Генерация новостей через GPT
    world_news = await generate_world_news(next_game_year, initiate_result, updated_metrics)  # Генерация новостей с использованием await
    logger.info(f"Генерация новостей завершена: {world_news}")

    # Отправляем новости пользователю
    if world_news:
        await update.message.reply_text(world_news)

        # Сохраняем новости в базу данных
        # save_world_news_to_db(world_id, world_news)  # Вставка в таблицу world_new

    else:
        await update.message.reply_text("Не удалось получить новости. Попробуй позже.")

    # Обновляем контекст и заносим в краткосрочную память
    context.user_data['world_data'] += f"\n\n Год: {next_game_year}\n Инициатива игрока: {initiation_details}\n Изменения: {initiate_result}"
    context.user_data['initiation_details'] = initiation_details
    context.user_data['game_year'] = next_game_year  # Перезаписываем next_game_year в context

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


async def generate_initiative_result_and_resources(world_id, world_data, character_description, next_game_year, initiation_details):
    # получить последнюю запись из таблицы ресурсов (current)
    current_money = get_current_money_from_db (conn, world_id)
    current_multiplier = get_current_money_multiplier_from_db (conn, world_id)

    # рассчитать доступные ресурсы умножив текущий баланс на множитель
    budget = current_money * current_multiplier

    # передать полученные цифры в промпт для генерации изменений после инициативы юзера
    initiate_result = await generate_world_changes(budget, current_multiplier, character_description, next_game_year, world_data, initiation_details)

    # записываем, как изменился мир в бд
    new_world_description = await clean_and_parse_json(initiate_result, ["world_changes", "facts"])
    world_storage.update_description(world_id, new_world_description)

    # записываем новый остаток денег для мира
    response_cost = await clean_and_parse_json(initiate_result, ["financial_evaluation", "estimated_cost"])
    print(f"Оценка затрат {response_cost}")
    if response_cost is None or response_cost == "":
        response_cost = 0
    new_money = budget - Decimal(response_cost)
    print(f"Новый бюджет {new_money}")
    save_new_money_to_db(conn, world_id, new_money)

    # записываем новый коэффициент денег для мира
    new_multiplier_delta = await clean_and_parse_json(initiate_result,["financial_evaluation", "money_multiplier_change"])
    print(f"new multiplier delta {new_multiplier_delta}")

    # проверяем, что оно не None и не пустая строка
    if new_multiplier_delta is None or new_multiplier_delta == "":
        print("Ошибка: `new_multiplier_delta` отсутствует, устанавливаем 0.0")
        new_multiplier_delta = 0.0
    else:
        try:
            # Преобразуем в float
            new_multiplier_delta = float(new_multiplier_delta)
        except ValueError:
            print(f"Ошибка: `new_multiplier_delta` содержит некорректное значение: {new_multiplier_delta}, устанавливаем 0.0")
            new_multiplier_delta = 0.0

    # вычисляем новый коэффициент роста
    current_multiplier = Decimal(current_multiplier)    # Убедимся, что current_multiplier — Decimal
    new_multiplier_delta = Decimal(str(new_multiplier_delta))  # Убедимся, что new_multiplier_delta — тоже Decimal

    new_multiplier = current_multiplier + new_multiplier_delta
    print(f"new multiplier {new_multiplier}")

    # сохраняем в базу данных
    save_new_money_multiplier_to_db(conn, world_id, new_multiplier)

    # вернуть ответ нпс
    nps_response = await clean_and_parse_json(initiate_result, ["world_changes", "npc_perspective"])

    return nps_response

async def clean_and_parse_json(gpt_response, key_path):
    """
    Очищает JSON-ответ от GPT, убирает лишние символы и парсит нужное поле.

    :param gpt_response: Ответ от GPT в виде строки (возможно, с обертками ```json)
    :param key_path: Список ключей для извлечения нужного значения (пример: ["world_changes", "npc_perspective"])
    :return: Значение по ключу или сообщение об ошибке
    """
    try:
        # Проверяем, что ответ не пустой
        if not gpt_response or not isinstance(gpt_response, str):
            print("Ошибка: Пустой или некорректный ответ от GPT.")
            return "Ошибка при обработке данных."

        # Убираем возможные обертки ```json ... ```
        cleaned_response = re.sub(r"```json|```", "", gpt_response).strip()

        # Парсим JSON
        data = json.loads(cleaned_response)

        # Проходим по ключам, чтобы добраться до нужного значения
        for key in key_path:
            if key not in data:
                print(f"Ошибка: Ключ '{key}' отсутствует в JSON-ответе.")
                return "Ошибка при обработке данных."
            data = data[key]

        return data  # Возвращаем найденное значение

    except json.JSONDecodeError as e:
        print(f"Ошибка при обработке JSON: {e}\nОтвет от GPT: {gpt_response}")
        return "Ошибка при обработке данных."
    except (KeyError, TypeError) as e:
        print(f"Ошибка доступа к данным JSON: {e}\nОтвет от GPT: {gpt_response}")
        return "Ошибка при обработке данных."

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
