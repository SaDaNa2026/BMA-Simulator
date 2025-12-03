import json
from functools import partial
from json import JSONDecodeError

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gio, GLib

from Building import Building
from ErrorAlert import ErrorAlert
from FileOpenDialog import FileOpenDialog
from FileSaveDialog import FileSaveDialog


class FileOperations:
    @staticmethod
    def show_open_dialog(parent):
        """Show a FileOpenDialog."""
        file_open_dialog = FileOpenDialog()
        file_open_dialog.open(parent, None, partial(FileOperations.on_file_open_response, parent=parent))

    @staticmethod
    def on_file_open_response(dialog, result, parent):
        """Callback for the open_file_dialog. If the file exists, pass it to the open_file method."""
        try:
            file = dialog.open_finish(result)
            if file is not None:
                FileOperations.open_file(parent, file)

        except GLib.Error as e:
            print(f"Open canceled or failed: {e.message}")

            if not e.message == "Dismissed by user":
                ErrorAlert.show(parent, "Öffnen fehlgeschlagen", e.message)

    @staticmethod
    def open_file(parent, file):
        """Parse the data from the provided file and decide how to load it."""
        print(f"Opening: {file.get_path()}")
        try:
            with open(file, "r") as file_dict:
                # Load building information
                load_dict = json.load(file_dict)

                filename = file.get_path()
                # Find the last dot in the filename
                dot_pos = filename.rfind('.')
                # The extension is everything after the last dot
                file_extension = filename[dot_pos + 1:]

                if file_extension == "building":
                    error_status = FileOperations.load_building_config(parent, load_dict)
                    return error_status

                elif file_extension == "scenario":
                    FileOperations.get_scenario_directory(parent, load_dict, file)

                else:
                    ErrorAlert.show(parent,
                                    "Invalide Dateiendung",
                                    "Es können nur Dateien geladen werden, die auf .building oder .scenario enden")

        except JSONDecodeError:
            ErrorAlert.show(parent, "Fehler beim Laden der Datei",
                            f"Invalides Dateiformat von {file.get_path()}\nStellen Sie sicher, "
                            f"dass die Datei dem JSON-Standard entspricht.")
            # Return error status
            return True

    @staticmethod
    def get_scenario_directory(parent, load_dict, scenario_file):
        """Get the directory the scenario file is saved in and enumerate its children."""
        directory = Gio.file_new_for_path(scenario_file.get_parent().get_path())

        # Get the directory contents asynchronously
        directory.enumerate_children_async(
            'standard::name',
            Gio.FileQueryInfoFlags.NONE,
            GLib.PRIORITY_DEFAULT,
            None,
            callback=partial(FileOperations.get_building_config_for_scenario, parent=parent, load_dict=load_dict)
        )

    @staticmethod
    def get_building_config_for_scenario(source_object, result, parent, load_dict):
        """Callback for get_scenario_directory. Finds the .building files in the directory and returns the file path.
        Throws an error if there is not exactly one .building file."""
        try:
            children = source_object.enumerate_children_finish(result)

            # A list to store the paths to the ".building" files in the directory
            building_file_list = []

            for child_info in children:
                # Get the filename
                child_name = child_info.get_name()
                # Find the last dot in the filename
                dot_pos = child_name.rfind('.')
                # The extension is everything after the last dot. Return empty string if there is no dot
                child_extension = child_name[dot_pos + 1:] if dot_pos != -1 else ""

                if child_extension == "building":
                    # Get the filepath of the child and add it to building_file_list
                    file_path = source_object.get_path() + "/" + child_name
                    building_file_list.append(file_path)

            # Check if exactly one .building file was found
            if len(building_file_list) == 0:
                raise GLib.Error("Keine .building-Datei in diesem Verzeichnis gefunden")

            if len(building_file_list) > 1:
                raise GLib.Error(f"Es wurden {len(building_file_list)} .building-Dateien gefunden.\nStellen Sie "
                                 f"sicher, dass pro Ordner nur eine .building-Datei existiert.")

            # Load the building_config file that has been found
            building_file = Gio.file_new_for_path(building_file_list[0])
            error_status = FileOperations.open_file(parent, building_file)

            if error_status:
                return

            FileOperations.apply_scenario(parent, load_dict)

        except GLib.Error as error:
            print(f"Error listing directory: {error}")
            ErrorAlert.show(parent, f"Öffnen fehlgeschlagen", error)

    @staticmethod
    def load_building_config(parent, load_dict):
        """Delete all current circuits, then create circuits and detectors according to the load_dict."""
        delete_list = [num for num in Building.circuit_dict]
        for circuit_number in delete_list:
            parent.delete_circuit(circuit_number)

        try:
            Building.description = load_dict["building_description"]

            for circuit_string in load_dict["circuit_dict"]:
                if not circuit_string.isdigit():
                    raise ValueError("Mindestens eine Melderlinien-Nummer ist keine natürliche Zahl.")

                circuit_number = int(circuit_string)

                if circuit_number < 1:
                    raise ValueError(f"Melderlinien-Nummer {circuit_number} ist kleiner als 1.")

                elif circuit_number >= 1000000000:
                    raise ValueError("Datei enthält eine Melderlinien-Nummer größer 1.000.000.000.")

                parent.create_circuit(circuit_number)

                for detector_string in load_dict["circuit_dict"][circuit_string]:
                    if not detector_string.isdigit():
                        raise ValueError(
                            f"Mindestens eine Meldernummer in Melderlinie {circuit_number} ist keine natürliche Zahl.")

                    detector_number = int(detector_string)
                    if detector_number < 1:
                        raise ValueError(f"Meldernummer {detector_number} ist kleiner als 1.")

                    elif detector_number >= 1000000000:
                        raise ValueError(
                            f"Datei enthält eine Melder-Nummer größer 1.000.000.000 in Melderlinie {circuit_number}.")

                    detector_description = load_dict["circuit_dict"][circuit_string][detector_string]

                    # Check for correct description format
                    if type(detector_description) is not str:
                        raise TypeError(
                            f"Melderbeschreibung von Melder {detector_number} hat falsches Format")

                    parent.create_detector(circuit_number, detector_number,
                                           detector_description=detector_description)

            print("File loaded successfully")

        except KeyError as e:
            print(f"KeyError: {e}")
            ErrorAlert.show(parent, ".building-Datei invalide", f"Key {e} fehlt oder ist falsch geschrieben.")
            # Return error_status
            return True

        except (ValueError, TypeError) as e:
            print(f"ValueError/TypeError: {e}")
            ErrorAlert.show(parent, ".building-Datei invalide", e)
            # Return error_status
            return True

    @staticmethod
    def apply_scenario(parent, load_dict):
        """Set all detectors listed in load_dict to active"""
        try:
            for name in load_dict["active_detector_list"]:
                # Split the list into circuit and detector numbers
                number_list = name.split("_")

                # Check for correct Syntax
                if len(number_list) != 2:
                    raise SyntaxError("Inkorrektes Format der Meldernummer")

                if not number_list[0].isdigit():
                    raise ValueError("Mindestens eine Melderlinien-Nummer ist keine natürliche Zahl.")

                if not number_list[1].isdigit():
                    raise ValueError("Mindestens eine Melder-Nummer ist keine natürliche Zahl.")

                # Retrieve numbers from strings
                circuit_number = int(number_list[0])
                detector_number = int(number_list[1])

                # Check if numbers are within valid range
                if circuit_number < 1:
                    raise ValueError("Datei enthält eine Melderlinien-Nummer kleiner 1.")

                elif circuit_number >= 1000000000:
                    raise ValueError("Datei enthält eine Melderlinien-Nummer größer 1.000.000.000")

                if detector_number < 1:
                    raise ValueError(
                        f"Melder-Nummer {detector_number} in Melderlinie {circuit_number} ist kleiner als 1.")

                elif detector_number >= 1000000000:
                    raise ValueError(
                        f"Datei enthält eine Melder-Nummer größer 1.000.000.000 in Melderlinie {circuit_number}")

                # Try to set the specified detector switch active
                try:
                    detector = Building.circuit_dict[circuit_number].detector_dict[detector_number]
                    detector.alarm_status = True
                    detector.detector_switch.set_active(True)

                except KeyError:
                    ErrorAlert.show(parent,
                                    ".scenario-Datei invalide",
                                    f"Melder {detector_number} in Melderlinie {circuit_number} ist im Szenario aktiv, "
                                    f"aber nicht in der Gebäudekonfiguration enthalten, die im selben Verzeichnis "
                                    f"liegt.")

        except KeyError as e:
            ErrorAlert.show(parent,
                            ".scenario-Datei invalide",
                            f"Key {e} fehlt oder ist falsch geschrieben.")

        except SyntaxError as e:
            ErrorAlert.show(parent, ".scenario-Datei invalide", e)

        except ValueError as e:
            ErrorAlert.show(parent, ".scenario-Datei invalide", e)

    @staticmethod
    def show_save_dialog(parent, file_type):
        """Show a FileSaveDialog."""
        file_save_dialog = FileSaveDialog(file_type)
        file_save_dialog.save(parent, None,
                              partial(FileOperations.on_file_save_response, parent=parent, file_type=file_type))

    @staticmethod
    def on_file_save_response(dialog, result, parent, file_type):
        """Callback for the save_file_dialog. Pass the destination to the save_to_file method."""
        try:
            file = dialog.save_finish(result)
            if file is not None:
                FileOperations.save_to_file(file, file_type)

        except GLib.Error as e:
            print(f"Save canceled or failed: {e.message}")

            if not e.message == "Dismissed by user":
                ErrorAlert.show(parent, "Speichern fehlgeschlagen", e.message)

    @staticmethod
    def save_to_file(file, file_type):
        """Call the correct method to create save_dict depending on file_type, then save it as json to the specified
        filepath."""
        path = file.get_path()
        print(f"Saving to: {path}")

        if file_type == "building":
            save_dict = FileOperations.create_building_save_dict()

        else:
            save_dict = FileOperations.create_scenario_save_dict()

        # Write save_dict to the file in json format
        with open(path, "w", encoding="utf-8") as config_dict:
            json.dump(save_dict, config_dict, sort_keys=True, indent=4)

        print("File saved successfully.")

    @staticmethod
    def create_building_save_dict():
        """Create a dictionary that contains all information about the current building configuration."""
        save_dict = {"circuit_dict": {}, "building_description": Building.description}

        for circuit_number in Building.circuit_dict:
            save_dict["circuit_dict"][circuit_number] = {}

            for detector_number in Building.circuit_dict[circuit_number].detector_dict:
                save_dict["circuit_dict"][circuit_number][detector_number] = \
                    Building.circuit_dict[circuit_number].detector_dict[detector_number].description

        return save_dict

    @staticmethod
    def create_scenario_save_dict():
        """Create a dictionary that contains a list of active detectors and a description."""
        save_dict = {"active_detector_list": [], "scenario_description": "Beschreibung"}

        for circuit_number in Building.circuit_dict:

            for detector_number in Building.circuit_dict[circuit_number].detector_dict:
                detector = Building.circuit_dict[circuit_number].detector_dict[detector_number]

                if detector.alarm_status:
                    save_dict["active_detector_list"].append(f"{circuit_number}_{detector_number}")

        return save_dict
