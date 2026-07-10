const { Telegraf, Markup } = require('telegraf');
const fs = require('fs');
const path = require('path');

// ============================================================
// КОНФИГУРАЦИЯ
// ============================================================

const DATA_DIR = path.join(__dirname, 'data');
const PIPELINE_PATH = path.join(__dirname, 'config', 'pipeline.json');

// Файлы данных
const DB = {
  employees: path.join(DATA_DIR, 'employees.json'),
  batches: path.join(DATA_DIR, 'batches.json'),
  defects: path.join(DATA_DIR, 'defects.json'),
  timesheets: path.join(DATA_DIR, 'timesheets.json'),
};

// Роли
const ROLES = {
  BOSS: 'начал��ник',
  TECHNOLOGIST: 'технолог',
  TIMEKEEPER: 'табельщик',
  ACCOUNTANT: 'бухгалтер',
  WORKER: 'сотрудник',
};

const ROLE_RU = {
  [ROLES.BOSS]: '👑 Начальник',
  [ROLES.TECHNOLOGIST]: '🔧 Технолог',
  [ROLES.TIMEKEEPER]: '⏱ Табельщик',
  [ROLES.ACCOUNTANT]: '💰 Бухгалтер',
  [ROLES.WORKER]: '👷 Сотрудник',
};

// ============================================================
// УТИЛИТЫ ДЛЯ РАБОТЫ С JSON-БАЗОЙ
// ============================================================

function readJSON(filePath) {
  try {
    if (!fs.existsSync(filePath)) return [];
    const data = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(data);
  } catch {
    return [];
  }
}

function writeJSON(filePath, data) {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
}

function getEmployees() { return readJSON(DB.employees); }
function saveEmployees(data) { writeJSON(DB.employees, data); }

function getBatches() { return readJSON(DB.batches); }
function saveBatches(data) { writeJSON(DB.batches, data); }

function getDefects() { return readJSON(DB.defects); }
function saveDefects(data) { writeJSON(DB.defects, data); }

function getTimesheets() { return readJSON(DB.timesheets); }
function saveTimesheets(data) { writeJSON(DB.timesheets, data); }

function getPipeline() {
  try {
    return JSON.parse(fs.readFileSync(PIPELINE_PATH, 'utf8'));
  } catch {
    return { processes: [] };
  }
}

// ============================================================
// ПОИСК СОТРУДНИКА
// ============================================================

function findEmployee(userId) {
  return getEmployees().find(e => e.userId === userId);
}

function findEmployeeByUsername(username) {
  return getEmployees().find(e => e.username === username.replace('@', ''));
}

// ============================================================
// ИНИЦИАЛИЗАЦИЯ БОТА
// ============================================================

const bot = new Telegraf(process.env.BOT_TOKEN);

// ============================================================
// КЛАВИАТУРЫ
// ============================================================

function mainMenu(role) {
  const buttons = [];
  
  switch (role) {
    case ROLES.BOSS:
      buttons.push(
        ['📊 Дэшборд'],
        ['📋 Все партии', '📸 Брак (все)'],
        ['👥 Сотрудники', '⏱ Табель'],
        ['💰 Отчёты']
      );
      break;
    case ROLES.TECHNOLOGIST:
      buttons.push(
        ['📋 Мои партии'],
        ['📸 Брак (проверка)'],
        ['✅ Готово']
      );
      break;
    case ROLES.TIMEKEEPER:
      buttons.push(
        ['⏱ Записать часы'],
        ['📊 Отчёт по часам']
      );
      break;
    case ROLES.ACCOUNTANT:
      buttons.push(
        ['📤 Загрузить ведомость'],
        ['💰 Моя зарплата']
      );
      break;
    case ROLES.WORKER:
      buttons.push(
        ['📋 Мои задачи'],
        ['📸 Сообщить о браке'],
        ['💰 Моя зарплата']
      );
      break;
  }
  
  return Markup.keyboard(buttons).resize();
}

function cancelKeyboard() {
  return Markup.keyboard(['❌ Отмена']).resize();
}

// ============================================================
// РЕГИСТРАЦИЯ И СТАРТ
// ============================================================

bot.start(async (ctx) => {
  const userId = ctx.from.id;
  const username = ctx.from.username || `user${userId}`;
  const fullName = `${ctx.from.first_name || ''} ${ctx.from.last_name || ''}`.trim() || username;
  
  let employee = findEmployee(userId);
  
  if (!employee) {
    // Авторегистрация как сотрудник
    const employees = getEmployees();
    
    // Первый регистрирующийся становится начальником
    const role = employees.length === 0 ? ROLES.BOSS : ROLES.WORKER;
    
    employee = {
      userId,
      username,
      fullName,
      role,
      registeredAt: new Date().toISOString(),
    };
    
    employees.push(employee);
    saveEmployees(employees);
    
    if (role === ROLES.BOSS) {
      await ctx.reply(
        `👋 Добро пожаловать, ${fullName}!\n\n` +
        `Вы зарегистрированы как **${ROLE_RU[role]}** (первый пользователь).\n\n` +
        `📌 **Ваши возможности:**\n` +
        `• 📊 Дэшборд производства\n` +
        `• 📋 Управление партиями\n` +
        `• 👥 Управление сотрудниками\n` +
        `• 📸 Контроль брака\n\n` +
        `Используйте /help для справки.`,
        { parse_mode: 'Markdown', ...mainMenu(role) }
      );
    } else {
      await ctx.reply(
        `👋 Добро пожаловать, ${fullName}!\n\n` +
        `Вы зарегистрированы как **${ROLE_RU[role]}**.\n` +
        `В��ш руководитель назначит вам роль и задачи.\n\n` +
        `Пока вы можете:\n` +
        `• 📋 Смотреть свои задачи\n` +
        `• 💰 Смотреть зарплату`,
        { parse_mode: 'Markdown', ...mainMenu(role) }
      );
    }
  } else {
    await ctx.reply(
      `👋 С возвращением, ${employee.fullName}!\n` +
      `Ваша роль: **${ROLE_RU[employee.role]}**`,
      { parse_mode: 'Markdown', ...mainMenu(employee.role) }
    );
  }
});

// ============================================================
// HELP
// ============================================================

bot.help(async (ctx) => {
  const employee = findEmployee(ctx.from.id);
  const role = employee ? employee.role : ROLES.WORKER;
  
  let helpText = '📖 **Справка по MES V2**\n\n';
  
  helpText += '**Основные команды:**\n';
  helpText += '• /start — Главное меню\n';
  helpText += '• /help — Эта справка\n\n';
  
  if (role === ROLES.BOSS) {
    helpText += '**👑 Начальник:**\n';
    helpText += '• 📊 Дэшборд — состояние производства\n';
    helpText += '• 📋 Все партии — управление партиями\n';
    helpText += '• 👥 Сотрудники — назначение ролей\n';
    helpText += '• 📸 Брак — просмотр всех дефектов\n';
    helpText += '• ⏱ Табель — учёт рабочего времени\n';
    helpText += '• /setrole @username роль — назначить роль\n\n';
  }
  
  if (role === ROLES.TECHNOLOGIST) {
    helpText += '**🔧 Технолог:**\n';
    helpText += '• 📋 Мои партии — доступные партии\n';
    helpText += '• 📸 Брак (проверка) — просмотр брака\n';
    helpText += '• ✅ Готово — завершить этап\n\n';
  }
  
  if (role === ROLES.TIMEKEEPER) {
    helpText += '**⏱ Табельщик:**\n';
    helpText += '• ⏱ Записать часы — внести часы сотруднику\n';
    helpText += '• 📊 Отчёт по часам — сводка\n\n';
  }
  
  if (role === ROLES.WORKER || role === ROLES.ACCOUNTANT) {
    helpText += '**👷 Сотрудник:**\n';
    helpText += '• 📋 Мои задачи — текущие задачи\n';
    helpText += '• 📸 Сообщить о браке — фото дефекта\n';
    helpText += '• 💰 Моя зарплата — личная ведомость\n\n';
  }
  
  helpText += '💡 **Принцип работы:**\n';
  helpText += 'Партия проходит этапы по цепочке. Вы видите только свои задачи.\n';
  helpText += 'Брак фиксируется фото. Зарплата — только личная.';
  
  await ctx.reply(helpText, { parse_mode: 'Markdown', ...mainMenu(role) });
});

// ============================================================
// НАЗНАЧЕНИЕ РОЛЕЙ (только для начальника)
// ============================================================

bot.command('setrole', async (ctx) => {
  const boss = findEmployee(ctx.from.id);
  if (!boss || boss.role !== ROLES.BOSS) {
    return ctx.reply('❌ Только начальник может назначать роли.');
  }
  
  const args = ctx.message.text.split(' ');
  if (args.length < 3) {
    return ctx.reply(
      '📌 Использование: /setrole @username роль\n\n' +
      'Доступные роли: начальник, технолог, табельщик, бухгалтер, сотрудник'
    );
  }
  
  const targetUsername = args[1].replace('@', '');
  const roleName = args.slice(2).join(' ').toLowerCase();
  
  const roleMap = {
    'начальник': ROLES.BOSS,
    'технолог': ROLES.TECHNOLOGIST,
    'табельщик': ROLES.TIMEKEEPER,
    'бухгалтер': ROLES.ACCOUNTANT,
    'сотрудник': ROLES.WORKER,
  };
  
  const newRole = roleMap[roleName];
  if (!newRole) {
    return ctx.reply('❌ Неизвестная роль. Доступны: начальник, технолог, табельщик, бухгалтер, сотрудник');
  }
  
  const employees = getEmployees();
  const target = employees.find(e => e.username === targetUsername);
  
  if (!target) {
    return ctx.reply(`❌ Пользователь @${targetUsername} не найден. Сначала он должен написать /start боту.`);
  }
  
  target.role = newRole;
  saveEmployees(employees);
  
  await ctx.reply(`✅ @${targetUsername} теперь ${ROLE_RU[newRole]}`);
});

// ============================================================
// СОЗДАНИЕ НОВОЙ ПАРТИИ (начальник)
// ============================================================

async function createBatch(ctx) {
  const pipeline = getPipeline();
  if (!pipeline.processes.length) {
    return ctx.reply('❌ Конвейер не настроен. Добавьте процессы в config/pipeline.json');
  }
  
  const batches = getBatches();
  const batchId = batches.length + 1;
  const firstProcess = pipeline.processes[0];
  
  const batch = {
    id: batchId,
    name: `Партия #${batchId}`,
    createdAt: new Date().toISOString(),
    currentProcessId: firstProcess.id,
    status: 'awaiting_start', // awaiting_start | in_progress | completed | defect
    history: [],
    assignedTo: null,
  };
  
  batches.push(batch);
  saveBatches(batches);
  
  await ctx.reply(
    `✅ **Создана новая партия!**\n\n` +
    `📦 Партия #${batchId}\n` +
    `📍 Текущий этап: **${firstProcess.name}**\n` +
    `👷 Ответственный: ${firstProcess.role}\n` +
    `⏱ Норма: ${firstProcess.normMinutes} мин\n\n` +
    `Сотрудник с ролью "${firstProcess.role}" может начать работу через кнопку "📋 Мои задачи".`,
    { parse_mode: 'Markdown', ...mainMenu(ROLES.BOSS) }
  );
}

// ============================================================
// НАЧАТЬ ЭТАП (сотрудник/технолог)
// ============================================================

async function startProcess(ctx, batchId) {
  const employee = findEmployee(ctx.from.id);
  if (!employee) return ctx.reply('❌ Сначала напишите /start');
  
  const batches = getBatches();
  const batch = batches.find(b => b.id === batchId);
  
  if (!batch) return ctx.reply('❌ Партия не найдена.');
  if (batch.status === 'completed') return ctx.reply('✅ Партия уже завершена.');
  
  const pipeline = getPipeline();
  const process = pipeline.processes.find(p => p.id === batch.currentProcessId);
  
  if (!process) return ctx.reply('❌ Этап не найден в конфигурации.');
  if (process.role !== employee.role) {
    return ctx.reply(`❌ Этот этап назначает ${process.role}. Ваша роль: ${ROLE_RU[employee.role]}`);
  }
  
  if (batch.assignedTo && batch.assignedTo !== employee.userId) {
    return ctx.reply('❌ Над этой партией уже работает другой сотрудник.');
  }
  
  batch.status = 'in_progress';
  batch.assignedTo = employee.userId;
  batch.startedAt = new Date().toISOString();
  
  batch.history.push({
    processId: process.id,
    processName: process.name,
    startedBy: employee.fullName,
    startedAt: batch.startedAt,
    status: 'in_progress',
  });
  
  saveBatches(batches);
  
  await ctx.reply(
    `✅ **Вы начали этап:** ${process.name}\n` +
    `📦 Партия #${batch.id}\n` +
    `⏱ Норма времени: ${process.normMinutes} мин\n\n` +
    `Когда закончите — нажмите "✅ Готово"`,
    { parse_mode: 'Markdown', ...mainMenu(employee.role) }
  );
}

// ============================================================
// ЗАВЕРШИТЬ ЭТАП
// ============================================================

async function completeProcess(ctx, batchId) {
  const employee = findEmployee(ctx.from.id);
  if (!employee) return ctx.reply('❌ Сначала напишите /start');
  
  const batches = getBatches();
  const batch = batches.find(b => b.id === batchId);
  
  if (!batch) return ctx.reply('❌ Партия не найдена.');
  if (batch.status !== 'in_progress') return ctx.reply('❌ Этап ещё не начат или уже завершён.');
  if (batch.assignedTo !== employee.userId) return ctx.reply('❌ Вы не работаете над этой партией.');
  
  const pipeline = getPipeline();
  const currentProcess = pipeline.processes.find(p => p.id === batch.currentProcessId);
  
  // Обновляем историю
  const historyEntry = batch.history.find(h => h.processId === batch.currentProcessId && h.status === 'in_progress');
  if (historyEntry) {
    historyEntry.status = 'completed';
    historyEntry.completedAt = new Date().toISOString();
  }
  
  // Ищем следующий этап
  const currentIndex = pipeline.processes.findIndex(p => p.id === batch.currentProcessId);
  const nextProcess = pipeline.processes[currentIndex + 1];
  
  if (nextProcess) {
    // Переходим к следующему этапу
    batch.currentProcessId = nextProcess.id;
    batch.status = 'awaiting_start';
    batch.assignedTo = null;
    batch.startedAt = null;
    
    saveBatches(batches);
    
    await ctx.reply(
      `✅ **Этап "${currentProcess.name}" завершён!**\n\n` +
      `📦 Партия #${batch.id} → **${nextProcess.name}**\n` +
      `👷 Ожидает: ${nextProcess.role}`,
      { parse_mode: 'Markdown', ...mainMenu(employee.role) }
    );
    
    // Уведомляем следующего сотрудника (если есть)
    const nextRoleEmployees = getEmployees().filter(e => e.role === nextProcess.role);
    // В YC Functions нет возможности отправлять сообщения без запроса,
    // поэтому просто пишем в ответ
    if (nextRoleEmployees.length > 0) {
      await ctx.reply(
        `📢 **Уведомление:** Партия #${batch.id} ожидает этап "${nextProcess.name}".\n` +
        `Сотрудники с ролью "${nextProcess.role}" могут начать через "📋 Мои задачи".`
      );
    }
  } else {
    // Партия полностью завершена
    batch.status = 'completed';
    batch.assignedTo = null;
    batch.completedAt = new Date().toISOString();
    
    saveBatches(batches);
    
    await ctx.reply(
      `🎉 **Партия #${batch.id} полностью завершена!**\n\n` +
      `Все этапы пройдены.`,
      { parse_mode: 'Markdown', ...mainMenu(employee.role) }
    );
  }
}

// ============================================================
// ПОКАЗАТЬ ЗАДАЧИ СОТРУДНИКА
// ============================================================

async function showMyTasks(ctx) {
  const employee = findEmployee(ctx.from.id);
  if (!employee) return ctx.reply('❌ Сначала напишите /start');
  
  const pipeline = getPipeline();
  const batches = getBatches();
  
  // Задачи, доступные для этого сотрудника
  const availableBatches = batches.filter(b => {
    if (b.status === 'completed') return false;
    const process = pipeline.processes.find(p => p.id === b.currentProcessId);
    return process && process.role === employee.role;
  });
  
  if (availableBatches.length === 0) {
    return ctx.reply('📭 Нет доступных задач.', mainMenu(employee.role));
  }
  
  let message = '📋 **Ваши задачи:**\n\n';
  
  for (const batch of availableBatches) {
    const process = pipeline.processes.find(p => p.id === batch.currentProcessId);
    const statusEmoji = batch.status === 'in_progress' ? '🔄' : '⏳';
    const statusText = batch.status === 'in_progress' ? 'В работе' : 'Ожидает';
    
    message += `${statusEmoji} **Партия #${batch.id}**\n`;
    message += `   Этап: ${process ? process.name : '?'}\n`;
    message += `   Статус: ${statusText}\n`;
    message += `   /start_${batch.id} — начать\n`;
    message += `   /done_${batch.id} — завершить\n\n`;
  }
  
  await ctx.reply(message, { parse_mode: 'Markdown', ...mainMenu(employee.role) });
}

// ============================================================
// БРАК — СООБЩИТЬ
// ============================================================

async function reportDefect(ctx) {
  const employee = findEmployee(ctx.from.id);
  if (!employee) return ctx.reply('❌ Сначала напишите /start');
  
  const batches = getBatches().filter(b => 
    b.assignedTo === employee.userId && b.status === 'in_progress'
  );
  
  if (batches.length === 0) {
    return ctx.reply('❌ У вас нет активных партий для сообщения о браке.', mainMenu(employee.role));
  }
  
  // ��охраняем состояние — ждём фото
  const userState = getUserState(ctx.from.id);
  userState.awaitingDefectPhoto = true;
  saveUserState(ctx.from.id, userState);
  
  const batchList = batches.map(b => `• Партия #${b.id}`).join('\n');
  
  await ctx.reply(
    `📸 **Сообщение о браке**\n\n` +
    `Ваши активные партии:\n${batchList}\n\n` +
    `Отправьте фото дефекта. Бот автоматически привяжет его к вашей активной партии.`,
    { parse_mode: 'Markdown', ...cancelKeyboard() }
  );
}

// ============================================================
// БРАК — ПРОВЕРКА (технолог)
// ============================================================

async function showDefects(ctx) {
  const employee = findEmployee(ctx.from.id);
  if (!employee) return ctx.reply('❌ Сначала напишите /start');
  
  if (employee.role !== ROLES.TECHNOLOGIST && employee.role !== ROLES.BOSS) {
    return ctx.reply('❌ Только технолог и начальник могут просматривать брак.');
  }
  
  const defects = getDefects();
  const pendingDefects = defects.filter(d => d.status === 'pending');
  
  if (pendingDefects.length === 0) {
    return ctx.reply('✅ Нет необработанных дефектов.', mainMenu(employee.role));
  }
  
  let message = `📸 **Брак (${pendingDefects.length} шт.)**\n\n`;
  
  for (const defect of pendingDefects.slice(0, 10)) {
    const batch = getBatches().find(b => b.id === defect.batchId);
    message += `🔴 Дефект #${defect.id}\n`;
    message += `   📦 Партия #${defect.batchId}\n`;
    message += `   🔧 Этап: ${defect.processName}\n`;
    message += `   👷 Обнаружил: ${defect.reportedBy}\n`;
    message += `   🕐 ${new Date(defect.reportedAt).toLocaleString('ru-RU')}\n`;
    message += `   /defect_${defect.id}_approve — ✅ Принять\n`;
    message += `   /defect_${defect.id}_reject — ❌ Отклонить\n\n`;
  }
  
  await ctx.reply(message, { parse_mode: 'Markdown', ...mainMenu(employee.role) });
}

// ============================================================
// ЗАРПЛАТА — ПОКАЗАТЬ
// ============================================================

async function showMySalary(ctx) {
  const employee = findEmployee(ctx.from.id);
  if (!employee) return ctx.reply('❌ Сначала напишите /start');
  
  const timesheets = getTimesheets().filter(t => t.userId === employee.userId);
  
  if (timesheets.length === 0) {
    return ctx.reply(
      '💰 **Моя зарплата**\n\n' +
      'Пока нет данных. Обратитесь к табельщику или бухгалтеру.',
      { parse_mode: 'Markdown', ...mainMenu(employee.role) }
    );
  }
  
  // Группируем по месяцам
  const byMonth = {};
  for (const t of timesheets) {
    const monthKey = t.date.substring(0, 7); // YYYY-MM
    if (!byMonth[monthKey]) byMonth[monthKey] = { hours: 0, entries: 0 };
    byMonth[monthKey].hours += t.hours;
    byMonth[monthKey].entries += 1;
  }
  
  let message = '💰 **Моя зарплата**\n\n';
  
  for (const [month, data] of Object.entries(byMonth)) {
    const [year, mon] = month.split('-');
    const monthNames = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
    const monthName = monthNames[parseInt(mon)];
    
    message += `📅 **${monthName} ${year}**\n`;
    message += `   ⏱ Часов: ${data.hours}\n`;
    message += `   📄 Записей: ${data.entries}\n\n`;
  }
  
  message += '📌 Полный отчёт будет доступен после загрузки ведомости бухгалтером.';
  
  await ctx.reply(message, { parse_mode: 'Markdown', ...mainMenu(employee.role) });
}

// ============================================================
// ТАБЕЛЬ — ЗАПИСАТЬ ЧАСЫ
// ============================================================

async function recordHours(ctx) {
  const employee = findEmployee(ctx.from.id);
  if (!employee || employee.role !== ROLES.TIMEKEEPER) {
    return ctx.reply('❌ Только табельщик может записывать часы.');
  }
  
  const employees = getEmployees();
  const employeeList = employees.map(e => 
    `• @${e.username} — ${e.fullName} (${ROLE_RU[e.role]})`
  ).join('\n');
  
  await ctx.reply(
    `⏱ **Запись часов**\n\n` +
    `Формат: /hours @username ГГГГ-ММ-ДД часы\n\n` +
    `Пример: /hours @ivanov 2026-07-15 8\n\n` +
    `**Сотрудники:**\n${employeeList}`,
    { parse_mode: 'Markdown', ...mainMenu(employee.role) }
  );
}

bot.command('hours', async (ctx) => {
  const timekeeper = findEmployee(ctx.from.id);
  if (!timekeeper || timekeeper.role !== ROLES.TIMEKEEPER) {
    return ctx.reply('❌ Только табельщик может записывать часы.');
  }
  
  const args = ctx.message.text.split(' ');
  if (args.length < 4) {
    return ctx.reply('❌ Формат: /hours @username ГГГГ-ММ-ДД часы');
  }
  
  const targetUsername = args[1].replace('@', '');
  const date = args[2];
  const hours = parseFloat(args[3]);
  
  if (isNaN(hours) || hours <= 0 || hours > 24) {
    return ctx.reply('❌ Некорректное количество часов (1-24).');
  }
  
  const target = findEmployeeByUsername(targetUsername);
  if (!target) {
    return ctx.reply(`❌ Сотрудник @${targetUsername} не найден.`);
  }
  
  const timesheets = getTimesheets();
  timesheets.push({
    id: timesheets.length + 1,
    userId: target.userId,
    username: target.username,
    fullName: target.fullName,
    date,
    hours,
    recordedBy: timekeeper.fullName,
    recordedAt: new Date().toISOString(),
  });
  saveTimesheets(timesheets);
  
  await ctx.reply(
    `✅ **Часы записаны!**\n\n` +
    `👷 ${target.fullName}\n` +
    `📅 ${date}\n` +
    `⏱ ${hours} ч.\n` +
    `✍️ Записал: ${timekeeper.fullName}`,
    { parse_mode: 'Markdown', ...mainMenu(timekeeper.role) }
  );
});

// ============================================================
// ДЭШБОРД (начальник)
// ============================================================

async function showDashboard(ctx) {
  const employee = findEmployee(ctx.from.id);
  if (!employee || employee.role !== ROLES.BOSS) {
    return ctx.reply('❌ Только начальник может просматривать дэшборд.');
  }
  
  const pipeline = getPipeline();
  const batches = getBatches();
  const employees = getEmployees();
  const defects = getDefects();
  
  // Статистика по партиям
  const totalBatches = batches.length;
  const completedBatches = batches.filter(b => b.status === 'completed').length;
  const inProgress = batches.filter(b => b.status === 'in_progress').length;
  const awaiting = batches.filter(b => b.status === 'awaiting_start').length;
  
  // Текущие этапы
  const stageStats = {};
  for (const p of pipeline.processes) {
    stageStats[p.name] = {
      total: 0,
      inProgress: 0,
      awaiting: 0,
    };
  }
  
  for (const batch of batches) {
    if (batch.status === 'completed') continue;
    const process = pipeline.processes.find(p => p.id === batch.currentProcessId);
    if (process && stageStats[process.name]) {
      stageStats[process.name].total++;
      if (batch.status === 'in_progress') stageStats[process.name].inProgress++;
      if (batch.status === 'awaiting_start') stageStats[process.name].awaiting++;
    }
  }
  
  // Загрузка сотрудников
  const activeWorkers = batches.filter(b => b.status === 'in_progress' && b.assignedTo).length;
  const totalWorkers = employees.filter(e => e.role === ROLES.WORKER || e.role === ROLES.TECHNOLOGIST).length;
  
  // Брак
  const pendingDefects = defects.filter(d => d.status === 'pending').length;
  
  let message = '📊 **Дэшборд производства**\n\n';
  
  message += `**📦 Партии:**\n`;
  message += `• Всего: ${totalBatches}\n`;
  message += `• ✅ Завершено: ${completedBatches}\n`;
  message += `• 🔄 В работе: ${inProgress}\n`;
  message += `• ⏳ Ожидают: ${awaiting}\n\n`;
  
  message += `**🏭 Этапы:**\n`;
  for (const [stageName, stats] of Object.entries(stageStats)) {
    if (stats.total > 0) {
      message += `• ${stageName}: ${stats.inProgress}🔄 / ${stats.awaiting}⏳\n`;
    }
  }
  
  message += `\n**👷 Сотрудники:**\n`;
  message += `• Всего: ${employees.length}\n`;
  message += `• Занято: ${activeWorkers}\n`;
  message += `• Свободно: ${totalWorkers - activeWorkers}\n\n`;
  
  message += `**📸 Брак:**\n`;
  message += `• Ожидает проверки: ${pendingDefects}\n`;
  
  await ctx.reply(message, { parse_mode: 'Markdown', ...mainMenu(employee.role) });
}

// ============================================================
// УПРАВ��ЕНИЕ СОСТОЯНИЕМ ПОЛЬЗОВАТЕЛЯ (in-memory для YC Functions)
// ============================================================

const userStates = {};

function getUserState(userId) {
  if (!userStates[userId]) {
    userStates[userId] = {};
  }
  return userStates[userId];
}

function saveUserState(userId, state) {
  userStates[userId] = state;
}

// ============================================================
// ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ
// ============================================================

bot.on('text', async (ctx) => {
  const employee = findEmployee(ctx.from.id);
  if (!employee) {
    return ctx.reply('👋 Напишите /start для регистрации.');
  }
  
  const text = ctx.message.text;
  const role = employee.role;
  
  // Обработка команд вида /start_N, /done_N, /defect_N_*
  if (text.startsWith('/start_')) {
    const batchId = parseInt(text.split('_')[1]);
    return startProcess(ctx, batchId);
  }
  
  if (text.startsWith('/done_')) {
    const batchId = parseInt(text.split('_')[1]);
    return completeProcess(ctx, batchId);
  }
  
  if (text.startsWith('/defect_')) {
    const parts = text.split('_');
    const defectId = parseInt(parts[1]);
    const action = parts[2]; // approve or reject
    
    const defects = getDefects();
    const defect = defects.find(d => d.id === defectId);
    
    if (!defect) return ctx.reply('❌ Дефект не найден.');
    
    if (action === 'approve') {
      defect.status = 'approved';
      defect.resolvedBy = employee.fullName;
      defect.resolvedAt = new Date().toISOString();
      saveDefects(defects);
      await ctx.reply(`✅ Дефект #${defectId} принят.`, mainMenu(role));
    } else if (action === 'reject') {
      defect.status = 'rejected';
      defect.resolvedBy = employee.fullName;
      defect.resolvedAt = new Date().toISOString();
      saveDefects(defects);
      await ctx.reply(`❌ Дефект #${defectId} отклонён.`, mainMenu(role));
    }
    return;
  }
  
  // Отмена
  if (text === '❌ Отмена') {
    const state = getUserState(ctx.from.id);
    state.awaitingDefectPhoto = false;
    saveUserState(ctx.from.id, state);
    return ctx.reply('❌ Действие отменено.', mainMenu(role));
  }
  
  // Меню
  switch (text) {
    // === НАЧАЛЬНИК ===
    case '📊 Дэшборд':
      return showDashboard(ctx);
      
    case '📋 Все партии': {
      if (role !== ROLES.BOSS) return ctx.reply('❌ Нет доступа.');
      const batches = getBatches();
      if (batches.length === 0) {
        return ctx.reply('📭 Нет партий. Создайте новую.', mainMenu(role));
      }
      let msg = '📋 **Все партии:**\n\n';
      for (const b of batches) {
        const pipeline = getPipeline();
        const process = pipeline.processes.find(p => p.id === b.currentProcessId);
        const statusMap = {
          'awaiting_start': '⏳ Ожидает',
          'in_progress': '🔄 В работе',
          'completed': '✅ Завершена',
          'defect': '🔴 Брак',
        };
        msg += `📦 **Партия #${b.id}**\n`;
        msg += `   Статус: ${statusMap[b.status] || b.status}\n`;
        msg += `   Этап: ${process ? process.name : '?'}\n`;
        if (b.completedAt) msg += `   Завершена: ${new Date(b.completedAt).toLocaleString('ru-RU')}\n`;
        msg += '\n';
      }
      msg += '➕ /newbatch — создать новую партию';
      return ctx.reply(msg, { parse_mode: 'Markdown', ...mainMenu(role) });
    }
      
    case '👥 Сотрудники': {
      if (role !== ROLES.BOSS) return ctx.reply('❌ Нет доступа.');
      const employees = getEmployees();
      let msg = '👥 **Сотрудники:**\n\n';
      for (const e of employees) {
        msg += `• @${e.username} — ${e.fullName}\n`;
        msg += `  Роль: ${ROLE_RU[e.role]}\n\n`;
      }
      msg += '📌 /setrole @username роль — назначить роль';
      return ctx.reply(msg, { parse_mode: 'Markdown', ...mainMenu(role) });
    }
      
    case '📸 Брак (все)':
    case '📸 Брак (проверка)':
      return showDefects(ctx);
      
    case '💰 Отчёты': {
      if (role !== ROLES.BOSS) return ctx.reply('❌ Нет доступа.');
      const timesheets = getTimesheets();
      const totalHours = timesheets.reduce((sum, t) => sum + t.hours, 0);
      const defects = getDefects();
      const approvedDefects = defects.filter(d => d.status === 'approved').length;
      
      let msg = '💰 **Отчёты**\n\n';
      msg += `⏱ Всего часов отработано: ${totalHours}\n`;
      msg += `📸 Зафиксировано брака: ${defects.length}\n`;
      msg += `✅ Подтверждено брака: ${approvedDefects}\n`;
      msg += `📄 Записей в табеле: ${timesheets.length}\n`;
      
      return ctx.reply(msg, { parse_mode: 'Markdown', ...mainMenu(role) });
    }
      
    case '⏱ Табель': {
      if (role !== ROLES.BOSS) return ctx.reply('❌ Нет доступа.');
      const timesheets = getTimesheets();
      if (timesheets.length === 0) return ctx.reply('📭 Нет записей.', mainMenu(role));
      
      // Группируем по сотрудникам
      const byEmployee = {};
      for (const t of timesheets) {
        if (!byEmployee[t.fullName]) byEmployee[t.fullName] = 0;
        byEmployee[t.fullName] += t.hours;
      }
      
      let msg = '⏱ **Табель учёта времени**\n\n';
      for (const [name, hours] of Object.entries(byEmployee)) {
        msg += `• ${name}: ${hours} ч.\n`;
      }
      
      return ctx.reply(msg, { parse_mode: 'Markdown', ...mainMenu(role) });
    }
      
    // === ТЕХНОЛОГ ===
    case '📋 Мои партии':
      return showMyTasks(ctx);
      
    case '✅ Готово': {
      if (role !== ROLES.TECHNOLOGIST && role !== ROLES.WORKER) {
        return ctx.reply('❌ Нет доступа.');
      }
      const activeBatches = getBatches().filter(b => 
        b.assignedTo === employee.userId && b.status === 'in_progress'
      );
      if (activeBatches.length === 0) {
        return ctx.reply('📭 Нет активных партий. Начните через "📋 Мои задачи".', mainMenu(role));
      }
      let msg = '✅ **Завершение этапа**\n\nВыберите партию:\n';
      for (const b of activeBatches) {
        msg += `• /done_${b.id} — Партия #${b.id}\n`;
      }
      return ctx.reply(msg, { parse_mode: 'Markdown', ...mainMenu(role) });
    }
      
    // === ТАБЕЛЬЩИК ===
    case '⏱ Записать часы':
      return recordHours(ctx);
      
    case '📊 Отчёт по часам': {
      if (role !== ROLES.TIMEKEEPER) return ctx.reply('❌ Нет доступа.');
      const timesheets = getTimesheets();
      if (timesheets.length === 0) return ctx.reply('📭 Нет записей.', mainMenu(role));
      
      let msg = '⏱ **Отчёт по часам**\n\n';
      const last10 = timesheets.slice(-10).reverse();
      for (const t of last10) {
        msg += `• ${t.fullName}: ${t.date} — ${t.hours} ч.\n`;
      }
      msg += `\n📄 Всего записей: ${timesheets.length}`;
      
      return ctx.reply(msg, { parse_mode: 'Markdown', ...mainMenu(role) });
    }
      
    // === СОТРУДНИК ===
    case '📋 Мои задачи':
      return showMyTasks(ctx);
      
    case '📸 Сообщить о браке':
      return reportDefect(ctx);
      
    case '💰 Моя зарплата':
      return showMySalary(ctx);
      
    case '📤 Загрузить ведомость': {
      if (role !== ROLES.ACCOUNTANT) return ctx.reply('❌ Только бухгалтер может загружать ведомости.');
      return ctx.reply(
        '📤 **Загрузка ведомости**\n\n' +
        'Функция загрузки зарплатных ведомостей будет доступна после подключения облачного хранилища.\n\n' +
        'Пока вы можете просмотреть свою зарплату через "💰 Моя зарплата".',
        { parse_mode: 'Markdown', ...mainMenu(role) }
      );
    }
      
    default:
      // Если пользователь ввёл /newbatch
      if (text === '/newbatch' && role === ROLES.BOSS) {
        return createBatch(ctx);
      }
      
      return ctx.reply(
        `❓ Неизвестная команда. Используйте /help для справки.`,
        mainMenu(role)
      );
  }
});

// ============================================================
// ОБРАБОТКА ФОТО (брак)
// ============================================================

bot.on('photo', async (ctx) => {
  const employee = findEmployee(ctx.from.id);
  if (!employee) return ctx.reply('❌ Сначала напишите /start.');
  
  const state = getUserState(ctx.from.id);
  
  if (!state.awaitingDefectPhoto) {
    return ctx.reply('📸 Чтобы сообщить о браке, нажмите "📸 Сообщить о браке" в меню.');
  }
  
  // Ищем активную партию сотрудника
  const batches = getBatches().filter(b => 
    b.assignedTo === employee.userId && b.status === 'in_progress'
  );
  
  if (batches.length === 0) {
    state.awaitingDefectPhoto = false;
    saveUserState(ctx.from.id, state);
    return ctx.reply('❌ У вас нет активных партий.', mainMenu(employee.role));
  }
  
  // Берём первую активную партию
  const batch = batches[0];
  const pipeline = getPipeline();
  const process = pipeline.processes.find(p => p.id === batch.currentProcessId);
  
  // Получаем file_id фото (самое большое разрешение)
  const photos = ctx.message.photo;
  const fileId = photos[photos.length - 1].file_id;
  
  // Сохраняем дефект
  const defects = getDefects();
  const defect = {
    id: defects.length + 1,
    batchId: batch.id,
    processId: process ? process.id : null,
    processName: process ? process.name : 'Неизвестно',
    reportedBy: employee.fullName,
    reportedByUserId: employee.userId,
    reportedAt: new Date().toISOString(),
    photoFileId: fileId,
    status: 'pending', // pending | approved | rejected
    resolvedBy: null,
    resolvedAt: null,
  };
  
  defects.push(defect);
  saveDefects(defects);
  
  // Сбрасываем состояние
  state.awaitingDefectPhoto = false;
  saveUserState(ctx.from.id, state);
  
  await ctx.reply(
    `✅ **Брак зафиксирован!**\n\n` +
    `📦 Партия #${batch.id}\n` +
    `🔧 Этап: ${process ? process.name : '?'}\n` +
    `🆔 Дефект #${defect.id}\n\n` +
    `Технолог проверит и вынесет решение.`,
    { parse_mode: 'Markdown', ...mainMenu(employee.role) }
  );
  
  // Отправляем фото технологам
  const technologists = getEmployees().filter(e => e.role === ROLES.TECHNOLOGIST);
  // В YC Functions нет возможности отправлять сообщения без запроса,
  // поэтому просто уведомляем отправителя
  if (technologists.length > 0) {
    await ctx.reply(
      `📢 **Уведомление:** Дефект #${defect.id} ожидает проверки технолога.\n` +
      `Технологи могут проверить через "📸 Брак (проверка)".`
    );
  }
});

// ============================================================
// ХЕНДЛЕР ДЛЯ YANDEX CLOUD FUNCTIONS
// ============================================================

let globalContext = null;

module.exports.handler = async function (event, context) {
  globalContext = context;
  
  const message = JSON.parse(event.body);
  await bot.handleUpdate(message);
  
  return {
    statusCode: 200,
    body: '',
  };
};