# metrics.py - модуль для работы с метриками мира в базе данных

import logging
from database.connection import get_db_connection

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция сохранения стартовых метрик в базу данных
def save_world_metrics_to_db(world_id, metrics):
    try:
        # Извлекаем метрики из словаря
        economy_metric = metrics.get("economy_metric", 0)
        social_stability_metric = metrics.get("social_stability_metric", 0)
        ecology_metric = metrics.get("ecology_metric", 0)
        security_metric = metrics.get("security_metric", 0)
        political_support_metric = metrics.get("political_support_metric", 0)

        # Установим соединение с базой данных
        conn = get_db_connection()
        cursor = conn.cursor()

        # Вставляем метрики в таблицу world_metrics
        cursor.execute(
            """
            INSERT INTO world_metrics 
            (world_id, economy_metric, social_stability_metric, ecology_metric, security_metric, political_support_metric, date_generated)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (world_id, economy_metric, social_stability_metric, ecology_metric, security_metric, political_support_metric)
        )

        conn.commit()  # Подтверждаем изменения

        # Логируем успешную запись данных
        logger.info(f"Метрики успешно записаны для мира с ID {world_id}.")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Ошибка при сохранении метрик: {e}")

# Функция для получения метрик мира по world_id
def get_world_metrics_by_id(world_id):
    try:
        conn = get_db_connection()  # Соединяемся с базой данных
        cursor = conn.cursor()

        # Запрос для получения всех метрик мира по world_id
        cursor.execute("""
            SELECT economy_metric, social_stability_metric, ecology_metric, security_metric, political_support_metric
            FROM world_metrics WHERE world_id = %s
        """, (world_id,))
        world_metrics = cursor.fetchone()  # Получаем результат

        cursor.close()
        conn.close()

        if world_metrics:
            return world_metrics[0]  # Возвращаем описание мира
        else:
            return None  # Если ничего не найдено, возвращаем None

    except Exception as e:
        logger.error(f"Ошибка при получении метрик мира для world_id {world_id}: {e}")
        return None
    
# Функция для получения актуальных метрик мира по world_id
def get_latest_world_metrics(world_id):
    """
    Получает последние (актуальные) метрики для указанного мира (world_id).
    """
    try:
        conn = get_db_connection()  # Подключаемся к БД
        cursor = conn.cursor()

        # Запрос для получения последних метрик (по дате создания)
        cursor.execute("""
            SELECT economy_metric, social_stability_metric, ecology_metric, 
                   security_metric, political_support_metric
            FROM world_metrics
            WHERE world_id = %s
            ORDER BY date_generated DESC  -- Сортируем по убыванию даты (последние записи в начале)
            LIMIT 1                       -- Берём только 1 самую свежую запись
        """, (world_id,))

        result = cursor.fetchone()  # Получаем 1 строку

        cursor.close()
        conn.close()

        if result:
            return {
                "economy_metric": result[0],
                "social_stability_metric": result[1],
                "ecology_metric": result[2],
                "security_metric": result[3],
                "political_support_metric": result[4]
            }
        else:
            return None  # Если данных нет, возвращаем None

    except Exception as e:
        logger.error(f"Ошибка при получении метрик мира (world_id={world_id}): {e}")
        return None