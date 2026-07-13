# config.py — Конфигурация MES V2
# =================================

import os
from pathlib import Path

# Пути к файлам
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"

# Файлы Excel-базы данных
DB_PIPELINE = DATA_DIR / "конвейер_настройки.xlsx"
DB_EMPLOYEES = DATA_DIR / "сотрудники.xlsx"
DB_BATCHES = DATA_DIR / "партии.xlsx"
DB_DEFECTS = DATA_DIR / "брак.xlsx"
DB_TIMESHEETS = DATA_DIR / "табель.xlsx"
DB_SALARY = DATA_DIR / "зарплата.xlsx"

# Роли
ROLE_BOSS = "начальник"
ROLE_TECHNOLOGIST = "технолог"
ROLE_TIMEKEEPER = "табельщик"
ROLE_ACCOUNTANT = "бухгалтер"
ROLE_WORKER = "сотрудник"

ROLES_RU = {
    ROLE_BOSS: "👑 Начальник",
    ROLE_TECHNOLOGIST: "🔧 Технолог",
    ROLE_TIMEKEEPER: "⏱ Табельщик",
    ROLE_ACCOUNTANT: "💰 Бухгалтер",
    ROLE_WORKER: "👷 Сотрудник",
}

# Статусы партий
BATCH_AWAITING = "ожидает"
BATCH_IN_PROGRESS = "в_работе"
BATCH_COMPLETED = "завершена"

# Статусы дефектов
DEFECT_PENDING = "ожидает"
DEFECT_APPROVED = "принят"
DEFECT_REJECTED = "отклонён"

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "8922842876:AAGAzs9tFpjoLTZ67_atVhRR-b4uuM_KQxM")
