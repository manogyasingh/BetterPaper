import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GdkPixbuf, Gio, Gdk
import os
from wallpaper import WallpaperManager

class BetterPaperWindow(Gtk.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application, title="Better Paper")
        self.set_default_size(900, 700)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        self.wallpaper_manager = WallpaperManager()
        self.current_pixbuf = None
        
        # Create header bar
        self.header = Gtk.HeaderBar()
        self.header.set_show_close_button(True)
        self.header.props.title = "Better Paper"
        self.set_titlebar(self.header)
        
        # Add open button
        self.open_button = Gtk.Button()
        self.open_button.set_label("Open")
        self.open_button.connect("clicked", self.on_open_clicked)
        self.header.pack_start(self.open_button)
        
        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.main_box.set_margin_start(12)
        self.main_box.set_margin_end(12)
        self.main_box.set_margin_top(12)
        self.main_box.set_margin_bottom(12)
        self.add(self.main_box)
        
        # Image preview
        self.image = Gtk.Image()
        self.image.set_size_request(640, 360)
        
        # Create a frame for the image
        image_frame = Gtk.Frame(label="Original Image")
        image_frame.add(self.image)
        self.main_box.pack_start(image_frame, False, False, 0)
        
        # Create preview area
        self.preview_area = Gtk.DrawingArea()
        self.preview_area.set_size_request(640, 360)
        self.preview_area.connect("draw", self.on_preview_draw)
        
        # Create a frame for the preview
        preview_frame = Gtk.Frame(label="Preview (how it will appear)")
        preview_frame.add(self.preview_area)
        self.main_box.pack_start(preview_frame, True, True, 0)
        
        # Wallpaper settings
        self.settings_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.main_box.pack_start(self.settings_box, False, False, 0)
        
        # Style selector
        self.style_label = Gtk.Label(label="Wallpaper Style:")
        self.settings_box.pack_start(self.style_label, False, False, 0)
        
        self.style_combo = Gtk.ComboBoxText()
        styles = ["Centered", "Scaled", "Stretched", "Spanned", "Zoom", "Tiled"]
        for style in styles:
            self.style_combo.append_text(style)
        self.style_combo.set_active(1)  # Default to Scaled
        self.style_combo.connect("changed", self.on_style_changed)
        self.settings_box.pack_start(self.style_combo, False, False, 0)
        
        # Apply button
        self.apply_button = Gtk.Button(label="Apply")
        self.apply_button.connect("clicked", self.on_apply_clicked)
        self.apply_button.set_sensitive(False)  # Disabled until an image is selected
        self.settings_box.pack_end(self.apply_button, False, False, 0)
        
        self.show_all()
    
    def on_style_changed(self, combo):
        # Redraw the preview when style changes
        self.preview_area.queue_draw()
    
    def on_preview_draw(self, widget, cr):
        if not self.current_pixbuf:
            return False
        
        # Get style
        style_text = self.style_combo.get_active_text().lower()
        
        # Get widget dimensions
        alloc = widget.get_allocation()
        widget_width = alloc.width
        widget_height = alloc.height
        
        # Get image dimensions
        img_width = self.current_pixbuf.get_width()
        img_height = self.current_pixbuf.get_height()
        
        # Draw background (simulate desktop)
        cr.set_source_rgb(0.2, 0.2, 0.2)  # Dark gray background
        cr.rectangle(0, 0, widget_width, widget_height)
        cr.fill()
        
        # Calculate scaling and position based on style
        if style_text == "centered":
            # Center without scaling
            x = (widget_width - img_width) / 2
            y = (widget_height - img_height) / 2
            
            # Draw the image at the calculated position
            Gdk.cairo_set_source_pixbuf(cr, self.current_pixbuf, x, y)
            cr.paint()
            
        elif style_text == "scaled":
            # Scale to fit while maintaining aspect ratio
            scale_x = widget_width / img_width
            scale_y = widget_height / img_height
            scale = min(scale_x, scale_y)
            
            new_width = img_width * scale
            new_height = img_height * scale
            
            x = (widget_width - new_width) / 2
            y = (widget_height - new_height) / 2
            
            # Scale and draw
            cr.save()
            cr.translate(x, y)
            cr.scale(scale, scale)
            Gdk.cairo_set_source_pixbuf(cr, self.current_pixbuf, 0, 0)
            cr.paint()
            cr.restore()
            
        elif style_text == "stretched":
            # Stretch to fill, ignoring aspect ratio
            # Draw the image stretched to fill the whole area
            cr.save()
            cr.scale(widget_width / img_width, widget_height / img_height)
            Gdk.cairo_set_source_pixbuf(cr, self.current_pixbuf, 0, 0)
            cr.paint()
            cr.restore()
            
        elif style_text == "zoom" or style_text == "spanned":
            # Zoom/Spanned: Scale to fill, maintaining aspect ratio (may crop)
            scale_x = widget_width / img_width
            scale_y = widget_height / img_height
            scale = max(scale_x, scale_y)
            
            new_width = img_width * scale
            new_height = img_height * scale
            
            x = (widget_width - new_width) / 2
            y = (widget_height - new_height) / 2
            
            # Scale and draw
            cr.save()
            cr.translate(x, y)
            cr.scale(scale, scale)
            Gdk.cairo_set_source_pixbuf(cr, self.current_pixbuf, 0, 0)
            cr.paint()
            cr.restore()
            
        elif style_text == "tiled":
            # Tile the image
            for x in range(0, widget_width, img_width):
                for y in range(0, widget_height, img_height):
                    Gdk.cairo_set_source_pixbuf(cr, self.current_pixbuf, x, y)
                    cr.paint()
        
        return True
        
    def on_open_clicked(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Select an Image",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Add file filters
        filter_images = Gtk.FileFilter()
        filter_images.set_name("Image files")
        filter_images.add_mime_type("image/jpeg")
        filter_images.add_mime_type("image/png")
        filter_images.add_pattern("*.jpg")
        filter_images.add_pattern("*.jpeg")
        filter_images.add_pattern("*.png")
        dialog.add_filter(filter_images)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self.load_image(filename)
            self.apply_button.set_sensitive(True)
            self.current_file = filename
            
        dialog.destroy()
    
    def load_image(self, filename):
        # Load original image for display
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename, 640, 360, True)
        self.image.set_from_pixbuf(pixbuf)
        
        # Store original pixbuf for preview
        self.current_pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
        
        # Update the preview
        self.preview_area.queue_draw()
    
    def on_apply_clicked(self, button):
        style_text = self.style_combo.get_active_text().lower()
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
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Wallpaper Applied"
        )
        dialog.format_secondary_text(
            f"The wallpaper has been set with style: {style_text}"
        )
        dialog.run()
        dialog.destroy()
