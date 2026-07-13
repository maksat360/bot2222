# handlers/worker.py — Команды сотрудника и технолога
# ====================================================

from telegram import Update
from telegram.ext import ContextTypes
from config import (
    ROLE_BOSS, ROLE_TECHNOLOGIST, ROLE_WORKER,
    BATCH_AWAITING, BATCH_IN_PROGRESS, BATCH_COMPLETED,
    DEFECT_PENDING, DEFECT_APPROVED, DEFECT_REJECTED,
)
from database import (
    find_employee_by_user_id, get_batches, get_pipeline,
    update_batch, get_defects, add_defect, update_defect,
    get_timesheets, get_salary_for_user,
)
from handlers.start import get_main_keyboard


# ============================================================
# ЗАДАЧИ СОТРУДНИКА
# ============================================================

async def cmd_my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📋 Мои задачи."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee:
        return await update.message.reply_text("❌ Сначала напишите /start")

    role = employee["Роль"]
    pipeline = get_pipeline()
    batches = get_batches()

    # Доступные партии для этой роли
    available = []
    for b in batches:
        if b["Статус"] == BATCH_COMPLETED:
            continue
        process = next((p for p in pipeline if p["id"] == b["Текущий этап (ID)"]), None)
        if process and process["role"] == role:
            available.append((b, process))

    if not available:
        return await update.message.reply_text(
            "📭 Нет доступных задач.",
            reply_markup=get_main_keyboard(role),
        )

    msg = "📋 **Ваши задачи:**\n\n"
    for batch, process in available:
        status_emoji = "🔄" if batch["Статус"] == BATCH_IN_PROGRESS else "⏳"
        status_text = "В работе" if batch["Статус"] == BATCH_IN_PROGRESS else "Ожидает"
        msg += f"{status_emoji} **Партия #{batch['ID партии']}**\n"
        msg += f"   Этап: {process['name']}\n"
        msg += f"   Статус: {status_text}\n"
        msg += f"   /start_{batch['ID партии']} — начать\n"
        msg += f"   /done_{batch['ID партии']} — завершить\n\n"

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_keyboard(role))


# ============================================================
# НАЧАТЬ ЭТАП
# ============================================================

async def cmd_start_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать этап (/start_N)."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee:
        return await update.message.reply_text("❌ Сначала напишите /start")

    # Извлекаем ID партии из команды
    text = update.message.text
    try:
        batch_id = int(text.split("_")[1])
    except (IndexError, ValueError):
        return await update.message.reply_text("❌ Неверный формат. Используйте /start_ID")

    batches = get_batches()
    batch = next((b for b in batches if b["ID партии"] == batch_id), None)
    if not batch:
        return await update.message.reply_text("❌ Партия не найдена.")
    if batch["Статус"] == BATCH_COMPLETED:
        return await update.message.reply_text("✅ Партия уже завершена.")

    pipeline = get_pipeline()
    process = next((p for p in pipeline if p["id"] == batch["Текущий этап (ID)"]), None)
    if not process:
        return await update.message.reply_text("❌ Этап не найден в конфигурации.")

    if process["role"] != employee["Роль"]:
        return await update.message.reply_text(
            f"❌ Этот этап назначает {process['role']}. Ваша роль: {employee['Роль']}"
        )

    if batch.get("Назначен на (ID сотрудника)") and batch["Назначен на (ID сотрудника)"] != user_id:
        return await update.message.reply_text("❌ Над этой партией уже работает другой сотрудник.")

    from datetime import datetime
    update_batch(batch_id, {
        "Статус": BATCH_IN_PROGRESS,
        "Назначен на (ID сотрудника)": user_id,
        "Начата": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })

    await update.message.reply_text(
        f"✅ **Вы начали этап:** {process['name']}\n"
        f"📦 Партия #{batch_id}\n"
        f"⏱ Норма времени: {process['norm_minutes']} мин\n\n"
        f"Когда закончите — нажмите /done_{batch_id}",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(employee["Роль"]),
    )


# ============================================================
# ЗАВЕРШИТЬ ЭТАП
# ============================================================

async def cmd_done_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершить этап (/done_N)."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee:
        return await update.message.reply_text("❌ Сначала напишите /start")

    text = update.message.text
    try:
        batch_id = int(text.split("_")[1])
    except (IndexError, ValueError):
        return await update.message.reply_text("❌ Неверный формат. Используйте /done_ID")

    batches = get_batches()
    batch = next((b for b in batches if b["ID партии"] == batch_id), None)
    if not batch:
        return await update.message.reply_text("❌ Партия не найдена.")
    if batch["Статус"] != BATCH_IN_PROGRESS:
        return await update.message.reply_text("❌ Этап ещё не начат или уже завершён.")
    if batch.get("Назначен на (ID сотрудника)") != user_id:
        return await update.message.reply_text("❌ Вы не работаете над этой партией.")

    pipeline = get_pipeline()
    current_process = next((p for p in pipeline if p["id"] == batch["Текущий этап (ID)"]), None)

    # Ищем следующий этап
    current_index = next((i for i, p in enumerate(pipeline) if p["id"] == batch["Текущий этап (ID)"]), -1)
    next_process = pipeline[current_index + 1] if current_index + 1 < len(pipeline) else None

    from datetime import datetime

    if next_process:
        # Переходим к следующему этапу
        update_batch(batch_id, {
            "Текущий этап (ID)": next_process["id"],
            "Статус": BATCH_AWAITING,
            "Назначен на (ID сотрудника)": "",
            "Начата": "",
        })

        await update.message.reply_text(
            f"✅ **Этап \"{current_process['name']}\" завершён!**\n\n"
            f"📦 Партия #{batch_id} → **{next_process['name']}**\n"
            f"👷 Ожидает: {next_process['role']}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(employee["Роль"]),
        )
    else:
        # Партия полностью завершена
        update_batch(batch_id, {
            "Статус": BATCH_COMPLETED,
            "Назначен на (ID сотрудника)": "",
            "Завершена": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

        await update.message.reply_text(
            f"🎉 **Партия #{batch_id} полностью завершена!**\n\n"
            f"Все этапы пройдены.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(employee["Роль"]),
        )


# ============================================================
# ГОТОВО (кнопка)
# ============================================================

async def cmd_ready(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """✅ Готово — показать активные партии для завершения."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee:
        return await update.message.reply_text("❌ Сначала напишите /start")

    batches = get_batches()
    active = [b for b in batches if b.get("Назначен на (ID сотрудника)") == user_id and b["Статус"] == BATCH_IN_PROGRESS]

    if not active:
        return await update.message.reply_text(
            "📭 Нет активных партий. Начните через \"📋 Мои задачи\".",
            reply_markup=get_main_keyboard(employee["Роль"]),
        )

    msg = "✅ **Завершение этапа**\n\nВыберите партию:\n"
    for b in active:
        msg += f"• /done_{b['ID партии']} — Партия #{b['ID партии']}\n"

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_keyboard(employee["Роль"]))


# ============================================================
# БРАК — СООБЩИТЬ
# ============================================================

async def cmd_report_defect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📸 Сообщить о браке."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee:
        return await update.message.reply_text("❌ Сначала напишите /start")

    batches = get_batches()
    active = [b for b in batches if b.get("Назначен на (ID сотрудника)") == user_id and b["Статус"] == BATCH_IN_PROGRESS]

    if not active:
        return await update.message.reply_text(
            "❌ У вас нет активных партий для сообщения о браке.",
            reply_markup=get_main_keyboard(employee["Роль"]),
        )

    # Сохраняем состояние — ждём фото
    context.user_data["awaiting_defect_photo"] = True

    batch_list = "\n".join([f"• Партия #{b['ID партии']}" for b in active])
    await update.message.reply_text(
        f"📸 **Сообщение о браке**\n\n"
        f"Ваши активные партии:\n{batch_list}\n\n"
        f"Отправьте фото дефекта. Бот автоматически привяжет его к вашей активной партии.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(employee["Роль"]),
    )


# ============================================================
# БРАК — ПРОВЕРКА (технолог/начальник)
# ============================================================

async def cmd_show_defects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📸 Просмотр брака."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee:
        return await update.message.reply_text("❌ Сначала напишите /start")

    if employee["Роль"] not in (ROLE_TECHNOLOGIST, ROLE_BOSS):
        return await update.message.reply_text("❌ Только технолог и начальник могут просматривать брак.")

    defects = get_defects()
    pending = [d for d in defects if d["Статус"] == DEFECT_PENDING]

    if not pending:
        return await update.message.reply_text(
            "✅ Нет необработанных дефектов.",
            reply_markup=get_main_keyboard(employee["Роль"]),
        )

    msg = f"📸 **Брак ({len(pending)} шт.)**\n\n"
    for d in pending[:10]:
        msg += f"🔴 Дефект #{d['ID']}\n"
        msg += f"   📦 Партия #{d['Партия ID']}\n"
        msg += f"   🔧 Этап: {d['Этап']}\n"
        msg += f"   👷 Обнаружил: {d['Сообщил']}\n"
        msg += f"   🕐 {d['Дата']}\n"
        msg += f"   /defect_{d['ID']}_approve — ✅ Принять\n"
        msg += f"   /defect_{d['ID']}_reject — ❌ Отклонить\n\n"

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_keyboard(employee["Роль"]))


# ============================================================
# БРАК — ОБРАБОТКА РЕШЕНИЯ
# ============================================================

async def cmd_defect_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка решения по дефекту (/defect_ID_approve|reject)."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee:
        return await update.message.reply_text("❌ Сначала напишите /start")

    if employee["Роль"] not in (ROLE_TECHNOLOGIST, ROLE_BOSS):
        return await update.message.reply_text("❌ Только технолог может обрабатывать брак.")

    text = update.message.text
    parts = text.split("_")
    if len(parts) < 3:
        return await update.message.reply_text("❌ Неверный формат.")

    try:
        defect_id = int(parts[1])
        action = parts[2]
    except (IndexError, ValueError):
        return await update.message.reply_text("❌ Неверный формат.")

    if action == "approve":
        update_defect(defect_id, DEFECT_APPROVED, employee["Имя"])
        await update.message.reply_text(f"✅ Дефект #{defect_id} принят.", reply_markup=get_main_keyboard(employee["Роль"]))
    elif action == "reject":
        update_defect(defect_id, DEFECT_REJECTED, employee["Имя"])
        await update.message.reply_text(f"❌ Дефект #{defect_id} отклонён.", reply_markup=get_main_keyboard(employee["Роль"]))
    else:
        await update.message.reply_text("❌ Неизвестное действие. Используйте approve или reject.")


# ============================================================
# ЗАРПЛАТА
# ============================================================

async def cmd_my_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """💰 Моя зарплата."""
    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee:
        return await update.message.reply_text("❌ Сначала напишите /start")

    salary = get_salary_for_user(user_id)

    if not salary:
        return await update.message.reply_text(
            "💰 **Моя зарплата**\n\n"
            "Пока нет данных. Обратитесь к табельщику или бухгалтеру.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(employee["Роль"]),
        )

    # Группируем по месяцам
    by_month = {}
    for s in salary:
        month_key = f"{s['Год']}-{s['Месяц']}"
        if month_key not in by_month:
            by_month[month_key] = {"hours": 0, "amount": 0}
        by_month[month_key]["hours"] += s.get("Отработано часов", 0) or 0
        by_month[month_key]["amount"] += s.get("Начислено", 0) or 0

    month_names = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
    }

    msg = "💰 **Моя зарплата**\n\n"
    for month_key, data in by_month.items():
        year, month_num = month_key.split("-")
        month_num = int(month_num)
        month_name = month_names.get(month_num, f"Месяц {month_num}")
        msg += f"📅 **{month_name} {year}**\n"
        msg += f"   ⏱ Часов: {data['hours']}\n"
        msg += f"   💵 Начислено: {data['amount']} сом\n\n"

    msg += "📌 Полный отчёт будет доступен после загрузки ведомости бухгалтером."

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_keyboard(employee["Роль"]))


# ============================================================
# ОБРАБОТКА ФОТО (БРАК)
# ============================================================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фото — фиксация брака."""
    if not context.user_data.get("awaiting_defect_photo"):
        return await update.message.reply_text(
            "📸 Чтобы сообщить о браке, нажмите \"📸 Сообщить о браке\" в меню."
        )

    user_id = str(update.effective_user.id)
    employee = find_employee_by_user_id(user_id)
    if not employee:
        return await update.message.reply_text("❌ Сначала напишите /start")

    batches = get_batches()
    active = [b for b in batches if b.get("Назначен на (ID сотрудника)") == user_id and b["Статус"] == BATCH_IN_PROGRESS]

    if not active:
        context.user_data["awaiting_defect_photo"] = False
        return await update.message.reply_text(
            "❌ У вас нет активных партий.",
            reply_markup=get_main_keyboard(employee["Роль"]),
        )

    batch = active[0]
    pipeline = get_pipeline()
    process = next((p for p in pipeline if p["id"] == batch["Текущий этап (ID)"]), None)

    # Получаем file_id фото (самое большое разрешение)
    photo_file_id = update.message.photo[-1].file_id

    defect_id = add_defect(
        batch_id=batch["ID партии"],
        process_name=process["name"] if process else "Неизвестно",
        reported_by=employee["Имя"],
        reported_by_id=user_id,
        photo_file_id=photo_file_id,
    )

    context.user_data["awaiting_defect_photo"] = False

    await update.message.reply_text(
        f"✅ **Брак зафиксирован!**\n\n"
        f"📦 Партия #{batch['ID партии']}\n"
        f"🔧 Этап: {process['name'] if process else '?'}\n"
        f"🆔 Дефект #{defect_id}\n\n"
        f"Технолог проверит и вынесет решение.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(employee["Роль"]),
    )