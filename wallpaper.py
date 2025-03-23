import subprocess
import os
from gi.repository import Gio

class WallpaperManager:
    def __init__(self):
        self.settings = Gio.Settings.new("org.gnome.desktop.background")
    
    def set_wallpaper(self, image_path, style="scaled"):
        """
        Set the desktop wallpaper
        
        Args:
            image_path (str): Path to the image file
            style (str): One of 'none', 'wallpaper', 'centered', 'scaled', 
                         'stretched', 'zoom', 'spanned'
        """
        # Ensure we have an absolute path
        image_path = os.path.abspath(image_path)
        
        # Convert file path to URI
        image_uri = f"file://{image_path}"
        
        # Set picture-uri in gsettings
        self.settings.set_string("picture-uri", image_uri)
        
        # Set dark mode picture-uri as well for GNOME 42+
        try:
            self.settings.set_string("picture-uri-dark", image_uri)
        except:
            pass  # Ignore if setting doesn't exist
        
        # Set the picture options (style)
        self.settings.set_string("picture-options", style)
        
        # Make sure changes are applied
        Gio.Settings.sync()
        
        return True
    
    def get_current_wallpaper(self):
        """Get the current wallpaper URI"""
        uri = self.settings.get_string("picture-uri")
        return uri.replace("file://", "") if uri.startswith("file://") else uri
    
    def get_current_style(self):
        """Get the current wallpaper style"""
        return self.settings.get_string("picture-options")
