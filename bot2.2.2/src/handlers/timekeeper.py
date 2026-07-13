# handlers/timekeeper.py — Команды табельщика
# ============================================

from telegram import Update
from telegram.ext import ContextTypes
from config import ROLE_TIMEKEEPER
from database import find_employee_by_user_id, get_employees, get_timesheets, add_timesheet
from handlers.start import get_main_keyboard


async def cmd_record_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⏱ Записать часы."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee or employee["Роль"] != ROLE_TIMEKEEPER:
        return await update.message.reply_text("❌ Только табельщик может записывать часы.")

    employees = get_employees()
    emp_list = "\n".join([
        f"• @{e['Username']} — {e['Имя']} ({e['Роль']})"
        for e in employees
    ])

    await update.message.reply_text(
        f"⏱ **Запись часов**\n\n"
        f"Формат: /hours @username ГГГГ-ММ-ДД часы\n\n"
        f"Пример: /hours @ivanov 2026-07-15 8\n\n"
        f"**Сотрудники:**\n{emp_list}",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(employee["Роль"]),
    )


async def cmd_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запись часов (/hours)."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee or employee["Роль"] != ROLE_TIMEKEEPER:
        return await update.message.reply_text("❌ Только табельщик может записывать часы.")

    args = context.args
    if len(args) < 3:
        return await update.message.reply_text("❌ Формат: /hours @username ГГГГ-ММ-ДД часы")

    target_username = args[0].replace("@", "")
    date = args[1]

    try:
        hours = float(args[2])
    except ValueError:
        return await update.message.reply_text("❌ Некорректное количество часов.")

    if hours <= 0 or hours > 24:
        return await update.message.reply_text("❌ Часы должны быть от 1 до 24.")

    employees = get_employees()
    target = None
    for e in employees:
        if e["Username"] == target_username:
            target = e
            break

    if not target:
        return await update.message.reply_text(f"❌ Сотрудник @{target_username} не найден.")

    add_timesheet(target["Telegram ID"], target["Имя"], date, hours, employee["Имя"])

    await update.message.reply_text(
        f"✅ **Часы записаны!**\n\n"
        f"👷 {target['Имя']}\n"
        f"📅 {date}\n"
        f"⏱ {hours} ч.\n"
        f"✍️ Записал: {employee['Имя']}",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(employee["Роль"]),
    )


async def cmd_hours_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Отчёт по часам."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee or employee["Роль"] != ROLE_TIMEKEEPER:
        return await update.message.reply_text("❌ Нет доступа.")

    timesheets = get_timesheets()
    if not timesheets:
        return await update.message.reply_text(
            "📭 Нет записей.",
            reply_markup=get_main_keyboard(employee["Роль"]),
        )

    msg = "⏱ **Отчёт по часам**\n\n"
    last_10 = timesheets[-10:]
    last_10.reverse()
    for t in last_10:
        msg += f"• {t['Имя']}: {t['Дата']} — {t['Часы']} ч.\n"

    msg += f"\n📄 Всего записей: {len(timesheets)}"

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_keyboard(employee["Роль"]))