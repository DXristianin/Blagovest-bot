<?php
/**
 * Plugin Name: LatePoint Telegram Notifications
 * Plugin URI: https://blagovest.net
 * Description: Интеграция LatePoint с Telegram ботом для уведомлений учителей и учеников
 * Version: 1.0.0
 * Author: Blagovest
 * Author URI: https://blagovest.net
 * Text Domain: latepoint-telegram
 * Requires at least: 5.0
 * Requires PHP: 7.4
 */

// Запретить прямой доступ к файлу
if (!defined('ABSPATH')) {
    exit;
}

// Константы плагина
define('LATEPOINT_TELEGRAM_VERSION', '1.0.0');
define('LATEPOINT_TELEGRAM_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('LATEPOINT_TELEGRAM_PLUGIN_URL', plugin_dir_url(__FILE__));

/**
 * Основной класс плагина
 */
class LatePoint_Telegram {

    private static $instance = null;

    /**
     * Получить экземпляр плагина (Singleton)
     */
    public static function get_instance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    /**
     * Конструктор
     */
    private function __construct() {
        $this->load_dependencies();
        $this->init_hooks();
    }

    /**
     * Загрузка зависимостей
     */
    private function load_dependencies() {
        require_once LATEPOINT_TELEGRAM_PLUGIN_DIR . 'includes/class-database.php';
        require_once LATEPOINT_TELEGRAM_PLUGIN_DIR . 'includes/class-hooks.php';
        require_once LATEPOINT_TELEGRAM_PLUGIN_DIR . 'includes/class-api.php';
        require_once LATEPOINT_TELEGRAM_PLUGIN_DIR . 'includes/class-webhook-sender.php';
    }

    /**
     * Инициализация хуков
     */
    private function init_hooks() {
        // Хук активации плагина
        register_activation_hook(__FILE__, array($this, 'activate'));

        // Хук деактивации плагина
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));

        // Инициализация компонентов
        add_action('plugins_loaded', array($this, 'init'));

        // Добавление меню в админке (приоритет 20, чтобы LatePoint загрузился первым)
        add_action('admin_menu', array($this, 'add_admin_menu'), 20);

        // Регистрация настроек
        add_action('admin_init', array($this, 'register_settings'));
    }

    /**
     * Инициализация плагина
     */
    public function init() {
        // Проверка что LatePoint активен
        if (!class_exists('OsBookingModel')) {
            add_action('admin_notices', array($this, 'latepoint_missing_notice'));
            return;
        }

        // Инициализация компонентов
        LatePoint_Telegram_Hooks::get_instance();
        LatePoint_Telegram_API::get_instance();
    }

    /**
     * Уведомление об отсутствии LatePoint
     */
    public function latepoint_missing_notice() {
        ?>
        <div class="notice notice-error">
            <p><?php _e('LatePoint Telegram требует установленный и активированный плагин LatePoint!', 'latepoint-telegram'); ?></p>
        </div>
        <?php
    }

    /**
     * Активация плагина
     */
    public function activate() {
        // Создание опций по умолчанию
        if (!get_option('latepoint_telegram_bot_token')) {
            add_option('latepoint_telegram_bot_token', '');
        }
        if (!get_option('latepoint_telegram_bot_url')) {
            add_option('latepoint_telegram_bot_url', '');
        }
        if (!get_option('latepoint_telegram_bot_username')) {
            add_option('latepoint_telegram_bot_username', 'blagovestnet_bot');
        }
        if (!get_option('latepoint_telegram_webhook_secret')) {
            add_option('latepoint_telegram_webhook_secret', bin2hex(random_bytes(32)));
        }

        // Создание таблицы для токенов
        LatePoint_Telegram_Database::get_instance()->create_table();

        // Очистка rewrite rules
        flush_rewrite_rules();
    }

    /**
     * Деактивация плагина
     */
    public function deactivate() {
        flush_rewrite_rules();
    }

    /**
     * Добавление меню в админке
     */
    public function add_admin_menu() {
        // Используем тот же метод определения capability что и LatePoint
        if (class_exists('OsAuthHelper') && method_exists('OsAuthHelper', 'get_current_user')) {
            $lp_user = OsAuthHelper::get_current_user();
            $capability = $lp_user->wp_capability ? $lp_user->wp_capability : 'manage_options';
        } else {
            // Fallback если LatePoint не загружен
            $capability = 'manage_options';
        }

        add_submenu_page(
            'latepoint',
            __('Telegram Integration', 'latepoint-telegram'),
            __('Telegram', 'latepoint-telegram'),
            $capability,
            'latepoint-telegram',
            array($this, 'render_admin_page')
        );
    }

    /**
     * Регистрация настроек
     */
    public function register_settings() {
        register_setting('latepoint_telegram_options', 'latepoint_telegram_bot_token');
        register_setting('latepoint_telegram_options', 'latepoint_telegram_bot_url');
        register_setting('latepoint_telegram_options', 'latepoint_telegram_bot_username');
        register_setting('latepoint_telegram_options', 'latepoint_telegram_webhook_secret');
    }

    /**
     * Отрисовка страницы настроек
     */
    public function render_admin_page() {
        // Дополнительная проверка прав доступа
        $has_access = false;

        if (class_exists('OsAuthHelper') && method_exists('OsAuthHelper', 'get_current_user')) {
            $lp_user = OsAuthHelper::get_current_user();
            $has_access = $lp_user->has_backend_access();
        } else {
            // Fallback для администраторов
            $has_access = current_user_can('manage_options');
        }

        if (!$has_access) {
            wp_die(__('У вас нет прав для доступа к этой странице.', 'latepoint-telegram'));
        }

        require_once LATEPOINT_TELEGRAM_PLUGIN_DIR . 'admin/settings-page-new.php';
    }
}

/**
 * Запуск плагина
 */
function latepoint_telegram_init() {
    return LatePoint_Telegram::get_instance();
}

// Инициализация плагина
latepoint_telegram_init();
