# LatePoint Telegram Integration

Интеграция между WordPress плагином LatePoint и Telegram ботом для автоматических уведомлений о бронированиях и управления расписанием.

## Описание проекта

Этот проект связывает систему онлайн-бронирования LatePoint (WordPress) с Telegram ботом, позволяя:

- Получать мгновенные уведомления о новых бронированиях в Telegram
- Напоминания клиентам о предстоящих встречах
- Управление бронированиями через Telegram интерфейс
- Двустороннюю синхронизацию данных между WordPress и Telegram

## Структура проекта

```
latepoint-telegram-integration/
├── bot/                          # Python Telegram бот
│   ├── bot.py                   # Главный файл бота
│   ├── config.example.py        # Шаблон конфигурации
│   ├── requirements.txt         # Python зависимости
│   ├── database/                # Модели и работа с БД
│   ├── handlers/                # Обработчики команд и событий
│   ├── services/                # Бизнес-логика
│   └── README.md
│
├── plugin/                       # WordPress плагин
│   ├── latepoint-telegram.php   # Главный файл плагина
│   ├── includes/                # PHP классы
│   ├── admin/                   # Админ интерфейс
│   └── README.md
│
├── .github/workflows/
│   └── deploy.yml               # GitHub Actions для автодеплоя
│
├── scripts/
│   └── sync-from-server.sh      # Скрипт первоначальной синхронизации
│
├── .gitignore
├── .env.example
├── SETUP_CICD.md               # Документация по настройке CI/CD
└── README.md                    # Этот файл
```

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone git@github.com:YOUR_USERNAME/latepoint-telegram-integration.git
cd latepoint-telegram-integration
```

### 2. Синхронизация файлов с production сервера

Если у вас уже есть работающий бот на сервере:

```bash
# Сделать скрипт исполняемым
chmod +x scripts/sync-from-server.sh

# Скачать файлы с сервера
./scripts/sync-from-server.sh
```

### 3. Настройка локального окружения

#### Для бота (Python):

```bash
cd bot

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Создать конфигурацию
cp config.example.py config.py
# Отредактировать config.py с вашими токенами
nano config.py

# Запустить бота локально
python bot.py
```

#### Для плагина (WordPress):

```bash
# Скопировать плагин в WordPress директорию
cp -r plugin/ /path/to/wordpress/wp-content/plugins/latepoint-telegram/

# Активировать плагин через WordPress админку
# Настроить параметры в Settings → LatePoint Telegram
```

## Автоматический деплой

Проект использует GitHub Actions для автоматического деплоя при push в ветку `main`.

### Настройка CI/CD

Подробная инструкция по настройке автоматического деплоя находится в [SETUP_CICD.md](SETUP_CICD.md).

**Кратко:**
1. Создать SSH ключи
2. Добавить GitHub Secrets (VPS_HOST, VPS_USERNAME, VPS_SSH_KEY)
3. Push в main → автоматический деплой

### Workflow разработки

```bash
# 1. Редактировать файлы локально
code bot/handlers/commands.py

# 2. Тестировать изменения
python bot/bot.py

# 3. Коммит и push
git add .
git commit -m "feat: add new booking command"
git push origin main

# 4. GitHub Actions автоматически задеплоит на production
# 5. Бот перезапустится с новым кодом через ~1-2 минуты
```

## Production окружение

- **Сервер:** 162.247.153.216
- **Бот:** `/opt/blagovest-telegram-bot/`
- **Плагин:** `/home/blagovest.net/public_html/wp-content/plugins/latepoint-telegram/`
- **Сервис:** `telegram-bot-blagovest.service` (systemd)
- **База данных:** SQLite (`bot_data.db`)
- **Логи:** `/opt/blagovest-telegram-bot/logs/bot.log`

### Управление ботом на сервере

```bash
# SSH на сервер
ssh root@162.247.153.216

# Проверить статус
systemctl status telegram-bot-blagovest

# Перезапустить
systemctl restart telegram-bot-blagovest

# Посмотреть логи
tail -f /opt/blagovest-telegram-bot/logs/bot.log

# Или через journalctl
journalctl -u telegram-bot-blagovest -f
```

## Основные функции

### Telegram Bot

- `/start` - Регистрация в системе
- `/bookings` - Просмотр бронирований
- `/schedule` - Показать расписание
- `/help` - Справка по командам

**Автоматические уведомления:**
- Новое бронирование создано
- Бронирование изменено/отменено
- Напоминание за 24 часа
- Напоминание за 1 час
- Напоминание за 15 минут

### WordPress Plugin

- Автоматическая отправка вебхуков в Telegram при событиях LatePoint
- Админ панель для настройки уведомлений
- Синхронизация данных клиентов с Telegram
- REST API для взаимодействия с ботом

## Конфигурация

### Переменные окружения

Основные настройки хранятся в `bot/config.py` (не в Git) и `.env`.

См. `.env.example` для списка всех доступных переменных.

**Обязательные:**
- `BOT_TOKEN` - Telegram bot token от @BotFather
- `WEBHOOK_SECRET` - Секретный ключ для вебхуков
- `WP_API_URL` - URL WordPress API

### Генерация WEBHOOK_SECRET

```bash
# Сгенерировать случайный секретный ключ
openssl rand -hex 32
```

Добавить этот ключ в:
1. `bot/config.py` → `WEBHOOK_SECRET`
2. WordPress admin → LatePoint Telegram Settings

## Безопасность

**Важно:**
- НЕ коммитьте `config.py`, `.env`, `*.db` файлы
- Используйте `config.example.py` и `.env.example` как шаблоны
- Храните токены и секреты в безопасности
- Регулярно обновляйте зависимости: `pip install -r requirements.txt --upgrade`

**Что игнорируется Git:**
- `bot/config.py` (токены и секреты)
- `bot/*.db` (база данных)
- `bot/logs/` (лог файлы)
- `__pycache__/`, `*.pyc` (Python кеш)

## Troubleshooting

### Бот не запускается

```bash
# Проверить логи
journalctl -u telegram-bot-blagovest -n 50

# Проверить конфигурацию
python bot/config.py

# Запустить вручную для диагностики
cd /opt/blagovest-telegram-bot
python3 bot.py
```

### Деплой не работает

См. раздел [Troubleshooting в SETUP_CICD.md](SETUP_CICD.md#troubleshooting).

### Плагин не отправляет уведомления

1. Проверить настройки в WordPress admin
2. Проверить что `WEBHOOK_SECRET` совпадает в боте и плагине
3. Проверить логи WordPress: Debug Log или Query Monitor
4. Проверить что бот доступен по URL

## Разработка

### Требования

- Python 3.8+
- pip / virtualenv
- Git
- SSH доступ к VPS (для деплоя)

### Установка dev зависимостей

```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8  # Для тестов и линтинга
```

### Запуск тестов

```bash
pytest tests/
```

### Линтинг и форматирование

```bash
# Проверка стиля кода
flake8 bot/

# Автоформатирование
black bot/
```

## Contributing

1. Fork репозитория
2. Создать feature ветку (`git checkout -b feature/amazing-feature`)
3. Коммит изменений (`git commit -m 'feat: add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing-feature`)
5. Открыть Pull Request

## Лицензия

Этот проект является частным и не имеет открытой лицензии.

## Контакты

При возникновении проблем или вопросов:
- Открыть Issue в репозитории
- Проверить [SETUP_CICD.md](SETUP_CICD.md) для инструкций по деплою
- Проверить логи на сервере

---

**Последнее обновление:** Ноябрь 2025
