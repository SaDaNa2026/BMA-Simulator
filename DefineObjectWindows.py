import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from DescriptionBox import DescriptionBox


class DefineObjectWindow(Gtk.Window):
    """Base class for a Window that lets the use create an object with a chosen number."""
    def __init__(self, handle_create_method, entry_label, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(350, 100)

        # Make the window modal and transient for the parent (parent window won't take focus until this window is closed)
        self.set_modal(True)
        self.set_transient_for(parent)

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

        self.choose_number_entry = Gtk.Entry(has_frame=True)
        self.choose_number_box.append(self.choose_number_entry)

        # Buttons to cancel or add the object
        self.confirmation_box = Gtk.CenterBox()
        self.main_box.append(self.confirmation_box)

        self.cancel_button = Gtk.Button(label="Schließen")
        self.cancel_button.connect("clicked", lambda button, *args: self.destroy())
        self.confirmation_box.set_start_widget(self.cancel_button)

        self.confirm_button = Gtk.Button(label="Hinzufügen")
        self.confirm_button.connect("clicked", handle_create_method)
        self.confirmation_box.set_end_widget(self.confirm_button)

        # Prepare labels if the ínput is incorrect
        self.same_number_warning_label = Gtk.Label()
        self.same_number_warning_label.set_markup(
            f"<span foreground='red'>Wählen Sie eine Nummer, die nicht bereits existiert.</span>")

        self.wrong_type_warning_label = Gtk.Label()
        self.wrong_type_warning_label.set_markup(f"<span foreground='red'>Geben Sie eine natürliche Zahl ein.</span>")

        self.small_number_warning_label = Gtk.Label()
        self.small_number_warning_label.set_markup(f"<span foreground='red'>Die Zahl muss größer 0 sein.</span>")

        self.large_number_warning_label = Gtk.Label()
        self.large_number_warning_label.set_markup(f"<span foreground='red'>Sie können nicht ernsthaft einen solch "
                                                   f"großen Wert benötigen.\nGeben Sie einen Werten kleiner "
                                                   f"1.000.000.000 ein.</span>")

    def get_number_entry(self):
        """Retrieve the entry and check it for correct syntax."""
        entry = self.choose_number_entry.get_text()

        # Remove old warnings
        if self.wrong_type_warning_label.get_parent():
            self.main_box.remove(self.wrong_type_warning_label)
        if self.same_number_warning_label.get_parent():
            self.main_box.remove(self.same_number_warning_label)
        if self.small_number_warning_label.get_parent():
            self.main_box.remove(self.small_number_warning_label)
        if self.large_number_warning_label.get_parent():
            self.main_box.remove(self.large_number_warning_label)

        # Check for correct type
        try:
            object_number = int(entry)
            if object_number <= 0:
                raise ValueError("small")
            if object_number > 999999999:
                raise ValueError("large")
            return object_number
        except ValueError as e:
            print("Input a positive integer smaller than 1000000000")
            if str(e) == "small":
                self.main_box.insert_child_after(self.small_number_warning_label, self.choose_number_box)
            if str(e) == "large":
                self.main_box.insert_child_after(self.large_number_warning_label, self.choose_number_box)
            else:
                self.main_box.insert_child_after(self.wrong_type_warning_label, self.choose_number_box)


class DefineCircuitWindow(DefineObjectWindow):
    """Window that lets the user create a circuit with a chosen number."""
    def __init__(self, create_circuit_callback, parent):
        super().__init__(handle_create_method=lambda button: self.handle_create_circuit(create_circuit_callback), entry_label="Nummer der Melderlinie:", parent=parent)
        self.set_title("Melderlinie hinzufügen")

    def handle_create_circuit(self, create_circuit_callback):
        circuit_number = self.get_number_entry()

        # Check if the entry could be retrieved and create the circuit
        if circuit_number is not None:
            try:
                create_circuit_callback(circuit_number)
            except AttributeError:
                print("AttributeError")
                self.main_box.insert_child_after(self.same_number_warning_label, self.choose_number_box)


class DefineDetectorWindow(DefineObjectWindow):
    """Window that lets the user create a detector with a chosen number and description."""
    def __init__(self, circuit_number, create_detector_callback, parent):
        super().__init__(handle_create_method=lambda button: self.handle_create_detector(create_detector_callback), entry_label="Nummer des Melders:", parent=parent)
        self.set_title(f"Melder zu Melderlinie {circuit_number} hinzufügen")

        self.circuit_number = circuit_number

        self.description_box = DescriptionBox()
        self.main_box.insert_child_after(self.description_box, self.choose_number_box)

    def handle_create_detector(self, create_detector_callback):
        """Retrieve the user entry and create the according detector"""
        detector_number = self.get_number_entry()
        detector_description = self.description_box.get_description()

        if detector_number is not None:
            try:
                create_detector_callback(circuit_number=self.circuit_number, detector_number=detector_number, detector_description=detector_description)
            except AttributeError:
                print("AttributeError")
                self.main_box.insert_child_after(self.same_number_warning_label, self.choose_number_box)
