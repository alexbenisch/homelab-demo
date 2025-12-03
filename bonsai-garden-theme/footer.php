    </div><!-- #content -->

    <footer id="colophon" class="site-footer">
        <div class="container">
            <div class="footer-content">
                <?php if (is_active_sidebar('footer-1')) : ?>
                    <div class="footer-section">
                        <?php dynamic_sidebar('footer-1'); ?>
                    </div>
                <?php endif; ?>

                <?php if (is_active_sidebar('footer-2')) : ?>
                    <div class="footer-section">
                        <?php dynamic_sidebar('footer-2'); ?>
                    </div>
                <?php endif; ?>

                <?php if (is_active_sidebar('footer-3')) : ?>
                    <div class="footer-section">
                        <?php dynamic_sidebar('footer-3'); ?>
                    </div>
                <?php else : ?>
                    <div class="footer-section">
                        <h3><?php _e('About Bonsai Garden', 'bonsai-garden'); ?></h3>
                        <p><?php _e('Cultivating beauty and tranquility through the ancient art of bonsai.', 'bonsai-garden'); ?></p>
                    </div>

                    <div class="footer-section">
                        <h3><?php _e('Quick Links', 'bonsai-garden'); ?></h3>
                        <?php
                        wp_nav_menu(array(
                            'theme_location' => 'footer',
                            'menu_id'        => 'footer-menu',
                            'container'      => false,
                            'fallback_cb'    => false,
                        ));
                        ?>
                    </div>

                    <div class="footer-section">
                        <h3><?php _e('Contact', 'bonsai-garden'); ?></h3>
                        <p>
                            <?php _e('Email:', 'bonsai-garden'); ?> <a href="mailto:info@k8s-demo.de">info@k8s-demo.de</a><br>
                            <?php _e('Phone:', 'bonsai-garden'); ?> +49 (0) 123 456789
                        </p>
                    </div>
                <?php endif; ?>
            </div>

            <div class="footer-bottom">
                <p>
                    &copy; <?php echo date('Y'); ?> <?php bloginfo('name'); ?>.
                    <?php _e('All rights reserved.', 'bonsai-garden'); ?>
                    <?php if (function_exists('the_privacy_policy_link')) {
                        the_privacy_policy_link(' | ', '');
                    } ?>
                </p>
            </div>
        </div>
    </footer>
</div><!-- #page -->

<?php wp_footer(); ?>

</body>
</html>
