<?php
/**
 * The template for displaying WooCommerce pages
 *
 * @package Bonsai_Garden
 */

get_header();
?>

<div class="container woocommerce-container">
    <main id="main" class="site-main">
        <?php woocommerce_content(); ?>
    </main>
</div>

<?php
get_footer();
?>
