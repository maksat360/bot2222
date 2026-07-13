# main.py — Точка входа Telegram-бота V2
# ========================================

import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config import BOT_TOKEN
from database import init_database
from auth import start, handle_login, show_main_menu
from salary import upload_salary_report, get_employee_salary_data
from conveyor import get_available_parties, complete_stage
from defect import report_defect, get_pending_defects, process_defect
from dashboard import get_dashboard
from time_tracking import record_hours, get_employee_hours
from marketing import get_pr_message

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def error_handler(update, context):
    """Глобальный обработчик ошибок."""
    logger.error(f"Ошибка: {context.error}", exc_info=True)
    if update and update.effective_message:
        await update.effective_message.reply_text(get_pr_message())


async def handle_text(update, context):
    """Обработчик текстовых сообщений (кнопок меню)."""
    text = update.message.text

    handlers = {
        "💰 Моя зарплата": handle_my_salary,
        "📋 Мои задачи": handle_my_tasks,
        "📸 Брак": handle_defect,
        "📊 Производство": handle_dashboard,
        "📋 Все партии": handle_all_parties,
        "⏱ Мои часы": handle_my_hours,
    }

    handler = handlers.get(text)
    if handler:
        await handler(update, context)
    else:
        await update.message.reply_text(
            "❓ Неизвестная команда. Используйте /start для входа в меню."
        )


async def handle_my_salary(update, context):
    """Показывает зарплату текущего пользователя."""
    login = context.user_data.get("login")
    if not login:
        await update.message.reply_text("❌ Вы не авторизованы. Используйте /start.")
        return

    data = get_employee_salary_data(login, "2026", "Июль")
    if data:
        text = (
            f"💰 **Зарплата**\n\n"
            f"ФИО: {data.get('ФИО', '')}\n"
            f"Должность: {data.get('Должность', '')}\n"
            f"Оклад: {data.get('Оклад', '')}\n"
            f"Отработано часов: {data.get('Отработано часов', '')}\n"
            f"Премия: {data.get('Премия', '')}\n"
            f"Удержания: {data.get('Удержания', '')}\n"
            f"**Итого к выдаче: {data.get('Итого к выдаче', '')}**"
        )
    else:
        text = "📭 Данные о зарплате пока не загружены."

    await update.message.reply_text(text)


async def handle_my_tasks(update, context):
    """Показывает задачи текущего пользователя."""
    role = context.user_data.get("role", "user")
    parties = get_available_parties(role)

    if not parties:
        await update.message.reply_text("📭 Нет доступных задач.")
        return

    text = "📋 **Ваши задачи:**\n\n"
    for party in parties:
        text += f"• Партия #{party['party_id']}: {party['name']} — этап: {party['stage']}\n"

    await update.message.reply_text(text)


async def handle_defect(update, context):
    """Обработчик брака."""
    await update.message.reply_text(
        "📸 Отпра��ьте фото брака, указав ID партии и процесса.\n"
        "Формат: /defect ID_партии ID_процесса"
    )


async def handle_dashboard(update, context):
    """Показывает дэшборд производства."""
    dashboard_text = get_dashboard()
    await update.message.reply_text(dashboard_text)


async def handle_all_parties(update, context):
    """Показывает все партии."""
    import pandas as pd
    from config import PARTIES_FILE

    try:
        df = pd.read_excel(PARTIES_FILE)
        text = "📋 **Все партии:**\n\n"
        for _, row in df.iterrows():
            text += f"• #{row['ID партии']} {row['Название']} — этап {row['Текущий этап']}, статус: {row['Статус']}\n"
    except FileNotFoundError:
        text = "📭 Нет данных о партиях."

    await update.message.reply_text(text)


async def handle_my_hours(update, context):
    """Показывает часы текущего пользователя."""
    login = context.user_data.get("login")
    if not login:
        await update.message.reply_text("❌ Вы не авторизованы. Используйте /start.")
        return

    hours = get_employee_hours(login, 7, 2026)  # Июль 2026
    await update.message.reply_text(f"⏱ Ваши часы за Июль 2026: {hours} ч.")


def main():
    """Главная функция запуска бота."""
    # Инициализируем базу данных
    init_database()

    # Создаём приложение
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))

    # Обработчик текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Обработчик ошибок
    app.add_error_handler(error_handler)

    logger.info("Бот запущен!")
    print("🤖 V2 Telegram-бот запущен! Нажмите Ctrl+C для остановки.")

    # Запускаем бота
    app.run_polling()


if __name__ == "__main__":
    main()