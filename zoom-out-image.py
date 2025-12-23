#!/usr/bin/env python3
"""
GIMP Script to zoom out an image by 25%
Creates a larger layer behind the original and fills with background color
"""

from gimpfu import *

def zoom_out_image(image, drawable, zoom_percent):
    """
    Zoom out an image by creating a larger canvas and filling empty space

    Args:
        image: The current image
        drawable: The active layer
        zoom_percent: Percentage to zoom out (e.g., 25 for 25% larger)
    """
    # Start an undo group
    pdb.gimp_image_undo_group_start(image)

    try:
        # Get original dimensions
        orig_width = image.width
        orig_height = image.height

        # Calculate new dimensions (25% larger = 1.25x)
        zoom_factor = 1.0 + (zoom_percent / 100.0)
        new_width = int(orig_width * zoom_factor)
        new_height = int(orig_height * zoom_factor)

        # Get the background color from the bottom-right pixel of the original image
        pdb.gimp_image_set_active_layer(image, drawable)
        bg_color = pdb.gimp_image_pick_color(image, drawable, orig_width - 1, orig_height - 1, False, False, 0)

        # Flatten the image first to ensure we're working with a single layer
        pdb.gimp_image_flatten(image)
        drawable = pdb.gimp_image_get_active_layer(image)

        # Resize the canvas (this will add transparent/empty space)
        offset_x = (new_width - orig_width) // 2
        offset_y = (new_height - orig_height) // 2
        pdb.gimp_image_resize(image, new_width, new_height, offset_x, offset_y)

        # Resize the layer to match the new canvas
        pdb.gimp_layer_resize_to_image_size(drawable)

        # Create a new layer below the current one
        bg_layer = pdb.gimp_layer_new(image, new_width, new_height, RGB_IMAGE, "Background", 100, NORMAL_MODE)
        pdb.gimp_image_insert_layer(image, bg_layer, None, 1)  # Insert below current layer

        # Fill the background layer with the background color
        pdb.gimp_context_set_foreground(bg_color)
        pdb.gimp_drawable_fill(bg_layer, FOREGROUND_FILL)

        # Flatten the image
        pdb.gimp_image_flatten(image)

        # Update the display
        pdb.gimp_displays_flush()

    finally:
        # End the undo group
        pdb.gimp_image_undo_group_end(image)

register(
    "python_fu_zoom_out_image",
    "Zoom out image by creating larger canvas with background fill",
    "Creates a layer 25% larger behind the current image and fills empty space with the image's background color",
    "Assistant",
    "Assistant",
    "2025",
    "<Image>/Filters/Custom/Zoom Out Image...",
    "RGB*, GRAY*",
    [
        (PF_INT, "zoom_percent", "Zoom out percentage", 25)
    ],
    [],
    zoom_out_image
)

main()
