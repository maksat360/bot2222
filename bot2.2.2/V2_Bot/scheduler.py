# scheduler.py — Фоновые задачи
# ===============================

import os
import threading
import schedule
import time
import logging

from pdf_generator import cleanup_temp_files

logger = logging.getLogger(__name__)


def check_new_reports():
    """Проверяет папку Отчёты на новые файлы."""
    reports_dir = os.path.join("cloud_storage", "Отчёты")
    if not os.path.exists(reports_dir):
        return

    for filename in os.listdir(reports_dir):
        filepath = os.path.join(reports_dir, filename)
        if os.path.isfile(filepath):
            logger.info(f"Обнаружен новый отчёт: {filename}")


def run_scheduler():
    """Запускает цикл планировщика в фоновом потоке."""
    schedule.every(5).minutes.do(check_new_reports)
    schedule.every().hour.do(cleanup_temp_files)

    while True:
        schedule.run_pending()
        time.sleep(1)


def start_scheduler():
    """Запускает фоновые задачи в отдельном потоке."""
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Планировщик фоновых задач запущен.")
    return scheduler_thread