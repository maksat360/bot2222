# bot.py — Главный файл MES V2 Telegram-бота
# ============================================
# Запуск: python bot.py
# Требуется: BOT_TOKEN в переменных окружения или .env файле

import os
import sys
from dotenv import load_dotenv

# Загружаем .env ДО ВСЕХ импортов
load_dotenv()

# Устанавливаем прокси ДО создания httpx клиента
proxy_url = os.getenv("PROXY_URL", "")
if proxy_url:
    os.environ["HTTP_PROXY"] = proxy_url
    os.environ["HTTPS_PROXY"] = proxy_url
    os.environ["ALL_PROXY"] = proxy_url
    print(f"🔌 Прокси: {proxy_url}")

import json
import logging
import urllib.request
import asyncio

from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, CallbackContext
)
from telegram import Update

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

# Глобальный экземпляр приложения и event loop для YC Functions
_application = None
_app_loop = None


async def _init_app_async():
    """Создаёт и возвращает экземпляр приложения с полной инициализацией (синглтон)."""
    global _application
    if _application is None:
        token = BOT_TOKEN or os.getenv("BOT_TOKEN")
        if not token:
            raise ValueError("BOT_TOKEN не указан!")

        # Инициализируем Excel-базы данных
        init_all_databases()

        app = ApplicationBuilder().token(token).build()

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

        # ВАЖНО: инициализируем и запускаем приложение,
        # чтобы внутренний обработчик очереди update_queue был активен
        await app.initialize()
        await app.start()

        _application = app
        logger.info("✅ Приложение PTB инициализировано и запущено")

    return _application


def _get_or_create_loop():
    """Возвращает или создаёт event loop (синглтон для YC Functions)."""
    global _app_loop
    if _app_loop is None or _app_loop.is_closed():
        _app_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_app_loop)
    return _app_loop


def _setup_webhook(invoke_url):
    """Устанавливает webhook для бота."""
    token = BOT_TOKEN or os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN не указан, webhook не установлен")
        return False, "BOT_TOKEN не указан"

    webhook_url = f"https://api.telegram.org/bot{token}/setWebhook?url={invoke_url}"
    try:
        req = urllib.request.Request(webhook_url, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            if result.get("ok"):
                logger.info(f"✅ Webhook установлен: {invoke_url}")
                return True, f"✅ Webhook установлен: {invoke_url}"
            else:
                logger.error(f"❌ Ошибка webhook: {result}")
                return False, f"❌ Ошибка: {result}"
    except Exception as e:
        logger.error(f"❌ Не удалось установить webhook: {e}")
        return False, f"❌ Ошибка: {e}"


def handler(event, context):
    """Хендлер для Yandex Cloud Functions (HTTP-триггер)."""
    try:
        # Инициализируем базы данных
        init_all_databases()

        http_method = event.get("httpMethod", "POST")

        # Если это GET-запрос — пытаемся установить webhook
        if http_method == "GET":
            headers = event.get("headers", {})
            host = headers.get("Host", "")
            url_path = event.get("url", "")

            base_path = url_path
            for suffix in ["/setup-webhook", "/setup", "/webhook"]:
                if base_path.endswith(suffix):
                    base_path = base_path[:-len(suffix)]
                    break

            invoke_url = f"https://{host}{base_path}"

            if not host:
                invoke_url = os.getenv("INVOKE_URL", "")

            success, message = _setup_webhook(invoke_url)

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "ok" if success else "error",
                    "message": message,
                    "invoke_url": invoke_url,
                }),
                "headers": {"Content-Type": "application/json"},
            }

        # POST-запрос — обрабатываем update от Telegram
        body = json.loads(event.get("body", "{}"))

        # Получаем или создаём event loop (единый для всех вызовов)
        loop = _get_or_create_loop()

        # Инициализируем приложение (если ещё не инициализировано)
        app = loop.run_until_complete(_init_app_async())

        # Обрабатываем update — process_update сам дожидается завершения обработки
        update = Update.de_json(body, app.bot)
        loop.run_until_complete(app.process_update(update))

        return {
            "statusCode": 200,
            "body": "",
        }
    except Exception as e:
        logger.error(f"YC Function error: {e}", exc_info=True)
        return {
            "statusCode": 200,
            "body": json.dumps({"error": str(e)}),
        }


def main():
    """Запуск бота в режиме polling (локально)."""
    token = BOT_TOKEN or os.getenv("BOT_TOKEN")
    if not token:
        print("❌ Ошибка: BOT_TOKEN не указан!")
        print("📌 Создайте файл .env и добавьте: BOT_TOKEN=ваш_токен")
        print("   Или установите переменную окружения BOT_TOKEN")
        return

    print("📁 Инициализация Excel-файлов...")
    init_all_databases()
    print("✅ Базы данных готовы!")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("newbatch", cmd_new_batch))
    app.add_handler(CommandHandler("setrole", cmd_setrole))
    app.add_handler(CommandHandler("hours", cmd_hours))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_error_handler(error_handler)

    print("🤖 MES V2 бот запущен!")
    print("📌 Нажмите Ctrl+C для остановки")
    print("=" * 40)

    app.run_polling()


if __name__ == "__main__":
    main()