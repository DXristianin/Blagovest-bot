"""
Конфигурация Telegram бота для LatePoint Integration

ВАЖНО: Этот файл является шаблоном!

Для использования:
1. Скопируйте этот файл: cp config.example.py config.py
2. Заполните реальными значениями в config.py
3. НЕ коммитьте config.py в Git!
"""

import os
from pathlib import Path

# ============================================================================
# БАЗОВЫЕ НАСТРОЙКИ
# ============================================================================

# Корневая директория проекта
BASE_DIR = Path(__file__).resolve().parent

# Режим работы: 'development' или 'production'
MODE = os.getenv('MODE', 'production')

# ============================================================================
# TELEGRAM BOT
# ============================================================================

# Токен Telegram бота (получите от @BotFather)
# Пример: '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# ID администраторов бота (через запятую)
ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',') if os.getenv('ADMIN_IDS') else []

# ============================================================================
# WORDPRESS API
# ============================================================================

# URL WordPress сайта с LatePoint
WP_SITE_URL = os.getenv('WP_SITE_URL', 'https://blagovest.net')

# API endpoint для интеграции с LatePoint
WP_API_URL = os.getenv(
    'WP_API_URL',
    f'{WP_SITE_URL}/wp-json/latepoint-telegram/v1'
)

# WordPress Nonce для аутентификации (опционально)
WP_NONCE = os.getenv('WP_NONCE', '')

# WordPress API Key (если используется)
WP_API_KEY = os.getenv('WP_API_KEY', '')

# ============================================================================
# WEBHOOK SECURITY
# ============================================================================

# Секретный ключ для вебхуков от WordPress
# Должен совпадать с настройками в WordPress плагине
# Сгенерируйте случайную строку: openssl rand -hex 32
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'YOUR_WEBHOOK_SECRET_HERE')

# ============================================================================
# DATABASE
# ============================================================================

# URL базы данных SQLite
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    f'sqlite+aiosqlite:///{BASE_DIR}/bot_data.db'
)

# Автоматическое создание таблиц при старте
AUTO_CREATE_TABLES = os.getenv('AUTO_CREATE_TABLES', 'true').lower() == 'true'

# ============================================================================
# WEB SERVER (для приёма вебхуков)
# ============================================================================

# Host для привязки сервера (0.0.0.0 = все интерфейсы)
HOST = os.getenv('HOST', '0.0.0.0')

# Port для веб-сервера
PORT = int(os.getenv('PORT', '8000'))

# Базовый URL бота для вебхуков (если используется Telegram webhook mode)
WEBHOOK_URL = os.getenv('WEBHOOK_URL', f'https://yourdomain.com/webhook/{BOT_TOKEN}')

# ============================================================================
# ЛОГИРОВАНИЕ
# ============================================================================

# Уровень логирования: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Путь к файлу логов
LOG_FILE = BASE_DIR / 'logs' / 'bot.log'

# Формат логов
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Максимальный размер файла логов (в байтах)
LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10 * 1024 * 1024))  # 10 MB

# Количество backup файлов логов
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))

# ============================================================================
# УВЕДОМЛЕНИЯ
# ============================================================================

# Время напоминаний перед событиями (в минутах)
REMINDER_TIMES = [
    60 * 24,  # За 24 часа
    60,       # За 1 час
    15,       # За 15 минут
]

# Интервал проверки предстоящих событий (в секундах)
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 60))

# ============================================================================
# ЛОКАЛИЗАЦИЯ
# ============================================================================

# Язык по умолчанию
DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'ru')

# Часовой пояс
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow')

# ============================================================================
# REDIS (опционально, для кеширования)
# ============================================================================

# Использовать Redis для кеширования
USE_REDIS = os.getenv('USE_REDIS', 'false').lower() == 'true'

# URL Redis сервера
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# ============================================================================
# RATE LIMITING
# ============================================================================

# Максимальное количество запросов в минуту на пользователя
RATE_LIMIT_PER_USER = int(os.getenv('RATE_LIMIT_PER_USER', 30))

# ============================================================================
# FEATURES FLAGS
# ============================================================================

# Включить автоматические напоминания
ENABLE_AUTO_REMINDERS = os.getenv('ENABLE_AUTO_REMINDERS', 'true').lower() == 'true'

# Включить веб-интерфейс для мониторинга
ENABLE_WEB_DASHBOARD = os.getenv('ENABLE_WEB_DASHBOARD', 'false').lower() == 'true'

# Включить режим отладки (подробные логи)
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# ============================================================================
# БЕЗОПАСНОСТЬ
# ============================================================================

# Разрешенные IP адреса для вебхуков (пустой список = все разрешены)
# Используйте для ограничения доступа к webhook endpoint
ALLOWED_IPS = os.getenv('ALLOWED_IPS', '').split(',') if os.getenv('ALLOWED_IPS') else []

# Таймаут для HTTP запросов к WordPress (в секундах)
HTTP_TIMEOUT = int(os.getenv('HTTP_TIMEOUT', 30))

# ============================================================================
# ПРОВЕРКА КОНФИГУРАЦИИ
# ============================================================================

def validate_config():
    """
    Проверяет, что все критические настройки заполнены
    Вызывается при старте бота
    """
    errors = []

    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        errors.append("BOT_TOKEN не установлен! Получите токен от @BotFather")

    if WEBHOOK_SECRET == 'YOUR_WEBHOOK_SECRET_HERE':
        errors.append("WEBHOOK_SECRET не установлен! Сгенерируйте случайную строку")

    if errors:
        print("\n" + "="*70)
        print("ОШИБКА КОНФИГУРАЦИИ!")
        print("="*70)
        for error in errors:
            print(f"  ❌ {error}")
        print("="*70)
        print("\nСкопируйте config.example.py в config.py и заполните настройки")
        print("="*70 + "\n")
        raise ValueError("Неверная конфигурация бота")

    return True


if __name__ == "__main__":
    # Тест конфигурации
    try:
        validate_config()
        print("✅ Конфигурация корректна")
    except ValueError as e:
        print(f"❌ {e}")
