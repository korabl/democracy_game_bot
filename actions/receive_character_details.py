import logging

import game_world
from database import save_chatacters_to_db, save_world_news_to_db

logger = logging.getLogger(__name__)

async def generate_character_description(user_id, world_id, world_data, character_details):
    character_description = await game_world.generate_character(world_data, character_details)
    # Сохраняем персонажа в базу данных
    save_chatacters_to_db(world_id, user_id, character_description)  # Вставка в таблицу characters
    return character_description

async def generate_news(world_id, world_data, world_metrics, game_year):
    # Подготавливаем дайджест новостей для пользователя
    logger.info("Попытка вызвать генерацию новостей для мира...")
    # Генерация новостей через GPT
    world_news = await game_world.generate_world_news(game_year, world_data, world_metrics)  # Генерация новостей с использованием await
    logger.info(f"Генерация новостей завершена: {world_news}")
    # Сохраняем новости в базу данных
    save_world_news_to_db(world_id, world_news)  # Вставка в таблицу world_news
    return world_news