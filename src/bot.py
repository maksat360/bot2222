# bot.py — Главный файл MES V2 Telegram-бота
# ============================================
# Запуск: python bot.py
# Требуется: BOT_TOKEN в переменных окружения или .env файле

import os
import json
import logging
from dotenv import load_dotenv

# Загружаем .env если есть
load_dotenv()

from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, CallbackContext
)
from telegram import Update
from telegram.request import HTTPXRequest
import httpx

from config import BOT_TOKEN
from database import init_all_databases, find_employee_by_user_id

from handlers.start import cmd_start, cmd_help, get_main_keyboard
from handlers.boss import (
    cmd_dashboard, cmd_all_batches, cmd_new_batch,
    cmd_employees, cmd_setrole, cmd_reports, cmd_tabel,
)
from handlers.worker import (
    cmd_my_tasks, cmd_start_process, cmd_done_process,
    cmd_ready, cmd_report_defect, cmd_show_defects,
    cmd_defect_decision, cmd_my_salary, handle_photo,
)
from handlers.timekeeper import cmd_record_hours, cmd_hours, cmd_hours_report
from handlers.accountant import cmd_upload_salary

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _build_app(token):
    """Создаёт приложение с поддержкой прокси (если указан PROXY_URL)."""
    proxy_url = os.getenv("PROXY_URL", "")
    if proxy_url:
        logger.info(f"🔌 Используется прокси: {proxy_url}")
        # Создаём httpx клиент с прокси
        transport = httpx.AsyncHTTPTransport(proxy=proxy_url)
        client = httpx.AsyncClient(transport=transport)
        request = HTTPXRequest(http_client=client)
        return ApplicationBuilder().token(token).request(request).build()
    else:
        return ApplicationBuilder().token(token).build()


async def error_handler(update: Update, context: CallbackContext):
    """Глобальный обработчик ошибок."""
    logger.error(f"Ошибка: {context.error}", exc_info=True)
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Произошла внутренняя ошибка. Попробуйте ещё раз."
        )


async def handle_text(update: Update, context: CallbackContext):
    """Обработка текстовых кнопок меню."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee:
        return await update.message.reply_text("👋 Напишите /start для регистрации.")

    text = update.message.text
    role = employee["Роль"]

    # Обработка команд вида /start_N, /done_N, /defect_N_*
    if text.startswith("/start_"):
        return await cmd_start_process(update, context)
    elif text.startswith("/done_"):
        return await cmd_done_process(update, context)
    elif text.startswith("/defect_"):
        return await cmd_defect_decision(update, context)

    # Кнопки меню
    menu_actions = {
        # Начальник
        "📊 Дэшборд": cmd_dashboard,
        "📋 Все партии": cmd_all_batches,
        "👥 Сотрудники": cmd_employees,
        "📸 Брак (все)": cmd_show_defects,
        "💰 Отчёты": cmd_reports,
        "⏱ Табель": cmd_tabel,

        # Технолог / Сотрудник
        "📋 Мои задачи": cmd_my_tasks,
        "📸 Брак (проверка)": cmd_show_defects,
        "✅ Готово": cmd_ready,
        "📸 Сообщить о браке": cmd_report_defect,
        "💰 Моя зарплата": cmd_my_salary,

        # Табельщик
        "⏱ Записать часы": cmd_record_hours,
        "📊 Отчёт по часам": cmd_hours_report,

        # Бухгалтер
        "📤 Загрузить ведомость": cmd_upload_salary,
    }

    handler = menu_actions.get(text)
    if handler:
        await handler(update, context)
    else:
        await update.message.reply_text(
            f"❓ Неизвестная команда. Используйте /help для справки.",
            reply_markup=get_main_keyboard(role),
        )


# ============================================================
# ХЕНДЛЕР ДЛЯ YANDEX CLOUD FUNCTIONS
# ============================================================

# Глобальный экземпляр приложения для YC Functions
_application = None


def _get_application():
    """Создаёт и возвращает экземпляр приложения (синглтон)."""
    global _application
    if _application is None:
        token = BOT_TOKEN or os.getenv("BOT_TOKEN")
        if not token:
            raise ValueError("BOT_TOKEN не указан!")

        # Инициализируем Excel-базы данных
        init_all_databases()

        app = _build_app(token)

        # Регистрируем команды
        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("help", cmd_help))
        app.add_handler(CommandHandler("newbatch", cmd_new_batch))
        app.add_handler(CommandHandler("setrole", cmd_setrole))
        app.add_handler(CommandHandler("hours", cmd_hours))

        # Обработчики текста
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        app.add_error_handler(error_handler)

        _application = app

    return _application


def handler(event, context):
    """Хендлер для Yandex Cloud Functions (HTTP-триггер)."""
    try:
        # Инициализируем базы данных
        init_all_databases()

        # Парсим входящий запрос от Telegram
        body = json.loads(event.get("body", "{}"))

        # Создаём update и обрабатываем
        app = _get_application()
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(app.process_update(
            Update.de_json(body, app.bot)
        ))

        return {
            "statusCode": 200,
            "body": "",
        }
    except Exception as e:
        logger.error(f"YC Function error: {e}", exc_info=True)
        return {
            "statusCode": 200,
            "body": "",
        }


def main():
    """Запуск бота в режиме polling (локально)."""
    # Проверяем токен
    token = BOT_TOKEN or os.getenv("BOT_TOKEN")
    if not token:
        print("❌ Ошибка: BOT_TOKEN не указан!")
        print("📌 Создайте файл .env и добавьте: BOT_TOKEN=ваш_токен")
        print("   Или установите переменную окружения BOT_TOKEN")
        return

    # Инициализируем Excel-базы данных
    print("📁 Инициализация Excel-файлов...")
    init_all_databases()
    print("✅ Базы данных готовы!")

    # Создаём приложение с поддержкой прокси
    app = _build_app(token)

    # Регистрируем команды
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("newbatch", cmd_new_batch))
    app.add_handler(CommandHandler("setrole", cmd_setrole))
    app.add_handler(CommandHandler("hours", cmd_hours))

    # Обработчики текста (кнопки меню)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Обработчик фото (брак)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Глобальный обработчик ошибок
    app.add_error_handler(error_handler)

    print("🤖 MES V2 бот запущен!")
    print("📌 Нажмите Ctrl+C для остановки")
    print("=" * 40)

    # Запускаем polling
    app.run_polling()


if __name__ == "__main__":
    main()