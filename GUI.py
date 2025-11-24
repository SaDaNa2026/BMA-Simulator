import json
import sys

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib, Gdk

from functools import partial


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(500, 500)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_box.set_margin_top(5)
        self.main_box.set_margin_bottom(5)
        self.main_box.set_margin_start(5)
        self.main_box.set_margin_end(5)
        self.main_box.set_spacing(5)
        self.set_child(self.main_box)


        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)

        # Buttons to save and load configurations
        self.save_button = Gtk.Button(label="Speichern")
        self.save_button.connect("clicked", self.on_save_clicked)
        self.header.pack_end(self.save_button)

        self.open_button = Gtk.Button(label="Öffnen")
        self.open_button.connect("clicked", self.on_open_clicked)
        self.header.pack_end(self.open_button)

        # Buttons to add or delete a circuit
        self.create_circuit_button = Gtk.Button(label="Melderlinie hinzufügen")
        self.create_circuit_button.connect("clicked", lambda button, *args: self.on_create_circuit_clicked())
        self.header.pack_start(self.create_circuit_button)

        self.delete_circuit_button = Gtk.Button(label="Melderlinie löschen")
        self.delete_circuit_button.connect("clicked", lambda button, *args: self.delete_circuit())
        self.header.pack_start(self.delete_circuit_button)

    def on_save_clicked(self, button):
        save_dict = {"circuit_dict" : {}, "building_description" : building.description}
        for circuit_number in building.circuit_dict:
            save_dict["circuit_dict"][circuit_number] = [detector_number for detector_number in
                                              building.circuit_dict[circuit_number].detector_dict]
        save_dialog = FileSaveDialog(button, save_dict)
        save_dialog.open_save_dialog()

    def on_open_clicked(self, button):
        """Loads a building configuration from a json file. Does not set the alarm_status of detectors"""
        # Delete all current circuits and their detectors
        delete_list = [num for num in building.circuit_dict]
        for circuit_number in delete_list:
            self.delete_circuit(circuit_number)

        open_dialog = FileOpenDialog(button)
        open_dialog.show_open_dialog(load_data_callback=self.load_data)

    def load_data(self, load_dict):
        # Callback to create circuits and detectors according to the json file
        for circuit_number in load_dict["circuit_dict"]:
            self.create_circuit(int(circuit_number))
            for detector_number in load_dict["circuit_dict"][circuit_number]:
                self.create_detector(int(circuit_number), int(detector_number))


    def on_create_circuit_clicked(self):
        """Creates a DefineCircuitWindow. Callback function for the create_circuit_button."""
        self.define_circuit = DefineCircuitWindow(self.create_circuit)
        self.define_circuit.present()

    def on_circuit_pressed(self, gesture, n_press, x, y, circuit_number):
        """Presents a context menu on a circuit_box"""
        # Get the circuit that was clicked
        circuit = building.circuit_dict[circuit_number]

        # Connect the buttons of the context menu
        circuit.context_menu.delete_circuit_button.connect("clicked", lambda button, *args: self.delete_circuit(circuit_number))

        # Create an invisible rectangle at the position of the click that the context menu points to
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1

        circuit.context_menu.set_pointing_to(rect)
        circuit.context_menu.popup()


    def create_circuit(self, circuit_number=None):
        """Creates a new Circuit instance with automatic numbering"""
        if circuit_number is None:
            circuit_number = len(building.circuit_dict) + 1

        # Set up the circuit and connect all buttons to their callback functions
        circuit = Circuit(circuit_number)
        circuit.add_detector_button.connect("clicked", lambda button, *args: self.create_detector(circuit_number=circuit_number))
        circuit.delete_detector_button.connect("clicked", lambda button, *args: self.delete_detector(circuit_number))
        circuit.click_controller.connect("pressed", partial(self.on_circuit_pressed, circuit_number=circuit_number))

        # Add the circuit to the main window and the circuit dict
        self.main_box.append(circuit)
        building.circuit_dict[circuit_number] = circuit
        return circuit

    def delete_circuit(self, circuit_number=None):
        """Delete the last circuit and print new detector state"""
        if circuit_number is None:
            if len(building.circuit_dict) > 0:
                index = len(building.circuit_dict)
                circuit = building.circuit_dict[index]
            else:
                return
        else:
            index = circuit_number
            circuit = building.circuit_dict[circuit_number]

        self.main_box.remove(circuit)
        del building.circuit_dict[index]
        self.print_detector_state()

    def create_detector(self, circuit_number, detector_number=None, alarm_status=False):
        """Creates a new Detector instance with automatic numbering"""
        if detector_number is None:
            detector_number = len(building.circuit_dict[circuit_number].detector_dict) + 1

        # Create new detector and add it to the detector_dict of the circuit that it belongs to
        detector = Detector(detector_number)
        building.circuit_dict[circuit_number].detector_dict[detector_number] = detector

        # Set the detector switch according to the alarm_status and connect it to its callback function
        detector.alarm_status = alarm_status
        detector.detector_switch.set_active(alarm_status)
        detector.detector_switch.connect('state-set',
                                         self.on_detector_toggled,
                                         circuit_number,
                                         detector_number)

        # Add the detector to its circuit
        circuit = building.circuit_dict[circuit_number]
        circuit.append(detector)
        return detector

    def delete_detector(self, circuit_number, detector_number=None):
        """Delete a detector"""
        # Get the detector object that needs to be removed and the circuit object from which it is removed
        if detector_number is None:
            index = len(building.circuit_dict[circuit_number].detector_dict)
        else:
            index = detector_number

        circuit = building.circuit_dict[circuit_number]
        detector = building.circuit_dict[circuit_number].detector_dict[index]

        # Delete the detector from the dictionary and remove it from its circuit
        del building.circuit_dict[circuit_number].detector_dict[index]
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
    def __init__(self, detector_number, *args, **kwargs):
        super().__init__(*args, orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.detector_switch = Gtk.Switch()
        self.detector_label = Gtk.Label(label=f"Melder {detector_number}")

        self.append(self.detector_switch)
        self.append(self.detector_label)

        self.alarm_status: bool


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
        self.add_detector_button = Gtk.Button(label="Melder hinzufügen")
        self.button_box.append(self.add_detector_button)
        self.delete_detector_button = Gtk.Button(label="Melder löschen")
        self.button_box.append(self.delete_detector_button)

        # Context menu
        self.context_menu = CircuitContextMenu()
        self.context_menu.set_parent(self)

        # A dictionary to manage detectors within this circuit
        self.detector_dict = {}


class Building:
    def __init__(self):
        self.circuit_dict = {}
        self.description = "Hier Gebäudebeschreibung einfügen"



class CircuitContextMenu(Gtk.Popover):
    def __init__(self):
        super().__init__()

        self.set_has_arrow(False)
        self.set_autohide(True)
        self.set_offset(100, 0)

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.set_child(self.vbox)

        self.delete_circuit_button = Gtk.Button(label="Melderlinie löschen")
        self.vbox.append(self.delete_circuit_button)



class FileSaveDialog:
    """Class to save the current building configuration to a json file"""
    def __init__(self, button, save_dict):
        # Pass information about the button that triggered the save dialog and the dictionary that should be saved
        self.button = button
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
        self.save_dialog.save(self.button.get_root(), None, self.on_file_save_response)

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
    def __init__(self, button):
        # Pass information about the button that triggered the load dialog
        self.button = button
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
        self.load_dialog.open(self.button.get_root(),
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


class DefineCircuitWindow(Gtk.Window):
    def __init__(self, create_circuit_callback, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(300, 300)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                margin_top=5,
                                margin_bottom=5,
                                margin_start=5,
                                margin_end=5)
        self.set_child(self.main_box)

        # Labeled Entry field for the user to put in the number of the circuit to be created
        self.choose_circuit_number_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.main_box.append(self.choose_circuit_number_box)

        self.choose_circuit_number_label = Gtk.Label(label="Nummer der Melderlinie")
        self.choose_circuit_number_box.append(self.choose_circuit_number_label)

        self.choose_circuit_number_entry = Gtk.Entry(has_frame=True)
        self.choose_circuit_number_box.append(self.choose_circuit_number_entry)

        # Buttons to cancel or add the circuit
        self.confirmation_box = Gtk.CenterBox()
        self.main_box.append(self.confirmation_box)

        self.cancel_button = Gtk.Button(label="Abbrechen")
        self.cancel_button.connect("clicked", lambda button, *args: self.destroy())
        self.confirmation_box.set_start_widget(self.cancel_button)

        self.confirm_button = Gtk.Button(label="Melderlinie hinzufügen")
        self.confirm_button.connect("clicked",
                                    lambda button, *args: create_circuit_callback(
                                        int(self.choose_circuit_number_entry.get_text())))
        self.confirmation_box.set_end_widget(self.confirm_button)




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
