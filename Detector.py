import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

from Menus import DetectorContextMenu


class Detector(Gtk.Box):
    """Contains a switch and a label with the number of the detector."""
    def __init__(self, circuit_number, detector_number, *args, **kwargs):
        super().__init__(*args, orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.detector_switch = Gtk.Switch()
        self.detector_label = Gtk.Label(label=f"Melder {detector_number}")

        self.append(self.detector_switch)
        self.append(self.detector_label)

        # A tool to register the detector_label being right-clicked
        self.click_controller = Gtk.GestureClick()
        self.click_controller.set_button(Gdk.BUTTON_SECONDARY)
        self.add_controller(self.click_controller)

        # Context menu
        self.menu_model = DetectorContextMenu(circuit_number, detector_number)
        self.context_menu_popover = Gtk.PopoverMenu.new_from_model(self.menu_model)
        self.context_menu_popover.set_parent(self)
        self.context_menu_popover.set_has_arrow(False)
