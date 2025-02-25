#characters.py - модуль для работы с персонажами в базе данных

import logging
from database.connection import get_db_connection

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для сохранения персонажа в базу данных и связь с миром
def save_chatacters_to_db(world_id, user_id, character_description):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Логируем полученные данные
        logger.info(f"Записываем персонажа для пользователя с ID {user_id}, мира с ID {world_id}: {character_description}")

        # Запись персонажа в таблицу characters
        cursor.execute(
            "INSERT INTO characters (user_id, world_id, character_description) VALUES (%s, %s, %s) RETURNING character_id",
            (user_id, world_id, character_description)
        )
        
        # Получаем сгенерированный character_id
        character_id = cursor.fetchone()[0]
        conn.commit()  # Сохраняем изменения в базе данных

        logger.info(f"Персонаж успешно создан с ID {character_id}.")

        cursor.close()
        conn.close()

        return character_id

    except Exception as e:
        logger.error(f"Ошибка при сохранении персонажа: {e}")
        return None