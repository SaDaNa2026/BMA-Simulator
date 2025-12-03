import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from MainWindow import MainWindow


class App(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.window = MainWindow(application=app)
        self.window.present()

        # Add shortcuts to the actions
        self.set_accels_for_action("data.save_building", ["<Ctrl><Shift>S"])
        self.set_accels_for_action("data.save_scenario", ["<Ctrl>S"])
        self.set_accels_for_action("data.open", ["<Ctrl>O"])
        self.set_accels_for_action("data.edit_mode", ["<Ctrl>E"])
