import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from DescriptionBox import DescriptionBox
from Model import Model


class EditWindow(Gtk.Window):
    """Base class for a window that lets the user edit a description."""
    def __init__(self, handle_edit, parent, title, default_text, *args, **kwargs):
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
        self.confirm_button.connect("clicked", handle_edit)
        self.confirmation_box.set_end_widget(self.confirm_button)


class EditDetectorWindow(EditWindow):
    """Window for editing the description of a detector."""
    def __init__(self, circuit_number, detector_number, edit_detector_callback, parent, *args, **kwargs):
        self.circuit_number = circuit_number
        self.detector_number = detector_number
        detector = Model.circuit_dict[circuit_number].detector_dict[detector_number]
        title = f"Bearbeite Melder {detector_number} (Linie {circuit_number})"
        super().__init__(lambda button: self.handle_edit_detector(edit_detector_callback), parent, title, detector.description, *args, **kwargs)

    def handle_edit_detector(self, edit_detector_callback):
        description = self.description_box.get_description()
        edit_detector_callback(self.circuit_number, self.detector_number, description)
        self.destroy()


class EditBuildingWindow(EditWindow):
    """Window for editing the building description."""
    def __init__(self, parent, *args, **kwargs):
        title = f"Gebäudebeschreibung bearbeiten"
        super().__init__(lambda button: self.handle_edit_building(), parent, title, Model.description, *args, **kwargs)

    def handle_edit_building(self):
        description = self.description_box.get_description()
        Model.description = description
        self.destroy()
