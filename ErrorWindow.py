import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class ErrorWindow(Gtk.Window):
    def __init__(self, parent, error_message, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_title("Fehler")
        self.set_modal(True)
        self.set_default_size(300, 60)
        self.set_transient_for(parent)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                spacing=10,
                                margin_start=5,
                                margin_end=5,
                                margin_top=5,
                                margin_bottom=5)
        self.set_child(self.main_box)

        self.error_label = Gtk.Label()
        self.error_label.set_markup(f"<span foreground='red' size='large'>{error_message}</span>")
        self.main_box.append(self.error_label)

        self.confirm_button = Gtk.Button(label="OK")
        self.confirm_button.connect("clicked", lambda button, *args: self.destroy())
        self.main_box.append(self.confirm_button)
