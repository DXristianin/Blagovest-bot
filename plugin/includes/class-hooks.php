<?php
/**
 * Класс для обработки LatePoint hooks
 */

if (!defined('ABSPATH')) {
    exit;
}

class LatePoint_Telegram_Hooks {

    private static $instance = null;

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
        $this->init_hooks();
    }

    /**
     * Регистрация hooks
     */
    private function init_hooks() {
        // Hooks для бронирований
        add_action('latepoint_booking_created', array($this, 'on_booking_created'), 10, 1);
        add_action('latepoint_booking_updated', array($this, 'on_booking_updated'), 10, 2);
        add_action('latepoint_booking_change_status', array($this, 'on_booking_status_changed'), 10, 2);

        // Hook для добавления поля Telegram в профили
        add_action('latepoint_agent_edit_form', array($this, 'add_telegram_field_to_agent_form'), 10, 1);
        add_action('latepoint_customer_edit_form', array($this, 'add_telegram_field_to_customer_form'), 10, 1);
    }

    /**
     * Обработка создания бронирования
     */
    public function on_booking_created($booking) {
        error_log('LatePoint Telegram: Booking created #' . $booking->id);

        try {
            // Получение данных бронирования
            $booking_data = $this->get_booking_data($booking);

            if (!$booking_data) {
                error_log('LatePoint Telegram: Failed to get booking data for #' . $booking->id);
                return;
            }

            // Отправка уведомлений
            $this->send_notification('booking_created', $booking_data);
        } catch (Exception $e) {
            error_log('LatePoint Telegram: Error processing booking_created: ' . $e->getMessage());
        }
    }

    /**
     * Обработка обновления бронирования
     */
    public function on_booking_updated($booking, $old_booking) {
        error_log('LatePoint Telegram: Booking updated #' . $booking->id);

        try {
            // Проверяем, что изменилось
            $changes = $this->detect_booking_changes($booking, $old_booking);

            if (empty($changes)) {
                return; // Нет значимых изменений
            }

            // Получение данных бронирования
            $booking_data = $this->get_booking_data($booking);
            $booking_data['changes'] = $changes;

            // Отправка уведомлений
            $this->send_notification('booking_updated', $booking_data);
        } catch (Exception $e) {
            error_log('LatePoint Telegram: Error processing booking_updated: ' . $e->getMessage());
        }
    }

    /**
     * Обработка изменения статуса бронирования
     */
    public function on_booking_status_changed($booking, $old_booking) {
        error_log('LatePoint Telegram: Booking status changed #' . $booking->id . ' from ' . $old_booking->status . ' to ' . $booking->status);

        try {
            // Получение данных бронирования
            $booking_data = $this->get_booking_data($booking);
            $booking_data['old_status'] = $old_booking->status;
            $booking_data['new_status'] = $booking->status;

            // Отправка уведомлений
            $this->send_notification('booking_status_changed', $booking_data);
        } catch (Exception $e) {
            error_log('LatePoint Telegram: Error processing booking_status_changed: ' . $e->getMessage());
        }
    }

    /**
     * Получение данных бронирования
     */
    private function get_booking_data($booking) {
        try {
            // Загрузка связанных объектов
            $customer = new OsCustomerModel($booking->customer_id);
            $agent = new OsAgentModel($booking->agent_id);
            $service = new OsServiceModel($booking->service_id);

            // Получение Telegram chat_id
            $agent_telegram = $this->get_telegram_chat_id('agent', $booking->agent_id);
            $customer_telegram = $this->get_telegram_chat_id('customer', $booking->customer_id);

            // Получение Google Meet URL
            $google_meet_url = '';
            if (class_exists('OsGoogleCalendarHelper')) {
                $google_meet_url = OsGoogleCalendarHelper::get_google_meet_conference_url_for_booking_id($booking->id);
            }

            // Формирование данных
            $data = array(
                'booking_id' => $booking->id,
                'booking_code' => $booking->booking_code,
                'status' => $booking->status,
                'start_date' => $booking->start_date,
                'start_time' => $this->format_time($booking->start_time),
                'end_time' => $this->format_time($booking->end_time),
                'start_datetime_utc' => $booking->start_datetime_utc,
                'end_datetime_utc' => $booking->end_datetime_utc,
                'duration' => $booking->duration,
                'agent_id' => $booking->agent_id,  // Добавляем agent_id для новой системы привязок
                'customer_id' => $booking->customer_id,
                'customer' => array(
                    'id' => $customer->id,
                    'name' => $customer->first_name . ' ' . $customer->last_name,
                    'email' => $customer->email,
                    'phone' => $customer->phone,
                    'telegram_chat_id' => $customer_telegram,
                    'timezone' => $booking->customer_timezone,
                ),
                'agent' => array(
                    'id' => $agent->id,
                    'name' => $agent->first_name . ' ' . $agent->last_name,
                    'email' => $agent->email,
                    'phone' => $agent->phone,
                    'telegram_chat_id' => $agent_telegram,
                ),
                'service' => array(
                    'id' => $service->id,
                    'name' => $service->name,
                    'duration' => $service->duration,
                ),
                'google_meet_url' => $google_meet_url,
            );

            return $data;
        } catch (Exception $e) {
            error_log('LatePoint Telegram: Error getting booking data: ' . $e->getMessage());
            return false;
        }
    }

    /**
     * Определение изменений в бронировании
     */
    private function detect_booking_changes($booking, $old_booking) {
        $changes = array();

        if ($booking->start_date != $old_booking->start_date) {
            $changes['start_date'] = array(
                'old' => $old_booking->start_date,
                'new' => $booking->start_date,
            );
        }

        if ($booking->start_time != $old_booking->start_time) {
            $changes['start_time'] = array(
                'old' => $this->format_time($old_booking->start_time),
                'new' => $this->format_time($booking->start_time),
            );
        }

        if ($booking->end_time != $old_booking->end_time) {
            $changes['end_time'] = array(
                'old' => $this->format_time($old_booking->end_time),
                'new' => $this->format_time($booking->end_time),
            );
        }

        if ($booking->agent_id != $old_booking->agent_id) {
            $changes['agent'] = array(
                'old' => $old_booking->agent_id,
                'new' => $booking->agent_id,
            );
        }

        return $changes;
    }

    /**
     * Получение Telegram chat_id пользователя
     */
    private function get_telegram_chat_id($user_type, $user_id) {
        if ($user_type === 'agent') {
            $agent = new OsAgentModel($user_id);
            if ($agent->wp_user_id) {
                return get_user_meta($agent->wp_user_id, 'telegram_chat_id', true);
            }
        } elseif ($user_type === 'customer') {
            $customer = new OsCustomerModel($user_id);
            if ($customer->wordpress_user_id) {
                return get_user_meta($customer->wordpress_user_id, 'telegram_chat_id', true);
            }
        }

        return '';
    }

    /**
     * Форматирование времени (из минут в HH:MM)
     */
    private function format_time($minutes) {
        $hours = floor($minutes / 60);
        $mins = $minutes % 60;
        return sprintf('%02d:%02d', $hours, $mins);
    }

    /**
     * Отправка уведомления в бот
     */
    private function send_notification($event_type, $data) {
        $webhook_sender = new LatePoint_Telegram_Webhook_Sender();
        $webhook_sender->send($event_type, $data);
    }

    /**
     * Добавление поля Telegram в форму редактирования агента
     */
    public function add_telegram_field_to_agent_form($agent) {
        $telegram_chat_id = '';
        if ($agent->wp_user_id) {
            $telegram_chat_id = get_user_meta($agent->wp_user_id, 'telegram_chat_id', true);
        }
        ?>
        <div class="os-form-group">
            <label for="telegram_chat_id"><?php _e('Telegram Chat ID', 'latepoint-telegram'); ?></label>
            <input type="text"
                   name="telegram_chat_id"
                   id="telegram_chat_id"
                   value="<?php echo esc_attr($telegram_chat_id); ?>"
                   class="os-form-control"
                   readonly />
            <div class="os-form-sub-label">
                <?php _e('Этот ID будет присвоен автоматически после регистрации в Telegram боте', 'latepoint-telegram'); ?>
            </div>
        </div>
        <?php
    }

    /**
     * Добавление поля Telegram в форму редактирования клиента
     */
    public function add_telegram_field_to_customer_form($customer) {
        $telegram_chat_id = '';
        if ($customer->wordpress_user_id) {
            $telegram_chat_id = get_user_meta($customer->wordpress_user_id, 'telegram_chat_id', true);
        }
        ?>
        <div class="os-form-group">
            <label for="telegram_chat_id"><?php _e('Telegram Chat ID', 'latepoint-telegram'); ?></label>
            <input type="text"
                   name="telegram_chat_id"
                   id="telegram_chat_id"
                   value="<?php echo esc_attr($telegram_chat_id); ?>"
                   class="os-form-control"
                   readonly />
            <div class="os-form-sub-label">
                <?php _e('Этот ID будет присвоен автоматически после регистрации в Telegram боте', 'latepoint-telegram'); ?>
            </div>
        </div>
        <?php
    }
}
