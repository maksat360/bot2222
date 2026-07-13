# time_tracking.py — Учёт рабочего времени
# ==========================================

import pandas as pd
from datetime import datetime
from config import TIME_FILE


def record_hours(employee, date, hours, project, manager):
    """Добавляет запись в файл учёт_времени.xlsx."""
    try:
        df = pd.read_excel(TIME_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "Сотрудник", "Дата", "Часы", "Проект", "Менеджер", "Дата записи"
        ])

    new_record = {
        "Сотрудник": employee,
        "Дата": date,
        "Часы": hours,
        "Проект": project,
        "Менеджер": manager,
        "Дата записи": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
    df.to_excel(TIME_FILE, index=False)

    return True


def get_employee_hours(employee_login, month, year):
    """Суммирует часы сотрудника за указанный месяц."""
    try:
        df = pd.read_excel(TIME_FILE)
    except FileNotFoundError:
        return 0

    # Фильтруем по сотруднику
    employee_df = df[df["Сотрудник"] == employee_login]

    if employee_df.empty:
        return 0

    # Фильтруем по месяцу и году
    employee_df["Дата"] = pd.to_datetime(employee_df["Дата"], errors="coerce")
    month_df = employee_df[
        (employee_df["Дата"].dt.month == month) &
        (employee_df["Дата"].dt.year == year)
    ]

    total_hours = month_df["Часы"].sum()
    return total_hours