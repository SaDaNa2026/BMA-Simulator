import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gio, Gtk



class FileOpenDialog(Gtk.FileDialog):
    """A FileDialog configured for opening files."""
    def __init__(self):
        current_dir = Gio.File.new_for_path(".")

        super().__init__(title="Konfiguration laden",
                       accept_label="Öffnen",
                       initial_folder=current_dir,
                       modal=True)

        # Add a file filter for the extensions used by this application
        extension_filter = Gtk.FileFilter()
        extension_filter.add_pattern("*.building")
        extension_filter.add_pattern("*.scenario")
        self.set_default_filter(extension_filter)