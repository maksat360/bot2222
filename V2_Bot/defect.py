# defect.py — Учёт брака
# ========================

import os
import pandas as pd
from datetime import datetime
from config import DEFECT_FILE


def report_defect(party_id, process_id, employee_login, photo_file_id):
    """Сохраняет информацию о браке."""
    # Создаём папку для фото брака
    photo_dir = os.path.join("cloud_storage", "Фото_брака", f"Партия_{party_id}")
    os.makedirs(photo_dir, exist_ok=True)

    # Формируем имя файла с датой и временем
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M-%S")
    photo_filename = f"Брак_{date_str}_{time_str}.jpg"
    photo_path = os.path.join(photo_dir, photo_filename)

    # Добавляем запись в файл брак.xlsx
    try:
        df = pd.read_excel(DEFECT_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "Партия", "Процесс", "Сотрудник",
            "Ссылка на фото", "Дата", "Время",
            "Статус", "Технолог_статус"
        ])

    new_record = {
        "Партия": party_id,
        "Процесс": process_id,
        "Сотрудник": employee_login,
        "Ссылка на фото": photo_path,
        "Дата": date_str,
        "Время": time_str,
        "Статус": "Новый",
        "Технолог_статус": "Не обработан",
    }

    df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
    df.to_excel(DEFECT_FILE, index=False)

    return new_record


def get_pending_defects():
    """Возвращает список браков со статусом 'Новый'."""
    try:
        df = pd.read_excel(DEFECT_FILE)
    except FileNotFoundError:
        return []

    pending = df[df["Статус"] == "Новый"]
    return pending.to_dict("records")


def process_defect(defect_id, decision):
    """Обновляет Технолог_статус на 'Принято' или 'Возврат'."""
    df = pd.read_excel(DEFECT_FILE)

    if decision not in ["Принято", "Возврат"]:
        raise ValueError("Решение должно быть 'Принято' или 'Возврат'")

    mask = df.index == defect_id
    if not mask.any():
        raise ValueError(f"Дефект с ID {defect_id} не найден")

    df.loc[mask, "Технолог_статус"] = decision
    df.loc[mask, "Статус"] = "Обработан"
    df.to_excel(DEFECT_FILE, index=False)

    return True