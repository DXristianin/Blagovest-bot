<?php
/**
 * Database management class for LatePoint Telegram
 * Handles agent token storage and bindings
 */

if (!defined('ABSPATH')) {
    exit;
}

class LatePoint_Telegram_Database {

    private static $instance = null;
    private $table_name;
    private $charset_collate;

    /**
     * Get instance (Singleton)
     */
    public static function get_instance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    /**
     * Constructor
     */
    private function __construct() {
        global $wpdb;
        $this->table_name = $wpdb->prefix . 'latepoint_telegram_tokens';
        $this->charset_collate = $wpdb->get_charset_collate();
    }

    /**
     * Create database table
     */
    public function create_table() {
        global $wpdb;

        $sql = "CREATE TABLE IF NOT EXISTS {$this->table_name} (
            id bigint(20) NOT NULL AUTO_INCREMENT,
            token varchar(64) NOT NULL,
            agent_id bigint(20) NOT NULL,
            created_at datetime NOT NULL,
            expires_at datetime NOT NULL,
            status varchar(20) DEFAULT 'pending',
            telegram_id bigint(20) DEFAULT NULL,
            telegram_username varchar(255) DEFAULT NULL,
            telegram_first_name varchar(255) DEFAULT NULL,
            telegram_last_name varchar(255) DEFAULT NULL,
            used_at datetime DEFAULT NULL,
            PRIMARY KEY  (id),
            UNIQUE KEY token (token),
            KEY agent_id (agent_id),
            KEY telegram_id (telegram_id),
            KEY status (status)
        ) {$this->charset_collate};";

        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);
    }

    /**
     * Generate a new token for agent
     *
     * @param int $agent_id LatePoint agent ID
     * @param int $expires_days Days until token expires (default 7)
     * @return array|false Token data or false on failure
     */
    public function generate_token($agent_id, $expires_days = 7) {
        global $wpdb;

        // Verify agent exists
        if (!$this->verify_agent_exists($agent_id)) {
            return false;
        }

        // Generate unique token
        $token = bin2hex(random_bytes(32));

        $data = array(
            'token' => $token,
            'agent_id' => $agent_id,
            'created_at' => current_time('mysql'),
            'expires_at' => date('Y-m-d H:i:s', strtotime("+{$expires_days} days")),
            'status' => 'pending'
        );

        $result = $wpdb->insert($this->table_name, $data);

        if ($result === false) {
            return false;
        }

        return array(
            'id' => $wpdb->insert_id,
            'token' => $token,
            'agent_id' => $agent_id,
            'created_at' => $data['created_at'],
            'expires_at' => $data['expires_at'],
            'bot_link' => $this->get_bot_link($token)
        );
    }

    /**
     * Mark token as used
     *
     * @param string $token Token string
     * @param int $telegram_id Telegram user ID
     * @param array $telegram_data Additional telegram user data
     * @return bool Success
     */
    public function mark_token_used($token, $telegram_id, $telegram_data = array()) {
        global $wpdb;

        $update_data = array(
            'status' => 'used',
            'telegram_id' => $telegram_id,
            'used_at' => current_time('mysql')
        );

        if (!empty($telegram_data['username'])) {
            $update_data['telegram_username'] = $telegram_data['username'];
        }
        if (!empty($telegram_data['first_name'])) {
            $update_data['telegram_first_name'] = $telegram_data['first_name'];
        }
        if (!empty($telegram_data['last_name'])) {
            $update_data['telegram_last_name'] = $telegram_data['last_name'];
        }

        $result = $wpdb->update(
            $this->table_name,
            $update_data,
            array('token' => $token)
        );

        return $result !== false;
    }

    /**
     * Get token data
     *
     * @param string $token Token string
     * @return object|null Token data
     */
    public function get_token($token) {
        global $wpdb;
        return $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM {$this->table_name} WHERE token = %s",
            $token
        ));
    }

    /**
     * Get all bindings (used tokens)
     *
     * @return array Array of binding objects with agent data
     */
    public function get_all_bindings() {
        global $wpdb;

        $query = "SELECT
            t.id,
            t.agent_id,
            t.telegram_id,
            t.telegram_username,
            t.telegram_first_name,
            t.telegram_last_name,
            t.created_at,
            t.used_at,
            a.first_name as agent_first_name,
            a.last_name as agent_last_name
        FROM {$this->table_name} t
        LEFT JOIN {$wpdb->prefix}latepoint_agents a ON t.agent_id = a.id
        WHERE t.status = 'used' AND t.telegram_id IS NOT NULL
        ORDER BY t.used_at DESC";

        return $wpdb->get_results($query);
    }

    /**
     * Get bindings for specific agent
     *
     * @param int $agent_id Agent ID
     * @return array Array of telegram IDs bound to this agent
     */
    public function get_agent_bindings($agent_id) {
        global $wpdb;

        return $wpdb->get_col($wpdb->prepare(
            "SELECT telegram_id FROM {$this->table_name}
            WHERE agent_id = %d AND status = 'used' AND telegram_id IS NOT NULL",
            $agent_id
        ));
    }

    /**
     * Get telegram user's current binding
     *
     * @param int $telegram_id Telegram user ID
     * @return object|null Binding data
     */
    public function get_telegram_binding($telegram_id) {
        global $wpdb;

        return $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM {$this->table_name}
            WHERE telegram_id = %d AND status = 'used'
            ORDER BY used_at DESC
            LIMIT 1",
            $telegram_id
        ));
    }

    /**
     * Unbind telegram account (mark as revoked)
     *
     * @param int $telegram_id Telegram user ID
     * @return bool Success
     */
    public function unbind_telegram($telegram_id) {
        global $wpdb;

        $result = $wpdb->update(
            $this->table_name,
            array('status' => 'revoked'),
            array(
                'telegram_id' => $telegram_id,
                'status' => 'used'
            )
        );

        return $result !== false;
    }

    /**
     * Delete expired tokens (cleanup)
     *
     * @return int Number of deleted tokens
     */
    public function cleanup_expired_tokens() {
        global $wpdb;

        $result = $wpdb->query(
            "DELETE FROM {$this->table_name}
            WHERE status = 'pending' AND expires_at < NOW()"
        );

        return $result;
    }

    /**
     * Verify agent exists in LatePoint
     *
     * @param int $agent_id Agent ID
     * @return bool Agent exists
     */
    private function verify_agent_exists($agent_id) {
        global $wpdb;

        $count = $wpdb->get_var($wpdb->prepare(
            "SELECT COUNT(*) FROM {$wpdb->prefix}latepoint_agents WHERE id = %d",
            $agent_id
        ));

        return $count > 0;
    }

    /**
     * Get bot link for token
     *
     * @param string $token Token string
     * @return string Bot deep link
     */
    private function get_bot_link($token) {
        $bot_username = get_option('latepoint_telegram_bot_username', 'blagovestnet_bot');
        return 'https://t.me/' . $bot_username . '?start=' . $token;
    }

    /**
     * Get table name
     *
     * @return string Table name
     */
    public function get_table_name() {
        return $this->table_name;
    }
}
