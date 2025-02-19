import logging
import psycopg2
from psycopg2 import sql

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для соединения с базой данных
def get_db_connection():
    conn = psycopg2.connect(
        dbname="game_world",  # Имя базы данных
        user="postgres",      # Имя пользователя для базы данных
        password="789077", # Пароль
        host="localhost",     # Хост базы данных
        port="5432"           # Порт PostgreSQL
    )
    return conn

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

# Функция для стратового сохранения мира в базу данных
def save_world_to_db(world_description):
    if not world_description:
        print("Ошибка: описание мира пустое!")
        return None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Логируем описание мира
        print(f"Записываем описание мира: {world_description}")

        cursor.execute(
            "INSERT INTO worlds (world_description, date_generated) VALUES (%s, CURRENT_TIMESTAMP) RETURNING world_id",
            (world_description,)
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

    
# Функция сохранения стартовых метрик в базу данных
def save_world_metrics_to_db(world_id, metrics_string):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Логируем полученные метрики
        logger.info(f"Записываем метрики для мира с ID {world_id}: {metrics_string}")

        # Запись метрик в таблицу world_metrics
        cursor.execute(
            "INSERT INTO world_metrics (world_id, metrics, date_generated) VALUES (%s, %s, CURRENT_TIMESTAMP)",
            (world_id, metrics_string)
        )

        conn.commit()  # Сохраняем изменения в базе данных

        logger.info(f"Метрики успешно записаны для мира с ID {world_id}.")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Ошибка при сохранении метрик: {e}")

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


    