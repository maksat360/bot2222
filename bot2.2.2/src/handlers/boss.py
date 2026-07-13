# handlers/boss.py — Команды начальника
# ======================================

from telegram import Update
from telegram.ext import ContextTypes
from config import ROLE_BOSS, ROLES_RU, BATCH_AWAITING, BATCH_IN_PROGRESS, BATCH_COMPLETED, DEFECT_PENDING
from database import (
    find_employee_by_user_id, get_employees, get_batches, get_defects,
    get_timesheets, get_pipeline, add_batch, update_employee_role,
)
from handlers.start import get_main_keyboard


async def cmd_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Дэшборд производства."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee or employee["Роль"] != ROLE_BOSS:
        return await update.message.reply_text("❌ Только начальник может просматривать дэшборд.")

    pipeline = get_pipeline()
    batches = get_batches()
    employees = get_employees()
    defects = get_defects()

    total = len(batches)
    completed = sum(1 for b in batches if b["Статус"] == BATCH_COMPLETED)
    in_progress = sum(1 for b in batches if b["Статус"] == BATCH_IN_PROGRESS)
    awaiting = sum(1 for b in batches if b["Статус"] == BATCH_AWAITING)

    # Статистика по этапам
    stage_stats = {}
    for p in pipeline:
        stage_stats[p["name"]] = {"total": 0, "in_progress": 0, "awaiting": 0}

    for batch in batches:
        if batch["Статус"] == BATCH_COMPLETED:
            continue
        current_id = batch["Текущий этап (ID)"]
        for p in pipeline:
            if p["id"] == current_id:
                stage_stats[p["name"]]["total"] += 1
                if batch["Статус"] == BATCH_IN_PROGRESS:
                    stage_stats[p["name"]]["in_progress"] += 1
                if batch["Статус"] == BATCH_AWAITING:
                    stage_stats[p["name"]]["awaiting"] += 1

    active_workers = sum(1 for b in batches if b["Статус"] == BATCH_IN_PROGRESS and b.get("Назначен на (ID сотрудника)"))
    total_workers = sum(1 for e in employees if e["Роль"] in ("сотрудник", "технолог"))
    pending_defects = sum(1 for d in defects if d["Статус"] == DEFECT_PENDING)

    msg = "📊 **Дэшборд производства**\n\n"
    msg += f"**📦 Партии:**\n"
    msg += f"• Всего: {total}\n"
    msg += f"• ✅ Завершено: {completed}\n"
    msg += f"• 🔄 В работе: {in_progress}\n"
    msg += f"• ⏳ Ожидают: {awaiting}\n\n"

    msg += f"**🏭 Этапы:**\n"
    for stage, stats in stage_stats.items():
        if stats["total"] > 0:
            msg += f"• {stage}: {stats['in_progress']}🔄 / {stats['awaiting']}⏳\n"

    msg += f"\n**👷 Сотрудники:**\n"
    msg += f"• Всего: {len(employees)}\n"
    msg += f"• Занято: {active_workers}\n"
    msg += f"• Свободно: {total_workers - active_workers}\n\n"

    msg += f"**📸 Брак:**\n"
    msg += f"• Ожидает проверки: {pending_defects}"

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_keyboard(ROLE_BOSS))


async def cmd_all_batches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📋 Все партии."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee or employee["Роль"] != ROLE_BOSS:
        return await update.message.reply_text("❌ Нет доступа.")

    batches = get_batches()
    if not batches:
        return await update.message.reply_text(
            "📭 Нет партий. Нажмите /newbatch чтобы создать.",
            reply_markup=get_main_keyboard(ROLE_BOSS),
        )

    pipeline = get_pipeline()
    status_map = {
        BATCH_AWAITING: "⏳ Ожидает",
        BATCH_IN_PROGRESS: "🔄 В работе",
        BATCH_COMPLETED: "✅ Завершена",
    }

    msg = "📋 **Все партии:**\n\n"
    for b in batches:
        process = next((p for p in pipeline if p["id"] == b["Текущий этап (ID)"]), None)
        msg += f"📦 **Партия #{b['ID партии']}**\n"
        msg += f"   Статус: {status_map.get(b['Статус'], b['Статус'])}\n"
        msg += f"   Этап: {process['name'] if process else '?'}\n"
        if b.get("Завершена"):
            msg += f"   Завершена: {b['Завершена']}\n"
        msg += "\n"

    msg += "➕ /newbatch — создать новую партию"
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_keyboard(ROLE_BOSS))


async def cmd_new_batch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """➕ Создать новую партию."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee or employee["Роль"] != ROLE_BOSS:
        return await update.message.reply_text("❌ Только начальник может создавать партии.")

    pipeline = get_pipeline()
    if not pipeline:
        return await update.message.reply_text("❌ Конвейер не настроен. Заполните файл конвейер_настройки.xlsx")

    first_process = pipeline[0]
    batch_id = add_batch(f"Партия #{len(get_batches()) + 1}", first_process["id"])

    await update.message.reply_text(
        f"✅ **Создана новая партия!**\n\n"
        f"📦 Партия #{batch_id}\n"
        f"📍 Текущий этап: **{first_process['name']}**\n"
        f"👷 Ответственный: {first_process['role']}\n"
        f"⏱ Норма: {first_process['norm_minutes']} мин\n\n"
        f"Сотрудник с ролью \"{first_process['role']}\" может начать работу.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(ROLE_BOSS),
    )


async def cmd_employees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """👥 Список сотрудников."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee or employee["Роль"] != ROLE_BOSS:
        return await update.message.reply_text("❌ Нет доступа.")

    employees = get_employees()
    msg = "👥 **Сотрудники:**\n\n"
    for e in employees:
        msg += f"• @{e['Username']} — {e['Имя']}\n"
        msg += f"  Роль: {ROLES_RU.get(e['Роль'], e['Роль'])}\n\n"

    msg += "📌 /setrole @username роль — назначить роль"
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_keyboard(ROLE_BOSS))


async def cmd_setrole(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """👑 Назначить роль сотруднику."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee or employee["Роль"] != ROLE_BOSS:
        return await update.message.reply_text("❌ Только начальник может назначать роли.")

    args = context.args
    if len(args) < 2:
        return await update.message.reply_text(
            "📌 Использование: /setrole @username роль\n\n"
            "Доступные роли: начальник, технолог, табельщик, бухгалтер, сотрудник"
        )

    target_username = args[0].replace("@", "")
    role_name = " ".join(args[1:]).lower()

    role_map = {
        "начальник": "начальник",
        "технолог": "технолог",
        "табельщик": "табельщик",
        "бухгалтер": "бухгалтер",
        "сотрудник": "сотрудник",
    }

    new_role = role_map.get(role_name)
    if not new_role:
        return await update.message.reply_text("❌ Неизвестная роль. Доступны: начальник, технолог, табельщик, бухгалтер, сотрудник")

    target = find_employee_by_user_id(None)  # заглушка
    employees = get_employees()
    target = None
    for e in employees:
        if e["Username"] == target_username:
            target = e
            break

    if not target:
        return await update.message.reply_text(f"❌ Пользователь @{target_username} не найден. Сначала он должен написать /start боту.")

    update_employee_role(target["Telegram ID"], new_role)
    await update.message.reply_text(f"✅ @{target_username} теперь {ROLES_RU.get(new_role, new_role)}")


async def cmd_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💰 Отчёты."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee or employee["Роль"] != ROLE_BOSS:
        return await update.message.reply_text("❌ Нет доступа.")

    timesheets = get_timesheets()
    total_hours = sum(t["Часы"] for t in timesheets)
    defects = get_defects()
    approved = sum(1 for d in defects if d["Статус"] == "принят")

    msg = "💰 **Отчёты**\n\n"
    msg += f"⏱ Всего часов отработано: {total_hours}\n"
    msg += f"📸 Зафиксировано брака: {len(defects)}\n"
    msg += f"✅ Подтверждено брака: {approved}\n"
    msg += f"📄 Записей в табеле: {len(timesheets)}"

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_keyboard(ROLE_BOSS))


async def cmd_tabel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⏱ Табель учёта времени."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee or employee["Роль"] != ROLE_BOSS:
        return await update.message.reply_text("❌ Нет доступа.")

    timesheets = get_timesheets()
    if not timesheets:
        return await update.message.reply_text("📭 Нет записей.", reply_markup=get_main_keyboard(ROLE_BOSS))

    by_employee = {}
    for t in timesheets:
        name = t["Имя"]
        by_employee[name] = by_employee.get(name, 0) + t["Часы"]

    msg = "⏱ **Табель учёта времени**\n\n"
    for name, hours in by_employee.items():
        msg += f"• {name}: {hours} ч.\n"

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_keyboard(ROLE_BOSS))