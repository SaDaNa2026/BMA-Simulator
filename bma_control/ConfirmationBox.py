import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class ConfirmationBox(Gtk.Box):
    def __init__(self, cancel_callback, confirm_callback, confirm_label: str = "OK") -> None:
        """A Box with two buttons: Cancel and Confirm. The label of the Confirm button can be specified"""
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL,
                         halign=Gtk.Align.END,
                         spacing=10,
                         hexpand=True,
                         margin_top=5,
                         margin_bottom=5,
                         margin_start=10,
                         margin_end=10)
        self.cancel_button = Gtk.Button(label="Abbrechen")
        self.cancel_button.connect("clicked", lambda button, *args: cancel_callback())
        self.append(self.cancel_button)
        self.confirm_button = Gtk.Button(label=confirm_label)
        self.confirm_button.connect("clicked", lambda button, *args: confirm_callback())
        self.append(self.confirm_button)
