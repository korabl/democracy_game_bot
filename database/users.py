# users.py - модуль для работы с пользователями в базе данных

import logging
import psycopg2
from psycopg2 import sql
import os
from database.connection import get_db_connection

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для создания пользователя
def create_user(telegram_id, username):
    try:
        # Подключаемся к базе данных
        conn = get_db_connection()
        cursor = conn.cursor()

        # Проверяем, существует ли уже пользователь
        cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
        existing_user = cursor.fetchone()

        if not existing_user:
            # Добавляем пользователя в базу данных
            cursor.execute(
                "INSERT INTO users (telegram_id, nickname, date_joined) VALUES (%s, %s, CURRENT_TIMESTAMP)",
                (telegram_id, username)
            )
            conn.commit()  # Сохраняем изменения в базе данных
            print(f"Пользователь с ID {telegram_id} добавлен в базу данных.")
        else:
            print(f"Пользователь с ID {telegram_id} уже существует.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка при добавлении пользователя в базу данных: {e}")

# Получение user_id по telegram_id
def get_user_id_by_telegram_id(telegram_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Получаем user_id по telegram_id
        cursor.execute("SELECT user_id FROM users WHERE telegram_id = %s", (telegram_id,))
        user_id = cursor.fetchone()

        cursor.close()
        conn.close()

        # Если user_id найден, возвращаем его
        if user_id:
            return user_id[0]  # Возвращаем первый элемент (user_id)
        else:
            return None  # Если не найден, возвращаем None

    except Exception as e:
        logger.error(f"Ошибка при получении user_id по telegram_id {telegram_id}: {e}")
        return None