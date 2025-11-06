import json
import sys

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(300, 300)

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
        self.save_button.connect("clicked", lambda button, *args: save_configuration())
        self.header.pack_end(self.save_button)

        self.load_button = Gtk.Button(label="Öffnen")
        self.load_button.connect("clicked", lambda button, *args: load_configuration())
        self.header.pack_end(self.load_button)

        # Buttons to add or delete a circuit
        self.create_circuit_button = Gtk.Button(label="Melderlinie hinzufügen")
        self.create_circuit_button.connect("clicked", lambda button, *args: create_circuit())
        self.header.pack_start(self.create_circuit_button)

        self.delete_circuit_button = Gtk.Button(label="Melderlinie löschen")
        self.delete_circuit_button.connect("clicked", lambda button, *args: delete_circuit())
        self.header.pack_start(self.delete_circuit_button)



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
        super().__init__(*args, orientation=Gtk.Orientation.VERTICAL, spacing=5)

        self.circuit_label = Gtk.Label()
        self.circuit_label.set_markup(f"<span size='large'>Melderlinie {circuit_number}</span>")
        self.append(self.circuit_label)

        # Buttons to add or delete detectors
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append(self.button_box)
        self.add_detector_button = Gtk.Button(label="Melder hinzufügen")
        self.add_detector_button.connect("clicked",
                                         lambda button, *args: create_detector(circuit_number=circuit_number),
                                         )
        self.button_box.append(self.add_detector_button)
        self.delete_detector_button = Gtk.Button(label="Melder löschen")
        self.delete_detector_button.connect("clicked",
                                            lambda button, *args: delete_detector(circuit_number))
        self.button_box.append(self.delete_detector_button)

        # A dictionary to manage detectors within this circuit
        self.detector_dict = {}


class Building:
    def __init__(self):
        self.circuit_dict = {}


def save_configuration(save_path="Objektkonfiguration.json"):
    """Saves the current building configuration to a json file"""
    # Create a json compatible dictionary containing all information about the current configuration
    save_dict = {}
    for circuit_number in building.circuit_dict:
        save_dict[circuit_number] = [detector_number for detector_number in building.circuit_dict[circuit_number].detector_dict]

    with open(save_path, "w")  as config_dict:
        json.dump(save_dict, config_dict, sort_keys=True, indent=4)

def load_configuration(open_path="Objektkonfiguration.json"):
    """Loads a building configuration from a json file. Does not set the alarm_status of detectors"""
    # Delete all current circuits and their detectors
    delete_list = [num for num in building.circuit_dict]
    for circuit_number in delete_list:
        delete_circuit(circuit_number)

    # Load json file and create the corresponding circuits and detectors
    with open(open_path, "r") as config_dict:
        open_dict = json.load(config_dict)

    for circuit_number in open_dict:
        create_circuit(circuit_number)
        for detector_number in open_dict[circuit_number]:
            create_detector(circuit_number, detector_number)

def create_circuit(circuit_number=None):
    """Creates a new Circuit instance with automatic numbering"""
    if circuit_number is None:
        circuit_number = len(building.circuit_dict) + 1

    circuit = Circuit(circuit_number)
    app.window.main_box.append(circuit)
    building.circuit_dict[circuit_number] = circuit
    return circuit

def delete_circuit(circuit_number=None):
    """Remove the last circuit and print new detector state"""
    if circuit_number is None:
        if len(building.circuit_dict) > 0:
            index = len(building.circuit_dict)
            circuit = building.circuit_dict[index]
        else:
            return
    else:
        index = circuit_number
        circuit = building.circuit_dict[circuit_number]

    app.window.main_box.remove(circuit)
    del building.circuit_dict[index]
    print_detector_state()



def create_detector(circuit_number, detector_number=None, alarm_status=False):
    """Creates a new Detector instance with automatic numbering"""
    if detector_number is None:
        detector_number = len(building.circuit_dict[circuit_number].detector_dict) + 1

    # Create new detector and add it to the detector_dict of the circuit that it belongs to
    detector = Detector(detector_number)
    building.circuit_dict[circuit_number].detector_dict[detector_number] = detector

    # Set the detector switch according to the alarm_status and connect it to its callback function
    detector.alarm_status = alarm_status
    detector.detector_switch.set_active(alarm_status)
    detector.detector_switch.connect('state-set', on_detector_toggled, circuit_number, detector_number)

    # Add the detector to its circuit
    circuit = building.circuit_dict[circuit_number]
    circuit.append(detector)
    return detector

def delete_detector(circuit_number):
    """Remove the last detector (needs consecutive numbering for now"""
    # Get the detector object that needs to be removed and the circuit object from which it is removed
    index = len(building.circuit_dict[circuit_number].detector_dict)
    circuit = building.circuit_dict[circuit_number]
    detector = building.circuit_dict[circuit_number].detector_dict[index]

    del building.circuit_dict[circuit_number].detector_dict[index]
    circuit.remove(detector)
    print_detector_state()


def on_detector_toggled(detector_switch, state, circuit_number, detector_number):
    """Callback function for detector_switch. Sets the alarm_status of the detector according to the postion of the switch and prints debugging info"""
    building.circuit_dict[circuit_number].detector_dict[detector_number].alarm_status = state
    print(f"Melder {detector_number} in Melderlinie {circuit_number} {'aktiviert' if state else 'deaktiviert'}")
    print_detector_state()

def print_detector_state():
    """Prints the active detectors to the console"""
    print(f"Aktive Melder: ")
    for circuit_number in building.circuit_dict.keys():
        for detector_number in building.circuit_dict[circuit_number].detector_dict.keys():
            if building.circuit_dict[circuit_number].detector_dict[detector_number].alarm_status:
                print(f"Melder {detector_number} in Melderlinie {circuit_number}")


class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.window = MainWindow(application=app)
        self.window.present()


building = Building()

app = MyApp(application_id="com.BMA.EXAMPLE")
app.run(sys.argv)
