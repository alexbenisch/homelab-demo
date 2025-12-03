<?php
/**
 * The main template file
 *
 * @package Bonsai_Garden
 */

get_header();
?>

<main id="main" class="site-main">
    <div class="container">
        <div class="content-area">
            <?php
            if (have_posts()) :
                ?>
                <header class="page-header">
                    <?php
                    the_archive_title('<h1 class="page-title">', '</h1>');
                    the_archive_description('<div class="archive-description">', '</div>');
                    ?>
                </header>

                <div class="grid grid-2 mt-4">
                    <?php
                    while (have_posts()) :
                        the_post();
                        ?>
                        <article id="post-<?php the_ID(); ?>" <?php post_class('card'); ?>>
                            <?php if (has_post_thumbnail()) : ?>
                                <a href="<?php the_permalink(); ?>">
                                    <?php the_post_thumbnail('bonsai-card', array('class' => 'card-image')); ?>
                                </a>
                            <?php endif; ?>

                            <div class="card-content">
                                <h2 class="card-title">
                                    <a href="<?php the_permalink(); ?>">
                                        <?php the_title(); ?>
                                    </a>
                                </h2>

                                <div class="entry-meta">
                                    <span class="posted-on">
                                        <?php echo get_the_date(); ?>
                                    </span>
                                    <span class="byline">
                                        <?php _e('by', 'bonsai-garden'); ?> <?php the_author(); ?>
                                    </span>
                                </div>

                                <div class="card-text">
                                    <?php the_excerpt(); ?>
                                </div>

                                <a href="<?php the_permalink(); ?>" class="btn btn-secondary">
                                    <?php _e('Read More', 'bonsai-garden'); ?>
                                </a>
                            </div>
                        </article>
                        <?php
                    endwhile;
                    ?>
                </div>

                <?php
                the_posts_pagination(array(
                    'mid_size'  => 2,
                    'prev_text' => __('&larr; Previous', 'bonsai-garden'),
                    'next_text' => __('Next &rarr;', 'bonsai-garden'),
                ));

            else :
                ?>
                <section class="no-results not-found">
                    <header class="page-header">
                        <h1 class="page-title"><?php _e('Nothing Found', 'bonsai-garden'); ?></h1>
                    </header>

                    <div class="page-content">
                        <p><?php _e('It seems we can\'t find what you\'re looking for. Perhaps searching can help.', 'bonsai-garden'); ?></p>
                        <?php get_search_form(); ?>
                    </div>
                </section>
                <?php
            endif;
            ?>
        </div>
    </div>
</main>

<?php
get_footer();
?>
