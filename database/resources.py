# resources.py - модуль для записи ресурсов мира в базу данных

import logging
from database.connection import get_db_connection

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Записываем ресурсы мира в базу данных
def save_world_resources_to_db(world_id, resources):
    try:
        # Извлекаем ресурсы из словаря
        money_resource = resources.get("Деньги (монет)", 0)  # Используем правильные ключи
        people_resource = resources.get("Население (людей)", 0)

        # Установим соединение с базой данных
        conn = get_db_connection()
        cursor = conn.cursor()

        # Вставляем ресурсы в таблицу world_resources
        cursor.execute(
            """
            INSERT INTO world_resources 
            (world_id, money_resource, people_resource, date_generated)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (world_id, money_resource, people_resource)  # Параметры для вставки
        )

        conn.commit()  # Подтверждаем изменения

        # Логируем успешную запись данных
        logger.info(f"Ресурсы успешно записаны для мира с ID {world_id}.")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Ошибка при сохранении ресурсов мира: {e}")
