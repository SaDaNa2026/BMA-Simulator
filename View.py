import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib, Gdk
from functools import partial

from MainWindow import MainWindow
from Circuit import Circuit
from Detector import Detector
from FileOpenDialog import FileOpenDialog
from FileSaveDialog import FileSaveDialog
from DefineObjectWindows import DefineCircuitWindow, DefineDetectorWindow
from EditWindows import EditBuildingWindow, EditDetectorWindow


class App(Gtk.Application):
    def __init__(self, data_action_entries, edit_action_entries, hidden_action_entries, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

        # Dictionary to store references to the widget objects
        self.circuit_dict = {}

        # Add the action entries to groups
        self.data_action_group = Gio.SimpleActionGroup.new()
        self.data_action_group.add_action_entries(data_action_entries, None)

        self.edit_action_group = Gio.SimpleActionGroup.new()
        self.edit_action_group.add_action_entries(edit_action_entries, None)

        self.hidden_action_group = Gio.SimpleActionGroup()
        self.hidden_action_group.add_action_entries(hidden_action_entries, None)

        # Set edit actions disabled
        for name in self.edit_action_group.list_actions():
            action = self.edit_action_group.lookup_action(name)
            if isinstance(action, Gio.SimpleAction):
                action.set_enabled(False)

        # Add shortcuts to the actions
        self.set_accels_for_action("data.save_building", ["<Ctrl><Shift>S"])
        self.set_accels_for_action("data.save_scenario", ["<Ctrl>S"])
        self.set_accels_for_action("data.open", ["<Ctrl>O"])
        self.set_accels_for_action("data.edit_mode", ["<Ctrl>E"])

        self.window = MainWindow(data_action_group=self.data_action_group,
                                 edit_action_group=self.edit_action_group,
                                 hidden_action_group=self.hidden_action_group)

    def on_activate(self, app):
        self.window.set_application(app)
        self.window.present()

    def show_open_dialog(self, open_response_callback):
        """Show a FileOpenDialog."""
        file_open_dialog = FileOpenDialog()
        file_open_dialog.open(self.window, None, open_response_callback)

    def show_save_dialog(self, save_response_callback, file_type):
        """Show a FileSaveDialog."""
        file_save_dialog = FileSaveDialog(file_type)
        file_save_dialog.save(self.window, None, partial(save_response_callback, file_type=file_type))

    def show_error_alert(self, error_message, error_detail):
        """Display an error alert."""
        error_alert = Gtk.AlertDialog(message=error_message, detail=error_detail, modal=True)
        error_alert.show(self.window)

    def show_define_circuit_window(self, create_circuit_callback):
        self.define_circuit_window = DefineCircuitWindow(create_circuit_callback, self.window)
        self.define_circuit_window.present()

    def show_define_detector_window(self, circuit_number, create_detector_callback):
        self.define_detector_window = DefineDetectorWindow(circuit_number, create_detector_callback, self.window)
        self.define_detector_window.present()

    def show_edit_building_window(self, edit_building_callback, current_description):
        self.edit_building_window = EditBuildingWindow(edit_building_callback, self.window, current_description)
        self.edit_building_window.present()

    def show_edit_detector_window(self, circuit_number, detector_number, edit_detector_callback, current_description):
        self.edit_detector_window = EditDetectorWindow(circuit_number, detector_number, edit_detector_callback, self.window, current_description)
        self.edit_detector_window.present()


    def on_circuit_pressed(self, gesture, n_press, x, y, circuit_number: int) -> None:
        """Present a context menu on a circuit if edit mode is enabled."""
        # Don't respond if edit mode is disabled
        if not self.data_action_group.lookup_action("edit_mode").get_state().get_boolean():
            return

        # Get the circuit that was clicked
        circuit = self.circuit_dict[circuit_number]

        # Create an invisible rectangle at the position of the click that the context menu points to
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1

        circuit.context_menu_popover.set_pointing_to(rect)
        circuit.context_menu_popover.popup()

    def on_detector_pressed(self, gesture, n_press, x, y, circuit_number: int, detector_number: int) -> None:
        """Present a context menu on a detector if edit mode is enabled."""
        # Don't respond if edit mode is disabled
        if not self.data_action_group.lookup_action("edit_mode").get_state().get_boolean():
            return

        # Get the detector that was clicked
        detector = self.circuit_dict[circuit_number].detector_dict[detector_number]

        # Create an invisible rectangle at the position of the click that the context menu points to
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1

        detector.context_menu_popover.set_pointing_to(rect)
        detector.context_menu_popover.popup()

    def toggle_edit_mode(self, action, *args) -> None:
        """Toggle between normal mode and edit mode."""
        # Update the action’s stored state
        current_state = action.get_state().get_boolean()
        new_state = not current_state
        action.set_state(GLib.Variant.new_boolean(new_state))

        # Update UI
        for name in self.edit_action_group.list_actions():
            action = self.edit_action_group.lookup_action(name)
            if isinstance(action, Gio.SimpleAction):
                action.set_enabled(new_state)

        self.window.add_menubutton.set_visible(new_state)

        # Print debug info
        if new_state:
            print("Edit mode active")

        else:
            print("Edit mode inactive")

    def add_circuit(self, circuit_number: int) -> None:
        """Create a new Circuit instance and add it to the window."""
        circuit = Circuit(circuit_number)
        self.circuit_dict[circuit_number] = circuit
        # Connect the event handler that detects if the circuit is right-clicked
        circuit.click_controller.connect("pressed", partial(self.on_circuit_pressed, circuit_number=circuit_number))
        self.window.main_box.append(circuit)

    def delete_circuit(self, circuit_number: int) -> None:
        """Delete the specified circuit."""
        circuit = self.circuit_dict[circuit_number]
        self.window.main_box.remove(circuit)
        del self.circuit_dict[circuit_number]

    def add_detector(self, circuit_number: int, detector_number: int, alarm_status: bool = False) -> None:
        """Create a new Detector instance and add it to the window."""
        detector = Detector(circuit_number, detector_number)
        self.circuit_dict[circuit_number].detector_dict[detector_number] = detector

        # Set the detector switch according to the alarm_status and connect it to its callback function
        detector.detector_switch.set_action_name("hidden_actions.detector_toggle")
        detector.detector_switch.set_action_target_value(GLib.Variant("s", f"{circuit_number}, {detector_number}"))
        detector.detector_switch.set_active(alarm_status)

        # Connect the event handler that detects if the circuit is right-clicked
        detector.click_controller.connect("pressed", partial(self.on_detector_pressed,
                                                             circuit_number=circuit_number,
                                                             detector_number=detector_number))

        # Add the detector to its circuit
        circuit = self.circuit_dict[circuit_number]
        circuit.append(detector)

    def delete_detector(self, circuit_number: int, detector_number: int) -> None:
        """Delete a specified detector."""
        # Get the corresponding objects
        circuit = self.circuit_dict[circuit_number]
        detector = self.circuit_dict[circuit_number].detector_dict[detector_number]

        # Delete the detector from the dictionary and remove it from its circuit
        circuit.remove(detector)
        del self.circuit_dict[circuit_number].detector_dict[detector_number]

    def write_to_console(self, text: str):
        if not isinstance(text, str):
            raise TypeError("Text must be str")
        self.window.console_buffer.set_text(text)

    def clear(self):
        delete_list = [num for num in self.circuit_dict]
        for circuit_number in delete_list:
            self.delete_circuit(circuit_number)