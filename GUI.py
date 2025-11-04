import sys

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

# A list to manage Melderlinie instances
melder_dict = {}


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(300, 300)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_box.set_margin_top(5)
        self.main_box.set_margin_bottom(5)
        self.main_box.set_margin_start(5)
        self.main_box.set_margin_end(5)
        self.main_box.set_spacing(5)
        self.set_child(self.main_box)

        # Buttons to add or delete a melderlinie
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)

        self.create_melderlinie_button = Gtk.Button(label="Melderlinie hinzufügen")
        self.create_melderlinie_button.connect("clicked", lambda button, *args: self.create_melderlinie())
        self.header.pack_start(self.create_melderlinie_button)

        self.delete_melderlinie_button = Gtk.Button(label="Melderlinie löschen")
        self.delete_melderlinie_button.connect("clicked", lambda button, *args: self.delete_melderlinie())
        self.header.pack_start(self.delete_melderlinie_button)

    def create_melderlinie(self, number=None):
        """Creates a new Melderlinie instance with automatic numbering"""
        if number is None:
            number = len(melder_dict) + 1

        melderlinie = Melderlinie(number)
        self.main_box.append(melderlinie)
        melder_dict[number] = {"melderlinie": melderlinie}
        return melderlinie

    def delete_melderlinie(self):
        """Remove a Melderlinie"""
        if len(melder_dict) > 0:
            self.index = len(melder_dict)
            melderlinie = melder_dict[self.index]["melderlinie"]
            self.main_box.remove(melderlinie)
            del melder_dict[self.index]


class Melder(Gtk.Box):
    def __init__(self, melder_number, *args, **kwargs):
        super().__init__(*args, orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.melder_switch = Gtk.Switch()
        self.melder_switch.set_active(False)

        self.melder_label = Gtk.Label(label=f"Melder {melder_number}")

        self.append(self.melder_switch)
        self.append(self.melder_label)


class Melderlinie(Gtk.Box):
    """A container for managing multiple Melder instances"""

    def __init__(self, melderlinie_number, *args, **kwargs):
        super().__init__(*args, orientation=Gtk.Orientation.VERTICAL, spacing=5)
        # A set to keep track of which melder is active
        self.active_melder_set = set()

        self.melderlinie_label = Gtk.Label()
        self.melderlinie_label.set_markup(f"<span size='large'>Melderlinie {melderlinie_number}</span>")
        self.append(self.melderlinie_label)

        # Buttons to add or delete melders
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append(self.button_box)
        self.add_melder_button = Gtk.Button(label="Melder hinzufügen")
        self.add_melder_button.connect("clicked",
                                       lambda button, *args: self.create_melder(melderlinie_number=melderlinie_number),
                                       )
        self.button_box.append(self.add_melder_button)
        self.delete_melder_button = Gtk.Button(label="Melder löschen")
        self.delete_melder_button.connect("clicked",
                                          lambda button, *args: self.delete_melder(melderlinie_number))
        self.button_box.append(self.delete_melder_button)

    def create_melder(self, melderlinie_number, melder_number=None):
        """Creates a new Melder instance with automatic numbering"""
        if melder_number is None:
            melder_number = len(melder_dict[melderlinie_number])
        melder = Melder(melder_number)
        melder_dict[melderlinie_number][melder_number] = melder

        melder.melder_switch.connect('state-set', self.on_melder_toggled, melderlinie_number, melder_number)
        self.append(melder)
        return melder

    def delete_melder(self, melderlinie_number):
        """Remove a melder"""
        self.index = len(melder_dict[melderlinie_number]) - 1
        melder = melder_dict[melderlinie_number][self.index]

        del melder_dict[melderlinie_number][self.index]
        self.remove(melder)
        self.active_melder_set.discard(self.index + 1)

    def on_melder_toggled(self, melder_switch, state, melderlinie_number, melder_number):
        if state:
            self.active_melder_set.add([melderlinie_number, melder_number])
        else:
            self.active_melder_set.discard()

        print(f"Melder {melder_number} in Melderlinie {melderlinie_number} {'activated' if state else 'deactivated'}")
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
