# marketing.py — Маркетинговые функции
# =====================================

from database import get_connection
from datetime import datetime


def get_pr_message():
    """Возвращает сообщение для пользователя при ошибке."""
    return (
        "Извините, нас стало слишком много, сервер не справляется. "
        "Мы расширяем мощности. Спасибо за понимание!"
    )


def create_showcase_companies():
    """Создаёт в таблице companies записи для компаний-витрин."""
    showcase_companies = [
        "Азия Текстиль",
        "Бишкек Швей",
        "Ош Пром",
        "Кара-Балта Стиль",
        "Токмок Текс",
    ]

    conn = get_connection()
    cursor = conn.cursor()

    for company_name in showcase_companies:
        company_id = company_name.lower().replace(" ", "_")
        cursor.execute(
            """
            INSERT OR IGNORE INTO companies (id, name, cloud_type, cloud_folder_id, created_at, is_active, is_showcase)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_id,
                company_name,
                "local",
                company_id,
                datetime.now(),
                1,
                1,
            )
        )

    conn.commit()
    conn.close()

    return len(showcase_companies)