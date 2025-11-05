#!/bin/bash

###############################################################################
# Скрипт для первоначального клонирования проекта LatePoint Telegram с сервера
#
# Использование: ./scripts/sync-from-server.sh
#
# Этот скрипт скачивает файлы с production сервера, исключая:
# - Конфигурационные файлы с токенами (config.py)
# - Базы данных (*.db)
# - Логи (logs/)
# - Кеш Python (__pycache__/, *.pyc)
###############################################################################

set -e  # Прервать выполнение при ошибке

SERVER="root@162.247.153.216"
BOT_PATH="/opt/blagovest-telegram-bot"
PLUGIN_PATH="/home/blagovest.net/public_html/wp-content/plugins/latepoint-telegram"

echo "🔄 Начинаю синхронизацию с production сервера..."
echo ""

# Проверка доступности сервера
if ! ssh -o ConnectTimeout=5 "$SERVER" "exit" 2>/dev/null; then
    echo "❌ Ошибка: Не удается подключиться к серверу $SERVER"
    echo "   Проверьте SSH ключ и доступ к серверу"
    exit 1
fi

# Скачать Python бота
echo "📦 Скачиваю Python Telegram бота..."
rsync -avz --progress \
    --exclude='config.py' \
    --exclude='*.db' \
    --exclude='bot_data.db' \
    --exclude='logs/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='*.pyd' \
    --exclude='.venv/' \
    --exclude='venv/' \
    --exclude='env/' \
    "$SERVER:$BOT_PATH/" ./bot/

echo ""
echo "🔌 Скачиваю WordPress плагин..."
rsync -avz --progress \
    --exclude='config.php' \
    --exclude='.DS_Store' \
    "$SERVER:$PLUGIN_PATH/" ./plugin/

echo ""
echo "✅ Синхронизация завершена успешно!"
echo ""
echo "📝 Следующие шаги:"
echo "   1. Создайте bot/config.py на основе bot/config.example.py"
echo "   2. Добавьте необходимые токены и настройки"
echo "   3. Закоммитьте изменения: git add . && git commit -m 'Initial commit'"
echo "   4. Настройте GitHub Secrets для CI/CD (см. SETUP_CICD.md)"
echo ""
