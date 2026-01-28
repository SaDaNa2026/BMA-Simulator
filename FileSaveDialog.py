import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gio, Gtk, GLib


class FileSaveDialog(Gtk.FileDialog):
    """When initiated, present a FileDialog to choose a location to save to. On confirmation of the selection,
    call the method to write data."""
    def __init__(self, file_type, last_dir=Gio.File.new_for_path("/home/lfs-bma"), last_name=""):
        super().__init__(accept_label="Speichern",
                                     initial_folder=last_dir,
                                     modal=True)

        # Set title and initial file name according to the file type to be saved
        if file_type == "building":
            if last_name == "":
                last_name = "Gebäudekonfiguration"
            self.set_title("Gebäudekonfiguration speichern")
            self.set_initial_name(f"{last_name}.building")
        else:
            if last_name == "":
                last_name = "Szenario"
            self.set_title("Szenario speichern")
            self.set_initial_name(f"{last_name}.scenario")

        # Add file filter according to file type
        extension_filter = Gtk.FileFilter()
        extension_filter.add_pattern(f"*.{file_type}")
        self.set_default_filter(extension_filter)
