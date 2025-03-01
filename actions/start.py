import logging

from database import get_user_id_by_telegram_id, create_user

logger = logging.getLogger(__name__)

def create_telegram_user(user_id: int, username: str):
    # Получаем user_id из базы данных по user_id
    user_id = get_user_id_by_telegram_id(user_id)
    create_user(user_id, username)
