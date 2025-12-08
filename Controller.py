import sys
from FileOperations import FileOperations
import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib
from json import JSONDecodeError

from Model import BuildingModel
from GtkApp import App


class Controller:
    def __init__(self):
        self.model = BuildingModel()
        self.view = App(self.on_save_building_clicked, self.on_save_scenario_clicked, self.on_open_clicked,
                        self.on_add_circuit_clicked, self.on_delete_circuit_clicked, self.on_add_detector_clicked,
                        self.on_delete_detector_clicked, self.on_edit_detector_clicked, self.on_edit_building_clicked,
                        application_id="org.example.BMA-control")
        self.view.run(sys.argv)

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

            except KeyError as e:
                print(f"KeyError: {e}")
                self.view.show_error_alert(".building-Datei invalide", f"Key {e} fehlt oder ist falsch geschrieben.")
                return True

            except (ValueError, TypeError) as e:
                print(f"ValueError/TypeError: {e}")
                self.view.show_error_alert(".building-Datei invalide", e)
                return True

        else:
            try:
                FileOperations.get_scenario_directory(file, load_dict, self.load_scenario_callback)

            except GLib.Error as error:
                print(f"Error listing directory: {error}")
                self.view.show_error_alert(f"Öffnen fehlgeschlagen", error)
                return True

    def load_scenario_callback(self, building_file, scenario_load_dict):
        building_error = self.load_file(building_file)
        if building_error:
            return

        try:
            FileOperations.apply_scenario(scenario_load_dict, self.model)

        except TypeError as e:
            self.view.show_error_alert("scenario-Datei invalide", f"TypeError: {e}")

        except KeyError as e:
            self.view.show_error_alert(".scenario-Datei invalide", f"KeyError: {e}")

        except SyntaxError as e:
            self.view.show_error_alert(".scenario-Datei invalide", f"SyntaxError: {e}")

        except ValueError as e:
            self.view.show_error_alert(".scenario-Datei invalide", f"ValueError: {e}")


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
        current_description = self.model.get_building_description()

        self.view.show_edit_detector_window(circuit_number, detector_number, self.edit_detector_callback, current_description)

    def on_edit_building_clicked(self, *args):
        """Create an EditBuildingWindow."""
        current_description = self.model.get_building_description()
        self.view.show_edit_building_window(self.edit_building_callback, current_description)

    def on_delete_circuit_clicked(self, action, parameter, *args):
        """Convert parameter to int and call the delete_circuit method."""
        circuit_number = parameter.get_int32()
        self.model.delete_circuit(circuit_number)

    def on_delete_detector_clicked(self, action, parameter, *args):
        """Convert parameters to int and call the delete_detector method."""
        parameter_string = parameter.get_string()
        parameter_list = parameter_string.split(", ")
        circuit_number = int(parameter_list[0])
        detector_number = int(parameter_list[1])

        self.model.delete_detector(circuit_number, detector_number)

    def add_circuit_callback(self, circuit_number):
        self.model.add_circuit(circuit_number)

    def add_detector_callback(self, circuit_number, detector_number, detector_description):
        self.model.add_detector(circuit_number, detector_number, detector_description)

    def edit_building_callback(self, description: str):
        """Change the building description."""
        self.model.set_building_description(description)

    def edit_detector_callback(self, circuit_number: int, detector_number: int, description: str):
        """Change a specified detector's description."""
        self.model.set_detector_description(circuit_number, detector_number, description)

    def on_detector_toggled(self, detector_switch, state, circuit_number, detector_number):
        """Callback function for detector_switch. Set the alarm_status of the detector according to the position of
        the switch and print debugging info."""
        self.model.set_detector_alarm_status(circuit_number, detector_number, state)
        print(f"Melder {detector_number} in Melderlinie {circuit_number} {'aktiviert' if state else 'deaktiviert'}")
        self.print_detector_state()

    def print_detector_state(self):
        """Print the active detectors to the console."""
        active_detector_list = self.model.get_active_detectors()
        print("Aktive Melder:")
        for reference in active_detector_list:
            circuit_number = reference[0]
            detector_number = reference[1]
            print(f"Melder {detector_number} in Meldergruppe {circuit_number}")
