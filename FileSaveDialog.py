import json

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gio, Gtk, GLib

from ErrorWindow import ErrorWindow
from FileOperations import FileOperations

class FileSaveDialog:
    """When initiated, present a FileDialog to choose a location to save to. On confirmation of the selection,
    call the method to write data."""
    def __init__(self, parent, file_type):
        self.parent = parent
        self.file_type = file_type

        # Present a file save dialog
        current_dir = Gio.File.new_for_path(".")
        self.save_dialog = Gtk.FileDialog(accept_label="Speichern",
                                     initial_folder=current_dir,
                                     modal=True)

        # Set title and initial file name according to the file type to be saved
        if file_type == "building":
            self.save_dialog.set_title("Gebäudekonfiguration speichern")
            self.save_dialog.set_initial_name("Gebäudekonfiguration.building")
        else:
            self.save_dialog.set_title("Szenario speichern")
            self.save_dialog.set_initial_name("Szenario.scenario")

        # Add file filter according to file type
        extension_filter = Gtk.FileFilter()
        extension_filter.add_pattern(f"*.{file_type}")
        self.save_dialog.set_default_filter(extension_filter)

    def open_save_dialog(self):
        """Show the dialog asynchronously"""
        self.save_dialog.save(self.parent, None, self.on_file_save_response)

    def on_file_save_response(self, dialog, result):
        try:
            file = dialog.save_finish(result)
            if file is not None:
                FileOperations.save_to_file(file, self.file_type)

        except GLib.Error as e:
            print(f"Save canceled or failed: {e.message}")

            if not e.message == "Dismissed by user":
                error_window = ErrorWindow(self.parent, f"Speichern fehlgeschlagen: {e.message}")
                error_window.present()
