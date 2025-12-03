from functools import partial

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib, Gdk

from Building import Building
from Circuit import Circuit
from DefineObjectWindows import DefineCircuitWindow, DefineDetectorWindow
from Detector import Detector
from EditWindows import EditDetectorWindow, EditBuildingWindow
from FileOperations import FileOperations
from Menus import DataMenu, AddMenu


class MainWindow(Gtk.ApplicationWindow):
    """Main Window of the application. Displays Detectors grouped in circuits as well as menus to access all
    application functionality."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(700, 500)
        self.set_title("Steuerung Übungs-BMA")

        # Create a box that contains all other widgets in this window
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_box.set_margin_top(5)
        self.main_box.set_margin_bottom(5)
        self.main_box.set_margin_start(5)
        self.main_box.set_margin_end(5)
        self.main_box.set_spacing(20)
        self.set_child(self.main_box)


        # Definition of the window header
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)

        # MenuButton to handle data operations
        self.data_menu = DataMenu()
        self.data_menubutton = Gtk.MenuButton(label="Datei", direction=Gtk.ArrowType.DOWN)
        self.data_menubutton.set_menu_model(self.data_menu)
        self.header.pack_start(self.data_menubutton)

        # MenuButton to add a circuit or edit the building description
        self.add_menu = AddMenu()
        self.add_menubutton = Gtk.MenuButton(label="+", direction=Gtk.ArrowType.DOWN)
        self.add_menubutton.set_menu_model(self.add_menu)
        self.add_menubutton.set_visible(False)
        self.header.pack_start(self.add_menubutton)


        # Actions for all buttons to connect to
        data_action_entries = [("save_building", self.on_save_building_clicked, None),
                               ("save_scenario", self.on_save_scenario_clicked, None),
                               ("open", self.on_open_clicked, None),
                               ("edit_mode", None, None, "false", self.on_edit_mode_clicked)]

        edit_action_entries = [("create_circuit", self.on_create_circuit_clicked, None),
                               ("delete_circuit", self.on_delete_circuit_clicked, "i"),
                               ("create_detector", self.on_create_detector_clicked, "i"),
                               ("delete_detector", self.on_delete_detector_clicked, "s"),
                               ("edit_detector", self.on_edit_detector_clicked, "s"),
                               ("edit_building", self.on_edit_building_clicked, None)]


        self.data_action_group = Gio.SimpleActionGroup.new()
        self.data_action_group.add_action_entries(data_action_entries, None)
        self.insert_action_group("data", self.data_action_group)

        self.edit_action_group = Gio.SimpleActionGroup.new()
        self.edit_action_group.add_action_entries(edit_action_entries, None)
        self.insert_action_group("edit", self.edit_action_group)

        # Set edit actions disabled
        for name in self.edit_action_group.list_actions():
            action = self.edit_action_group.lookup_action(name)
            if isinstance(action, Gio.SimpleAction):
                action.set_enabled(False)


    def on_save_building_clicked(self, *args):
        """Create a FileSaveDialog to save the building configuration."""
        FileOperations.show_save_dialog(self, "building")

    def on_save_scenario_clicked(self, *args):
        """Create a FileSaveDialog to save the scenario."""
        FileOperations.show_save_dialog(self, "scenario")

    def on_open_clicked(self, *args):
        """Creates a FileOpenDialog."""
        FileOperations.show_open_dialog(self)

    def on_circuit_pressed(self, gesture, n_press, x, y, circuit_number):
        """Present a context menu on a circuit_box if edit mode is enabled."""
        # Don't respond if edit mode is disabled
        if not self.data_action_group.lookup_action("edit_mode").get_state().get_boolean():
            return

        # Get the circuit that was clicked
        circuit = Building.circuit_dict[circuit_number]

        # Create an invisible rectangle at the position of the click that the context menu points to
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1

        circuit.context_menu_popover.set_pointing_to(rect)
        circuit.context_menu_popover.popup()

    def on_detector_pressed(self, gesture, n_press, x, y, circuit_number, detector_number):
        """Present a context menu on a circuit_bo if edit mode is enabled."""
        # Don't respond if edit mode is disabled
        if not self.data_action_group.lookup_action("edit_mode").get_state().get_boolean():
            return

        # Get the circuit that was clicked
        detector = Building.circuit_dict[circuit_number].detector_dict[detector_number]

        # Create an invisible rectangle at the position of the click that the context menu points to
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1

        detector.context_menu_popover.set_pointing_to(rect)
        detector.context_menu_popover.popup()

    def on_create_circuit_clicked(self, *args):
        """Create a DefineCircuitWindow."""
        self.define_circuit = DefineCircuitWindow(self.create_circuit, self)
        self.define_circuit.present()

    def on_create_detector_clicked(self, action, parameter, *args):
        """Creates a DefineDetectorWindow."""
        # Convert the action parameter to int
        circuit_number = parameter.get_int32()

        self.define_detector = DefineDetectorWindow(circuit_number, self.create_detector, self)
        self.define_detector.present()

    def on_edit_detector_clicked(self, action, parameter, *args):
        """Create an EditDetectorWindow."""
        # Convert parameters to int
        parameter_string = parameter.get_string()
        parameter_list = parameter_string.split(", ")
        circuit_number = int(parameter_list[0])
        detector_number = int(parameter_list[1])

        self.edit_detector_window = EditDetectorWindow(circuit_number, detector_number, self.edit_detector, self)
        self.edit_detector_window.present()

    def on_edit_building_clicked(self, *args):
        """Create an EditBuildingWindow."""
        self.edit_building_window = EditBuildingWindow(self)
        self.edit_building_window.present()

    def on_delete_circuit_clicked(self, action, parameter, *args):
        """Convert parameter to int and call the delete_circuit method."""
        circuit_number = parameter.get_int32()
        self.delete_circuit(circuit_number)

    def on_delete_detector_clicked(self, action, parameter, *args):
        """Convert parameters to int and call the delete_detector method."""
        parameter_string = parameter.get_string()
        parameter_list = parameter_string.split(", ")
        circuit_number = int(parameter_list[0])
        detector_number = int(parameter_list[1])

        self.delete_detector(circuit_number, detector_number)

    def on_edit_mode_clicked(self, action, *args):
        """Toggle between normal mode and edit mode."""
        # Update the action’s stored state
        current_state = action.get_state().get_boolean()
        new_state =  not current_state
        action.set_state(GLib.Variant.new_boolean(new_state))

        # Update UI
        for name in self.edit_action_group.list_actions():
            action = self.edit_action_group.lookup_action(name)
            if isinstance(action, Gio.SimpleAction):
                action.set_enabled(new_state)

        self.add_menubutton.set_visible(new_state)

        # Print debug info
        if new_state:
            print("Edit mode active")

        else:
            print("Edit mode inactive")


    def create_circuit(self, circuit_number):
        """Create a new Circuit instance."""

        # Raise an exception if a circuit with this number already exists
        if circuit_number in Building.circuit_dict:
            raise AttributeError

        circuit = Circuit(circuit_number)

        # Connect the event handler that detects if the circuit is right-clicked
        circuit.click_controller.connect("pressed", partial(self.on_circuit_pressed, circuit_number=circuit_number))

        # Add the circuit to the main window and the circuit dict
        self.main_box.append(circuit)
        Building.circuit_dict[circuit_number] = circuit
        return circuit

    def delete_circuit(self, circuit_number):
        """Delete the specified circuit and print the new detector state."""

        circuit = Building.circuit_dict[circuit_number]
        print(f"delete circuit {circuit_number}")

        self.main_box.remove(circuit)
        del Building.circuit_dict[circuit_number]
        self.print_detector_state()

    def create_detector(self, circuit_number, detector_number, alarm_status=False, detector_description="Beschreibung"):
        """Create a new Detector instance."""
        # Raise an exception if a detector with this number already exists
        if detector_number in Building.circuit_dict[circuit_number].detector_dict:
            raise AttributeError

        # Create new detector and add it to the detector_dict of the circuit that it belongs to
        detector = Detector(circuit_number, detector_number)
        Building.circuit_dict[circuit_number].detector_dict[detector_number] = detector

        detector.description = detector_description

        # Set the detector switch according to the alarm_status and connect it to its callback function
        detector.alarm_status = alarm_status
        detector.detector_switch.set_active(alarm_status)
        detector.detector_switch.connect('state-set',
                                         self.on_detector_toggled,
                                         circuit_number,
                                         detector_number)

        # Connect the event handler that detects if the circuit is right-clicked
        detector.click_controller.connect("pressed", partial(self.on_detector_pressed,
                                                             circuit_number=circuit_number,
                                                             detector_number=detector_number))

        # Add the detector to its circuit
        circuit = Building.circuit_dict[circuit_number]
        circuit.append(detector)
        return detector

    def delete_detector(self, circuit_number, detector_number):
        """Delete a specified detector."""
        # Get the corresponding objects
        circuit = Building.circuit_dict[circuit_number]
        detector = Building.circuit_dict[circuit_number].detector_dict[detector_number]

        # Delete the detector from the dictionary and remove it from its circuit
        del Building.circuit_dict[circuit_number].detector_dict[detector_number]
        circuit.remove(detector)
        self.print_detector_state()

    def edit_detector(self, circuit_number, detector_number, description):
        """Change a specified detector's description."""
        detector = Building.circuit_dict[circuit_number].detector_dict[detector_number]
        detector.description = description


    def on_detector_toggled(self, detector_switch, state, circuit_number, detector_number):
        """Callback function for detector_switch. Set the alarm_status of the detector according to the position of
        the switch and print debugging info."""
        Building.circuit_dict[circuit_number].detector_dict[detector_number].alarm_status = state
        print(f"Melder {detector_number} in Melderlinie {circuit_number} {'aktiviert' if state else 'deaktiviert'}")
        self.print_detector_state()

    def print_detector_state(self):
        """Print the active detectors to the console."""
        print(f"Aktive Melder: ")
        for circuit_number in Building.circuit_dict.keys():
            for detector_number in Building.circuit_dict[circuit_number].detector_dict.keys():
                if Building.circuit_dict[circuit_number].detector_dict[detector_number].alarm_status:
                    print(f"Melder {detector_number} in Melderlinie {circuit_number}")
