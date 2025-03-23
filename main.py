#!/usr/bin/env python3
# filepath: /home/manogya/Desktop/betterpaper/main.py
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib
import sys
import os
from window import BetterPaperWindow

class BetterPaperApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.gnome.BetterPaper",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.window = None
        
    def do_activate(self):
        # Get the window or create one if it doesn't exist
        if not self.window:
            self.window = BetterPaperWindow(application=self)
        
        self.window.present()
        
def main():
    # Create and run the application
    app = BetterPaperApplication()
    return app.run(sys.argv)
    
if __name__ == "__main__":
    sys.exit(main())