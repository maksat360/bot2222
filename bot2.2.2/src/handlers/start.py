# handlers/start.py — Регистрация и главное меню
# ================================================

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from config import ROLES_RU, ROLE_BOSS, ROLE_WORKER
from database import find_employee_by_user_id, add_employee, get_employees


def get_main_keyboard(role):
    """Возвращает клавиатуру в зависимости от роли."""
    if role == ROLE_BOSS:
        buttons = [
            ["📊 Дэшборд"],
            ["📋 Все партии", "📸 Брак (все)"],
            ["👥 Сотрудники", "⏱ Табель"],
            ["💰 Отчёты"],
        ]
    elif role == "технолог":
        buttons = [
            ["📋 Мои задачи"],
            ["📸 Брак (проверка)"],
            ["✅ Готово"],
        ]
    elif role == "табельщик":
        buttons = [
            ["⏱ Записать часы"],
            ["📊 Отчёт по часам"],
        ]
    elif role == "бухгалтер":
        buttons = [
            ["📤 Загрузить ведомость"],
            ["💰 Моя зарплата"],
        ]
    else:  # сотрудник
        buttons = [
            ["📋 Мои задачи"],
            ["📸 Сообщить о браке"],
            ["💰 Моя зарплата"],
        ]

    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or f"user{user.id}"
    full_name = (user.first_name or "") + (" " + (user.last_name or "")).strip()
    if not full_name.strip():
        full_name = username

    employee = find_employee_by_user_id(user_id)

    if not employee:
        # Первый регистрирующийся — начальник
        employees = get_employees()
        role = ROLE_BOSS if len(employees) == 0 else ROLE_WORKER

        add_employee(user_id, username, full_name.strip(), role)

        if role == ROLE_BOSS:
            await update.message.reply_text(
                f"👋 Добро пожаловать, {full_name.strip()}!\n\n"
                f"Вы зарегистрированы как **{ROLES_RU[role]}** (первый пользователь).\n\n"
                f"📌 **Ваши возможности:**\n"
                f"• 📊 Дэшборд производства\n"
                f"• 📋 Управление партиями\n"
                f"• 👥 Управление сотрудниками\n"
                f"• 📸 Контроль брака\n\n"
                f"Используйте /help для справки.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard(role),
            )
        else:
            await update.message.reply_text(
                f"👋 Добро пожаловать, {full_name.strip()}!\n\n"
                f"Вы зарегистрированы как **{ROLES_RU[role]}**.\n"
                f"Ваш руководитель назначит вам роль и задачи.\n\n"
                f"Пока вы можете:\n"
                f"• 📋 Смотреть свои задачи\n"
                f"• 💰 Смотреть зарплату",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard(role),
            )
    else:
        role = employee["Роль"]
        await update.message.reply_text(
            f"👋 С возвращением, {employee['Имя']}!\n"
            f"Ваша роль: **{ROLES_RU.get(role, role)}**",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(role),
        )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    role = employee["Роль"] if employee else ROLE_WORKER

    help_text = "📖 **Справка по MES V2**\n\n"
    help_text += "**Основные команды:**\n"
    help_text += "• /start — Главное меню\n"
    help_text += "• /help — Эта справка\n\n"

    if role == ROLE_BOSS:
        help_text += "**👑 Начальник:**\n"
        help_text += "• 📊 Дэшборд — состояние производства\n"
        help_text += "• 📋 Все партии — управление партиями\n"
        help_text += "• 👥 Сотрудники — назначение ролей\n"
        help_text += "• 📸 Брак — просмотр всех дефектов\n"
        help_text += "• ⏱ Табель — учёт рабочего времени\n"
        help_text += "• /setrole @username роль — назначить роль\n\n"
    elif role == "технолог":
        help_text += "**🔧 Технолог:**\n"
        help_text += "• 📋 Мои задачи — доступные партии\n"
        help_text += "• 📸 Брак (проверка) — просмотр брака\n"
        help_text += "• ✅ Готово — завершить этап\n\n"
    elif role == "табельщик":
        help_text += "**⏱ Табельщик:**\n"
        help_text += "• ⏱ Записать часы — внести часы сотруднику\n"
        help_text += "• 📊 Отчёт по часам — сводка\n\n"
    else:
        help_text += "**👷 Сотрудник:**\n"
        help_text += "• 📋 Мои задачи — текущие задачи\n"
        help_text += "• 📸 Сообщить о браке — фото дефекта\n"
        help_text += "• 💰 Моя зарплата — личная ведомость\n\n"

    help_text += "💡 **Принцип работы:**\n"
    help_text += "Партия проходит этапы по цепочке. Вы видите только свои задачи.\n"
    help_text += "Брак фиксируется фото. Зарплата — только личная."

    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(role),
    )