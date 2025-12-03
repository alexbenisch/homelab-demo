<?php
/**
 * Bonsai Garden Theme Functions
 *
 * @package Bonsai_Garden
 */

// Exit if accessed directly
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Theme Setup
 */
function bonsai_garden_setup() {
    // Add default posts and comments RSS feed links to head
    add_theme_support('automatic-feed-links');

    // Let WordPress manage the document title
    add_theme_support('title-tag');

    // Enable support for Post Thumbnails
    add_theme_support('post-thumbnails');
    set_post_thumbnail_size(1200, 800, true);

    // Add custom image sizes
    add_image_size('bonsai-hero', 1920, 800, true);
    add_image_size('bonsai-card', 600, 400, true);
    add_image_size('bonsai-thumb', 400, 300, true);

    // Register navigation menus
    register_nav_menus(array(
        'primary' => __('Primary Menu', 'bonsai-garden'),
        'footer' => __('Footer Menu', 'bonsai-garden'),
    ));

    // Switch default core markup to output valid HTML5
    add_theme_support('html5', array(
        'search-form',
        'comment-form',
        'comment-list',
        'gallery',
        'caption',
    ));

    // Add theme support for selective refresh for widgets
    add_theme_support('customize-selective-refresh-widgets');

    // Add support for custom logo
    add_theme_support('custom-logo', array(
        'height'      => 100,
        'width'       => 400,
        'flex-height' => true,
        'flex-width'  => true,
    ));

    // Add support for editor styles
    add_theme_support('editor-styles');
    add_editor_style('style.css');

    // Add support for WooCommerce
    add_theme_support('woocommerce');
    add_theme_support('wc-product-gallery-zoom');
    add_theme_support('wc-product-gallery-lightbox');
    add_theme_support('wc-product-gallery-slider');
}
add_action('after_setup_theme', 'bonsai_garden_setup');

/**
 * Set content width
 */
function bonsai_garden_content_width() {
    $GLOBALS['content_width'] = apply_filters('bonsai_garden_content_width', 1200);
}
add_action('after_setup_theme', 'bonsai_garden_content_width', 0);

/**
 * Register widget areas
 */
function bonsai_garden_widgets_init() {
    register_sidebar(array(
        'name'          => __('Sidebar', 'bonsai-garden'),
        'id'            => 'sidebar-1',
        'description'   => __('Add widgets here to appear in your sidebar.', 'bonsai-garden'),
        'before_widget' => '<div id="%1$s" class="widget %2$s">',
        'after_widget'  => '</div>',
        'before_title'  => '<h3 class="widget-title">',
        'after_title'   => '</h3>',
    ));

    register_sidebar(array(
        'name'          => __('Footer 1', 'bonsai-garden'),
        'id'            => 'footer-1',
        'description'   => __('Add widgets here to appear in your footer.', 'bonsai-garden'),
        'before_widget' => '<div id="%1$s" class="widget %2$s">',
        'after_widget'  => '</div>',
        'before_title'  => '<h3 class="widget-title">',
        'after_title'   => '</h3>',
    ));

    register_sidebar(array(
        'name'          => __('Footer 2', 'bonsai-garden'),
        'id'            => 'footer-2',
        'description'   => __('Add widgets here to appear in your footer.', 'bonsai-garden'),
        'before_widget' => '<div id="%1$s" class="widget %2$s">',
        'after_widget'  => '</div>',
        'before_title'  => '<h3 class="widget-title">',
        'after_title'   => '</h3>',
    ));

    register_sidebar(array(
        'name'          => __('Footer 3', 'bonsai-garden'),
        'id'            => 'footer-3',
        'description'   => __('Add widgets here to appear in your footer.', 'bonsai-garden'),
        'before_widget' => '<div id="%1$s" class="widget %2$s">',
        'after_widget'  => '</div>',
        'before_title'  => '<h3 class="widget-title">',
        'after_title'   => '</h3>',
    ));
}
add_action('widgets_init', 'bonsai_garden_widgets_init');

/**
 * Enqueue scripts and styles
 */
function bonsai_garden_scripts() {
    // Enqueue Google Fonts
    wp_enqueue_style(
        'bonsai-garden-fonts',
        'https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Lora:wght@400;500;600&family=Noto+Sans:wght@400;500;600&display=swap',
        array(),
        null
    );

    // Enqueue main stylesheet
    wp_enqueue_style(
        'bonsai-garden-style',
        get_stylesheet_uri(),
        array(),
        wp_get_theme()->get('Version')
    );

    // Enqueue WooCommerce styles
    if (class_exists('WooCommerce')) {
        wp_enqueue_style(
            'bonsai-garden-woocommerce',
            get_template_directory_uri() . '/assets/css/woocommerce.css',
            array('bonsai-garden-style'),
            wp_get_theme()->get('Version')
        );
    }

    // Enqueue main JavaScript
    wp_enqueue_script(
        'bonsai-garden-script',
        get_template_directory_uri() . '/assets/js/main.js',
        array('jquery'),
        wp_get_theme()->get('Version'),
        true
    );

    // Add comment reply script
    if (is_singular() && comments_open() && get_option('thread_comments')) {
        wp_enqueue_script('comment-reply');
    }
}
add_action('wp_enqueue_scripts', 'bonsai_garden_scripts');

/**
 * Custom excerpt length
 */
function bonsai_garden_excerpt_length($length) {
    return 30;
}
add_filter('excerpt_length', 'bonsai_garden_excerpt_length');

/**
 * Custom excerpt more
 */
function bonsai_garden_excerpt_more($more) {
    return '...';
}
add_filter('excerpt_more', 'bonsai_garden_excerpt_more');

/**
 * Add custom body classes
 */
function bonsai_garden_body_classes($classes) {
    // Add class if WooCommerce is active
    if (class_exists('WooCommerce')) {
        $classes[] = 'woocommerce-active';
    }

    // Add class for page templates
    if (is_page_template('front-page.php')) {
        $classes[] = 'landing-page';
    }

    return $classes;
}
add_filter('body_class', 'bonsai_garden_body_classes');

/**
 * WooCommerce: Declare support for features
 */
function bonsai_garden_woocommerce_support() {
    add_theme_support('woocommerce', array(
        'thumbnail_image_width' => 400,
        'single_image_width'    => 600,
        'product_grid'          => array(
            'default_rows'    => 3,
            'min_rows'        => 2,
            'max_rows'        => 8,
            'default_columns' => 3,
            'min_columns'     => 2,
            'max_columns'     => 4,
        ),
    ));
}
add_action('after_setup_theme', 'bonsai_garden_woocommerce_support');

/**
 * WooCommerce: Remove default wrappers
 */
remove_action('woocommerce_before_main_content', 'woocommerce_output_content_wrapper', 10);
remove_action('woocommerce_after_main_content', 'woocommerce_output_content_wrapper_end', 10);

/**
 * WooCommerce: Add custom wrappers
 */
function bonsai_garden_wrapper_start() {
    echo '<div class="container"><main id="main" class="site-main">';
}
add_action('woocommerce_before_main_content', 'bonsai_garden_wrapper_start', 10);

function bonsai_garden_wrapper_end() {
    echo '</main></div>';
}
add_action('woocommerce_after_main_content', 'bonsai_garden_wrapper_end', 10);

/**
 * Customizer additions
 */
function bonsai_garden_customize_register($wp_customize) {
    // Add hero section
    $wp_customize->add_section('bonsai_hero', array(
        'title'    => __('Hero Section', 'bonsai-garden'),
        'priority' => 30,
    ));

    // Hero title
    $wp_customize->add_setting('bonsai_hero_title', array(
        'default'           => __('Cultivate Beauty, One Tree at a Time', 'bonsai-garden'),
        'sanitize_callback' => 'sanitize_text_field',
    ));

    $wp_customize->add_control('bonsai_hero_title', array(
        'label'   => __('Hero Title', 'bonsai-garden'),
        'section' => 'bonsai_hero',
        'type'    => 'text',
    ));

    // Hero subtitle
    $wp_customize->add_setting('bonsai_hero_subtitle', array(
        'default'           => __('Discover our curated collection of bonsai trees, tools, and expert care guides', 'bonsai-garden'),
        'sanitize_callback' => 'sanitize_textarea_field',
    ));

    $wp_customize->add_control('bonsai_hero_subtitle', array(
        'label'   => __('Hero Subtitle', 'bonsai-garden'),
        'section' => 'bonsai_hero',
        'type'    => 'textarea',
    ));

    // Hero button text
    $wp_customize->add_setting('bonsai_hero_button_text', array(
        'default'           => __('Explore Our Collection', 'bonsai-garden'),
        'sanitize_callback' => 'sanitize_text_field',
    ));

    $wp_customize->add_control('bonsai_hero_button_text', array(
        'label'   => __('Hero Button Text', 'bonsai-garden'),
        'section' => 'bonsai_hero',
        'type'    => 'text',
    ));

    // Hero button URL
    $wp_customize->add_setting('bonsai_hero_button_url', array(
        'default'           => '/shop',
        'sanitize_callback' => 'esc_url_raw',
    ));

    $wp_customize->add_control('bonsai_hero_button_url', array(
        'label'   => __('Hero Button URL', 'bonsai-garden'),
        'section' => 'bonsai_hero',
        'type'    => 'url',
    ));
}
add_action('customize_register', 'bonsai_garden_customize_register');

/**
 * Helper function to get customizer value with default
 */
function bonsai_get_option($option, $default = '') {
    return get_theme_mod($option, $default);
}
