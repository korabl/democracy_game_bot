# worlds.py - модуль для работы с мирами в базе данных

import logging
from database.connection import get_db_connection, insert_returning_id, fetchone

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Класс, который будет в себе хранить набор функций для работы с миром
class World:
    def __init__(self):
        # Создание нового соединения к базке - ресурсозатратно, поэтому подключаемся один раз и сохраняем соединение в переменной
        self.conn = get_db_connection()

    # При удалении экземпляра класса, закрываем соединение с БД
    def __del__(self):
        self.conn.close()

    # сохраняем мир в базку, возвращаем айдишник
    def save(self, year, description):
        if not description:
            logger.error("Ошибка: описание мира пустое!")
            return None

        logger.info(f"Записываем описание мира: {description}")

        try:
            world_id = insert_returning_id(
                self.conn,
                "INSERT INTO worlds (in_game_year, world_description, date_generated) VALUES (%s, %s, CURRENT_TIMESTAMP) RETURNING world_id",
                (year, description)
            )
            return world_id
        except Exception as e:
            logger.error(f"Ошибка при сохранении мира: {e}")
        return None

    # Получаем описание мира по айдишнику
    def get(self, world_id):
        try:
            result = fetchone(
                self.conn,
                "SELECT world_description FROM worlds WHERE world_id = %s",
                (world_id,)
            )

            return result
        except Exception as e:
            logger.error(f"Ошибка при получении описания мира для world_id {world_id}: {e}")
            return None

    # Обновляем описание мира после инициативы
    def update_description(self, world_id, new_description):
        """
        Обновляет описание мира.

        :param world_id: ID мира.
        :param new_description: Новое описание.
        :return: True, если успешно, иначе False.
        """
        if not new_description:
            logger.error("Ошибка: новое описание мира пустое!")
            return False

        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE worlds
                    SET world_description = %s
                    WHERE world_id = %s;
                """, (new_description, world_id))
            self.conn.commit()
            logger.info(f"Описание мира обновлено для world_id {world_id}.")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении описания мира: {e}")
            self.conn.rollback()
            return False