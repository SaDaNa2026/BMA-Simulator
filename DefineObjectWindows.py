import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
from ModalWindow import ModalWindow
from DescriptionBox import DescriptionBox


class DefineObjectWindow(ModalWindow):
    """Base class for a Window that lets the use create an object with a chosen number."""
    def __init__(self, handle_create_method, entry_label, parent, max_length=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                margin_top=5,
                                margin_bottom=5,
                                margin_start=5,
                                margin_end=5,
                                spacing=10)
        self.set_child(self.main_box)

        # Labeled Entry field for the user to put in the number of the object to be created
        self.choose_number_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.main_box.append(self.choose_number_box)

        self.choose_number_label = Gtk.Label(label=entry_label)
        self.choose_number_box.append(self.choose_number_label)

        # Entry field to define the number of the circuit/detector. Set a max length if provided
        self.choose_number_entry = Gtk.Entry(has_frame=True, activates_default=True)
        if max_length is not None:
            self.choose_number_entry.set_max_length(max_length)
            self.choose_number_entry.set_max_width_chars(max_length)
            self.choose_number_entry.connect("changed", self.validate_input, max_length)
        self.choose_number_box.append(self.choose_number_entry)

        # Buttons to cancel or add the object
        self.confirmation_box = Gtk.CenterBox()
        self.main_box.append(self.confirmation_box)

        self.cancel_button = Gtk.Button(label="Abbrechen")
        self.cancel_button.connect("clicked", lambda button, *args: self.destroy())
        self.confirmation_box.set_start_widget(self.cancel_button)

        self.confirm_button = Gtk.Button(label="Hinzufügen")
        self.confirm_button.connect("clicked", handle_create_method)
        self.confirmation_box.set_end_widget(self.confirm_button)
        # Set confirm button as default widget so it is activated when enter is pressed inside the Entry
        self.set_default_widget(self.confirm_button)

        # Prepare a label to display an error if the input is wrong
        self.warning_label = Gtk.Label()

    def validate_input(self, entry, max_length):
        """Changes the CSS class of the entry to error if the input contains non-digit characters"""
        text = entry.get_text()
        if text.isdigit() and len(text) <= max_length:
            entry.remove_css_class("error")
        else:
            entry.add_css_class("error")

    def get_number_entry(self) -> int:
        """Retrieve the entry and check it for correct syntax."""
        entry = self.choose_number_entry.get_text()

        # Remove old warnings
        if self.warning_label.get_parent():
            self.main_box.remove(self.warning_label)

        return int(entry)


class DefineCircuitWindow(DefineObjectWindow):
    """Window that lets the user create a circuit with a chosen number."""
    def __init__(self, create_circuit_callback, parent):
        super().__init__(handle_create_method=lambda button: self.handle_create_circuit(create_circuit_callback),
                         entry_label="Nummer der Meldergruppe:",
                         parent=parent,
                         max_length=5)
        self.set_title("Meldergruppe hinzufügen")

    def handle_create_circuit(self, create_circuit_callback):
        try:
            circuit_number = self.get_number_entry()
        except ValueError:
            self.warning_label.set_markup(f"<span foreground='red'>Geben Sie eine natürliche Zahl ein.</span>")
            self.main_box.insert_child_after(self.warning_label, self.choose_number_box)
            return
        try:
            create_circuit_callback(circuit_number)
        except ValueError as e:
            self.warning_label.set_markup(f"<span foreground='red'>{e}.</span>")
            self.main_box.insert_child_after(self.warning_label, self.choose_number_box)


class DefineDetectorWindow(DefineObjectWindow):
    """Window that lets the user create a detector with a chosen number and description."""
    def __init__(self, circuit_number, create_detector_callback, parent):
        super().__init__(handle_create_method=lambda button: self.handle_create_detector(create_detector_callback),
                         entry_label="Nummer des Melders:",
                         parent=parent,
                         max_length=2)
        self.set_title(f"Melder zu Meldergruppe {circuit_number} hinzufügen")

        self.circuit_number = circuit_number

        self.description_box = DescriptionBox(max_length=20)
        self.main_box.insert_child_after(self.description_box, self.choose_number_box)

    def handle_create_detector(self, create_detector_callback):
        """Retrieve the user entry and create the according detector"""
        try:
            detector_number = self.get_number_entry()
        except ValueError:
            self.warning_label.set_markup(f"<span foreground='red'>Geben Sie eine natürliche Zahl ein.</span>")
            self.main_box.insert_child_after(self.warning_label, self.choose_number_box)
            return
        try:
            description = self.description_box.get_description()
            create_detector_callback(self.circuit_number, detector_number, description)
        except ValueError as e:
            self.warning_label.set_markup(f"<span foreground='red'>{e}</span>")
            self.main_box.insert_child_after(self.warning_label, self.description_box)
