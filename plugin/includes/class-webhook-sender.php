<?php
/**
 * Класс для отправки webhook уведомлений в Telegram бот
 */

if (!defined('ABSPATH')) {
    exit;
}

class LatePoint_Telegram_Webhook_Sender {

    /**
     * Отправка webhook уведомления
     */
    public function send($event_type, $data) {
        $bot_url = get_option('latepoint_telegram_bot_url');
        $webhook_secret = get_option('latepoint_telegram_webhook_secret');

        if (empty($bot_url)) {
            error_log('LatePoint Telegram: Bot URL not configured');
            return false;
        }

        // URL webhook endpoint бота
        $webhook_url = rtrim($bot_url, '/') . '/webhook/notification';

        // Подготовка payload
        $payload = array(
            'event_type' => $event_type,
            'data' => $data,
            'timestamp' => current_time('timestamp'),
            'signature' => $this->generate_signature($data, $webhook_secret),
        );

        // Отправка асинхронного запроса
        $response = wp_remote_post($webhook_url, array(
            'method' => 'POST',
            'timeout' => 10,
            'blocking' => false, // Асинхронная отправка
            'headers' => array(
                'Content-Type' => 'application/json',
                'X-Webhook-Secret' => $webhook_secret,
            ),
            'body' => json_encode($payload),
        ));

        if (is_wp_error($response)) {
            error_log('LatePoint Telegram: Webhook send error: ' . $response->get_error_message());
            return false;
        }

        error_log('LatePoint Telegram: Webhook sent successfully for event: ' . $event_type);
        return true;
    }

    /**
     * Генерация подписи для безопасности
     */
    private function generate_signature($data, $secret) {
        return hash_hmac('sha256', json_encode($data), $secret);
    }
}
