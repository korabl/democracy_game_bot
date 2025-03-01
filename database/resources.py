# resources.py - модуль для записи ресурсов мира в базу данных

import logging
import psycopg2
from database.connection import get_db_connection, conn

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

def get_current_money_from_db(world_id):
    try:
        with conn.cursor() as cursor:
            # Запрос для получения последних ресурсов денег (по дате создания)
            cursor.execute("""
                SELECT money_resource
                FROM world_resources
                WHERE world_id = %s
                ORDER BY date_generated DESC  -- Сортируем по убыванию даты (последние записи в начале)
                LIMIT 1                       -- Берём только 1 самую свежую запись
            """, (world_id,))

            result = cursor.fetchone()  # Получаем первую строку результата

            if result:
                return result[0]  # Возвращаем значение money_resource
            else:
                return 0  # Если данных нет, возвращаем 0

    except psycopg2.Error as e:
        print(f"Ошибка при попытке получения последних данных о деньгах в бд: {e}")
        return None

def get_current_money_multiplier_from_db(world_id):
    try:
        with conn.cursor() as cursor:
            # Запрос для получения последнего коэффициента денег (по дате создания)
            cursor.execute("""
                SELECT money_multiplier
                FROM world_resources
                WHERE world_id = %s
                ORDER BY date_generated DESC  -- Сортируем по убыванию даты (последние записи в начале)
                LIMIT 1                       -- Берём только 1 самую свежую запись
            """, (world_id,))

            result = cursor.fetchone()  # Получаем первую строку результата

            if result:
                return result[0]  # Возвращаем значение money_multiplier
            else:
                return 0  # Если данных нет, возвращаем 0

    except psycopg2.Error as e:
        print(f"Ошибка при попытке получения последних данных о коэф росте деньгах в бд: {e}")
        return None


def save_new_money_to_db(world_id, new_money):
    """
    Обновляет ресурс денег (money_resource) для указанного мира в базе данных.

    :param connection: Объект подключения к базе данных
    :param world_id: ID мира, для которого обновляется значение
    :param new_money: Новое значение денег (money_resource)
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE world_resources
                SET money_resource = %s
                WHERE world_id = %s;
            """, (new_money, world_id))
        conn.commit()  # Фиксируем изменения в базе
        print(f"Обновлено money_resource для world_id={world_id}: {new_money}")
    except psycopg2.Error as e:
        print(f"Ошибка при обновлении money_resource: {e}")
        conn.rollback()  # Откатываем изменения в случае ошибки

def save_new_money_multiplier_to_db(world_id: object, new_multiplier: object) -> None:
    """
    Обновляет коэффициент роста денег (money_multiplier) для указанного мира в базе данных.

    :param connection: Объект подключения к базе данных
    :param world_id: ID мира, для которого обновляется значение
    :param new_multiplier: Новое значение коэффициента роста денег (money_multiplier)
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE world_resources
                SET money_multiplier = %s
                WHERE world_id = %s;
            """, (new_multiplier, world_id))
        conn.commit()  # Фиксируем изменения в базе
        print(f"Обновлено money_multiplier для world_id={world_id}: {new_multiplier}")
    except psycopg2.Error as e:
        print(f"Ошибка при обновлении money_multiplier: {e}")
        conn.rollback()  # Откатываем изменения в случае ошибки
