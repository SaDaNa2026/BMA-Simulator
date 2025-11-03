import sys
from re import fullmatch

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk



class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create main horizontal box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(self.main_box)

        # Create vertical box for melder
        self.melderlinie = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.append(self.melderlinie)

        # Store melder instances in a list for easy access
        self.melder = []

        # Button to add a melder
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)
        self.create_melder_button = Gtk.Button(label="Melder hinzufügen")
        self.create_melder_button.connect("clicked", self.create_melder)
        self.header.pack_start(self.create_melder_button)

    def create_melder(self, number=None):
        """Creates a new Melder instance with automatic numbering"""
        if number is None:
            number = len(self.melder) + 1

        # Create new Melder instance
        melder = Melder()

        # Add to container
        self.melderlinie.append(melder)

        # Store in list
        self.melder.append(melder)

        # Return the created melder
        return melder

    def get_melder_by_number(self, number):
        """Gets a melder by its number (1-based index)"""
        if 1 <= number <= len(self.melder):
            return self.melder[number - 1]
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
        self.win.present()

app = MyApp(application_id="com.BMA.EXAMPLE")
app.run(sys.argv)