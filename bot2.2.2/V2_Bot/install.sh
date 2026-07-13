#!/bin/bash
# install.sh — Установка Python-бота на macOS
# =============================================

echo "🚀 Установка V2 Telegram-бота..."
echo ""

# 1. Проверяем Python 3.11+
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "✅ Python найден: $PYTHON_VERSION"

    # Извлекаем мажорную и минорную версию
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
        echo "❌ Требуется Python 3.11 или выше."
        echo "   Установите через: brew install python@3.11"
        exit 1
    fi
else
    echo "❌ Python не найден."
    echo "   Установите через: brew install python@3.11"
    exit 1
fi

# 2. Создаём виртуальное окружение
echo ""
echo "📦 Создание виртуального окружения..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Ошибка при создании виртуального окружения."
    exit 1
fi
echo "✅ Виртуальное окружение создано."

# 3. Активируем venv и устанавливаем зависимости
echo ""
echo "📚 Установка зависимостей..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Ошибка при установке зависимостей."
    exit 1
fi
echo "✅ Зависимости установлены."

# 4. Создаём необходимые папки
echo ""
echo "📁 Создание папок..."
mkdir -p data
mkdir -p cloud_storage/Временные
echo "✅ Папки созданы."

# 5. Завершение
echo ""
echo "========================================"
echo "✅ Установка завершена!"
echo ""
echo "📌 Вставьте токен в config.py:"
echo "   BOT_TOKEN = \"ваш_токен_сюда\""
echo ""
echo "📌 Или установите переменную окружения:"
echo "   export BOT_TOKEN=\"ваш_токен_сюда\""
echo ""
echo "🚀 Запустите бота:"
echo "   ./start.sh"
echo "========================================"