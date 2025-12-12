import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class DescriptionBox(Gtk.Box):
    """Contains a label and a textview. Can be used where the user can edit a description."""
    def __init__(self, default_text=""):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.description_label = Gtk.Label(label="Beschreibung:")
        self.append(self.description_label)

        self.description_textview = Gtk.TextView()
        self.append(self.description_textview)
        self.textbuffer = self.description_textview.get_buffer()
        self.textbuffer.set_text(default_text)

    def get_description(self):
        """Get the content of the TextView. Raise an error if the description is longer than 20 characters."""
        start = self.textbuffer.get_start_iter()
        end = self.textbuffer.get_end_iter()
        description = self.textbuffer.get_text(start, end, True)
        return description
