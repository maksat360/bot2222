# conveyor.py — Производственный конвейер
# =========================================

import os
import pandas as pd
from datetime import datetime
from config import CONVEYOR_CONFIG, PARTIES_FILE


def get_conveyor_config():
    """Читает файл конвейер_настройки.xlsx и возвращает список этапов."""
    try:
        df = pd.read_excel(CONVEYOR_CONFIG)
        stages = []
        for _, row in df.iterrows():
            stages.append({
                "id": row.get("ID", len(stages) + 1),
                "name": row.get("Название этапа", ""),
                "role": row.get("Ответственный (роль)", ""),
                "norm_minutes": row.get("Норма времени (мин)", 0),
                "requires_photo": str(row.get("Требует фотоотчёт", "Нет")).lower() == "да",
            })
        return stages
    except FileNotFoundError:
        return []


def get_available_parties(employee_role):
    """Возвращает список партий, где текущий этап соответствует роли сотрудника."""
    try:
        df = pd.read_excel(PARTIES_FILE)
    except FileNotFoundError:
        return []

    stages = get_conveyor_config()
    available = []

    for _, row in df.iterrows():
        current_stage_id = row.get("Текущий этап", 1)
        stage = next((s for s in stages if s["id"] == current_stage_id), None)

        if stage and stage["role"] == employee_role:
            available.append({
                "party_id": row.get("ID партии", ""),
                "name": row.get("Название", ""),
                "stage": stage["name"],
                "requires_photo": stage["requires_photo"],
            })

    return available


def complete_stage(party_id, employee_login, photo_path=None):
    """Завершает текущий этап партии."""
    df = pd.read_excel(PARTIES_FILE)
    stages = get_conveyor_config()

    # Находим партию
    mask = df["ID партии"] == party_id
    if not mask.any():
        raise ValueError(f"Партия с ID {party_id} не найдена")

    row_idx = df[mask].index[0]
    current_stage_id = df.at[row_idx, "Текущий этап"]

    # Проверяем, требует ли этап фото
    stage = next((s for s in stages if s["id"] == current_stage_id), None)
    if stage and stage["requires_photo"] and not photo_path:
        raise ValueError("Этот этап требует фотоотчёт")

    # Сохраняем фото, если есть
    if photo_path:
        photo_dir = os.path.join("cloud_storage", "Фото_партий", f"Партия_{party_id}")
        os.makedirs(photo_dir, exist_ok=True)
        photo_filename = f"Этап_{current_stage_id}.jpg"
        photo_dest = os.path.join(photo_dir, photo_filename)
        os.rename(photo_path, photo_dest)

    # Увеличиваем текущий этап на 1
    next_stage_id = current_stage_id + 1
    df.at[row_idx, "Текущий этап"] = next_stage_id

    # Если этапов больше нет — партия завершена
    if next_stage_id > len(stages):
        df.at[row_idx, "Статус"] = "завершена"
        df.at[row_idx, "Завершена"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    df.to_excel(PARTIES_FILE, index=False)
    return True