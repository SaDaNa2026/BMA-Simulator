import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from Menus import DataMenu, AddMenu


class MainWindow(Gtk.ApplicationWindow):
    """Main Window of the application. Displays Detectors grouped in circuits as well as menus to access all
    application functionality."""

    def __init__(self, data_action_group, edit_action_group, hidden_action_group, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(700, 500)
        self.set_title("Steuerung Übungs-BMA")

        # Create a box that contains all other widgets in this window
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_box.set_margin_top(5)
        self.main_box.set_margin_bottom(5)
        self.main_box.set_margin_start(5)
        self.main_box.set_margin_end(5)
        self.main_box.set_spacing(20)
        self.set_child(self.main_box)

        # Definition of the window header
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)

        # MenuButton to handle data operations
        self.data_menu = DataMenu()
        self.data_menubutton = Gtk.MenuButton(label="Datei", direction=Gtk.ArrowType.DOWN)
        self.data_menubutton.set_menu_model(self.data_menu)
        self.header.pack_start(self.data_menubutton)

        # MenuButton to add a circuit or edit the building description
        self.add_menu = AddMenu()
        self.add_menubutton = Gtk.MenuButton(label="+", direction=Gtk.ArrowType.DOWN)
        self.add_menubutton.set_menu_model(self.add_menu)
        self.add_menubutton.set_visible(False)
        self.header.pack_start(self.add_menubutton)

        # Bind the action groups to the window
        self.insert_action_group("data", data_action_group)
        self.insert_action_group("edit", edit_action_group)
        self.insert_action_group("hidden_actions", hidden_action_group)