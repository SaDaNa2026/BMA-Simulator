import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

from Menus import DetectorContextMenu


class Detector(Gtk.Box):
    """Contains a switch and a label with the number of the detector."""
    def __init__(self, circuit_number, detector_number, description, *args, **kwargs):
        super().__init__(*args, orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.detector_switch = Gtk.Switch()
        self.label_text = f"{detector_number}: {description}"
        self.detector_label = Gtk.Label(label=self.label_text)

        self.append(self.detector_switch)
        self.append(self.detector_label)

        self.right_click_controller = Gtk.GestureClick(button=Gdk.BUTTON_SECONDARY)
        self.add_controller(self.right_click_controller)

        self.left_click_controller = Gtk.GestureClick(button=Gdk.BUTTON_PRIMARY)
        self.add_controller(self.left_click_controller)

        # Context menu
        self.menu_model = DetectorContextMenu(circuit_number, detector_number)
        self.context_menu_popover = Gtk.PopoverMenu.new_from_model(self.menu_model)
        self.context_menu_popover.set_parent(self)
        self.context_menu_popover.set_has_arrow(False)

    def set_highlight(self, highlight: bool) -> None:
        """Highlight the detector by changing the label color"""
        if highlight:
            self.detector_label.set_markup(f"<span foreground='blue'>{self.label_text}</span>")
        else:
            self.detector_label.set_markup(f"<span foreground='black'>{self.label_text}</span>")