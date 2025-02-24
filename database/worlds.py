# worlds.py - модуль для работы с мирами в базе данных

import logging
import psycopg2
from psycopg2 import sql
import os
from database.connection import get_db_connection

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для стратового сохранения мира в базу данных
def save_world_to_db(in_game_year, world_description):
    if not world_description:
        print("Ошибка: описание мира пустое!")
        return None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Логируем описание мира
        print(f"Записываем описание мира: {world_description}")

        cursor.execute(
            "INSERT INTO worlds (in_game_year, world_description, date_generated) VALUES (%s, %s, CURRENT_TIMESTAMP) RETURNING world_id",
            (in_game_year, world_description)
        )
        
        # Получаем сгенерированный world_id
        world_id = cursor.fetchone()[0]
        
        # Логируем успешную запись
        print(f"Мир успешно создан с ID {world_id}.")
        
        conn.commit()  # Сохраняем изменения

        cursor.close()
        conn.close()
        return world_id
    except Exception as e:
        print(f"Ошибка при сохранении мира: {e}")
        return None

# Функция для получения описания мира по world_id
def get_world_description_by_id(world_id):
    try:
        conn = get_db_connection()  # Соединяемся с базой данных
        cursor = conn.cursor()

        # Запрос для получения описания мира по world_id
        cursor.execute("SELECT world_description FROM worlds WHERE world_id = %s", (world_id,))
        world_description = cursor.fetchone()  # Получаем результат

        cursor.close()
        conn.close()

        if world_description:
            return world_description[0]  # Возвращаем описание мира
        else:
            return None  # Если ничего не найдено, возвращаем None

    except Exception as e:
        logger.error(f"Ошибка при получении описания мира для world_id {world_id}: {e}")
        return None
