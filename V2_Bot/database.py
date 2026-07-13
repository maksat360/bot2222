# database.py — База данных SQLite
# =================================

import sqlite3
import os

DB_PATH = os.path.join("data", "bot.db")


def get_connection():
    """Возвращает подключение к базе данных."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Создаёт таблицы базы данных, если их нет."""
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица компаний
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id TEXT PRIMARY KEY,
            name TEXT,
            cloud_type TEXT,
            cloud_folder_id TEXT,
            created_at TIMESTAMP,
            trial_ends_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            is_showcase BOOLEAN DEFAULT 0
        )
    """)

    # Таблица сессий
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            telegram_id TEXT PRIMARY KEY,
            login TEXT,
            company_id TEXT,
            role TEXT,
            logged_in_at TIMESTAMP
        )
    """)

    # Таблица глобальных паролей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_passwords (
            password_hash TEXT PRIMARY KEY,
            company_id TEXT,
            created_at TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()