# salary.py — Зарплатные отчёты
# ===============================

import os
import pandas as pd
from config import SALARY_ROOT, SALARY_PERSONAL, TEMP_DIR


def upload_salary_report(file_path, year, month):
    """Загружает общий Excel-отчёт и разбивает на личные файлы."""
    required_columns = [
        "Логин", "ФИО", "Должность", "Оклад",
        "Отработано часов", "Премия", "Удержания", "Итого к выдаче"
    ]

    df = pd.read_excel(file_path)

    # Проверяем наличие всех колонок
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Отсутствует обязательная колонка: {col}")

    # Создаём папку для месяца
    month_dir = os.path.join(SALARY_ROOT, str(year), str(month))
    os.makedirs(month_dir, exist_ok=True)

    # Сохраняем общий отчёт
    general_path = os.path.join(month_dir, f"Общий_отчет_{month}_{year}.xlsx")
    df.to_excel(general_path, index=False)

    # Разбиваем на личные файлы
    split_into_personal_files(year, month, df)

    return general_path


def split_into_personal_files(year, month, df=None):
    """Разбивает общий отчёт на личные файлы сотрудников."""
    if df is None:
        month_dir = os.path.join(SALARY_ROOT, str(year), str(month))
        general_path = os.path.join(month_dir, f"Общий_отчет_{month}_{year}.xlsx")
        df = pd.read_excel(general_path)

    for _, row in df.iterrows():
        login = row["Логин"]
        employee_dir = os.path.join(SALARY_PERSONAL, f"Сотрудник_{login}")
        os.makedirs(employee_dir, exist_ok=True)

        personal_path = os.path.join(employee_dir, f"Зарплата_{month}_{year}.xlsx")
        personal_df = pd.DataFrame([row])
        personal_df.to_excel(personal_path, index=False)


def get_available_periods(employee_login):
    """Сканирует папку сотрудника и возвращает список доступных периодов."""
    employee_dir = os.path.join(SALARY_PERSONAL, f"Сотрудник_{employee_login}")

    if not os.path.exists(employee_dir):
        return []

    periods = []
    for filename in os.listdir(employee_dir):
        if filename.startswith("Зарплата_") and filename.endswith(".xlsx"):
            parts = filename.replace(".xlsx", "").split("_")
            if len(parts) >= 3:
                month = parts[1]
                year = parts[2]
                periods.append({"year": year, "month": month})

    return periods


def get_employee_salary_data(employee_login, year, month):
    """Читает личный файл сотрудника и возвращает словарь с данными."""
    employee_dir = os.path.join(SALARY_PERSONAL, f"Сотрудник_{employee_login}")
    personal_path = os.path.join(employee_dir, f"Зарплата_{month}_{year}.xlsx")

    if not os.path.exists(personal_path):
        return None

    df = pd.read_excel(personal_path)
    if df.empty:
        return None

    return df.iloc[0].to_dict()


def merge_all_salaries(year, month):
    """Собирает все личные файлы за период в один общий отчёт."""
    if not os.path.exists(SALARY_PERSONAL):
        return None

    all_data = []
    for emp_dir in os.listdir(SALARY_PERSONAL):
        emp_path = os.path.join(SALARY_PERSONAL, emp_dir)
        if not os.path.isdir(emp_path):
            continue

        personal_path = os.path.join(emp_path, f"Зарплата_{month}_{year}.xlsx")
        if os.path.exists(personal_path):
            df = pd.read_excel(personal_path)
            all_data.append(df)

    if not all_data:
        return None

    merged_df = pd.concat(all_data, ignore_index=True)

    month_dir = os.path.join(SALARY_ROOT, str(year), str(month))
    os.makedirs(month_dir, exist_ok=True)
    merged_path = os.path.join(month_dir, f"Сводный_отчет_{month}_{year}.xlsx")
    merged_df.to_excel(merged_path, index=False)

    return merged_path