import json
import re
from decimal import Decimal

from database import get_current_money_from_db, get_current_money_multiplier_from_db, save_new_money_to_db, \
    save_new_money_multiplier_to_db, save_world_metrics_to_db
from database.worlds import world_storage
from game_world import generate_world_changes, update_world_metrics, generate_world_news

def get_current_money(world_id):
    return get_current_money_from_db(world_id)

async def generate_initiative_result_and_resources(world_id, character_description, next_game_year, world_data, initiation_details):
    # получить последнюю запись из таблицы ресурсов (current)
    current_money = get_current_money_from_db(world_id)
    current_multiplier = get_current_money_multiplier_from_db(world_id)

    # рассчитать доступные ресурсы умножив текущий баланс на множитель
    budget = current_money * current_multiplier

    # передать полученные цифры в промпт для генерации изменений после инициативы юзера
    initiate_result = await generate_world_changes(budget, current_multiplier, character_description, next_game_year, world_data, initiation_details)

    # записываем, как изменился мир в бд
    new_world_description = await clean_and_parse_json(initiate_result, ["world_changes", "facts"])
    world_storage.update_description(world_id, new_world_description)

    # записываем новый остаток денег для мира
    response_cost = await clean_and_parse_json(initiate_result, ["financial_evaluation", "estimated_cost"])
    print(f"Оценка затрат {response_cost}")
    if response_cost is None or response_cost == "":
        response_cost = 0
    new_money = budget - Decimal(response_cost)
    print(f"Новый бюджет {new_money}")
    save_new_money_to_db(world_id, new_money)

    # записываем новый коэффициент денег для мира
    new_multiplier_delta = await clean_and_parse_json(initiate_result,["financial_evaluation", "money_multiplier_change"])
    print(f"new multiplier delta {new_multiplier_delta}")

    # проверяем, что оно не None и не пустая строка
    if new_multiplier_delta is None or new_multiplier_delta == "":
        print("Ошибка: `new_multiplier_delta` отсутствует, устанавливаем 0.0")
        new_multiplier_delta = 0.0
    else:
        try:
            # Преобразуем в float
            new_multiplier_delta = float(new_multiplier_delta)
        except ValueError:
            print(f"Ошибка: `new_multiplier_delta` содержит некорректное значение: {new_multiplier_delta}, устанавливаем 0.0")
            new_multiplier_delta = 0.0

    # вычисляем новый коэффициент роста
    current_multiplier = Decimal(current_multiplier)    # Убедимся, что current_multiplier — Decimal
    new_multiplier_delta = Decimal(str(new_multiplier_delta))  # Убедимся, что new_multiplier_delta — тоже Decimal

    new_multiplier = current_multiplier + new_multiplier_delta
    print(f"new multiplier {new_multiplier}")

    # сохраняем в базу данных
    save_new_money_multiplier_to_db(world_id, new_multiplier)

    # вернуть ответ нпс
    nps_response = await clean_and_parse_json(initiate_result, ["world_changes", "npc_perspective"])

    return nps_response

async def update_metrics(world_id, world_data, world_metrics, initiation_details):
    # Апдейт метрик для мира после инициативы пользователя
    metrics_dict = await update_world_metrics(world_data, initiation_details)  # Генерация метрик от GPT
    print(f"Изменения метрик нового мира: {metrics_dict}")

    # Определяем, какие изменения вносим в метрики(суммируем старые и новые значения)
    updated_metrics = {}

    # Преобразуем строковые значения "+" и "-" в числа (1 и -1 соответственно)
    for key in world_metrics:
        if metrics_dict[key] == "+":
            updated_metrics[key] = world_metrics[key] + 1
        elif metrics_dict[key] == "-":
            updated_metrics[key] = world_metrics[key] - 1
        elif metrics_dict[key] == "0":
            updated_metrics[key] = world_metrics[key]
        else:
            # Если пришло число, просто складываем
            updated_metrics[key] = world_metrics[key] + int(metrics_dict.get(key, 0))

    # Обновляем метрики в БД
    save_world_metrics_to_db(world_id, updated_metrics)
    print(f"✅ Метрики обновлены для мира {world_id}: {updated_metrics}")
    return updated_metrics

async def clean_and_parse_json(gpt_response, key_path):
    """
    Очищает JSON-ответ от GPT, убирает лишние символы и парсит нужное поле.

    :param gpt_response: Ответ от GPT в виде строки (возможно, с обертками ```json)
    :param key_path: Список ключей для извлечения нужного значения (пример: ["world_changes", "npc_perspective"])
    :return: Значение по ключу или сообщение об ошибке
    """
    try:
        # Проверяем, что ответ не пустой
        if not gpt_response or not isinstance(gpt_response, str):
            print("Ошибка: Пустой или некорректный ответ от GPT.")
            return "Ошибка при обработке данных."

        # Убираем возможные обертки ```json ... ```
        cleaned_response = re.sub(r"```json|```", "", gpt_response).strip()

        # Парсим JSON
        data = json.loads(cleaned_response)

        # Проходим по ключам, чтобы добраться до нужного значения
        for key in key_path:
            if key not in data:
                print(f"Ошибка: Ключ '{key}' отсутствует в JSON-ответе.")
                return "Ошибка при обработке данных."
            data = data[key]

        return data  # Возвращаем найденное значение

    except json.JSONDecodeError as e:
        print(f"Ошибка при обработке JSON: {e}\nОтвет от GPT: {gpt_response}")
        return "Ошибка при обработке данных."
    except (KeyError, TypeError) as e:
        print(f"Ошибка доступа к данным JSON: {e}\nОтвет от GPT: {gpt_response}")
        return "Ошибка при обработке данных."

