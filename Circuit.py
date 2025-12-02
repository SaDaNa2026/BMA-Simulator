import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

from Menus import CircuitContextMenu


class Circuit(Gtk.Box):
    """A container for managing multiple Detector instances"""
    def __init__(self, circuit_number, *args, **kwargs):
        super().__init__(*args, orientation=Gtk.Orientation.VERTICAL, spacing=10)

        self.circuit_label = Gtk.Label()
        self.circuit_label.set_markup(f"<span size='large'>Melderlinie {circuit_number}</span>")
        self.append(self.circuit_label)

        # A tool to register the label of the circuit box being clicked
        self.click_controller = Gtk.GestureClick()
        self.click_controller.set_button(Gdk.BUTTON_SECONDARY)
        self.circuit_label.add_controller(self.click_controller)

        # Buttons to add or delete detectors
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.append(self.button_box)


        # Context menu
        self.menu_model = CircuitContextMenu(circuit_number)
        self.context_menu_popover = Gtk.PopoverMenu.new_from_model(self.menu_model)
        self.context_menu_popover.set_parent(self)
        self.context_menu_popover.set_has_arrow(False)

        # A dictionary to manage detectors within this circuit
        self.detector_dict = {}
