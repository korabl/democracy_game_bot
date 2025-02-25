# connection.py - модуль для подключения к базе данных

import psycopg2
from dotenv import load_dotenv
import os

# Загружаем переменные окружения из .env
load_dotenv()


def get_db_connection():
    """Подключение к базе данных."""
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    return conn


def insert_returning_id(conn, query, vars=None):
    cursor = conn.cursor()
    cursor.execute(query, vars)

    result = cursor.fetchone()[0]

    conn.commit()
    cursor.close()

    return result


def fetchone(conn, query, vars=None):
    cursor = conn.cursor()

    cursor.execute(query, vars)
    result = cursor.fetchone()

    cursor.close()

    if not result:
        return None

    return result[0]
