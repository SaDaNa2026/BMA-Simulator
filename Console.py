import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class Console(Gtk.Frame):
    def __init__(self, label):
        super().__init__(label=label, hexpand=True)
        self.buffer = Gtk.TextBuffer()
        self.console = Gtk.TextView(editable=False,
                                    buffer=self.buffer,
                                    cursor_visible=False,
                                    left_margin=10,
                                    top_margin=10,
                                    monospace=True)
        self.set_child(self.console)