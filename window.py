import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, GdkPixbuf, Gio, Gdk
import os
import sys
import cairo
from wallpaper import WallpaperManager

class BetterPaperWindow(Gtk.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application, title="Better Paper")
        self.set_default_size(900, 700)
        
        self.wallpaper_manager = WallpaperManager()
        self.current_pixbuf = None
        self.current_file = None
        
        # Create header bar
        header = Gtk.HeaderBar()
        self.set_titlebar(header)
        
        # Add open button
        self.open_button = Gtk.Button(label="Open")
        self.open_button.connect("clicked", self.on_open_clicked)
        header.pack_start(self.open_button)
        
        # Main container as a ScrolledWindow for better resizing behavior
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_propagate_natural_height(True)
        self.set_child(scrolled)
        
        # Main box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.main_box.set_margin_start(12)
        self.main_box.set_margin_end(12)
        self.main_box.set_margin_top(12)
        self.main_box.set_margin_bottom(12)
        scrolled.set_child(self.main_box)
        
        # Get screen dimensions to calculate aspect ratio
        display = Gdk.Display.get_default()
        monitors = display.get_monitors()
        
        if monitors.get_n_items() > 0:
            monitor = monitors.get_item(0)
            geometry = monitor.get_geometry()
            self.screen_width = geometry.width
            self.screen_height = geometry.height
        else:
            # Default fallback if no monitor information is available
            self.screen_width = 1920
            self.screen_height = 1080
            
        screen_aspect = self.screen_width / self.screen_height
        
        # Calculate preview size based on screen aspect ratio
        preview_width = 800
        preview_height = int(preview_width / screen_aspect)
        
        # Create preview area with screen aspect ratio
        self.preview_area = Gtk.DrawingArea()
        self.preview_area.set_content_width(preview_width)
        self.preview_area.set_content_height(preview_height)
        self.preview_area.set_draw_func(self.on_preview_draw, None)
        
        # Create a frame for the preview
        preview_frame = Gtk.Frame()
        preview_frame.set_child(self.preview_area)
        preview_frame.set_label(f"Preview (Screen: {self.screen_width}x{self.screen_height})")
        self.main_box.append(preview_frame)
        
        # Wallpaper settings
        self.settings_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.settings_box.set_margin_top(12)
        self.main_box.append(self.settings_box)
        
        # Style selector
        self.style_label = Gtk.Label(label="Wallpaper Style:")
        self.settings_box.append(self.style_label)
        
        self.style_combo = Gtk.DropDown.new_from_strings(
            ["Centered", "Scaled", "Stretched", "Spanned", "Zoom", "Tiled"])
        self.style_combo.set_selected(1)  # Default to Scaled
        self.style_combo.connect("notify::selected", self.on_style_changed)
        self.settings_box.append(self.style_combo)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        self.settings_box.append(spacer)
        
        # Apply button
        self.apply_button = Gtk.Button(label="Apply")
        self.apply_button.connect("clicked", self.on_apply_clicked)
        self.apply_button.set_sensitive(False)  # Disabled until an image is selected
        self.settings_box.append(self.apply_button)
    
    def on_style_changed(self, dropdown, gparam):
        # Redraw the preview when style changes
        self.preview_area.queue_draw()
    
    def on_preview_draw(self, drawing_area, cr, width, height, user_data):
        if not self.current_pixbuf:
            return False
        
        try:
            # Get the widget dimensions for scaling
            widget_width = width
            widget_height = height
            
            # Draw directly on the widget's context
            # Draw background (simulate desktop)
            cr.set_source_rgb(0.2, 0.2, 0.2)  # Dark gray background
            cr.rectangle(0, 0, widget_width, widget_height)
            cr.fill()
            
            # Get style
            selected = self.style_combo.get_selected()
            styles = ["centered", "scaled", "stretched", "spanned", "zoom", "tiled"]
            if 0 <= selected < len(styles):
                style_text = styles[selected]
            else:
                style_text = "scaled"  # Default
            
            # Get image dimensions
            img_width = self.current_pixbuf.get_width()
            img_height = self.current_pixbuf.get_height()
            
            # Scale down large images for better performance
            if max(img_width, img_height) > 1000:
                scale_factor = 1000 / max(img_width, img_height)
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)
                pixbuf = self.current_pixbuf.scale_simple(new_width, new_height, 
                                                          GdkPixbuf.InterpType.BILINEAR)
            else:
                pixbuf = self.current_pixbuf
                new_width = img_width
                new_height = img_height
            
            # Calculate how the image would appear on the screen, then scale to widget
            if style_text == "centered":
                # Center without scaling
                scale_x = widget_width / self.screen_width
                scale_y = widget_height / self.screen_height
                scale = min(scale_x, scale_y)
                
                img_screen_width = new_width
                img_screen_height = new_height
                
                x = (widget_width - (img_screen_width * scale)) / 2
                y = (widget_height - (img_screen_height * scale)) / 2
                
                cr.save()
                cr.translate(x, y)
                cr.scale(scale, scale)
                Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
                cr.paint()
                cr.restore()
                
            elif style_text == "scaled":
                # Scale to fit while maintaining aspect ratio
                screen_scale_x = self.screen_width / new_width
                screen_scale_y = self.screen_height / new_height
                screen_scale = min(screen_scale_x, screen_scale_y)
                
                img_screen_width = new_width * screen_scale
                img_screen_height = new_height * screen_scale
                
                # Now scale down to widget
                widget_scale = min(widget_width / img_screen_width, widget_height / img_screen_height)
                
                final_width = img_screen_width * widget_scale
                final_height = img_screen_height * widget_scale
                
                x = (widget_width - final_width) / 2
                y = (widget_height - final_height) / 2
                
                cr.save()
                cr.translate(x, y)
                cr.scale(screen_scale * widget_scale, screen_scale * widget_scale)
                Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
                cr.paint()
                cr.restore()
                
            elif style_text == "stretched":
                # Stretch to fill the entire widget
                cr.save()
                cr.scale(widget_width / new_width, widget_height / new_height)
                Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
                cr.paint()
                cr.restore()
                
            elif style_text == "zoom" or style_text == "spanned":
                # Zoom/Spanned: Scale to fill, maintaining aspect ratio (may crop)
                screen_scale_x = self.screen_width / new_width
                screen_scale_y = self.screen_height / new_height
                screen_scale = max(screen_scale_x, screen_scale_y)
                
                img_screen_width = new_width * screen_scale
                img_screen_height = new_height * screen_scale
                
                # Now scale down to widget
                widget_scale = min(widget_width / img_screen_width, widget_height / img_screen_height)
                
                final_width = img_screen_width * widget_scale
                final_height = img_screen_height * widget_scale
                
                x = (widget_width - final_width) / 2
                y = (widget_height - final_height) / 2
                
                cr.save()
                cr.translate(x, y)
                cr.scale(screen_scale * widget_scale, screen_scale * widget_scale)
                Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
                cr.paint()
                cr.restore()
                
            elif style_text == "tiled":
                # For tiling, draw the scaled image repeatedly
                try:
                    # Get a scaled version of the image appropriate for tiling preview
                    tile_size = min(100, new_width)  # Keep tiles small
                    tile_scale = tile_size / new_width
                    tile_width = int(new_width * tile_scale)
                    tile_height = int(new_height * tile_scale)
                    
                    if tile_width == 0 or tile_height == 0:
                        raise ValueError("Invalid tile dimensions")
                    
                    # Scale the pixbuf to tile size
                    tile_pixbuf = pixbuf.scale_simple(tile_width, tile_height, 
                                                     GdkPixbuf.InterpType.BILINEAR)
                    
                    # Draw the tiles directly
                    for x in range(0, widget_width + tile_width, tile_width):
                        for y in range(0, widget_height + tile_height, tile_height):
                            Gdk.cairo_set_source_pixbuf(cr, tile_pixbuf, x, y)
                            cr.rectangle(x, y, tile_width, tile_height)
                            cr.fill()
                            
                except Exception as e:
                    # Fallback for tiling - just draw a single instance
                    print(f"Tiling pattern error: {e}", file=sys.stderr)
                    cr.save()
                    cr.translate(widget_width/2 - new_width/2, widget_height/2 - new_height/2)
                    Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
                    cr.paint()
                    cr.restore()
            
            return True
            
        except Exception as e:
            print(f"Preview rendering error: {e}", file=sys.stderr)
            
            # Fallback simple preview
            cr.set_source_rgb(0.2, 0.2, 0.2)  # Dark gray background
            cr.rectangle(0, 0, widget_width, widget_height)
            cr.fill()
            
            # Display error message in the preview
            cr.set_source_rgb(1, 0.3, 0.3)  # Red text
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(14)
            cr.move_to(20, 50)
            cr.show_text(f"Preview error: {str(e)}")
            cr.move_to(20, 80)
            cr.show_text("The wallpaper will still be applied correctly.")
            
            return True
    
    def on_open_clicked(self, button):
        # Create a file chooser dialog
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Select an Image")
        
        # File filter for images
        filters = Gtk.FileFilter.new()
        filters.set_name("Image files")
        filters.add_mime_type("image/jpeg")
        filters.add_mime_type("image/png")
        filters.add_pattern("*.jpg")
        filters.add_pattern("*.jpeg")
        filters.add_pattern("*.png")
        
        dialog.set_default_filter(filters)
        
        # Open the dialog and handle the response
        dialog.open(self, None, self.on_file_dialog_response)
    
    def on_file_dialog_response(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                filename = file.get_path()
                self.load_image(filename)
                self.apply_button.set_sensitive(True)
                self.current_file = filename
        except GLib.Error as e:
            print(f"File dialog error: {e.message}")
    
    def load_image(self, filename):
        try:
            # Store original pixbuf for preview
            self.current_pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
            
            # Update the preview
            self.preview_area.queue_draw()
        except Exception as e:
            print(f"Error loading image: {e}", file=sys.stderr)
            
            # Show error dialog
            dialog = Gtk.AlertDialog.new("Error Loading Image")
            dialog.set_detail(f"Could not load image: {str(e)}")
            dialog.show(self)
    
    def on_apply_clicked(self, button):
        if not self.current_file:
            return
            
        # Get the selected style
        selected = self.style_combo.get_selected()
        styles = ["Centered", "Scaled", "Stretched", "Spanned", "Zoom", "Tiled"]
        if 0 <= selected < len(styles):
            style_text = styles[selected].lower()
        else:
            style_text = "scaled"  # Default
        
        # Map style text to GNOME settings value
        style_map = {
            "centered": "centered",
            "scaled": "scaled",
            "stretched": "stretched",
            "spanned": "spanned",
            "zoom": "zoom",
            "tiled": "wallpaper"
        }
        style = style_map.get(style_text, "scaled")
        
        self.wallpaper_manager.set_wallpaper(self.current_file, style)
        
        # Show success message
        dialog = Gtk.AlertDialog.new("Wallpaper Applied")
        dialog.set_detail(f"The wallpaper has been set with style: {style_text}")
        dialog.show(self)
