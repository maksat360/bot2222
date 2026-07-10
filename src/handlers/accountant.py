# handlers/accountant.py — Команды бухгалтера
# ============================================

from telegram import Update
from telegram.ext import ContextTypes
from config import ROLE_ACCOUNTANT
from database import find_employee_by_user_id
from handlers.start import get_main_keyboard


async def cmd_upload_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📤 Загрузить ведомость."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee or employee["Роль"] != ROLE_ACCOUNTANT:
        return await update.message.reply_text("❌ Только бухгалтер может загружать ведомости.")

    await update.message.reply_text(
        "📤 **Загрузка ведомости**\n\n"
        "Функция загрузки зарплатных ведомостей будет доступна после подключения облачного хранилища.\n\n"
        "Пока вы можете просмотреть свою зарплату через \"💰 Моя зарплата\".",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(employee["Роль"]),
    )