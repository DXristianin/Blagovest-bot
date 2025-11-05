<?php
/**
 * Страница настроек плагина в админке
 */

if (!defined('ABSPATH')) {
    exit;
}

// Сохранение настроек
if (isset($_POST['submit']) && check_admin_referer('latepoint_telegram_settings')) {
    update_option('latepoint_telegram_bot_token', sanitize_text_field($_POST['bot_token']));
    update_option('latepoint_telegram_bot_url', esc_url_raw($_POST['bot_url']));

    echo '<div class="notice notice-success"><p>' . __('Настройки сохранены!', 'latepoint-telegram') . '</p></div>';
}

$bot_token = get_option('latepoint_telegram_bot_token');
$bot_url = get_option('latepoint_telegram_bot_url');
$webhook_secret = get_option('latepoint_telegram_webhook_secret');

// Генерация токена регистрации для текущего пользователя
$current_user = wp_get_current_user();
$registration_token = get_user_meta($current_user->ID, 'telegram_registration_token', true);
$token_expires = get_user_meta($current_user->ID, 'telegram_registration_token_expires', true);
$telegram_chat_id = get_user_meta($current_user->ID, 'telegram_chat_id', true);
$telegram_username = get_user_meta($current_user->ID, 'telegram_username', true);

$token_valid = $registration_token && $token_expires && time() < $token_expires;

?>

<div class="wrap latepoint-telegram-settings">
    <h1><?php echo esc_html(get_admin_page_title()); ?></h1>

    <div class="latepoint-telegram-admin-wrapper">
        <!-- Настройки бота -->
        <div class="os-widget">
            <div class="os-widget-header">
                <h3><?php _e('Настройки Telegram бота', 'latepoint-telegram'); ?></h3>
            </div>
            <div class="os-widget-body">
                <form method="post" action="">
                    <?php wp_nonce_field('latepoint_telegram_settings'); ?>

                    <div class="os-row">
                        <div class="os-col-12">
                            <div class="os-form-group">
                                <label for="bot_token">
                                    <?php _e('Bot Token', 'latepoint-telegram'); ?>
                                    <span class="os-form-label-description">
                                        <?php _e('Токен бота от @BotFather', 'latepoint-telegram'); ?>
                                    </span>
                                </label>
                                <input type="text"
                                       name="bot_token"
                                       id="bot_token"
                                       value="<?php echo esc_attr($bot_token); ?>"
                                       class="os-form-control"
                                       placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11" />
                            </div>
                        </div>
                    </div>

                    <div class="os-row">
                        <div class="os-col-12">
                            <div class="os-form-group">
                                <label for="bot_url">
                                    <?php _e('Bot Service URL', 'latepoint-telegram'); ?>
                                    <span class="os-form-label-description">
                                        <?php _e('URL где запущен Python сервис бота (например: http://localhost:8000)', 'latepoint-telegram'); ?>
                                    </span>
                                </label>
                                <input type="url"
                                       name="bot_url"
                                       id="bot_url"
                                       value="<?php echo esc_attr($bot_url); ?>"
                                       class="os-form-control"
                                       placeholder="http://localhost:8000" />
                            </div>
                        </div>
                    </div>

                    <div class="os-row">
                        <div class="os-col-12">
                            <div class="os-form-group">
                                <label>
                                    <?php _e('Webhook Secret', 'latepoint-telegram'); ?>
                                    <span class="os-form-label-description">
                                        <?php _e('Секретный ключ для безопасной передачи данных (не изменяйте)', 'latepoint-telegram'); ?>
                                    </span>
                                </label>
                                <input type="text"
                                       value="<?php echo esc_attr($webhook_secret); ?>"
                                       class="os-form-control"
                                       readonly />
                                <div class="os-form-helper-text">
                                    <?php _e('Этот ключ используется для подписи webhook запросов. Скопируйте его в настройки Python бота.', 'latepoint-telegram'); ?>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="os-form-buttons">
                        <button type="submit" name="submit" class="latepoint-btn latepoint-btn-primary">
                            <?php _e('Сохранить настройки', 'latepoint-telegram'); ?>
                        </button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Регистрация в боте -->
        <div class="os-widget" style="margin-top: 20px;">
            <div class="os-widget-header">
                <h3><?php _e('Ваша регистрация в Telegram боте', 'latepoint-telegram'); ?></h3>
            </div>
            <div class="os-widget-body">
                <?php if ($telegram_chat_id): ?>
                    <div class="os-form-message-w status-success">
                        <div class="os-form-message-body">
                            <strong><?php _e('Вы успешно зарегистрированы!', 'latepoint-telegram'); ?></strong>
                            <div style="margin-top: 10px;">
                                <p><strong><?php _e('Telegram Username:', 'latepoint-telegram'); ?></strong> @<?php echo esc_html($telegram_username); ?></p>
                                <p><strong><?php _e('Chat ID:', 'latepoint-telegram'); ?></strong> <?php echo esc_html($telegram_chat_id); ?></p>
                            </div>
                        </div>
                    </div>
                <?php else: ?>
                    <div class="os-form-sub-header">
                        <h4><?php _e('Как зарегистрироваться в боте:', 'latepoint-telegram'); ?></h4>
                    </div>

                    <ol style="margin-left: 20px; line-height: 1.8;">
                        <li><?php _e('Найдите бота в Telegram (имя бота укажет администратор)', 'latepoint-telegram'); ?></li>
                        <li><?php _e('Нажмите кнопку "Start" или отправьте команду /start', 'latepoint-telegram'); ?></li>
                        <li><?php _e('Используйте следующую команду для регистрации:', 'latepoint-telegram'); ?></li>
                    </ol>

                    <div id="telegram-registration-token-section" style="margin-top: 20px;">
                        <?php if ($token_valid): ?>
                            <div class="os-form-group">
                                <label><?php _e('Команда для регистрации:', 'latepoint-telegram'); ?></label>
                                <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 14px; position: relative;">
                                    <code id="registration-command">/start <?php echo esc_html($registration_token); ?></code>
                                    <button type="button"
                                            onclick="copyToClipboard('<?php echo esc_js($registration_token); ?>')"
                                            class="latepoint-btn latepoint-btn-sm"
                                            style="position: absolute; right: 10px; top: 10px;">
                                        <?php _e('Копировать', 'latepoint-telegram'); ?>
                                    </button>
                                </div>
                                <div class="os-form-helper-text" style="margin-top: 10px;">
                                    <?php
                                    $minutes_left = ceil(($token_expires - time()) / 60);
                                    printf(__('Токен действителен еще %d минут. Скопируйте команду и отправьте её боту.', 'latepoint-telegram'), $minutes_left);
                                    ?>
                                </div>
                            </div>
                        <?php else: ?>
                            <button type="button"
                                    onclick="generateRegistrationToken()"
                                    class="latepoint-btn latepoint-btn-primary"
                                    id="generate-token-btn">
                                <?php _e('Сгенерировать токен регистрации', 'latepoint-telegram'); ?>
                            </button>
                            <div id="token-result" style="margin-top: 20px; display: none;"></div>
                        <?php endif; ?>
                    </div>
                <?php endif; ?>
            </div>
        </div>

        <!-- Инструкции -->
        <div class="os-widget" style="margin-top: 20px;">
            <div class="os-widget-header">
                <h3><?php _e('Инструкция по настройке', 'latepoint-telegram'); ?></h3>
            </div>
            <div class="os-widget-body">
                <div class="os-form-sub-header">
                    <h4><?php _e('1. Создание Telegram бота', 'latepoint-telegram'); ?></h4>
                </div>
                <ol style="margin-left: 20px; line-height: 1.8;">
                    <li><?php _e('Откройте Telegram и найдите @BotFather', 'latepoint-telegram'); ?></li>
                    <li><?php _e('Отправьте команду /newbot', 'latepoint-telegram'); ?></li>
                    <li><?php _e('Следуйте инструкциям для создания бота', 'latepoint-telegram'); ?></li>
                    <li><?php _e('Скопируйте токен и вставьте его выше', 'latepoint-telegram'); ?></li>
                </ol>

                <div class="os-form-sub-header" style="margin-top: 20px;">
                    <h4><?php _e('2. Установка Python сервиса', 'latepoint-telegram'); ?></h4>
                </div>
                <ol style="margin-left: 20px; line-height: 1.8;">
                    <li><?php _e('Установите Python 3.9 или выше на сервере', 'latepoint-telegram'); ?></li>
                    <li><?php _e('Загрузите файлы бота в директорию /opt/blagovest-telegram-bot/', 'latepoint-telegram'); ?></li>
                    <li><?php _e('Установите зависимости: pip install -r requirements.txt', 'latepoint-telegram'); ?></li>
                    <li><?php _e('Настройте файл config.py с токеном бота и webhook secret', 'latepoint-telegram'); ?></li>
                    <li><?php _e('Запустите сервис: systemctl start telegram-bot', 'latepoint-telegram'); ?></li>
                </ol>

                <div class="os-form-sub-header" style="margin-top: 20px;">
                    <h4><?php _e('3. Настройка уведомлений', 'latepoint-telegram'); ?></h4>
                </div>
                <p style="margin-left: 20px; line-height: 1.8;">
                    <?php _e('После регистрации учителей и учеников в боте, они автоматически будут получать уведомления о новых бронированиях, изменениях и напоминания перед уроками.', 'latepoint-telegram'); ?>
                </p>
            </div>
        </div>
    </div>
</div>

<script>
function generateRegistrationToken() {
    const btn = document.getElementById('generate-token-btn');
    btn.disabled = true;
    btn.textContent = '<?php _e('Генерация...', 'latepoint-telegram'); ?>';

    fetch('<?php echo rest_url('latepoint-telegram/v1/generate-token'); ?>', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-WP-Nonce': '<?php echo wp_create_nonce('wp_rest'); ?>'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const resultDiv = document.getElementById('token-result');
            resultDiv.innerHTML = `
                <div class="os-form-group">
                    <label><?php _e('Команда для регистрации:', 'latepoint-telegram'); ?></label>
                    <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 14px; position: relative;">
                        <code>/start ${data.token}</code>
                        <button type="button"
                                onclick="copyToClipboard('${data.token}')"
                                class="latepoint-btn latepoint-btn-sm"
                                style="position: absolute; right: 10px; top: 10px;">
                            <?php _e('Копировать', 'latepoint-telegram'); ?>
                        </button>
                    </div>
                    <div class="os-form-helper-text" style="margin-top: 10px;">
                        <?php _e('Токен действителен 15 минут. Скопируйте команду и отправьте её боту.', 'latepoint-telegram'); ?>
                    </div>
                </div>
            `;
            resultDiv.style.display = 'block';
            btn.style.display = 'none';
        } else {
            alert('<?php _e('Ошибка генерации токена', 'latepoint-telegram'); ?>');
            btn.disabled = false;
            btn.textContent = '<?php _e('Сгенерировать токен регистрации', 'latepoint-telegram'); ?>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('<?php _e('Ошибка генерации токена', 'latepoint-telegram'); ?>');
        btn.disabled = false;
        btn.textContent = '<?php _e('Сгенерировать токен регистрации', 'latepoint-telegram'); ?>';
    });
}

function copyToClipboard(token) {
    const text = '/start ' + token;
    navigator.clipboard.writeText(text).then(() => {
        alert('<?php _e('Команда скопирована в буфер обмена!', 'latepoint-telegram'); ?>');
    }).catch(err => {
        console.error('Failed to copy:', err);
        // Fallback для старых браузеров
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        alert('<?php _e('Команда скопирована!', 'latepoint-telegram'); ?>');
    });
}
</script>

<style>
.latepoint-telegram-admin-wrapper {
    max-width: 1200px;
}

.os-widget {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 5px;
    overflow: hidden;
}

.os-widget-header {
    background: #f7f7f7;
    border-bottom: 1px solid #ddd;
    padding: 15px 20px;
}

.os-widget-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
}

.os-widget-body {
    padding: 20px;
}

.os-form-group {
    margin-bottom: 20px;
}

.os-form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
}

.os-form-label-description {
    display: block;
    font-weight: 400;
    font-size: 13px;
    color: #666;
    margin-top: 3px;
}

.os-form-control {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.os-form-helper-text {
    font-size: 13px;
    color: #666;
    margin-top: 5px;
}

.os-form-message-w.status-success {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 4px;
    padding: 15px;
}

.os-form-message-w.status-success .os-form-message-body {
    color: #155724;
}

.os-form-buttons {
    margin-top: 30px;
}

.latepoint-btn {
    display: inline-block;
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    text-decoration: none;
    transition: all 0.2s;
}

.latepoint-btn-primary {
    background: #2271b1;
    color: #fff;
}

.latepoint-btn-primary:hover {
    background: #135e96;
}

.latepoint-btn-sm {
    padding: 5px 10px;
    font-size: 12px;
}

.os-form-sub-header h4 {
    font-size: 15px;
    font-weight: 600;
    margin: 10px 0;
}
</style>
