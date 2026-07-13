# config.py — Конфигурация Telegram-бота V2
# ============================================

import os

# Токен бота (получить у @BotFather)
BOT_TOKEN = "8922842876:AAGexcEWd7rG8I8_qocp_6ThZR1bcQCjhqY"

# Путь к папке облачного хранилища
CLOUD_PATH = "cloud_storage"

# Пути к файлам Excel
USERS_FILE = os.path.join(CLOUD_PATH, "пользователи.xlsx")
PARTIES_FILE = os.path.join(CLOUD_PATH, "партии.xlsx")
TIME_FILE = os.path.join(CLOUD_PATH, "учёт_времени.xlsx")
DEFECT_FILE = os.path.join(CLOUD_PATH, "брак.xlsx")
CONVEYOR_CONFIG = os.path.join(CLOUD_PATH, "конвейер_настройки.xlsx")

# Пути к папкам зарплат
SALARY_ROOT = os.path.join(CLOUD_PATH, "Зарплатные_отчеты")
SALARY_PERSONAL = os.path.join(CLOUD_PATH, "Зарплаты")
TEMP_DIR = os.path.join(CLOUD_PATH, "Временные")

# Настройки
TRIAL_DAYS = 60
CACHE_TTL_SECONDS = 300
TEMP_CLEANUP_MINUTES = 10
DROPBOX_CHECK_MINUTES = 5
