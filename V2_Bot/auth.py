# auth.py — Авторизация пользователей
# =====================================

import pandas as pd
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext

from config import USERS_FILE
from database import get_connection


async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start."""
    user_id = str(update.effective_user.id)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sessions WHERE telegram_id = ?", (user_id,))
    session = cursor.fetchone()
    conn.close()

    if session:
        await show_main_menu(update, session["role"])
    else:
        await update.message.reply_text(
            "👋 Добро пожаловать! Пожалуйста, введите ваш логин и пароль через пробел.\n"
            "Пример: Иванов Иван123"
        )
        context.user_data["awaiting_login"] = True


async def handle_login(update: Update, context: CallbackContext):
    """Обработчик текстового сообщения с логином и паролем."""
    if not context.user_data.get("awaiting_login"):
        return

    text = update.message.text.strip()
    parts = text.split(" ", 1)

    if len(parts) != 2:
        await update.message.reply_text(
            "❌ Неверный формат. Введите логин и пароль через пробел.\n"
            "Пример: Иванов Иван123"
        )
        return

    login, password = parts

    # Читаем файл пользователи.xlsx
    try:
        df = pd.read_excel(USERS_FILE)
    except FileNotFoundError:
        await update.message.reply_text("❌ База пользователей не найдена. Обратитесь к администратору.")
        return

    # Ищем пользователя
    user_row = df[(df["Логин"] == login) & (df["Пароль"] == password)]

    if user_row.empty:
        await update.message.reply_text("❌ Неверный логин или пароль. Попробуйте снова.")
        return

    user_data = user_row.iloc[0]
    telegram_id = str(update.effective_user.id)

    # Сохраняем telegram_id в файл пользователи.xlsx
    df.loc[df["Логин"] == login, "Telegram ID"] = telegram_id
    df.to_excel(USERS_FILE, index=False)

    # Создаём сессию в SQLite
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO sessions (telegram_id, login, company_id, role, logged_in_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (telegram_id, login, user_data.get("Компания", ""), user_data.get("Роль", "user"), datetime.now())
    )
    conn.commit()
    conn.close()

    context.user_data["awaiting_login"] = False
    context.user_data["login"] = login
    context.user_data["role"] = user_data.get("Роль", "user")

    await update.message.reply_text(f"✅ Добро пожаловать, {user_data.get('ФИО', login)}!")
    await show_main_menu(update, user_data.get("Роль", "user"))


async def show_main_menu(update: Update, user_role: str):
    """Показывает клавиатуру в зависимости от роли пользователя."""
    if user_role == "admin":
        keyboard = [
            ["📊 Производство", "📋 Все партии"],
            ["📸 Брак", "💰 Моя зарплата"],
        ]
    else:
        keyboard = [
            ["📋 Мои задачи", "📸 Брак"],
            ["💰 Моя зарплата", "⏱ Мои часы"],
        ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Главное меню:", reply_markup=reply_markup)