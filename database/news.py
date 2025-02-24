# news.py - модуль для работы с новостями в базе данных

import logging
import psycopg2
from psycopg2 import sql
import os
from database.connection import get_db_connection

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для сохранения новостей в базу данных
def save_world_news_to_db(world_id, world_news):
    try:
        if not world_news:
            logger.warning(f"Мир с ID {world_id} не имеет новостей для записи.")
            return None  # Если нет новостей, не записываем их
        
        conn = get_db_connection()
        cursor = conn.cursor()

        # Логируем полученные данные
        logger.info(f"Записываем новости для мира с ID {world_id}: {world_news}")

        # Запись новости в таблицу WORLD_METRICS
        cursor.execute(
            "INSERT INTO WORLD_METRICS (world_id, world_news) VALUES (%s, %s) RETURNING metric_id",
            (world_id, world_news)
        )
        
        # Получаем сгенерированный metric_id
        metric_id = cursor.fetchone()[0]
        conn.commit()  # Сохраняем изменения в базе данных

        logger.info(f"Персонаж успешно создан с ID {metric_id}.")

        cursor.close()
        conn.close()

        return metric_id

    except Exception as e:
        logger.error(f"Ошибка при сохранении новостей: {e}")
        return None