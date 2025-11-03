import sys

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk



class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(self.main_box)

        # Buttons to add or delete melderlinie
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)

        self.create_melderlinie_button = Gtk.Button(label="Melderlinie hinzufügen")
        self.create_melderlinie_button.connect("clicked", lambda button, *args: self.create_melderlinie())
        self.header.pack_start(self.create_melderlinie_button)

        self.delete_melderlinie_button = Gtk.Button(label="Melderlinie löschen")
        self.delete_melderlinie_button.connect("clicked", lambda button, *args: self.delete_melderlinie())
        self.header.pack_start(self.delete_melderlinie_button)

        self.melderlinie_list = []


    def create_melderlinie(self, number=None):
        """Creates a new Melderlinie instance with automatic numbering"""
        if number is None:
            number = len(self.melderlinie_list) + 1

        melderlinie = Melderlinie(number)
        self.main_box.append(melderlinie)
        self.melderlinie_list.append(melderlinie)
        return melderlinie

    def delete_melderlinie(self):
        """Remove a Melderlinie"""
        if len(self.melderlinie_list) > 0:
            self.index = len(self.melderlinie_list) - 1
            melderlinie = self.melderlinie_list.pop(self.index)
            self.main_box.remove(melderlinie)



class Melder(Gtk.Box):
    def __init__(self, melder_number, *args, **kwargs):
        super().__init__(*args, orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        self.melder_switch = Gtk.Switch()
        self.melder_switch.set_active(False)

        self.melder_label = Gtk.Label(label=f"Melder {melder_number}")

        self.append(self.melder_switch)
        self.append(self.melder_label)

class Melderlinie(Gtk.Box):
    """A container for managing multiple Melder instances"""

    def __init__(self, melderlinie_number, *args, **kwargs):
        super().__init__(*args, orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.melder_list = []
        self.active_melder_set = set()

        self.melderlinie_label = Gtk.Label(label=f"Melderlinie {melderlinie_number}")
        self.append(self.melderlinie_label)

        # Buttons to add or delete melders
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append(self.button_box)
        self.add_melder_button = Gtk.Button(label="Melder hinzufügen")
        self.add_melder_button.connect("clicked", lambda button, *args: self.create_melder())
        self.button_box.append(self.add_melder_button)
        self.delete_melder_button = Gtk.Button(label="Melder löschen")
        self.delete_melder_button.connect("clicked", lambda button, *args: self.delete_melder())
        self.button_box.append(self.delete_melder_button)

    def create_melder(self, number=None):
        """Creates a new Melder instance with automatic numbering"""
        if number is None:
            number = len(self.melder_list) + 1

        melder = Melder(number)
        self.melder_list.append(melder)

        melder.melder_switch.connect('state-set', self.on_melder_toggled, number)
        self.append(melder)
        return melder

    def delete_melder(self):
        """Remove a melder"""
        if len(self.melder_list) > 0:
            self.index = len(self.melder_list) - 1
            melder = self.melder_list.pop(self.index)

            self.remove(melder)
            self.active_melder_set.discard(self.index + 1)

    def on_melder_toggled(self, melder_switch, state, melder_number):
        if state:
            self.active_melder_set.add(melder_number)
        else:
            self.active_melder_set.discard(melder_number)

        print(f"Melder {melder_number} {'activated' if state else 'deactivated'}")
        print(f"Currently active melders: {sorted(self.active_melder_set)}")

class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()

app = MyApp(application_id="com.BMA.EXAMPLE")
app.run(sys.argv)