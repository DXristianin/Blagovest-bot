# LatePoint Telegram Integration Plugin

WordPress плагин для интеграции LatePoint с Telegram ботом.

## Описание

Этот плагин связывает систему онлайн-бронирования LatePoint с Telegram ботом, автоматически отправляя уведомления о событиях бронирования.

## Возможности

- Автоматическая отправка вебхуков в Telegram бот при событиях LatePoint
- Поддержка событий: создание, обновление, отмена бронирований
- Синхронизация данных клиентов с Telegram
- REST API для взаимодействия с Telegram ботом
- Админ панель для настройки уведомлений
- Безопасная аутентификация через webhook secret
- Логирование всех взаимодействий

## Требования

- WordPress 5.0+
- PHP 7.4+
- LatePoint плагин установлен и активен
- Telegram бот настроен и запущен

## Структура плагина

```
plugin/
├── latepoint-telegram.php        # Главный файл плагина
│
├── includes/                      # PHP классы
│   ├── class-database.php        # Работа с БД WordPress
│   ├── class-hooks.php           # LatePoint хуки и события
│   ├── class-api.php             # REST API endpoints
│   ├── class-webhook-sender.php  # Отправка вебхуков в Telegram бот
│   └── class-logger.php          # Логирование
│
├── admin/                         # Админ интерфейс
│   ├── settings-page.php         # Страница настроек
│   ├── css/
│   │   └── admin-style.css
│   └── js/
│       └── admin-script.js
│
├── assets/                        # Ресурсы
│   ├── css/
│   └── js/
│
└── README.md                      # Этот файл
```

## Установка

### Автоматическая (через GitHub Actions)

Плагин автоматически деплоится при push в `main` ветку.

### Ручная установка

1. **Скопировать файлы плагина:**
   ```bash
   # На сервере
   cp -r plugin/ /home/blagovest.net/public_html/wp-content/plugins/latepoint-telegram/
   ```

2. **Установить права доступа:**
   ```bash
   chown -R www-data:www-data /home/blagovest.net/public_html/wp-content/plugins/latepoint-telegram/
   chmod -R 755 /home/blagovest.net/public_html/wp-content/plugins/latepoint-telegram/
   ```

3. **Активировать плагин:**
   - WordPress Admin → Plugins
   - Найти "LatePoint Telegram Integration"
   - Нажать "Activate"

## Настройка

### 1. Открыть настройки плагина

WordPress Admin → Settings → LatePoint Telegram

### 2. Основные настройки

**Telegram Bot URL:**
```
http://162.247.153.216:8000/webhook
```
URL вашего Telegram бота для отправки вебхуков.

**Webhook Secret:**
```
your-super-secret-key-here
```
Секретный ключ для безопасной аутентификации (должен совпадать с `WEBHOOK_SECRET` в боте).

Сгенерировать:
```bash
openssl rand -hex 32
```

**Enable Notifications:**
- ☑ Booking Created - Уведомление о новом бронировании
- ☑ Booking Updated - Уведомление об изменении
- ☑ Booking Cancelled - Уведомление об отмене
- ☑ Customer Registered - Уведомление о новом клиенте

### 3. Сохранить настройки

Нажать "Save Changes" внизу страницы.

### 4. Тестирование

Создать тестовое бронирование в LatePoint и проверить:
1. Логи плагина (Settings → LatePoint Telegram → Logs)
2. Логи бота на сервере
3. Получение уведомления в Telegram

## События и хуки

### LatePoint Events

Плагин подключается к следующим хукам LatePoint:

**Бронирования:**
```php
add_action('latepoint_booking_created', 'send_booking_webhook');
add_action('latepoint_booking_updated', 'send_booking_webhook');
add_action('latepoint_booking_cancelled', 'send_booking_webhook');
```

**Клиенты:**
```php
add_action('latepoint_customer_created', 'send_customer_webhook');
add_action('latepoint_customer_updated', 'send_customer_webhook');
```

### Данные вебхука

Формат отправляемых данных:

```json
{
  "event": "booking_created",
  "timestamp": 1699876543,
  "data": {
    "booking_id": 123,
    "customer_id": 456,
    "customer_name": "Иван Иванов",
    "customer_phone": "+7 999 123-45-67",
    "customer_email": "ivan@example.com",
    "service_id": 1,
    "service_name": "Консультация",
    "agent_id": 2,
    "agent_name": "Мария Петрова",
    "start_date": "2024-11-10",
    "start_time": "14:00",
    "end_time": "15:00",
    "duration": 60,
    "price": "2500",
    "status": "approved",
    "notes": "Первичная консультация",
    "custom_fields": {
      "telegram_chat_id": "123456789"
    }
  }
}
```

## REST API

Плагин предоставляет REST API для взаимодействия с Telegram ботом.

### Базовый URL

```
https://blagovest.net/wp-json/latepoint-telegram/v1
```

### Endpoints

#### GET /bookings/{id}

Получить информацию о бронировании.

**Request:**
```bash
curl https://blagovest.net/wp-json/latepoint-telegram/v1/bookings/123
```

**Response:**
```json
{
  "success": true,
  "data": {
    "booking_id": 123,
    "customer_name": "Иван Иванов",
    ...
  }
}
```

#### GET /customer/{id}

Получить информацию о клиенте.

**Request:**
```bash
curl https://blagovest.net/wp-json/latepoint-telegram/v1/customer/456
```

#### POST /link-telegram

Связать Telegram аккаунт с клиентом LatePoint.

**Request:**
```bash
curl -X POST https://blagovest.net/wp-json/latepoint-telegram/v1/link-telegram \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 456,
    "telegram_chat_id": "123456789",
    "telegram_username": "@ivanov"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Telegram account linked successfully"
}
```

## Разработка

### Добавление нового события

1. **Найти LatePoint хук:**
   ```php
   // В LatePoint plugin найти нужное действие
   do_action('latepoint_some_event', $data);
   ```

2. **Добавить обработчик в `includes/class-hooks.php`:**
   ```php
   public function register_hooks() {
       add_action('latepoint_some_event', [$this, 'handle_some_event'], 10, 1);
   }

   public function handle_some_event($data) {
       $webhook_data = [
           'event' => 'some_event',
           'timestamp' => time(),
           'data' => $this->prepare_event_data($data)
       ];

       $this->webhook_sender->send($webhook_data);
   }
   ```

3. **Добавить настройку в админке:**
   ```php
   // admin/settings-page.php
   <label>
       <input type="checkbox" name="enable_some_event" value="1" />
       Enable Some Event Notifications
   </label>
   ```

### Добавление нового API endpoint

1. **Создать метод в `includes/class-api.php`:**
   ```php
   public function register_routes() {
       register_rest_route('latepoint-telegram/v1', '/my-endpoint', [
           'methods' => 'GET',
           'callback' => [$this, 'handle_my_endpoint'],
           'permission_callback' => '__return_true'
       ]);
   }

   public function handle_my_endpoint($request) {
       return new WP_REST_Response([
           'success' => true,
           'data' => 'Hello from API'
       ], 200);
   }
   ```

### Тестирование

```bash
# Проверить активацию плагина
wp plugin list

# Активировать
wp plugin activate latepoint-telegram

# Деактивировать
wp plugin deactivate latepoint-telegram

# Просмотреть настройки
wp option get latepoint_telegram_settings

# Обновить настройки
wp option update latepoint_telegram_settings '{"bot_url":"http://...","webhook_secret":"..."}'
```

### Логирование

Плагин записывает логи в:
- WordPress Debug Log (если WP_DEBUG включен)
- Отдельная таблица БД `wp_latepoint_telegram_logs`

**Включить WordPress Debug:**
```php
// wp-config.php
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
define('WP_DEBUG_DISPLAY', false);
```

**Просмотр логов:**
```bash
# WordPress debug log
tail -f /path/to/wordpress/wp-content/debug.log

# Или через админку
Settings → LatePoint Telegram → Logs
```

## Troubleshooting

### Плагин не отправляет вебхуки

1. **Проверить настройки:**
   - Settings → LatePoint Telegram
   - Убедиться что Bot URL правильный
   - Webhook Secret заполнен

2. **Проверить логи:**
   ```bash
   tail -f /home/blagovest.net/public_html/wp-content/debug.log
   ```

3. **Тестовый запрос:**
   ```bash
   # Из WordPress сервера
   curl -X POST http://162.247.153.216:8000/webhook \
     -H "Content-Type: application/json" \
     -H "X-Webhook-Secret: your-secret" \
     -d '{"event":"test","data":{}}'
   ```

4. **Проверить доступность бота:**
   ```bash
   # Проверить что порт открыт
   telnet 162.247.153.216 8000
   ```

### Ошибка "Could not connect to bot"

**Причины:**
- Бот не запущен на сервере
- Неправильный URL бота
- Файрвол блокирует соединение
- Неверный порт

**Решение:**
```bash
# На сервере бота
systemctl status telegram-bot-blagovest

# Проверить что порт слушается
netstat -tulpn | grep 8000

# Проверить файрвол
ufw status
```

### Webhook возвращает 401 Unauthorized

**Причина:** Неверный `Webhook Secret`.

**Решение:**
1. Проверить secret в настройках плагина
2. Проверить secret в `config.py` бота
3. Убедиться что они идентичны

### LatePoint события не срабатывают

**Причины:**
- LatePoint плагин не активен
- Хуки изменились в новой версии LatePoint
- PHP ошибки

**Решение:**
1. Проверить активность LatePoint:
   ```bash
   wp plugin list | grep latepoint
   ```

2. Проверить PHP ошибки:
   ```bash
   tail -f /var/log/php-fpm/error.log
   ```

3. Проверить версию LatePoint и совместимость хуков

## Безопасность

**Важно:**
- Используйте сильный `Webhook Secret`
- Храните secret в безопасности
- Не коммитьте секреты в Git
- Регулярно обновляйте WordPress и плагины
- Используйте HTTPS для production
- Ограничьте доступ к API по IP (опционально)

## Деплой

### Автоматический

Плагин автоматически деплоится через GitHub Actions:

```yaml
# .github/workflows/deploy.yml
- name: Deploy WordPress plugin
  run: |
    rsync -av --delete \
      --exclude='config.php' \
      plugin/ \
      $PLUGIN_DEST/
```

### Ручной

```bash
# На вашей машине
cd /path/to/latepoint-telegram-integration

# Синхронизировать с сервером
rsync -avz --exclude='config.php' \
  plugin/ \
  root@162.247.153.216:/home/blagovest.net/public_html/wp-content/plugins/latepoint-telegram/

# На сервере установить права
ssh root@162.247.153.216 "chown -R www-data:www-data /home/blagovest.net/public_html/wp-content/plugins/latepoint-telegram/"
```

## Удаление

1. **Деактивировать плагин:**
   ```bash
   wp plugin deactivate latepoint-telegram
   ```

2. **Удалить файлы:**
   ```bash
   rm -rf /home/blagovest.net/public_html/wp-content/plugins/latepoint-telegram/
   ```

3. **Очистить настройки (опционально):**
   ```bash
   wp option delete latepoint_telegram_settings
   ```

4. **Удалить таблицы БД (опционально):**
   ```sql
   DROP TABLE IF EXISTS wp_latepoint_telegram_logs;
   ```

## Дополнительная информация

- [LatePoint Documentation](https://latepoint.com/docs/)
- [WordPress Plugin Development](https://developer.wordpress.org/plugins/)
- [REST API Handbook](https://developer.wordpress.org/rest-api/)
- [Action Reference](https://codex.wordpress.org/Plugin_API/Action_Reference)

## Contributing

См. корневой [README.md](../README.md) для инструкций по внесению изменений.

## Лицензия

Частный проект без открытой лицензии.

---

Для вопросов и проблем см. корневой [README.md](../README.md) и [SETUP_CICD.md](../SETUP_CICD.md).
