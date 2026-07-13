# dashboard.py — Дэшборд начальника
# ===================================

import pandas as pd
from datetime import datetime
from config import PARTIES_FILE, CONVEYOR_CONFIG


def get_dashboard():
    """Возвращает текстовую сводку по всем партиям."""
    try:
        parties_df = pd.read_excel(PARTIES_FILE)
    except FileNotFoundError:
        return "❌ Файл с партиями не найден."

    try:
        config_df = pd.read_excel(CONVEYOR_CONFIG)
    except FileNotFoundError:
        return "❌ Файл настроек конвейера не найден."

    # Создаём словарь норм времени для этапов
    norms = {}
    for _, row in config_df.iterrows():
        norms[row["ID"]] = row["Норма времени (мин)"]

    report_lines = ["📊 **Дэшборд производства**\n"]

    for _, party in parties_df.iterrows():
        party_id = party.get("ID партии", "")
        party_name = party.get("Название", "")
        current_stage = party.get("Текущий этап", 1)
        status = party.get("Статус", "")
        created_at = party.get("Создана", "")

        if status == "завершена":
            report_lines.append(f"✅ Партия #{party_id} ({party_name}) — **ЗАВЕРШЕНА**")
            continue

        # Получаем норму для текущего этапа
        norm_minutes = norms.get(current_stage, 60)

        # Вычисляем время на текущем этапе
        if created_at:
            try:
                created_time = datetime.strptime(str(created_at), "%Y-%m-%d %H:%M")
                elapsed_minutes = (datetime.now() - created_time).total_seconds() / 60
            except ValueError:
                elapsed_minutes = 0
        else:
            elapsed_minutes = 0

        # Определяем статус
        if elapsed_minutes < norm_minutes * 1.5:
            indicator = "✅"
        elif elapsed_minutes > norm_minutes * 4:
            indicator = "🚨"
        elif elapsed_minutes > norm_minutes * 2:
            indicator = "⚠️"
        else:
            indicator = "✅"

        # Прогноз готовности: сумма норм оставшихся этапов
        remaining_stages = [s for s in norms.keys() if s >= current_stage]
        remaining_time = sum(norms.get(s, 0) for s in remaining_stages)

        report_lines.append(
            f"{indicator} Партия #{party_id} ({party_name})\n"
            f"   • Этап {current_stage}: {elapsed_minutes:.0f} мин (норма: {norm_minutes} мин)\n"
            f"   • ⏱ Прогноз готовности: ~{remaining_time} мин\n"
        )

    if len(report_lines) == 1:
        report_lines.append("📭 Нет активных партий.")

    return "\n".join(report_lines)