<?php
/**
 * Plugin Name: Bonsai Chatbot
 * Plugin URI: https://wordpress.k8s-demo.de
 * Description: Integrates Ollama chatbot with WooCommerce shop for customer support and product inquiries
 * Version: 1.0.0
 * Author: Bonsai Garten
 * Author URI: https://wordpress.k8s-demo.de
 * License: GPL v2 or later
 * Text Domain: bonsai-chatbot
 */

// Exit if accessed directly
if (!defined('ABSPATH')) {
    exit;
}

// Define plugin constants
define('BONSAI_CHATBOT_VERSION', '1.0.0');
define('BONSAI_CHATBOT_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('BONSAI_CHATBOT_PLUGIN_URL', plugin_dir_url(__FILE__));

/**
 * Main plugin class
 */
class Bonsai_Chatbot {

    /**
     * Instance of this class
     */
    private static $instance = null;

    /**
     * Get instance
     */
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    /**
     * Constructor
     */
    private function __construct() {
        $this->init_hooks();
    }

    /**
     * Initialize hooks
     */
    private function init_hooks() {
        // Enqueue scripts and styles
        add_action('wp_enqueue_scripts', array($this, 'enqueue_scripts'));

        // Add chatbot widget to footer
        add_action('wp_footer', array($this, 'render_chatbot_widget'));

        // Register AJAX endpoints
        add_action('wp_ajax_bonsai_chatbot_send_message', array($this, 'ajax_send_message'));
        add_action('wp_ajax_nopriv_bonsai_chatbot_send_message', array($this, 'ajax_send_message'));

        // Add settings page
        add_action('admin_menu', array($this, 'add_settings_page'));
        add_action('admin_init', array($this, 'register_settings'));
    }

    /**
     * Enqueue scripts and styles
     */
    public function enqueue_scripts() {
        // Enqueue CSS
        wp_enqueue_style(
            'bonsai-chatbot-style',
            BONSAI_CHATBOT_PLUGIN_URL . 'assets/css/chatbot.css',
            array(),
            BONSAI_CHATBOT_VERSION
        );

        // Enqueue JavaScript
        wp_enqueue_script(
            'bonsai-chatbot-script',
            BONSAI_CHATBOT_PLUGIN_URL . 'assets/js/chatbot.js',
            array('jquery'),
            BONSAI_CHATBOT_VERSION,
            true
        );

        // Localize script with AJAX URL and nonce
        wp_localize_script('bonsai-chatbot-script', 'bonsaiChatbot', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('bonsai_chatbot_nonce'),
            'welcome_message' => get_option('bonsai_chatbot_welcome_message', 'Hello! How can I help you with our bonsai products today?'),
        ));
    }

    /**
     * Render chatbot widget in footer
     */
    public function render_chatbot_widget() {
        ?>
        <div id="bonsai-chatbot-container">
            <button id="bonsai-chatbot-toggle" aria-label="Open chat">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>

            <div id="bonsai-chatbot-widget" style="display: none;">
                <div class="chatbot-header">
                    <h3>Bonsai Assistant</h3>
                    <button id="bonsai-chatbot-close" aria-label="Close chat">&times;</button>
                </div>

                <div class="chatbot-messages" id="bonsai-chatbot-messages">
                    <!-- Messages will be added here via JavaScript -->
                </div>

                <div class="chatbot-input-container">
                    <input
                        type="text"
                        id="bonsai-chatbot-input"
                        placeholder="Ask about bonsai care, products, shipping..."
                        autocomplete="off"
                    />
                    <button id="bonsai-chatbot-send" aria-label="Send message">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
        <?php
    }

    /**
     * AJAX handler for sending messages to chatbot
     */
    public function ajax_send_message() {
        // Verify nonce
        check_ajax_referer('bonsai_chatbot_nonce', 'nonce');

        $message = isset($_POST['message']) ? sanitize_text_field($_POST['message']) : '';

        if (empty($message)) {
            wp_send_json_error(array('message' => 'Message cannot be empty'));
        }

        // Get plugin settings
        $api_url = get_option('bonsai_chatbot_api_url', 'https://chatbot.k8s-demo.de');
        $api_username = get_option('bonsai_chatbot_api_username', '');
        $api_password = get_option('bonsai_chatbot_api_password', '');
        $use_rag = get_option('bonsai_chatbot_use_rag', '1') === '1';

        // Prepare request
        $endpoint = trailingslashit($api_url) . 'chat';

        $body = array(
            'message' => $message,
            'use_rag' => $use_rag,
            'top_k' => 5,
        );

        // Add system prompt for WooCommerce context
        $system_prompt = "You are a helpful assistant for a bonsai shop. Help customers with product questions, care instructions, shipping information, and orders. Be friendly and knowledgeable about bonsai trees.";
        $body['system_prompt'] = $system_prompt;

        $args = array(
            'method' => 'POST',
            'timeout' => 30,
            'headers' => array(
                'Content-Type' => 'application/json',
            ),
            'body' => json_encode($body),
        );

        // Add HTTP Basic Auth if credentials are provided
        if (!empty($api_username) && !empty($api_password)) {
            $args['headers']['Authorization'] = 'Basic ' . base64_encode($api_username . ':' . $api_password);
        }

        // Make request to chatbot API
        $response = wp_remote_post($endpoint, $args);

        if (is_wp_error($response)) {
            wp_send_json_error(array('message' => 'Failed to connect to chatbot: ' . $response->get_error_message()));
        }

        $response_code = wp_remote_retrieve_response_code($response);
        $response_body = wp_remote_retrieve_body($response);

        if ($response_code !== 200) {
            wp_send_json_error(array('message' => 'Chatbot API error: ' . $response_code));
        }

        $data = json_decode($response_body, true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            wp_send_json_error(array('message' => 'Invalid response from chatbot'));
        }

        // Return chatbot response
        wp_send_json_success(array(
            'response' => isset($data['response']) ? $data['response'] : 'No response from chatbot',
            'sources' => isset($data['sources']) ? $data['sources'] : array(),
            'model' => isset($data['model']) ? $data['model'] : '',
        ));
    }

    /**
     * Add settings page to admin menu
     */
    public function add_settings_page() {
        add_options_page(
            'Bonsai Chatbot Settings',
            'Bonsai Chatbot',
            'manage_options',
            'bonsai-chatbot-settings',
            array($this, 'render_settings_page')
        );
    }

    /**
     * Register plugin settings
     */
    public function register_settings() {
        register_setting('bonsai_chatbot_settings', 'bonsai_chatbot_api_url');
        register_setting('bonsai_chatbot_settings', 'bonsai_chatbot_api_username');
        register_setting('bonsai_chatbot_settings', 'bonsai_chatbot_api_password');
        register_setting('bonsai_chatbot_settings', 'bonsai_chatbot_use_rag');
        register_setting('bonsai_chatbot_settings', 'bonsai_chatbot_welcome_message');
    }

    /**
     * Render settings page
     */
    public function render_settings_page() {
        if (!current_user_can('manage_options')) {
            return;
        }

        // Save settings if form submitted
        if (isset($_POST['submit']) && check_admin_referer('bonsai_chatbot_settings_nonce')) {
            update_option('bonsai_chatbot_api_url', sanitize_text_field($_POST['api_url']));
            update_option('bonsai_chatbot_api_username', sanitize_text_field($_POST['api_username']));
            update_option('bonsai_chatbot_api_password', sanitize_text_field($_POST['api_password']));
            update_option('bonsai_chatbot_use_rag', isset($_POST['use_rag']) ? '1' : '0');
            update_option('bonsai_chatbot_welcome_message', sanitize_text_field($_POST['welcome_message']));
            echo '<div class="notice notice-success"><p>Settings saved successfully!</p></div>';
        }

        $api_url = get_option('bonsai_chatbot_api_url', 'https://chatbot.k8s-demo.de');
        $api_username = get_option('bonsai_chatbot_api_username', '');
        $api_password = get_option('bonsai_chatbot_api_password', '');
        $use_rag = get_option('bonsai_chatbot_use_rag', '1') === '1';
        $welcome_message = get_option('bonsai_chatbot_welcome_message', 'Hello! How can I help you with our bonsai products today?');

        ?>
        <div class="wrap">
            <h1>Bonsai Chatbot Settings</h1>

            <form method="post" action="">
                <?php wp_nonce_field('bonsai_chatbot_settings_nonce'); ?>

                <table class="form-table">
                    <tr>
                        <th scope="row"><label for="api_url">Chatbot API URL</label></th>
                        <td>
                            <input
                                type="url"
                                id="api_url"
                                name="api_url"
                                value="<?php echo esc_attr($api_url); ?>"
                                class="regular-text"
                                required
                            />
                            <p class="description">URL of your Ollama chatbot API (e.g., https://chatbot.k8s-demo.de)</p>
                        </td>
                    </tr>

                    <tr>
                        <th scope="row"><label for="api_username">API Username</label></th>
                        <td>
                            <input
                                type="text"
                                id="api_username"
                                name="api_username"
                                value="<?php echo esc_attr($api_username); ?>"
                                class="regular-text"
                            />
                            <p class="description">HTTP Basic Auth username (if required)</p>
                        </td>
                    </tr>

                    <tr>
                        <th scope="row"><label for="api_password">API Password</label></th>
                        <td>
                            <input
                                type="password"
                                id="api_password"
                                name="api_password"
                                value="<?php echo esc_attr($api_password); ?>"
                                class="regular-text"
                            />
                            <p class="description">HTTP Basic Auth password (if required)</p>
                        </td>
                    </tr>

                    <tr>
                        <th scope="row"><label for="use_rag">Enable RAG (Knowledge Base)</label></th>
                        <td>
                            <input
                                type="checkbox"
                                id="use_rag"
                                name="use_rag"
                                value="1"
                                <?php checked($use_rag, true); ?>
                            />
                            <label for="use_rag">Use retrieval-augmented generation for more accurate responses</label>
                        </td>
                    </tr>

                    <tr>
                        <th scope="row"><label for="welcome_message">Welcome Message</label></th>
                        <td>
                            <input
                                type="text"
                                id="welcome_message"
                                name="welcome_message"
                                value="<?php echo esc_attr($welcome_message); ?>"
                                class="large-text"
                            />
                            <p class="description">Initial message shown when chat opens</p>
                        </td>
                    </tr>
                </table>

                <?php submit_button(); ?>
            </form>
        </div>
        <?php
    }
}

// Initialize plugin
Bonsai_Chatbot::get_instance();
