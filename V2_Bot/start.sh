#!/bin/bash
# start.sh — Запуск Python-бота на macOS
# ========================================

echo "🚀 Запуск V2 Telegram-бота..."
echo ""

# 1. Проверяем существование виртуального окружения
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено."
    echo "   Сначала выполните: ./install.sh"
    exit 1
fi

# 2. Активируем виртуальное окружение
source venv/bin/activate

# 3. Проверяем, что токен не дефолтный
if grep -q "ВАШ_ТОКЕН_БОТА" config.py 2>/dev/null; then
    echo "❌ Ошибка: токен бота не настроен!"
    echo ""
    echo "📌 Отредактируйте файл config.py:"
    echo "   BOT_TOKEN = \"ваш_токен_сюда\""
    echo ""
    echo "📌 Или установите переменную окружения:"
    echo "   export BOT_TOKEN=\"ваш_токен_сюда\""
    exit 1
fi

# 4. Запускаем бота
echo "✅ Запуск main.py..."
python main.py

# 5. Обработка ошибок
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Бот завершился с ошибкой."
    echo ""
    echo "📌 Проверьте:"
    echo "   1. Токен бота в config.py"
    echo "   2. Установлены ли зависимости (./install.sh)"
    echo "   3. Интернет-соединение"
    exit 1
fi