<?php
/**
 * Класс REST API для взаимодействия с Telegram ботом
 */

if (!defined('ABSPATH')) {
    exit;
}

class LatePoint_Telegram_API {

    private static $instance = null;
    private $namespace = 'latepoint-telegram/v1';

    /**
     * Получить экземпляр класса (Singleton)
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
        add_action('rest_api_init', array($this, 'register_routes'));
    }

    /**
     * Регистрация REST API маршрутов
     */
    public function register_routes() {
        // Генерация токена регистрации
        register_rest_route($this->namespace, '/generate-token', array(
            'methods' => 'POST',
            'callback' => array($this, 'generate_token'),
            'permission_callback' => array($this, 'check_user_permission'),
        ));

        // Регистрация Telegram chat_id
        register_rest_route($this->namespace, '/register', array(
            'methods' => 'POST',
            'callback' => array($this, 'register_user'),
            'permission_callback' => '__return_true', // Публичный endpoint с проверкой токена внутри
        ));

        // Получение расписания
        register_rest_route($this->namespace, '/schedule', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_schedule'),
            'permission_callback' => array($this, 'verify_bot_request_permission'),
        ));

        // Получение деталей бронирования
        register_rest_route($this->namespace, '/booking/(?P<id>\d+)', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_booking'),
            'permission_callback' => array($this, 'verify_bot_request_permission'),
        ));

        // Обновление статуса бронирования
        register_rest_route($this->namespace, '/booking/(?P<id>\d+)/status', array(
            'methods' => 'POST',
            'callback' => array($this, 'update_booking_status'),
            'permission_callback' => array($this, 'verify_bot_request_permission'),
        ));

        // Получение информации о пользователе по chat_id
        register_rest_route($this->namespace, '/user-info', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_user_info'),
            'permission_callback' => array($this, 'verify_bot_request_permission'),
        ));

        // === Новые эндпоинты для agent tokens ===

        // Генерация токена для агента
        register_rest_route($this->namespace, '/agent-token/generate', array(
            'methods' => 'POST',
            'callback' => array($this, 'generate_agent_token'),
            'permission_callback' => array($this, 'check_admin_permission'),
        ));

        // Получение всех привязок (agent-telegram)
        register_rest_route($this->namespace, '/agent-bindings', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_agent_bindings'),
            'permission_callback' => array($this, 'check_admin_permission'),
        ));

        // Отвязка Telegram аккаунта от агента
        register_rest_route($this->namespace, '/agent-binding/unbind', array(
            'methods' => 'POST',
            'callback' => array($this, 'unbind_agent_telegram'),
            'permission_callback' => array($this, 'check_admin_permission'),
        ));

        // Подтверждение использования токена (вызывается ботом)
        register_rest_route($this->namespace, '/agent-token/confirm', array(
            'methods' => 'POST',
            'callback' => array($this, 'confirm_agent_token'),
            'permission_callback' => array($this, 'verify_webhook_secret'),
        ));

        // Получение telegram_ids для агента (для отправки уведомлений)
        register_rest_route($this->namespace, '/agent-telegram-ids/(?P<agent_id>\d+)', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_agent_telegram_ids'),
            'permission_callback' => array($this, 'verify_webhook_secret'),
        ));
    }

    /**
     * Проверка прав пользователя
     */
    public function check_user_permission() {
        return is_user_logged_in();
    }

    /**
     * Проверка прав доступа к API (для запросов от бота)
     * Проверяет что chat_id зарегистрирован в системе
     */
    public function verify_bot_request_permission($request) {
        // Проверка через webhook secret для внутренних запросов
        $webhook_secret = $request->get_header('X-Webhook-Secret');
        $stored_secret = get_option('latepoint_telegram_webhook_secret');

        if ($webhook_secret && $webhook_secret === $stored_secret) {
            return true;
        }

        // Проверка что chat_id зарегистрирован
        $chat_id = $request->get_param('chat_id');
        if (empty($chat_id)) {
            return false;
        }

        // Проверить что этот chat_id существует в системе
        $users = get_users(array(
            'meta_key' => 'telegram_chat_id',
            'meta_value' => $chat_id,
        ));

        return !empty($users);
    }

    /**
     * Генерация токена для регистрации в боте
     */
    public function generate_token($request) {
        $user_id = get_current_user_id();

        // Генерация уникального токена
        $token = bin2hex(random_bytes(16));
        $expires_at = time() + (15 * 60); // Токен действителен 15 минут

        // Сохранение токена
        update_user_meta($user_id, 'telegram_registration_token', $token);
        update_user_meta($user_id, 'telegram_registration_token_expires', $expires_at);

        return new WP_REST_Response(array(
            'success' => true,
            'token' => $token,
            'expires_at' => $expires_at,
            'expires_in' => 900,
        ), 200);
    }

    /**
     * Регистрация пользователя (связывание chat_id с пользователем)
     */
    public function register_user($request) {
        $token = $request->get_param('token');
        $chat_id = $request->get_param('chat_id');
        $username = $request->get_param('username');

        if (empty($token) || empty($chat_id)) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'Token and chat_id are required',
            ), 400);
        }

        // Поиск пользователя по токену
        $users = get_users(array(
            'meta_key' => 'telegram_registration_token',
            'meta_value' => $token,
        ));

        if (empty($users)) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'Invalid token',
            ), 404);
        }

        $user = $users[0];
        $expires_at = get_user_meta($user->ID, 'telegram_registration_token_expires', true);

        // Проверка срока действия токена
        if (time() > $expires_at) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'Token expired',
            ), 401);
        }

        // Сохранение chat_id
        update_user_meta($user->ID, 'telegram_chat_id', $chat_id);
        update_user_meta($user->ID, 'telegram_username', $username);
        update_user_meta($user->ID, 'telegram_registered_at', current_time('mysql'));

        // Удаление токена
        delete_user_meta($user->ID, 'telegram_registration_token');
        delete_user_meta($user->ID, 'telegram_registration_token_expires');

        // Определение типа пользователя (agent или customer)
        $user_type = $this->get_user_type($user->ID);

        return new WP_REST_Response(array(
            'success' => true,
            'user_id' => $user->ID,
            'user_type' => $user_type,
            'name' => $user->display_name,
            'email' => $user->user_email,
        ), 200);
    }

    /**
     * Получение расписания пользователя
     */
    public function get_schedule($request) {
        $chat_id = $request->get_param('chat_id');
        $period = $request->get_param('period'); // 'today' или 'week'
        $date_from = $request->get_param('date_from');
        $date_to = $request->get_param('date_to');

        if (empty($chat_id)) {
            return new WP_REST_Response(array('success' => false, 'message' => 'chat_id required'), 400);
        }

        // Поиск пользователя по chat_id
        $user = $this->get_user_by_chat_id($chat_id);
        if (!$user) {
            return new WP_REST_Response(array('success' => false, 'message' => 'User not found'), 404);
        }

        // Определение периода
        if ($period === 'today') {
            $date_from = current_time('Y-m-d');
            $date_to = $date_from;
        } elseif ($period === 'week') {
            $date_from = current_time('Y-m-d');
            $date_to = date('Y-m-d', strtotime('+7 days'));
        }

        // Получение бронирований
        $bookings = $this->get_user_bookings($user->ID, $date_from, $date_to);

        return new WP_REST_Response(array(
            'success' => true,
            'bookings' => $bookings,
            'period' => array(
                'from' => $date_from,
                'to' => $date_to,
            ),
        ), 200);
    }

    /**
     * Получение деталей бронирования
     */
    public function get_booking($request) {
        $booking_id = $request->get_param('id');
        $chat_id = $request->get_param('chat_id');

        if (empty($chat_id)) {
            return new WP_REST_Response(array('success' => false, 'message' => 'chat_id required'), 400);
        }

        // Загрузка бронирования
        $booking = new OsBookingModel($booking_id);
        if (!$booking->id) {
            return new WP_REST_Response(array('success' => false, 'message' => 'Booking not found'), 404);
        }

        // Получение полных данных
        $booking_data = $this->format_booking_data($booking);

        return new WP_REST_Response(array(
            'success' => true,
            'booking' => $booking_data,
        ), 200);
    }

    /**
     * Обновление статуса бронирования
     */
    public function update_booking_status($request) {
        $booking_id = $request->get_param('id');
        $new_status = $request->get_param('status');
        $chat_id = $request->get_param('chat_id');

        if (empty($chat_id) || empty($new_status)) {
            return new WP_REST_Response(array('success' => false, 'message' => 'chat_id and status required'), 400);
        }

        // Проверка прав доступа
        $user = $this->get_user_by_chat_id($chat_id);
        if (!$user) {
            return new WP_REST_Response(array('success' => false, 'message' => 'User not found'), 404);
        }

        // Загрузка бронирования
        $booking = new OsBookingModel($booking_id);
        if (!$booking->id) {
            return new WP_REST_Response(array('success' => false, 'message' => 'Booking not found'), 404);
        }

        // Проверка что пользователь имеет право изменять это бронирование
        $user_type = $this->get_user_type($user->ID);
        $has_permission = false;

        if ($user_type === 'agent') {
            $agent = $this->get_agent_by_wp_user_id($user->ID);
            if ($agent && $agent->id == $booking->agent_id) {
                $has_permission = true;
            }
        } elseif ($user_type === 'customer') {
            $customer = $this->get_customer_by_wp_user_id($user->ID);
            if ($customer && $customer->id == $booking->customer_id) {
                $has_permission = true;
            }
        }

        if (!$has_permission) {
            return new WP_REST_Response(array('success' => false, 'message' => 'Permission denied'), 403);
        }

        // Обновление статуса
        $booking->status = $new_status;
        if ($booking->save()) {
            return new WP_REST_Response(array(
                'success' => true,
                'booking_id' => $booking->id,
                'new_status' => $new_status,
            ), 200);
        } else {
            return new WP_REST_Response(array('success' => false, 'message' => 'Failed to update status'), 500);
        }
    }

    /**
     * Получение информации о пользователе
     */
    public function get_user_info($request) {
        $chat_id = $request->get_param('chat_id');

        if (empty($chat_id)) {
            return new WP_REST_Response(array('success' => false, 'message' => 'chat_id required'), 400);
        }

        $user = $this->get_user_by_chat_id($chat_id);
        if (!$user) {
            return new WP_REST_Response(array('success' => false, 'message' => 'User not found'), 404);
        }

        $user_type = $this->get_user_type($user->ID);
        $latepoint_id = null;

        if ($user_type === 'agent') {
            $agent = $this->get_agent_by_wp_user_id($user->ID);
            $latepoint_id = $agent ? $agent->id : null;
        } elseif ($user_type === 'customer') {
            $customer = $this->get_customer_by_wp_user_id($user->ID);
            $latepoint_id = $customer ? $customer->id : null;
        }

        return new WP_REST_Response(array(
            'success' => true,
            'user_type' => $user_type,
            'wp_user_id' => $user->ID,
            'latepoint_id' => $latepoint_id,
            'name' => $user->display_name,
            'email' => $user->user_email,
        ), 200);
    }

    /**
     * Получение пользователя по chat_id
     */
    private function get_user_by_chat_id($chat_id) {
        $users = get_users(array(
            'meta_key' => 'telegram_chat_id',
            'meta_value' => $chat_id,
        ));

        return !empty($users) ? $users[0] : false;
    }

    /**
     * Определение типа пользователя
     */
    private function get_user_type($user_id) {
        // Проверка на агента
        $agent = $this->get_agent_by_wp_user_id($user_id);
        if ($agent) {
            return 'agent';
        }

        // Проверка на клиента
        $customer = $this->get_customer_by_wp_user_id($user_id);
        if ($customer) {
            return 'customer';
        }

        return 'unknown';
    }

    /**
     * Получение агента по WordPress user_id
     */
    private function get_agent_by_wp_user_id($user_id) {
        global $wpdb;
        $table = $wpdb->prefix . 'latepoint_agents';
        $agent_data = $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM {$table} WHERE wp_user_id = %d",
            $user_id
        ));

        return $agent_data ? new OsAgentModel($agent_data->id) : false;
    }

    /**
     * Получение клиента по WordPress user_id
     */
    private function get_customer_by_wp_user_id($user_id) {
        global $wpdb;
        $table = $wpdb->prefix . 'latepoint_customers';
        $customer_data = $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM {$table} WHERE wordpress_user_id = %d",
            $user_id
        ));

        return $customer_data ? new OsCustomerModel($customer_data->id) : false;
    }

    /**
     * Получение бронирований пользователя
     */
    private function get_user_bookings($user_id, $date_from, $date_to) {
        global $wpdb;
        $bookings_table = $wpdb->prefix . 'latepoint_bookings';

        $user_type = $this->get_user_type($user_id);

        if ($user_type === 'agent') {
            $agent = $this->get_agent_by_wp_user_id($user_id);
            $sql = $wpdb->prepare(
                "SELECT * FROM {$bookings_table}
                WHERE agent_id = %d
                AND start_date >= %s
                AND start_date <= %s
                AND status IN ('approved', 'pending')
                ORDER BY start_date, start_time",
                $agent->id, $date_from, $date_to
            );
        } elseif ($user_type === 'customer') {
            $customer = $this->get_customer_by_wp_user_id($user_id);
            $sql = $wpdb->prepare(
                "SELECT * FROM {$bookings_table}
                WHERE customer_id = %d
                AND start_date >= %s
                AND start_date <= %s
                AND status IN ('approved', 'pending')
                ORDER BY start_date, start_time",
                $customer->id, $date_from, $date_to
            );
        } else {
            return array();
        }

        $results = $wpdb->get_results($sql);
        $bookings = array();

        foreach ($results as $result) {
            $booking = new OsBookingModel($result->id);
            $bookings[] = $this->format_booking_data($booking);
        }

        return $bookings;
    }

    /**
     * Форматирование данных бронирования
     */
    private function format_booking_data($booking) {
        $customer = new OsCustomerModel($booking->customer_id);
        $agent = new OsAgentModel($booking->agent_id);
        $service = new OsServiceModel($booking->service_id);

        // Получение Google Meet URL
        $google_meet_url = '';
        if (class_exists('OsGoogleCalendarHelper')) {
            $google_meet_url = OsGoogleCalendarHelper::get_google_meet_conference_url_for_booking_id($booking->id);
        }

        return array(
            'id' => $booking->id,
            'booking_code' => $booking->booking_code,
            'status' => $booking->status,
            'start_date' => $booking->start_date,
            'start_time' => $this->format_time($booking->start_time),
            'end_time' => $this->format_time($booking->end_time),
            'duration' => $booking->duration,
            'customer' => array(
                'id' => $customer->id,
                'name' => $customer->first_name . ' ' . $customer->last_name,
                'email' => $customer->email,
                'phone' => $customer->phone,
            ),
            'agent' => array(
                'id' => $agent->id,
                'name' => $agent->first_name . ' ' . $agent->last_name,
                'email' => $agent->email,
                'phone' => $agent->phone,
            ),
            'service' => array(
                'id' => $service->id,
                'name' => $service->name,
            ),
            'google_meet_url' => $google_meet_url,
            'timezone' => $booking->customer_timezone,
        );
    }

    /**
     * Форматирование времени
     */
    private function format_time($minutes) {
        $hours = floor($minutes / 60);
        $mins = $minutes % 60;
        return sprintf('%02d:%02d', $hours, $mins);
    }

    // ========== Agent Token Methods ==========

    /**
     * Проверка прав администратора
     */
    public function check_admin_permission() {
        if (!is_user_logged_in()) {
            return false;
        }

        // Проверяем через LatePoint если доступен
        if (class_exists('OsAuthHelper') && method_exists('OsAuthHelper', 'get_current_user')) {
            $lp_user = OsAuthHelper::get_current_user();
            return $lp_user->has_backend_access();
        }

        // Fallback для обычных админов WordPress
        return current_user_can('manage_options');
    }

    /**
     * Проверка webhook secret
     */
    public function verify_webhook_secret($request) {
        $secret = $request->get_header('X-Webhook-Secret');
        $stored_secret = get_option('latepoint_telegram_webhook_secret');

        return $secret === $stored_secret;
    }

    /**
     * Генерация токена для агента
     * POST /agent-token/generate
     * Body: { "agent_id": 2 }
     */
    public function generate_agent_token($request) {
        try {
            $agent_id = $request->get_param('agent_id');

            error_log('LatePoint Telegram: generate_agent_token called with agent_id=' . $agent_id);

            if (empty($agent_id)) {
                return new WP_REST_Response(array(
                    'success' => false,
                    'message' => 'agent_id is required',
                ), 400);
            }

            $db = LatePoint_Telegram_Database::get_instance();
            $token_data = $db->generate_token($agent_id);

            if (!$token_data) {
                error_log('LatePoint Telegram: Failed to generate token for agent_id=' . $agent_id);
                return new WP_REST_Response(array(
                    'success' => false,
                    'message' => 'Failed to generate token. Agent may not exist.',
                ), 500);
            }

            error_log('LatePoint Telegram: Token generated successfully: ' . $token_data['token']);

            // Отправка webhook боту для синхронизации токена
            $this->notify_bot_about_token($token_data);

            return new WP_REST_Response(array(
                'success' => true,
                'token' => $token_data['token'],
                'bot_link' => $token_data['bot_link'],
                'expires_at' => $token_data['expires_at'],
                'agent_id' => $token_data['agent_id'],
            ), 200);
        } catch (Exception $e) {
            error_log('LatePoint Telegram: Exception in generate_agent_token: ' . $e->getMessage());
            error_log('LatePoint Telegram: Stack trace: ' . $e->getTraceAsString());
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'Internal error: ' . $e->getMessage(),
            ), 500);
        }
    }

    /**
     * Получение всех привязок agent-telegram
     * GET /agent-bindings
     */
    public function get_agent_bindings($request) {
        $db = LatePoint_Telegram_Database::get_instance();
        $bindings = $db->get_all_bindings();

        $formatted = array();
        foreach ($bindings as $binding) {
            $telegram_name = trim(($binding->telegram_first_name ?? '') . ' ' . ($binding->telegram_last_name ?? ''));
            if (empty($telegram_name)) {
                $telegram_name = $binding->telegram_username ?? 'Unknown';
            }

            $agent_name = trim(($binding->agent_first_name ?? '') . ' ' . ($binding->agent_last_name ?? ''));

            $formatted[] = array(
                'id' => $binding->id,
                'agent_id' => $binding->agent_id,
                'agent_name' => $agent_name,
                'telegram_id' => $binding->telegram_id,
                'telegram_username' => $binding->telegram_username,
                'telegram_name' => $telegram_name,
                'created_at' => $binding->created_at,
                'used_at' => $binding->used_at,
            );
        }

        return new WP_REST_Response(array(
            'success' => true,
            'bindings' => $formatted,
        ), 200);
    }

    /**
     * Отвязка Telegram аккаунта
     * POST /agent-binding/unbind
     * Body: { "telegram_id": 12345 }
     */
    public function unbind_agent_telegram($request) {
        $telegram_id = $request->get_param('telegram_id');

        if (empty($telegram_id)) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'telegram_id is required',
            ), 400);
        }

        $db = LatePoint_Telegram_Database::get_instance();
        $success = $db->unbind_telegram($telegram_id);

        if (!$success) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'Failed to unbind telegram account',
            ), 500);
        }

        // Уведомить бота об отвязке
        $this->notify_bot_about_unbind($telegram_id);

        return new WP_REST_Response(array(
            'success' => true,
            'message' => 'Telegram account unbound successfully',
        ), 200);
    }

    /**
     * Подтверждение использования токена (вызывается ботом)
     * POST /agent-token/confirm
     * Body: { "token": "...", "telegram_id": 12345, "telegram_data": {...} }
     */
    public function confirm_agent_token($request) {
        $token = $request->get_param('token');
        $telegram_id = $request->get_param('telegram_id');
        $telegram_data = $request->get_param('telegram_data') ?? array();

        if (empty($token) || empty($telegram_id)) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'token and telegram_id are required',
            ), 400);
        }

        $db = LatePoint_Telegram_Database::get_instance();

        // Получить токен
        $token_obj = $db->get_token($token);
        if (!$token_obj) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'Invalid token',
            ), 404);
        }

        // Проверить статус и срок действия
        if ($token_obj->status !== 'pending') {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'Token already used or revoked',
            ), 400);
        }

        if (strtotime($token_obj->expires_at) < time()) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'Token expired',
            ), 400);
        }

        // Отвязать предыдущую привязку этого telegram_id (если есть)
        $db->unbind_telegram($telegram_id);

        // Пометить токен как использованный
        $success = $db->mark_token_used($token, $telegram_id, $telegram_data);

        if (!$success) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'Failed to mark token as used',
            ), 500);
        }

        // Получить информацию об агенте
        $agent = new OsAgentModel($token_obj->agent_id);

        return new WP_REST_Response(array(
            'success' => true,
            'agent_id' => $token_obj->agent_id,
            'agent_name' => $agent->first_name . ' ' . $agent->last_name,
        ), 200);
    }

    /**
     * Получение telegram_ids для агента
     * GET /agent-telegram-ids/{agent_id}
     */
    public function get_agent_telegram_ids($request) {
        $agent_id = $request->get_param('agent_id');

        $db = LatePoint_Telegram_Database::get_instance();
        $telegram_ids = $db->get_agent_bindings($agent_id);

        return new WP_REST_Response(array(
            'success' => true,
            'agent_id' => $agent_id,
            'telegram_ids' => $telegram_ids,
        ), 200);
    }

    /**
     * Уведомить бота о новом токене
     */
    private function notify_bot_about_token($token_data) {
        $bot_url = get_option('latepoint_telegram_bot_url');
        if (empty($bot_url)) {
            return;
        }

        $webhook_url = trailingslashit($bot_url) . 'api/agent-token';

        wp_remote_post($webhook_url, array(
            'headers' => array(
                'Content-Type' => 'application/json',
                'X-Webhook-Secret' => get_option('latepoint_telegram_webhook_secret'),
            ),
            'body' => json_encode(array(
                'token' => $token_data['token'],
                'agent_id' => $token_data['agent_id'],
                'expires_at' => $token_data['expires_at'],
            )),
            'timeout' => 10,
        ));
    }

    /**
     * Уведомить бота об отвязке
     */
    private function notify_bot_about_unbind($telegram_id) {
        $bot_url = get_option('latepoint_telegram_bot_url');
        if (empty($bot_url)) {
            return;
        }

        $webhook_url = trailingslashit($bot_url) . 'api/unbind/' . $telegram_id;

        wp_remote_request($webhook_url, array(
            'method' => 'DELETE',
            'headers' => array(
                'X-Webhook-Secret' => get_option('latepoint_telegram_webhook_secret'),
            ),
            'timeout' => 10,
        ));
    }
}
