#!/usr/bin/env python3
# filepath: /home/manogya/Desktop/betterpaper/launcher.py
"""
Launcher script for BetterPaper
This script ensures GTK 4.0 is loaded before any other modules that might use GTK 3.0
"""
import os
import sys
import importlib.util

# Clear any preloaded GTK modules from sys.modules
for module_name in list(sys.modules.keys()):
    if module_name.startswith('gi.repository.Gtk') or module_name == 'gi.repository':
        del sys.modules[module_name]

# Ensure GTK 4.0 is used
os.environ['GI_TYPELIB_PATH'] = '/usr/lib/girepository-1.0'
os.environ['GI_TYPELIB_VERSION'] = '4.0'

# Now we can safely import gi and require GTK 4.0
import gi
gi.require_version('Gtk', '4.0')

# Run the main application
if __name__ == "__main__":
    # Import and run the main module
    spec = importlib.util.spec_from_file_location("main", os.path.join(os.path.dirname(__file__), "main.py"))
    main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main)
    sys.exit(main.main())