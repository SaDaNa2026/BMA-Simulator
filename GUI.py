import sys
from re import fullmatch

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk



class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(self.main_box)

        self.melderlinie = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.append(self.melderlinie)

        # Store melder instances in a list for easy access
        self.melder_list = []
        self.active_melder_set = set()

        # Button to add a melder
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)

        self.create_melder_button = Gtk.Button(label="Melder hinzufügen")
        self.create_melder_button.connect("clicked", lambda button, *args: self.create_melder())
        self.header.pack_start(self.create_melder_button)

        self.delete_melder_button = Gtk.Button(label="Melder löschen")
        self.delete_melder_button.connect("clicked", lambda button, *args: self.delete_melder())
        self.header.pack_start(self.delete_melder_button)

    def create_melder(self, number=None):
        """Creates a new Melder instance with automatic numbering"""
        if number is None:
            number = len(self.melder_list) + 1

        melder = Melder()

        melder.melder_switch.connect('state-set', self.on_melder_toggled, number)

        self.melderlinie.append(melder)

        self.melder_list.append(melder)

        return melder

    def delete_melder(self):
        """Remove a melder"""
        self.index = len(self.melder_list) - 1
        melder = self.melder_list.pop(self.index)

        # Remove from container
        self.melderlinie.remove(melder)

        self.active_melder_set.discard(self.index + 1)

    def on_melder_toggled(self, melder_switch, state, melder_number):
        if state:
            self.active_melder_set.add(melder_number)
        else:
            self.active_melder_set.discard(melder_number)

        print(f"Melder {melder_number} {'activated' if state else 'deactivated'}")
        print(f"Currently active melders: {sorted(self.active_melder_set)}")

    def get_melder_by_number(self, number):
        """Gets a melder by its number (1-based index)"""
        if 1 <= number <= len(self.melder_list):
            return self.melder_list[number - 1]
        return None

class Melder(Gtk.Box):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, orientation=Gtk.Orientation.VERTICAL, spacing=5)

        self.melder_switch = Gtk.Switch()
        self.melder_switch.set_active(False)

        self.melder_label = Gtk.Label(label="Melder")

        self.append(self.melder_switch)
        self.append(self.melder_label)


class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app)

        for i in range(3):
            self.win.create_melder(number=i + 1)

        self.win.present()

app = MyApp(application_id="com.BMA.EXAMPLE")
app.run(sys.argv)