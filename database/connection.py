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
