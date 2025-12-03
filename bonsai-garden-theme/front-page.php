<?php
/**
 * Template Name: Front Page (Landing Page)
 * Description: Beautiful bonsai garden landing page
 *
 * @package Bonsai_Garden
 */

get_header();
?>

<!-- Hero Section -->
<section class="hero">
    <div class="hero-content">
        <h1><?php echo esc_html(bonsai_get_option('bonsai_hero_title', __('Cultivate Beauty, One Tree at a Time', 'bonsai-garden'))); ?></h1>
        <p><?php echo esc_html(bonsai_get_option('bonsai_hero_subtitle', __('Discover our curated collection of bonsai trees, tools, and expert care guides', 'bonsai-garden'))); ?></p>
        <div class="hero-buttons">
            <a href="<?php echo esc_url(bonsai_get_option('bonsai_hero_button_url', '/shop')); ?>" class="btn btn-primary">
                <?php echo esc_html(bonsai_get_option('bonsai_hero_button_text', __('Explore Our Collection', 'bonsai-garden'))); ?>
            </a>
            <a href="#about" class="btn btn-secondary">
                <?php _e('Learn More', 'bonsai-garden'); ?>
            </a>
        </div>
    </div>
</section>

<!-- Featured Products Section -->
<?php if (class_exists('WooCommerce')) : ?>
<section class="section featured-products">
    <div class="container">
        <div class="section-header text-center">
            <h2><?php _e('Featured Bonsai Trees', 'bonsai-garden'); ?></h2>
            <p><?php _e('Handpicked selections for every skill level', 'bonsai-garden'); ?></p>
        </div>

        <div class="grid grid-3 mt-4">
            <?php
            $args = array(
                'post_type'      => 'product',
                'posts_per_page' => 3,
                'meta_key'       => '_featured',
                'meta_value'     => 'yes',
                'orderby'        => 'date',
                'order'          => 'DESC',
            );

            $featured_products = new WP_Query($args);

            if ($featured_products->have_posts()) :
                while ($featured_products->have_posts()) : $featured_products->the_post();
                    global $product;
                    ?>
                    <div class="card product-card">
                        <?php if (has_post_thumbnail()) : ?>
                            <a href="<?php the_permalink(); ?>">
                                <?php the_post_thumbnail('bonsai-card', array('class' => 'card-image')); ?>
                            </a>
                        <?php endif; ?>
                        <div class="card-content">
                            <h3 class="card-title">
                                <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
                            </h3>
                            <p class="card-price"><?php echo $product->get_price_html(); ?></p>
                            <p class="card-text"><?php echo wp_trim_words(get_the_excerpt(), 15); ?></p>
                            <a href="<?php echo esc_url($product->add_to_cart_url()); ?>" class="btn btn-primary">
                                <?php echo esc_html($product->add_to_cart_text()); ?>
                            </a>
                        </div>
                    </div>
                    <?php
                endwhile;
                wp_reset_postdata();
            else :
                ?>
                <p><?php _e('No featured products found.', 'bonsai-garden'); ?></p>
                <?php
            endif;
            ?>
        </div>

        <div class="text-center mt-4">
            <a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>" class="btn btn-secondary">
                <?php _e('View All Products', 'bonsai-garden'); ?>
            </a>
        </div>
    </div>
</section>
<?php endif; ?>

<!-- About Section -->
<section id="about" class="section section-alt about-section">
    <div class="container">
        <div class="grid grid-2">
            <div class="about-content">
                <h2><?php _e('The Art of Bonsai', 'bonsai-garden'); ?></h2>
                <p><?php _e('For centuries, the art of bonsai has been a meditation, a practice of patience, and a celebration of nature\'s beauty in miniature form.', 'bonsai-garden'); ?></p>
                <p><?php _e('At Bonsai Garden, we bring this ancient tradition to your home with carefully curated trees, expert guidance, and everything you need to begin your journey.', 'bonsai-garden'); ?></p>
                <ul class="features-list">
                    <li>✓ <?php _e('Premium quality bonsai trees from experienced growers', 'bonsai-garden'); ?></li>
                    <li>✓ <?php _e('Professional-grade tools and accessories', 'bonsai-garden'); ?></li>
                    <li>✓ <?php _e('Comprehensive care guides for beginners', 'bonsai-garden'); ?></li>
                    <li>✓ <?php _e('Expert support via our AI-powered chatbot', 'bonsai-garden'); ?></li>
                </ul>
                <a href="/about" class="btn btn-accent">
                    <?php _e('Our Story', 'bonsai-garden'); ?>
                </a>
            </div>
            <div class="about-image">
                <div class="image-placeholder" style="background: linear-gradient(135deg, #2d5016 0%, #4a7c25 100%); height: 400px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.2rem;">
                    <?php _e('Bonsai Garden Image', 'bonsai-garden'); ?>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Categories Section -->
<section class="section categories-section">
    <div class="container">
        <div class="section-header text-center">
            <h2><?php _e('Shop by Category', 'bonsai-garden'); ?></h2>
            <p><?php _e('Find exactly what you need to grow your collection', 'bonsai-garden'); ?></p>
        </div>

        <div class="grid grid-4 mt-4">
            <?php
            $categories = array(
                array(
                    'title' => __('Live Bonsai Trees', 'bonsai-garden'),
                    'icon'  => '🌳',
                    'link'  => '/product-category/bonsai-trees',
                    'desc'  => __('Juniper, Ficus, Maple, and more', 'bonsai-garden'),
                ),
                array(
                    'title' => __('Tools & Accessories', 'bonsai-garden'),
                    'icon'  => '✂️',
                    'link'  => '/product-category/tools',
                    'desc'  => __('Professional pruning and shaping tools', 'bonsai-garden'),
                ),
                array(
                    'title' => __('Pots & Containers', 'bonsai-garden'),
                    'icon'  => '🏺',
                    'desc'  => __('Beautiful ceramic and traditional pots', 'bonsai-garden'),
                    'link'  => '/product-category/pots',
                ),
                array(
                    'title' => __('Care Guides', 'bonsai-garden'),
                    'icon'  => '📚',
                    'link'  => '/product-category/guides',
                    'desc'  => __('Digital and printed bonsai manuals', 'bonsai-garden'),
                ),
            );

            foreach ($categories as $category) :
                ?>
                <div class="card category-card text-center">
                    <div class="card-content">
                        <div class="category-icon" style="font-size: 4rem; margin-bottom: 1rem;">
                            <?php echo $category['icon']; ?>
                        </div>
                        <h3 class="card-title"><?php echo esc_html($category['title']); ?></h3>
                        <p class="card-text"><?php echo esc_html($category['desc']); ?></p>
                        <a href="<?php echo esc_url($category['link']); ?>" class="btn btn-secondary">
                            <?php _e('Browse', 'bonsai-garden'); ?>
                        </a>
                    </div>
                </div>
                <?php
            endforeach;
            ?>
        </div>
    </div>
</section>

<!-- Why Choose Us Section -->
<section class="section section-alt why-us-section">
    <div class="container">
        <div class="section-header text-center">
            <h2><?php _e('Why Choose Bonsai Garden?', 'bonsai-garden'); ?></h2>
        </div>

        <div class="grid grid-3 mt-4">
            <?php
            $benefits = array(
                array(
                    'icon'  => '🌱',
                    'title' => __('Healthy & Hardy Trees', 'bonsai-garden'),
                    'desc'  => __('Every tree is carefully inspected and comes with a health guarantee', 'bonsai-garden'),
                ),
                array(
                    'icon'  => '🚚',
                    'title' => __('Safe Delivery', 'bonsai-garden'),
                    'desc'  => __('Expert packaging ensures your bonsai arrives in perfect condition', 'bonsai-garden'),
                ),
                array(
                    'icon'  => '💬',
                    'title' => __('Expert Support', 'bonsai-garden'),
                    'desc'  => __('Get instant answers from our AI chatbot trained on bonsai care', 'bonsai-garden'),
                ),
            );

            foreach ($benefits as $benefit) :
                ?>
                <div class="card benefit-card text-center">
                    <div class="card-content">
                        <div class="benefit-icon" style="font-size: 3rem; margin-bottom: 1rem;">
                            <?php echo $benefit['icon']; ?>
                        </div>
                        <h3 class="card-title"><?php echo esc_html($benefit['title']); ?></h3>
                        <p class="card-text"><?php echo esc_html($benefit['desc']); ?></p>
                    </div>
                </div>
                <?php
            endforeach;
            ?>
        </div>
    </div>
</section>

<!-- CTA Section -->
<section class="section cta-section" style="background: var(--gradient-hero); color: white; text-align: center;">
    <div class="container">
        <h2 style="color: white;"><?php _e('Ready to Start Your Bonsai Journey?', 'bonsai-garden'); ?></h2>
        <p style="font-size: 1.2rem; margin-bottom: 2rem; opacity: 0.95;">
            <?php _e('Join thousands of bonsai enthusiasts worldwide', 'bonsai-garden'); ?>
        </p>
        <a href="/shop" class="btn btn-accent" style="font-size: 1.1rem; padding: 1rem 2.5rem;">
            <?php _e('Shop Now', 'bonsai-garden'); ?>
        </a>
    </div>
</section>

<?php
get_footer();
?>
