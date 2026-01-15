import sys
from FileOperations import FileOperations
import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib
from json import JSONDecodeError
from mcp23017 import MCP23017, i2c, INPUT
import smbus3

from Model import BuildingModel
from View import App
from LCDController import LCDController


class Controller:
    def __init__(self):
        self.model = BuildingModel()
        self.lcd = LCDController(self.model)

        # Actions for all buttons to connect to
        data_action_entries = [("save_building", self.on_save_building_clicked, None),
                               ("save_scenario", self.on_save_scenario_clicked, None),
                               ("open", self.on_open_clicked, None),
                               ("edit_mode", None, None, "false", self.on_edit_mode_clicked)]

        edit_action_entries = [("create_circuit", self.on_add_circuit_clicked, None),
                               ("delete_circuit", self.on_delete_circuit_clicked, "i"),
                               ("create_detector", self.on_add_detector_clicked, "i"),
                               ("delete_detector", self.on_delete_detector_clicked, "s"),
                               ("edit_detector", self.on_edit_detector_clicked, "s"),
                               ("edit_building", self.on_edit_building_clicked, None)]

        hidden_action_entries = [("detector_toggle", self.on_detector_toggled, "s"),
                                 ("previous_alarm", self.lcd.previous_alarm, None),
                                 ("next_alarm", self.lcd.next_alarm, None),
                                 ("clear_alarms", self.on_clear_alarms_clicked, None)]

        self.view = App(data_action_entries, edit_action_entries, hidden_action_entries, application_id="org.example.BMA-control")
        self.view.run(sys.argv)

        # Set up the port expander
        # i2c_controller = i2c.I2C(smbus3.SMBus(1))
        # self.mcp = MCP23017(0x27, i2c_controller)
        # self.mcp.pin_mode(0, INPUT)

        # GLib.timeout_add(100, self.poll_buttons)

    def poll_buttons(self):
        print(self.mcp.digital_read(0))

    def on_save_building_clicked(self, *args):
        """Create a FileSaveDialog to save the building configuration."""
        self.view.show_save_dialog(self.on_file_save_response, "building")

    def on_save_scenario_clicked(self, *args):
        """Create a FileSaveDialog to save the scenario."""
        self.view.show_save_dialog(self.on_file_save_response, "scenario")

    def on_file_save_response(self, dialog, result, file_type: str):
        try:
            file = FileOperations.retrieve_save_file(dialog, result)

        except GLib.Error as e:
            print(f"Save canceled or failed: {e.message}")
            if not e.message == "Dismissed by user":
                self.view.show_error_alert("Speichern fehlgeschlagen", e.message)
            return

        if file_type == "building":
            save_dict = FileOperations.create_building_save_dict(self.model)

        elif file_type == "scenario":
            save_dict = FileOperations.create_scenario_save_dict(self.model)

        else:
            self.view.show_error_alert("Invalide Dateiendung", "Datein müssen auf .building oder .scenario enden")
            return

        FileOperations.save_to_file(file, save_dict)

    def on_open_clicked(self, *args):
        """Creates a FileOpenDialog."""
        self.view.show_open_dialog(self.on_file_open_response)

    def on_file_open_response(self, dialog, result):
        try:
            file = FileOperations.retrieve_open_file(dialog, result)
        except GLib.Error as e:
            print(f"Open canceled or failed: {e.message}")
            if not e.message == "Dismissed by user":
                self.view.show_error_alert("Öffnen fehlgeschlagen", e.message)
            return
        self.load_file(file)

    def load_file(self, file):
        try:
            load_dict, file_type = FileOperations.open_file(file)

        except JSONDecodeError:
            self.view.show_error_alert("Fehler beim Laden der Datei",
                                       f"Invalides Dateiformat von {file.get_path()}\nStellen Sie sicher, "
                                       f"dass die Datei dem JSON-Standard entspricht.")
            return True

        except RuntimeError as e:
            self.view.show_error_alert("Fehler beim Laden der Datei", e)
            return True

        if file_type == "building":
            try:
                FileOperations.load_building_config(self.model, load_dict)
                self.redraw_view()

            except KeyError as e:
                print(f"KeyError: {e}")
                self.view.show_error_alert(".building-Datei invalide", f"Key {e} fehlt oder ist falsch geschrieben.")
                self.model.clear_data()
                return True

            except (ValueError, TypeError) as e:
                print(f"ValueError/TypeError: {e}")
                self.view.show_error_alert(".building-Datei invalide", e)
                self.model.clear_data()
                return True

        else:
            try:
                FileOperations.get_scenario_directory(file, load_dict, self.load_scenario_callback)

            except GLib.Error as error:
                print(f"Error listing directory: {error.message}")
                self.view.show_error_alert(f"Öffnen fehlgeschlagen", error.message)
                return True

    def load_scenario_callback(self, building_file, scenario_load_dict):
        building_error = self.load_file(building_file)
        if building_error:
            return

        try:
            FileOperations.apply_scenario(scenario_load_dict, self.model)

        except TypeError as e:
            self.view.show_error_alert("scenario-Datei invalide", f"TypeError: {e}")
            return

        except KeyError as e:
            self.view.show_error_alert(".scenario-Datei invalide", f"KeyError: {e}")
            return

        except SyntaxError as e:
            self.view.show_error_alert(".scenario-Datei invalide", f"SyntaxError: {e}")
            return

        except ValueError as e:
            self.view.show_error_alert(".scenario-Datei invalide", f"ValueError: {e}")
            return

        self.redraw_view()
        self.print_detector_state()
        for detector in self.model.get_active_detectors():
            self.lcd.add_alarm(detector)


    def on_detector_toggled(self, action, parameter, *args):
        """Callback function for detector_switch. Set the alarm_status of the detector according to the position of
        the switch and print debugging info."""
        # Convert parameter to int
        parameter_string = parameter.get_string()
        parameter_list = parameter_string.split(", ")
        circuit_number = int(parameter_list[0])
        detector_number = int(parameter_list[1])

        # Toggle alarm status
        current_state = self.model.get_detector_alarm_status(circuit_number, detector_number)
        new_state = not current_state
        self.model.set_detector_alarm_status(circuit_number, detector_number, new_state)

        print(f"Melder {detector_number} in Melderlinie {circuit_number} {'aktiviert' if new_state else 'deaktiviert'}")
        self.print_detector_state()
        self.redraw_view()
        if new_state:
            self.lcd.add_alarm((circuit_number, detector_number))

    def on_edit_mode_clicked(self, action, *args):
        self.view.toggle_edit_mode(action, *args)

    def on_add_circuit_clicked(self, *args):
        """Create a DefineCircuitWindow."""
        self.view.show_define_circuit_window(self.add_circuit_callback)

    def on_add_detector_clicked(self, action, parameter, *args):
        """Creates a DefineDetectorWindow."""
        # Convert the action parameter to int
        circuit_number = parameter.get_int32()
        self.view.show_define_detector_window(circuit_number, self.add_detector_callback)

    def on_edit_detector_clicked(self, action, parameter, *args):
        """Create an EditDetectorWindow."""
        # Convert parameters to int
        parameter_string = parameter.get_string()
        parameter_list = parameter_string.split(", ")
        circuit_number = int(parameter_list[0])
        detector_number = int(parameter_list[1])
        current_description = self.model.get_detector_description(circuit_number, detector_number)

        self.view.show_edit_detector_window(circuit_number, detector_number, self.edit_detector_callback, current_description)

    def on_edit_building_clicked(self, *args):
        """Create an EditBuildingWindow."""
        current_description = self.model.get_building_description()
        self.view.show_edit_building_window(self.edit_building_callback, current_description)

    def on_delete_circuit_clicked(self, action, parameter, *args):
        """Convert parameter to int and call the delete_circuit method."""
        circuit_number = parameter.get_int32()
        self.model.delete_circuit(circuit_number)
        self.redraw_view()
        self.print_detector_state()

    def on_delete_detector_clicked(self, action, parameter, *args):
        """Convert parameters to int and delete the specified detector."""
        parameter_string = parameter.get_string()
        parameter_list = parameter_string.split(", ")
        circuit_number = int(parameter_list[0])
        detector_number = int(parameter_list[1])

        self.model.delete_detector(circuit_number, detector_number)
        self.redraw_view()
        self.print_detector_state()

    def on_clear_alarms_clicked(self, *args):
        """Clear all alarms."""
        self.model.clear_alarms()
        self.lcd.clear_alarms()
        self.redraw_view()
        self.print_detector_state()

    def add_circuit_callback(self, circuit_number):
        self.model.add_circuit(circuit_number)
        self.redraw_view()

    def add_detector_callback(self, circuit_number, detector_number, detector_description):
        self.model.add_detector(circuit_number, detector_number, detector_description)
        self.redraw_view()

    def edit_building_callback(self, description: str):
        """Change the building description."""
        self.model.set_building_description(description)

    def edit_detector_callback(self, circuit_number: int, detector_number: int, description: str):
        """Change a specified detector's description."""
        self.model.set_detector_description(circuit_number, detector_number, description)
        self.print_detector_state()


    def print_detector_state(self):
        """Print the active detectors to the console."""
        active_detector_list = self.model.get_active_detectors()
        active_detector_text = ""
        print("Aktive Melder:")

        for reference in active_detector_list:
            circuit_number = reference[0]
            detector_number = reference[1]
            detector_description = self.model.get_detector_description(circuit_number, detector_number)
            for i in range(4-len(str(circuit_number))):
                active_detector_text += " "
            active_detector_text += f"{circuit_number}/{detector_number}"
            for i in range(2-len(str(detector_number))):
                active_detector_text += " "
            active_detector_text += f"        {detector_description}\n"

        print(active_detector_text)
        self.view.write_to_console(active_detector_text)

    def redraw_view(self):
        """Redraw the view according to the current model state."""
        self.view.clear()
        for circuit_number in self.model.get_circuits():
            self.view.add_circuit(circuit_number)
            for detector_number in self.model.get_detectors_for_circuit(circuit_number):
                alarm_status = self.model.get_detector_alarm_status(circuit_number, detector_number)
                self.view.add_detector(circuit_number, detector_number, alarm_status)