/**
 * Bonsai Garden Theme JavaScript
 */
(function($) {
    'use strict';

    /**
     * Initialize theme
     */
    function initTheme() {
        smoothScrollInit();
        mobileMenuInit();
        cartUpdateInit();
    }

    /**
     * Smooth scroll for anchor links
     */
    function smoothScrollInit() {
        $('a[href*="#"]:not([href="#"])').on('click', function() {
            if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && location.hostname == this.hostname) {
                var target = $(this.hash);
                target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
                if (target.length) {
                    $('html, body').animate({
                        scrollTop: target.offset().top - 80
                    }, 800);
                    return false;
                }
            }
        });
    }

    /**
     * Mobile menu toggle
     */
    function mobileMenuInit() {
        // Add mobile menu button if not exists
        if ($('.mobile-menu-toggle').length === 0 && $(window).width() < 768) {
            $('.header-container').prepend('<button class="mobile-menu-toggle" aria-label="Toggle menu">☰</button>');
        }

        $(document).on('click', '.mobile-menu-toggle', function() {
            $('.main-navigation').slideToggle(300);
        });

        // Close menu on window resize if open
        $(window).on('resize', function() {
            if ($(window).width() >= 768) {
                $('.main-navigation').removeAttr('style');
            }
        });
    }

    /**
     * Update cart count on AJAX add to cart
     */
    function cartUpdateInit() {
        if (typeof wc_add_to_cart_params === 'undefined') {
            return;
        }

        $(document.body).on('added_to_cart', function(event, fragments, cart_hash, $button) {
            // Update cart count
            updateCartCount();
        });
    }

    /**
     * Update cart count display
     */
    function updateCartCount() {
        $.ajax({
            url: wc_add_to_cart_params.wc_ajax_url.toString().replace('%%endpoint%%', 'get_refreshed_fragments'),
            type: 'POST',
            success: function(data) {
                if (data && data.fragments) {
                    $.each(data.fragments, function(key, value) {
                        $(key).replaceWith(value);
                    });
                }
            }
        });
    }

    /**
     * Add to cart button loading state
     */
    $(document).on('click', '.add_to_cart_button', function() {
        $(this).addClass('loading');
    });

    $(document.body).on('added_to_cart', function() {
        $('.add_to_cart_button').removeClass('loading');
    });

    /**
     * Initialize on document ready
     */
    $(document).ready(function() {
        initTheme();
    });

})(jQuery);
