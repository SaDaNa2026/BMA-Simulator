import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
from functools import partial

from DescriptionBox import DescriptionBox

class EditWindow(Gtk.Window):
    """Base class for a window that lets the user edit a description."""
    def __init__(self, edit_callback, parent, title, default_text, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(350, 100)
        self.set_title(title)

        # Make the window modal and transient for the parent
        self.set_modal(True)
        self.set_transient_for(parent)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                margin_top=5,
                                margin_bottom=5,
                                margin_start=5,
                                margin_end=5,
                                spacing=10)
        self.set_child(self.main_box)

        self.description_box = DescriptionBox(default_text)
        self.main_box.append(self.description_box)

        # Buttons to cancel or confirm
        self.confirmation_box = Gtk.CenterBox()
        self.main_box.append(self.confirmation_box)

        self.cancel_button = Gtk.Button(label="Schließen")
        self.cancel_button.connect("clicked", lambda button, *args: self.destroy())
        self.confirmation_box.set_start_widget(self.cancel_button)

        self.confirm_button = Gtk.Button(label="Bestätigen")
        self.confirm_button.connect("clicked", edit_callback)
        self.confirmation_box.set_end_widget(self.confirm_button)

        # Label to display an error if the description is too long
        self.long_description_warning_label = Gtk.Label()
        self.long_description_warning_label.set_markup(f"<span foreground='red'>Die Beschreibung darf höchstens 20 "
                                                       f"Zeichen lang sein,\ndamit sie auf das FAT passt.</span>")

    def get_description(self):
        # Remove old warnings
        if self.long_description_warning_label.get_parent():
            self.main_box.remove(self.long_description_warning_label)

        description = self.description_box.get_description()
        return description



class EditDetectorWindow(EditWindow):
    """Window for editing the description of a detector."""
    def __init__(self, circuit_number, detector_number, edit_detector_callback, parent, current_description, *args, **kwargs):
        self.circuit_number = circuit_number
        self.detector_number = detector_number
        title = f"Bearbeite Melder {detector_number} (Linie {circuit_number})"
        super().__init__(lambda button, *args: self.handle_edit(edit_detector_callback), parent, title, current_description, *args, **kwargs)

    def handle_edit(self, edit_detector_callback):
        description = self.get_description()
        try:
            edit_detector_callback(self.circuit_number, self.detector_number, description)
            self.destroy()
        except ValueError:
            self.main_box.insert_child_after(self.long_description_warning_label, self.description_box)


class EditBuildingWindow(EditWindow):
    """Window for editing the building description."""
    def __init__(self, edit_building_callback, parent, current_description, *args, **kwargs):
        title = f"Gebäudebeschreibung bearbeiten"
        super().__init__(lambda button, *args: self.handle_edit(edit_building_callback), parent, title, current_description, *args, **kwargs)

    def handle_edit(self, edit_building_callback):
        description = self.get_description()
        try:
            edit_building_callback(description)
            self.destroy()
        except ValueError:
            self.main_box.insert_child_after(self.long_description_warning_label, self.description_box)