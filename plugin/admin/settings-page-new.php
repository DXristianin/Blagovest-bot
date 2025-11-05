<?php
/**
 * Страница настроек плагина в админке (с вкладками)
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

// Получить активную вкладку
$active_tab = isset($_GET['tab']) ? sanitize_text_field($_GET['tab']) : 'settings';

// Получить список агентов
$agents = array();
if (class_exists('OsAgentModel')) {
    global $wpdb;
    $agents_data = $wpdb->get_results("SELECT * FROM {$wpdb->prefix}latepoint_agents ORDER BY first_name, last_name");
    foreach ($agents_data as $agent_data) {
        $agents[] = array(
            'id' => $agent_data->id,
            'name' => $agent_data->first_name . ' ' . $agent_data->last_name,
            'email' => $agent_data->email,
        );
    }
}

?>

<div class="wrap latepoint-telegram-settings">
    <h1><?php echo esc_html(get_admin_page_title()); ?></h1>

    <!-- Вкладки -->
    <nav class="nav-tab-wrapper wp-clearfix">
        <a href="<?php echo admin_url('admin.php?page=latepoint-telegram&tab=settings'); ?>"
           class="nav-tab <?php echo $active_tab === 'settings' ? 'nav-tab-active' : ''; ?>">
            <?php _e('Настройки', 'latepoint-telegram'); ?>
        </a>
        <a href="<?php echo admin_url('admin.php?page=latepoint-telegram&tab=agent-bindings'); ?>"
           class="nav-tab <?php echo $active_tab === 'agent-bindings' ? 'nav-tab-active' : ''; ?>">
            <?php _e('Привязка агентов', 'latepoint-telegram'); ?>
        </a>
        <a href="<?php echo admin_url('admin.php?page=latepoint-telegram&tab=bindings-list'); ?>"
           class="nav-tab <?php echo $active_tab === 'bindings-list' ? 'nav-tab-active' : ''; ?>">
            <?php _e('Список привязок', 'latepoint-telegram'); ?>
        </a>
    </nav>

    <div class="latepoint-telegram-admin-wrapper" style="margin-top: 20px;">

        <?php if ($active_tab === 'settings'): ?>
            <!-- ВКЛАДКА: Настройки -->
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

        <?php elseif ($active_tab === 'agent-bindings'): ?>
            <!-- ВКЛАДКА: Привязка агентов -->
            <div class="os-widget">
                <div class="os-widget-header">
                    <h3><?php _e('Генерация ссылки для привязки агента к Telegram', 'latepoint-telegram'); ?></h3>
                </div>
                <div class="os-widget-body">
                    <div class="os-form-sub-header">
                        <p><?php _e('Выберите агента и сгенерируйте ссылку для привязки к Telegram. Отправьте эту ссылку агенту, чтобы он мог получать уведомления о новых записях.', 'latepoint-telegram'); ?></p>
                    </div>

                    <div class="os-form-group">
                        <label for="agent-select">
                            <?php _e('Выберите агента:', 'latepoint-telegram'); ?>
                        </label>
                        <select id="agent-select" class="os-form-control" style="max-width: 400px;">
                            <option value="">-- <?php _e('Выберите агента', 'latepoint-telegram'); ?> --</option>
                            <?php foreach ($agents as $agent): ?>
                                <option value="<?php echo esc_attr($agent['id']); ?>">
                                    <?php echo esc_html($agent['name']); ?>
                                    (<?php echo esc_html($agent['email']); ?>)
                                </option>
                            <?php endforeach; ?>
                        </select>
                    </div>

                    <div class="os-form-buttons">
                        <button type="button" id="generate-agent-token-btn" class="latepoint-btn latepoint-btn-primary" disabled>
                            <?php _e('Сгенерировать ссылку', 'latepoint-telegram'); ?>
                        </button>
                    </div>

                    <div id="agent-token-result" style="margin-top: 30px; display: none;">
                        <!-- Результат будет вставлен сюда через JS -->
                    </div>
                </div>
            </div>

        <?php elseif ($active_tab === 'bindings-list'): ?>
            <!-- ВКЛАДКА: Список привязок -->
            <div class="os-widget">
                <div class="os-widget-header">
                    <h3><?php _e('Список привязок Telegram ↔ Агент', 'latepoint-telegram'); ?></h3>
                </div>
                <div class="os-widget-body">
                    <div id="bindings-list-container">
                        <p><?php _e('Загрузка...', 'latepoint-telegram'); ?></p>
                    </div>
                </div>
            </div>

        <?php endif; ?>

    </div>
</div>

<script>
jQuery(document).ready(function($) {

    // === Agent Bindings Tab ===

    // Активация кнопки при выборе агента
    $('#agent-select').on('change', function() {
        const agentId = $(this).val();
        $('#generate-agent-token-btn').prop('disabled', !agentId);
    });

    // Генерация токена для агента
    $('#generate-agent-token-btn').on('click', function() {
        const agentId = $('#agent-select').val();
        if (!agentId) return;

        const btn = $(this);
        btn.prop('disabled', true).text('<?php _e('Генерация...', 'latepoint-telegram'); ?>');

        console.log('Generating token for agent:', agentId);

        $.ajax({
            url: '<?php echo rest_url('latepoint-telegram/v1/agent-token/generate'); ?>',
            method: 'POST',
            data: JSON.stringify({ agent_id: parseInt(agentId) }),
            contentType: 'application/json',
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-WP-Nonce', '<?php echo wp_create_nonce('wp_rest'); ?>');
                console.log('Nonce:', '<?php echo wp_create_nonce('wp_rest'); ?>');
            },
            success: function(response) {
                console.log('Success response:', response);
                if (response.success) {
                    const botLink = response.bot_link;
                    const expiresAt = new Date(response.expires_at).toLocaleString('ru-RU');

                    $('#agent-token-result').html(`
                        <div class="os-form-message-w status-success">
                            <div class="os-form-message-body">
                                <strong><?php _e('Ссылка сгенерирована успешно!', 'latepoint-telegram'); ?></strong>
                                <div style="margin-top: 15px;">
                                    <label style="display: block; margin-bottom: 8px; font-weight: 600;">
                                        <?php _e('Ссылка для регистрации:', 'latepoint-telegram'); ?>
                                    </label>
                                    <div style="background: #fff; padding: 15px; border-radius: 5px; border: 1px solid #c3e6cb; font-family: monospace; font-size: 14px; position: relative; word-break: break-all;">
                                        <a href="${botLink}" target="_blank">${botLink}</a>
                                        <button type="button"
                                                onclick="copyAgentLink('${botLink}')"
                                                class="latepoint-btn latepoint-btn-sm"
                                                style="position: absolute; right: 10px; top: 10px;">
                                            <?php _e('Копировать', 'latepoint-telegram'); ?>
                                        </button>
                                    </div>
                                    <div class="os-form-helper-text" style="margin-top: 10px;">
                                        <?php _e('Действует до:', 'latepoint-telegram'); ?> ${expiresAt}<br>
                                        <?php _e('Отправьте эту ссылку агенту. После перехода по ссылке агент будет получать уведомления о новых записях.', 'latepoint-telegram'); ?>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).show();

                    btn.prop('disabled', false).text('<?php _e('Сгенерировать ещё одну ссылку', 'latepoint-telegram'); ?>');
                } else {
                    alert('<?php _e('Ошибка при генерации ссылки', 'latepoint-telegram'); ?>: ' + (response.message || 'Unknown error'));
                    btn.prop('disabled', false).text('<?php _e('Сгенерировать ссылку', 'latepoint-telegram'); ?>');
                }
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
                console.error('XHR:', xhr);
                console.error('Response:', xhr.responseText);
                alert('<?php _e('Ошибка при генерации ссылки', 'latepoint-telegram'); ?>: ' + xhr.responseText);
                btn.prop('disabled', false).text('<?php _e('Сгенерировать ссылку', 'latepoint-telegram'); ?>');
            }
        });
    });

    // === Bindings List Tab ===

    <?php if ($active_tab === 'bindings-list'): ?>
    loadBindingsList();
    <?php endif; ?>

    function loadBindingsList() {
        $.ajax({
            url: '<?php echo rest_url('latepoint-telegram/v1/agent-bindings'); ?>',
            method: 'GET',
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-WP-Nonce', '<?php echo wp_create_nonce('wp_rest'); ?>');
            },
            success: function(response) {
                if (response.success && response.bindings) {
                    displayBindings(response.bindings);
                } else {
                    $('#bindings-list-container').html('<p><?php _e('Не удалось загрузить список привязок', 'latepoint-telegram'); ?></p>');
                }
            },
            error: function() {
                $('#bindings-list-container').html('<p><?php _e('Ошибка при загрузке списка', 'latepoint-telegram'); ?></p>');
            }
        });
    }

    function displayBindings(bindings) {
        if (bindings.length === 0) {
            $('#bindings-list-container').html('<p><?php _e('Нет активных привязок', 'latepoint-telegram'); ?></p>');
            return;
        }

        let html = '<table class="wp-list-table widefat fixed striped">';
        html += '<thead><tr>';
        html += '<th><?php _e('Агент', 'latepoint-telegram'); ?></th>';
        html += '<th><?php _e('Telegram ID', 'latepoint-telegram'); ?></th>';
        html += '<th><?php _e('Telegram Username', 'latepoint-telegram'); ?></th>';
        html += '<th><?php _e('Имя в Telegram', 'latepoint-telegram'); ?></th>';
        html += '<th><?php _e('Дата привязки', 'latepoint-telegram'); ?></th>';
        html += '<th><?php _e('Действия', 'latepoint-telegram'); ?></th>';
        html += '</tr></thead><tbody>';

        bindings.forEach(function(binding) {
            html += '<tr>';
            html += '<td><strong>' + binding.agent_name + '</strong> (ID: ' + binding.agent_id + ')</td>';
            html += '<td>' + binding.telegram_id + '</td>';
            html += '<td>' + (binding.telegram_username ? '@' + binding.telegram_username : '-') + '</td>';
            html += '<td>' + binding.telegram_name + '</td>';
            html += '<td>' + new Date(binding.used_at).toLocaleString('ru-RU') + '</td>';
            html += '<td><button type="button" class="button button-small unbind-btn" data-telegram-id="' + binding.telegram_id + '"><?php _e('Отвязать', 'latepoint-telegram'); ?></button></td>';
            html += '</tr>';
        });

        html += '</tbody></table>';
        $('#bindings-list-container').html(html);

        // Обработчик отвязки
        $('.unbind-btn').on('click', function() {
            const telegramId = $(this).data('telegram-id');
            if (confirm('<?php _e('Вы уверены, что хотите отвязать этот Telegram аккаунт?', 'latepoint-telegram'); ?>')) {
                unbindTelegram(telegramId);
            }
        });
    }

    function unbindTelegram(telegramId) {
        $.ajax({
            url: '<?php echo rest_url('latepoint-telegram/v1/agent-binding/unbind'); ?>',
            method: 'POST',
            data: JSON.stringify({ telegram_id: telegramId }),
            contentType: 'application/json',
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-WP-Nonce', '<?php echo wp_create_nonce('wp_rest'); ?>');
            },
            success: function(response) {
                if (response.success) {
                    alert('<?php _e('Telegram аккаунт успешно отвязан', 'latepoint-telegram'); ?>');
                    loadBindingsList();
                } else {
                    alert('<?php _e('Ошибка при отвязке', 'latepoint-telegram'); ?>: ' + (response.message || 'Unknown error'));
                }
            },
            error: function() {
                alert('<?php _e('Ошибка при отвязке', 'latepoint-telegram'); ?>');
            }
        });
    }
});

function copyAgentLink(link) {
    navigator.clipboard.writeText(link).then(() => {
        alert('<?php _e('Ссылка скопирована в буфер обмена!', 'latepoint-telegram'); ?>');
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('<?php _e('Ошибка копирования. Скопируйте ссылку вручную.', 'latepoint-telegram'); ?>');
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

.latepoint-btn-primary:disabled {
    background: #ccc;
    cursor: not-allowed;
}

.latepoint-btn-sm {
    padding: 5px 10px;
    font-size: 12px;
}

.os-form-sub-header {
    margin-bottom: 20px;
}

.os-form-sub-header h4 {
    font-size: 15px;
    font-weight: 600;
    margin: 10px 0;
}

.os-form-sub-header p {
    color: #666;
    line-height: 1.6;
}
</style>
