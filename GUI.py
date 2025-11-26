import json
import sys
from multiprocessing.process import parent_process

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib, Gdk

from functools import partial


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(500, 500)

        # Create a box that contains all other widgets in this window
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_box.set_margin_top(5)
        self.main_box.set_margin_bottom(5)
        self.main_box.set_margin_start(5)
        self.main_box.set_margin_end(5)
        self.main_box.set_spacing(10)
        self.set_child(self.main_box)


        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)

        # Buttons to save and load configurations
        self.save_button = Gtk.Button(label="Speichern")
        self.save_button.set_action_name("win.save")
        self.header.pack_end(self.save_button)

        self.open_button = Gtk.Button(label="Öffnen")
        self.open_button.set_action_name("win.open")
        self.header.pack_end(self.open_button)

        # Buttons to add or delete a circuit
        self.create_circuit_button = Gtk.Button(label="Melderlinie hinzufügen")
        self.create_circuit_button.set_action_name("win.create_circuit")
        self.header.pack_start(self.create_circuit_button)


        # Actions for all buttons to connect to
        self.save_action = Gio.SimpleAction(name="save")
        self.save_action.connect("activate", self.on_save_clicked)
        self.add_action(self.save_action)

        self.open_action = Gio.SimpleAction(name="open")
        self.open_action.connect("activate", self.on_open_clicked)
        self.add_action(self.open_action)

        self.create_circuit_action = Gio.SimpleAction(name="create_circuit")
        self.create_circuit_action.connect("activate", self.on_create_circuit_clicked)
        self.add_action(self.create_circuit_action)

        self.delete_circuit_action = Gio.SimpleAction(name="delete_circuit", parameter_type=GLib.VariantType("i"))
        self.delete_circuit_action.connect("activate", self.delete_circuit)
        self.add_action(self.delete_circuit_action)

        self.create_detector_action = Gio.SimpleAction(name="create_detector", parameter_type=GLib.VariantType("i"))
        self.create_detector_action.connect("activate", self.on_create_detector_clicked)
        self.add_action(self.create_detector_action)

        self.delete_detector_action = Gio.SimpleAction(name="delete_detector", parameter_type=GLib.VariantType("s"))
        self.delete_detector_action.connect("activate", self.delete_detector)
        self.add_action(self.delete_detector_action)


    def on_save_clicked(self, action, parameter):
        """Save the building structure to a json file"""
        save_dict = {"circuit_dict" : {}, "building_description" : building.description}
        for circuit_number in building.circuit_dict:
            save_dict["circuit_dict"][circuit_number] = {}
            for detector_number in building.circuit_dict[circuit_number].detector_dict:
                save_dict["circuit_dict"][circuit_number][detector_number] = building.circuit_dict[circuit_number].detector_dict[detector_number].detector_info
        save_dialog = FileSaveDialog(save_dict)
        save_dialog.open_save_dialog()

    def on_open_clicked(self, action, parameter):
        """Loads a building configuration from a json file. Does not set the alarm_status of detectors"""
        # Delete all current circuits
        delete_list = [num for num in building.circuit_dict]
        for circuit_number in delete_list:
            self.delete_circuit_action.activate(GLib.Variant("i", circuit_number))

        open_dialog = FileOpenDialog()
        open_dialog.show_open_dialog(load_data_callback=self.load_data)

    def load_data(self, load_dict):
        """Create circuits and detectors according to the json file"""
        for circuit_number in load_dict["circuit_dict"]:
            self.create_circuit(int(circuit_number))
            for detector_number in load_dict["circuit_dict"][circuit_number]:
                detector_info = load_dict["circuit_dict"][circuit_number][detector_number]
                self.create_detector(int(circuit_number), int(detector_number), detector_description=detector_info)


    def on_circuit_pressed(self, gesture, n_press, x, y, circuit_number):
        """Presents a context menu on a circuit_box"""
        # Get the circuit that was clicked
        circuit = building.circuit_dict[circuit_number]

        # Create an invisible rectangle at the position of the click that the context menu points to
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1

        circuit.context_menu_popover.set_pointing_to(rect)
        circuit.context_menu_popover.popup()

    def on_detector_pressed(self, gesture, n_press, x, y, circuit_number, detector_number):
        """Presents a context menu on a circuit_box"""
        # Get the circuit that was clicked
        detector = building.circuit_dict[circuit_number].detector_dict[detector_number]

        # Create an invisible rectangle at the position of the click that the context menu points to
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1

        detector.context_menu_popover.set_pointing_to(rect)
        detector.context_menu_popover.popup()

    def on_create_circuit_clicked(self, action, parameter):
        """Creates a DefineCircuitWindow. Callback function for the create_circuit_button."""
        self.define_circuit = DefineCircuitWindow(self.create_circuit, self)
        self.define_circuit.present()

    def on_create_detector_clicked(self, action, parameter):
        """Creates a DefineDetectorWindow. Callback function for the create_detector_button."""
        # Convert the action parameter to int
        circuit_number = parameter.get_int32()

        self.define_detector = DefineDetectorWindow(self.create_detector, circuit_number, self)
        self.define_detector.present()

    def create_circuit(self, circuit_number):
        """Creates a new Circuit instance with automatic numbering"""

        # Raise an exception if a circuit with this number already exists
        if circuit_number in building.circuit_dict:
            raise AttributeError

        circuit = Circuit(circuit_number)

        # Connect the event handler that detects if the circuit is right-clicked
        circuit.click_controller.connect("pressed", partial(self.on_circuit_pressed, circuit_number=circuit_number))

        # Add the circuit to the main window and the circuit dict
        self.main_box.append(circuit)
        building.circuit_dict[circuit_number] = circuit
        return circuit

    def delete_circuit(self, action, parameter):
        """Delete the last circuit and print new detector state"""
        # Convert parameter to int
        circuit_number = parameter.get_int32()
        circuit = building.circuit_dict[circuit_number]

        self.main_box.remove(circuit)
        del building.circuit_dict[circuit_number]
        self.print_detector_state()

    def create_detector(self, circuit_number, detector_number, alarm_status=False, detector_description="Beschreibung"):
        """Creates a new Detector instance"""
        # Raise an exception if a detector with this number already exists
        if detector_number in building.circuit_dict[circuit_number].detector_dict:
            raise AttributeError

        # Create new detector and add it to the detector_dict of the circuit that it belongs to
        detector = Detector(circuit_number, detector_number)
        building.circuit_dict[circuit_number].detector_dict[detector_number] = detector

        detector.detector_info = detector_description

        # Set the detector switch according to the alarm_status and connect it to its callback function
        detector.alarm_status = alarm_status
        detector.detector_switch.set_active(alarm_status)
        detector.detector_switch.connect('state-set',
                                         self.on_detector_toggled,
                                         circuit_number,
                                         detector_number)

        # Connect the event handler that detects if the circuit is right-clicked
        detector.click_controller.connect("pressed", partial(self.on_detector_pressed, circuit_number=circuit_number, detector_number=detector_number))

        # Add the detector to its circuit
        circuit = building.circuit_dict[circuit_number]
        circuit.append(detector)
        return detector

    def delete_detector(self, action, parameter):
        """Delete a specified detector"""
        # Convert parameters to int
        parameter_string = parameter.get_string()
        parameter_list = parameter_string.split(", ")
        circuit_number = int(parameter_list[0])
        detector_number = int(parameter_list[1])

        # Get the corresponding objects
        circuit = building.circuit_dict[circuit_number]
        detector = building.circuit_dict[circuit_number].detector_dict[detector_number]

        # Delete the detector from the dictionary and remove it from its circuit
        del building.circuit_dict[circuit_number].detector_dict[detector_number]
        circuit.remove(detector)
        self.print_detector_state()


    def on_detector_toggled(self, detector_switch, state, circuit_number, detector_number):
        """Callback function for detector_switch. Sets the alarm_status of the detector according to the position of the switch and prints debugging info"""
        building.circuit_dict[circuit_number].detector_dict[detector_number].alarm_status = state
        print(f"Melder {detector_number} in Melderlinie {circuit_number} {'aktiviert' if state else 'deaktiviert'}")
        self.print_detector_state()

    def print_detector_state(self):
        """Prints the active detectors to the console"""
        print(f"Aktive Melder: ")
        for circuit_number in building.circuit_dict.keys():
            for detector_number in building.circuit_dict[circuit_number].detector_dict.keys():
                if building.circuit_dict[circuit_number].detector_dict[detector_number].alarm_status:
                    print(f"Melder {detector_number} in Melderlinie {circuit_number}")


class Detector(Gtk.Box):
    """Contains a switch and a label with the number of the detector"""
    def __init__(self, circuit_number, detector_number, *args, **kwargs):
        super().__init__(*args, orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.detector_switch = Gtk.Switch()
        self.detector_label = Gtk.Label(label=f"Melder {detector_number}")

        self.append(self.detector_switch)
        self.append(self.detector_label)

        self.alarm_status: bool

        self.detector_info: str

        # A tool to register the detector_label being right-clicked
        self.click_controller = Gtk.GestureClick()
        self.click_controller.set_button(Gdk.BUTTON_SECONDARY)
        self.add_controller(self.click_controller)

        # Context menu
        self.menu_model = DetectorContextMenu(circuit_number, detector_number)
        self.context_menu_popover = Gtk.PopoverMenu.new_from_model(self.menu_model)
        self.context_menu_popover.set_parent(self)
        self.context_menu_popover.set_has_arrow(False)


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


class Building:
    def __init__(self):
        self.circuit_dict = {}
        self.description = "Hier Gebäudebeschreibung einfügen"



class CircuitContextMenu(Gio.Menu):
    def __init__(self, circuit_number):
        super().__init__()
        create_detector_item = Gio.MenuItem.new("Melder hinzufügen", "win.create_detector")
        create_detector_item.set_attribute_value("target", GLib.Variant("i", circuit_number))
        self.append_item(create_detector_item)
        delete_circuit_item = Gio.MenuItem.new("Melderlinie löschen", "win.delete_circuit")
        delete_circuit_item.set_attribute_value("target", GLib.Variant("i", circuit_number))
        self.append_item(delete_circuit_item)

class DetectorContextMenu(Gio.Menu):
    def __init__(self, circuit_number, detector_number):
        super().__init__()
        edit_detector_item = Gio.MenuItem.new("Melder bearbeiten", "win.edit_detector")
        edit_detector_item.set_attribute_value("target", GLib.Variant("s", f"{circuit_number}, {detector_number}"))
        self.append_item(edit_detector_item)
        delete_detector_item = Gio.MenuItem.new("Melder löschen", "win.delete_detector")
        delete_detector_item.set_attribute_value("target", GLib.Variant("s", f"{circuit_number}, {detector_number}"))
        self.append_item(delete_detector_item)


class FileSaveDialog:
    """Class to save the current building configuration to a json file"""
    def __init__(self, save_dict):
        self.save_dict = save_dict

        # Present a file save dialog
        current_dir = Gio.File.new_for_path(".")
        self.save_dialog = Gtk.FileDialog(title="Konfiguration speichern",
                                     accept_label="Speichern",
                                     initial_folder=current_dir,
                                     initial_name="Gebäudekonfiguration.json",
                                     modal=True)

        # Add JSON file filter
        json_filter = Gtk.FileFilter()
        json_filter.set_name("JSON Files")
        json_filter.add_pattern("*.json")
        self.save_dialog.set_default_filter(json_filter)

    def open_save_dialog(self):
        """Show the dialog asynchronously"""
        self.save_dialog.save(bma_control.window, None, self.on_file_save_response)

    def on_file_save_response(self, dialog, result):
        try:
            file = dialog.save_finish(result)
            if file is not None:
                path = file.get_path()
                print(f"Saving to: {path}")

                # Example of writing content to the chosen file
                with open(path, "w", encoding="utf-8") as config_dict:
                    json.dump(self.save_dict, config_dict, sort_keys=True, indent=4)

                print("File saved successfully.")
        except GLib.Error as e:
            print(f"Save canceled or failed: {e.message}")


class FileOpenDialog:
    """Class to load a building from a json file"""
    def __init__(self):
        # Create a dictionary to save the data loaded from the json file
        self.load_dict = {}

        # Present a file load dialog
        current_dir = Gio.File.new_for_path(".")
        self.load_dialog = Gtk.FileDialog(title="Konfiguration laden",
                                     accept_label="Öffnen",
                                     initial_folder=current_dir,
                                     modal=True)

        # Add JSON file filter
        json_filter = Gtk.FileFilter()
        json_filter.set_name("JSON Files")
        json_filter.add_pattern("*.json")
        self.load_dialog.set_default_filter(json_filter)

    def show_open_dialog(self, load_data_callback):
        """Show the dialog asynchronously"""
        self.load_dialog.open(bma_control.window,
                              None,
                              partial(self.on_file_open_response, load_data_callback=load_data_callback))

    def on_file_open_response(self, dialog, result, load_data_callback):
        """Callback for the file dialog. Loads the json file from the selected path if it exists and passes the data
        to a callback function."""
        try:
            file = dialog.open_finish(result)
            if file is not None:
                path = file.get_path()
                print(f"Opening: {path}")

                with open(path, "r") as config_dict:
                    # Load building information
                    self.load_dict = json.load(config_dict)
                    building.description = self.load_dict["building_description"]

                    # Send data to the function that adds circuits and detectors
                    GLib.idle_add(load_data_callback, self.load_dict)

                    print("File loaded successfully")

        except GLib.Error as e:
            print(f"Open canceled or failed: {e.message}")


class DefineObjectWindow(Gtk.Window):
    """A base class for Windows that let the use create objects with a chosen number"""
    def __init__(self, handle_create_method, entry_label, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(350, 100)

        # Make it modal and transient for the parent
        self.set_modal(True)
        self.set_transient_for(parent)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                margin_top=5,
                                margin_bottom=5,
                                margin_start=5,
                                margin_end=5,
                                spacing=10)
        self.set_child(self.main_box)

        # Labeled Entry field for the user to put in the number of the circuit to be created
        self.choose_number_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.main_box.append(self.choose_number_box)

        self.choose_number_label = Gtk.Label(label=entry_label)
        self.choose_number_box.append(self.choose_number_label)

        self.choose_number_entry = Gtk.Entry(has_frame=True)
        self.choose_number_box.append(self.choose_number_entry)

        # Buttons to cancel or add the circuit
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
        """Retrieve the entry and check it for correct syntax"""
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
    """A Window that lets the user create a circuit with a chosen number"""
    def __init__(self, create_circuit_callback, parent):
        super().__init__(handle_create_method=lambda button: self.handle_create_circuit(create_circuit_callback), entry_label="Nummer der Melderlinie:", parent=parent)

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
    """A Window that lets the user create a detector with a chosen number and description"""
    def __init__(self, create_detector_callback, circuit_number, parent):
        super().__init__(handle_create_method=lambda button: self.handle_create_detector(create_detector_callback), entry_label="Nummer des Melders:", parent=parent)

        self.circuit_number = circuit_number

        self.description_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.main_box.insert_child_after(self.description_box, self.choose_number_box)

        self.description_label = Gtk.Label(label="Beschreibung")
        self.description_box.append(self.description_label)

        self.description_textview = Gtk.TextView()
        self.description_box.append(self.description_textview)
        self.textbuffer = self.description_textview.get_buffer()

    def handle_create_detector(self, create_detector_callback):
        detector_number = self.get_number_entry()

        # Get contents of the TextView
        start = self.textbuffer.get_start_iter()
        end = self.textbuffer.get_end_iter()
        detector_description = self.textbuffer.get_text(start, end, True)

        if detector_number is not None:
            try:
                create_detector_callback(circuit_number=self.circuit_number, detector_number=detector_number, detector_description=detector_description)
            except AttributeError:
                print("AttributeError")
                self.main_box.insert_child_after(self.same_number_warning_label, self.choose_number_box)



class App(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.window = MainWindow(application=app)
        self.window.present()


building = Building()

bma_control = App(application_id="com.BMA.EXAMPLE")
bma_control.run(sys.argv)
