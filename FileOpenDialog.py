from functools import partial

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gio, Gtk, GLib

from ErrorWindow import ErrorWindow


class FileOpenDialog:
    """Class to load a building from a json file"""
    def __init__(self, parent):
        self.parent = parent

        # Create a dictionary to save the data loaded from the json file
        self.load_dict = {}

        # Present a file load dialog
        current_dir = Gio.File.new_for_path(".")
        self.load_dialog = Gtk.FileDialog(title="Konfiguration laden",
                                     accept_label="Öffnen",
                                     initial_folder=current_dir,
                                     modal=True)

        # Add a file filter for the extensions used by this application
        extension_filter = Gtk.FileFilter()
        extension_filter.add_pattern("*.building")
        extension_filter.add_pattern("*.scenario")
        self.load_dialog.set_default_filter(extension_filter)

    def show_open_dialog(self, open_file_callback):
        """Show the dialog asynchronously"""
        self.load_dialog.open(self.parent,
                              None,
                              partial(self.on_file_open_response, open_file_callback=open_file_callback))

    def on_file_open_response(self, dialog, result, open_file_callback):
        """Callback for the file dialog. Loads the json file from the selected path if it exists and passes the data
        to a callback function."""
        try:
            file = dialog.open_finish(result)
            if file is not None:
                open_file_callback(file)

        except GLib.Error as e:
            print(f"Open canceled or failed: {e.message}")

            if not e.message == "Dismissed by user":
                error_window = ErrorWindow(self.parent, f"Öffnen fehlgeschlagen: {e.message}")
                error_window.present()
