# Настройка CI/CD для LatePoint Telegram Integration

Эта инструкция покажет, как настроить автоматический деплой проекта на VPS при помощи GitHub Actions.

## Содержание

1. [Обзор системы деплоя](#обзор-системы-деплоя)
2. [Предварительные требования](#предварительные-требования)
3. [Создание SSH ключей](#создание-ssh-ключей)
4. [Настройка GitHub Secrets](#настройка-github-secrets)
5. [Первоначальная настройка на сервере](#первоначальная-настройка-на-сервере)
6. [Синхронизация файлов с сервера](#синхронизация-файлов-с-сервера)
7. [Workflow разработки](#workflow-разработки)
8. [Troubleshooting](#troubleshooting)

---

## Обзор системы деплоя

Система использует GitHub Actions для автоматического деплоя при push в ветку `main`:

```
Push to main → GitHub Actions → SSH на VPS → git pull → Установка зависимостей → Перезапуск сервисов
```

**Что деплоится:**
- Python Telegram бот → `/opt/blagovest-telegram-bot/`
- WordPress плагин → `/home/blagovest.net/public_html/wp-content/plugins/latepoint-telegram/`

**Что сохраняется:**
- `config.py` (конфигурация с токенами)
- `bot_data.db` (база данных SQLite)
- `logs/` (лог файлы)

---

## Предварительные требования

- GitHub аккаунт с правами администратора репозитория
- SSH доступ к VPS (162.247.153.216)
- Git установлен на локальной машине и VPS
- Python 3.8+ на VPS
- Systemd сервис `telegram-bot-blagovest` настроен на VPS

---

## Создание SSH ключей

### 1. Генерация новой пары SSH ключей

На вашей локальной машине (MacBook):

```bash
# Создать директорию для ключей если её нет
mkdir -p ~/.ssh

# Сгенерировать новую пару ключей ED25519
ssh-keygen -t ed25519 -C "github-actions-latepoint-bot" -f ~/.ssh/github_actions_latepoint_bot

# Или RSA, если ED25519 не поддерживается
ssh-keygen -t rsa -b 4096 -C "github-actions-latepoint-bot" -f ~/.ssh/github_actions_latepoint_bot
```

**Важно:** Не устанавливайте passphrase (нажмите Enter когда спросит).

Это создаст два файла:
- `~/.ssh/github_actions_latepoint_bot` (приватный ключ)
- `~/.ssh/github_actions_latepoint_bot.pub` (публичный ключ)

### 2. Добавление публичного ключа на VPS

```bash
# Скопировать публичный ключ на сервер
ssh-copy-id -i ~/.ssh/github_actions_latepoint_bot.pub root@162.247.153.216

# Или вручную:
cat ~/.ssh/github_actions_latepoint_bot.pub | ssh root@162.247.153.216 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### 3. Тестирование SSH соединения

```bash
# Протестировать подключение с новым ключом
ssh -i ~/.ssh/github_actions_latepoint_bot root@162.247.153.216 "echo 'SSH connection successful!'"
```

Если видите "SSH connection successful!", всё работает.

---

## Настройка GitHub Secrets

GitHub Secrets хранят конфиденциальные данные (SSH ключи, пароли) в зашифрованном виде.

### 1. Открыть настройки репозитория

1. Перейти в ваш GitHub репозиторий
2. **Settings** → **Secrets and variables** → **Actions**
3. Нажать **New repository secret**

### 2. Создать необходимые секреты

#### VPS_HOST

```
Name: VPS_HOST
Value: 162.247.153.216
```

#### VPS_USERNAME

```
Name: VPS_USERNAME
Value: root
```

#### VPS_SSH_KEY

```bash
# Скопировать приватный ключ в буфер обмена (macOS)
cat ~/.ssh/github_actions_latepoint_bot | pbcopy
```

```
Name: VPS_SSH_KEY
Value: (вставить содержимое приватного ключа)
```

Должно начинаться с:
- `-----BEGIN OPENSSH PRIVATE KEY-----` (ED25519)
- `-----BEGIN RSA PRIVATE KEY-----` (RSA)

#### VPS_PORT (опционально)

```
Name: VPS_PORT
Value: 22
```

### 3. Проверка созданных секретов

После создания вы должны увидеть 3-4 секрета:
- `VPS_HOST`
- `VPS_USERNAME`
- `VPS_SSH_KEY`
- `VPS_PORT` (опционально)

---

## Первоначальная настройка на сервере

### 1. Подключиться к VPS

```bash
ssh root@162.247.153.216
```

### 2. Настроить Git на сервере

```bash
cd /opt/blagovest-telegram-bot

# Инициализировать Git репозиторий
git init

# Добавить remote (замените YOUR_USERNAME на ваш GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/latepoint-telegram-integration.git

# Или если используете SSH
git remote add origin git@github.com:YOUR_USERNAME/latepoint-telegram-integration.git

# Настроить Git для разрешения git pull в non-bare репозитории
git config receive.denyCurrentBranch updateInstead
```

### 3. Создать config.py (если ещё не создан)

```bash
cd /opt/blagovest-telegram-bot

# Скопировать шаблон (после первого git pull)
cp bot/config.example.py config.py

# Отредактировать с реальными токенами
nano config.py
```

### 4. Создать директорию для логов

```bash
mkdir -p /opt/blagovest-telegram-bot/logs
mkdir -p /opt/backups
```

### 5. Проверить Systemd сервис

```bash
# Проверить статус сервиса
systemctl status telegram-bot-blagovest

# Посмотреть конфигурацию
cat /etc/systemd/system/telegram-bot-blagovest.service

# Если нужно создать сервис, используйте этот шаблон:
cat > /etc/systemd/system/telegram-bot-blagovest.service <<EOF
[Unit]
Description=LatePoint Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/blagovest-telegram-bot
ExecStart=/usr/bin/python3 /opt/blagovest-telegram-bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузить systemd и включить автозапуск
systemctl daemon-reload
systemctl enable telegram-bot-blagovest
systemctl start telegram-bot-blagovest
```

---

## Синхронизация файлов с сервера

После настройки CI/CD нужно скачать файлы с production сервера в локальный репозиторий.

### 1. Запустить скрипт синхронизации

```bash
# На вашей локальной машине (MacBook)
cd /path/to/latepoint-telegram-integration

# Сделать скрипт исполняемым
chmod +x scripts/sync-from-server.sh

# Запустить синхронизацию
./scripts/sync-from-server.sh
```

Скрипт скачает файлы, исключая:
- `config.py` (содержит токены)
- `*.db` (база данных)
- `logs/` (лог файлы)
- `__pycache__/` (Python кеш)

### 2. Создать config.py локально (для разработки)

```bash
cp bot/config.example.py bot/config.py
# Отредактировать с тестовыми/dev значениями
```

**Важно:** `bot/config.py` в `.gitignore` и НЕ будет закоммичен.

### 3. Закоммитить и запушить

```bash
git add .
git commit -m "Initial setup: Add bot and plugin files"
git push origin main
```

GitHub Actions автоматически запустится и сделает деплой.

---

## Workflow разработки

### Типичный цикл разработки:

1. **Локальная разработка**
   ```bash
   # Редактировать файлы локально
   code bot/handlers/commands.py
   ```

2. **Тестирование (опционально)**
   ```bash
   # Запустить локально для тестов
   python3 bot/bot.py
   ```

3. **Коммит изменений**
   ```bash
   git add bot/handlers/commands.py
   git commit -m "feat: add new booking command"
   ```

4. **Push в main**
   ```bash
   git push origin main
   ```

5. **Автоматический деплой**
   - GitHub Actions запустится автоматически
   - Проверить статус: [GitHub Actions tab](https://github.com/YOUR_USERNAME/latepoint-telegram-integration/actions)
   - Деплой займёт ~1-2 минуты

6. **Проверка на production**
   ```bash
   # SSH на сервер
   ssh root@162.247.153.216

   # Проверить статус бота
   systemctl status telegram-bot-blagovest

   # Посмотреть логи
   tail -f /opt/blagovest-telegram-bot/logs/bot.log
   ```

### Просмотр логов деплоя

1. Перейти в репозиторий на GitHub
2. Вкладка **Actions**
3. Выбрать последний workflow run
4. Кликнуть на job "Deploy to VPS"
5. Развернуть шаги для просмотра логов

---

## Troubleshooting

### Проблема: GitHub Actions не может подключиться по SSH

**Симптомы:**
```
ssh: connect to host 162.247.153.216 port 22: Connection refused
```

**Решение:**
1. Проверить, что VPS доступен:
   ```bash
   ping 162.247.153.216
   ```

2. Проверить SSH доступ с локальной машины:
   ```bash
   ssh -i ~/.ssh/github_actions_latepoint_bot root@162.247.153.216
   ```

3. Проверить что публичный ключ добавлен на сервер:
   ```bash
   ssh root@162.247.153.216 "cat ~/.ssh/authorized_keys"
   ```

### Проблема: Permission denied (publickey)

**Симптомы:**
```
Permission denied (publickey,gssapi-keyex,gssapi-with-mic)
```

**Решение:**
1. Проверить формат приватного ключа в GitHub Secrets
2. Убедиться что ключ начинается с `-----BEGIN` и заканчивается `-----END`
3. Пересоздать SSH ключ и повторить процесс

### Проблема: git pull fails с "fatal: not a git repository"

**Симптомы:**
```
fatal: not a git repository (or any of the parent directories): .git
```

**Решение:**
```bash
ssh root@162.247.153.216
cd /opt/blagovest-telegram-bot
git init
git remote add origin https://github.com/YOUR_USERNAME/latepoint-telegram-integration.git
git fetch origin main
git reset --hard origin/main
```

### Проблема: Systemd service не перезапускается

**Симптомы:**
```
Failed to restart telegram-bot-blagovest.service: Unit not found
```

**Решение:**
```bash
ssh root@162.247.153.216

# Проверить существование сервиса
systemctl list-unit-files | grep telegram-bot

# Если нет, создать (см. секцию "Первоначальная настройка на сервере")

# Перезагрузить systemd
systemctl daemon-reload
systemctl enable telegram-bot-blagovest
systemctl start telegram-bot-blagovest
```

### Проблема: Bot не запускается после деплоя

**Симптомы:**
```
systemctl status telegram-bot-blagovest
● telegram-bot-blagovest.service - LatePoint Telegram Bot
   Active: failed (Result: exit-code)
```

**Решение:**
```bash
# Посмотреть подробные логи
journalctl -u telegram-bot-blagovest -n 50 --no-pager

# Проверить конфигурацию
cat /opt/blagovest-telegram-bot/config.py

# Проверить что config.py существует и содержит правильные токены

# Проверить Python зависимости
pip3 install -r /opt/blagovest-telegram-bot/requirements.txt

# Попробовать запустить вручную для диагностики
cd /opt/blagovest-telegram-bot
python3 bot.py
```

### Проблема: WordPress plugin не обновляется

**Симптомы:**
Бот обновился, но плагин показывает старую версию.

**Решение:**
```bash
ssh root@162.247.153.216

# Проверить что файлы скопировались
ls -la /home/blagovest.net/public_html/wp-content/plugins/latepoint-telegram/

# Проверить права доступа
chown -R www-data:www-data /home/blagovest.net/public_html/wp-content/plugins/latepoint-telegram/

# Вручную запустить rsync из workflow
rsync -av --delete \
  --exclude='config.php' \
  /opt/blagovest-telegram-bot/plugin/ \
  /home/blagovest.net/public_html/wp-content/plugins/latepoint-telegram/
```

### Проблема: Backup занимает много места

**Решение:**
```bash
ssh root@162.247.153.216

# Посмотреть размер backups
du -sh /opt/backups/*

# Удалить старые backups (автоматически оставляет последние 5)
ls -t /opt/backups/blagovest-bot-backup-*.tar.gz | tail -n +6 | xargs rm

# Или удалить backups старше 7 дней
find /opt/backups -name "blagovest-bot-backup-*.tar.gz" -mtime +7 -delete
```

### Получение помощи

Если проблема не решается:

1. Проверить логи GitHub Actions
2. Проверить логи бота: `tail -f /opt/blagovest-telegram-bot/logs/bot.log`
3. Проверить systemd логи: `journalctl -u telegram-bot-blagovest -f`
4. Открыть Issue в репозитории с подробным описанием проблемы

---

## Дополнительные ресурсы

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [appleboy/ssh-action](https://github.com/appleboy/ssh-action)
- [Systemd Service Management](https://www.freedesktop.org/software/systemd/man/systemctl.html)
- [Git Workflows](https://www.atlassian.com/git/tutorials/comparing-workflows)

---

**Последнее обновление:** Ноябрь 2025
