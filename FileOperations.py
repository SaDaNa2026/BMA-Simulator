import json
from pathlib import Path
from functools import partial
from git import Repo, InvalidGitRepositoryError, NULL_TREE
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gio, GLib


class FileOperations:
    @staticmethod
    def retrieve_open_file(dialog, result):
        """Retrieve the file path from an open dialog."""
        file = dialog.open_finish(result)
        return file

    @staticmethod
    def open_file(file):
        """Parse the data from the provided file and decide how to load it."""
        print(f"Opening: {file.get_path()}")

        with open(file, "r") as file_dict:
            # Load building information
            load_dict = json.load(file_dict)

            filename = file.get_path()
            file_extension = Path(filename).suffix.lstrip(".")
            if file_extension != "building" and file_extension != "scenario":
                raise RuntimeError("Es können nur Dateien geladen werden, die auf .building oder .scenario enden")

            return load_dict, file_extension

    @staticmethod
    def get_scenario_directory(scenario_file, load_dict, load_scenario_callback):
        """Get the directory the scenario file is saved in and enumerate its children."""
        directory = Gio.file_new_for_path(scenario_file.get_parent().get_path())

        # Get the directory contents asynchronously
        directory.enumerate_children_async(
            'standard::name',
            Gio.FileQueryInfoFlags.NONE,
            GLib.PRIORITY_DEFAULT,
            None,
            callback=partial(FileOperations.get_building_config_for_scenario,
                             scenario_load_dict=load_dict,
                             load_scenario_callback=load_scenario_callback)
        )

    @staticmethod
    def get_building_config_for_scenario(source_object, result, scenario_load_dict, load_scenario_callback):
        """Callback for get_scenario_directory. Finds the .building files in the directory and returns the file path.
        Throws an error if there is not exactly one .building file."""
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
            raise GLib.Error(message="Keine .building-Datei in diesem Verzeichnis gefunden.")

        if len(building_file_list) > 1:
            raise GLib.Error(message=f"Es wurden {len(building_file_list)} .building-Dateien gefunden.\nStellen Sie "
                             f"sicher, dass pro Ordner nur eine .building-Datei existiert.")

        # Load the building_config file that has been found
        building_file = Gio.file_new_for_path(building_file_list[0])
        load_scenario_callback(building_file, scenario_load_dict)

    @staticmethod
    def load_building_config(model, load_dict, add_circuit_function, add_detector_function):
        """Delete the current configuration, then parse the data from the load_dict."""
        model.clear_data()
        model.set_building_description(load_dict["building_description"])

        for circuit_string in load_dict["circuit_dict"]:
            if not circuit_string.isdigit():
                raise ValueError("Mindestens eine Meldergruppen-Nummer ist keine natürliche Zahl.")

            circuit_number = int(circuit_string)
            add_circuit_function(circuit_number)

            for detector_string in load_dict["circuit_dict"][circuit_string]:
                if not detector_string.isdigit():
                    raise ValueError(
                        f"Mindestens eine Meldernummer in Meldergruppe {circuit_number} ist keine natürliche Zahl.")

                detector_number = int(detector_string)
                detector_description = load_dict["circuit_dict"][circuit_string][detector_string]
                add_detector_function(circuit_number, detector_number,
                                   description=detector_description)

        print("File loaded successfully")

    @staticmethod
    def apply_scenario(load_dict, circuit_dict, edit_action_group, model):
        """Set all detectors listed in load_dict to active"""
        for number_list in load_dict["active_detector_list"]:
            # Check for correct Syntax
            if not type(number_list) == list:
                raise TypeError("Inkorrektes Format der Meldernummer.")

            if not len(number_list) == 2:
                raise SyntaxError("Inkorrektes Format der Meldernummer.")

            if not type(number_list[0]) == int:
                raise TypeError("Mindestens eine Meldergruppen-Nummer ist keine natürliche Zahl.")

            if not type(number_list[1]) == int:
                raise TypeError("Mindestens eine Melder-Nummer ist keine natürliche Zahl.")

            # Retrieve numbers from strings
            circuit_number = int(number_list[0])
            detector_number = int(number_list[1])

            # Try to set the specified detector switch active
            try:
                detector = circuit_dict[circuit_number].detector_dict[detector_number]
                detector.detector_switch.set_active(True)

            except KeyError:
                raise KeyError(f"Melder {detector_number} in Meldergruppe {circuit_number} ist im Szenario aktiv, "
                               f"aber nicht in der Gebäudekonfiguration enthalten, die im selben Verzeichnis "
                               f"liegt.")

        for number_list in load_dict["disabled_detector_list"]:
            # Check for correct Syntax
            if not type(number_list) == list:
                raise TypeError("Inkorrektes Format der Meldernummer.")

            if not len(number_list) == 2:
                raise SyntaxError("Inkorrektes Format der Meldernummer.")

            if not type(number_list[0]) == int:
                raise TypeError("Mindestens eine Meldergruppen-Nummer ist keine natürliche Zahl.")

            if not type(number_list[1]) == int:
                raise TypeError("Mindestens eine Melder-Nummer ist keine natürliche Zahl.")

            # Retrieve numbers from strings
            circuit_number = int(number_list[0])
            detector_number = int(number_list[1])

            try:
                enable_action = edit_action_group.lookup_action(f"enable_detector_{circuit_number}_{detector_number}")
                enable_action.change_state(GLib.Variant.new_boolean(True))
                print(enable_action.get_state())

            except KeyError:
                raise KeyError(f"Melder {detector_number} in Meldergruppe {circuit_number} ist im Szenario abgeschaltet, "
                               f"aber nicht in der Gebäudekonfiguration enthalten, die im selben Verzeichnis "
                               f"liegt.")

        model.set_extinguisher_triggered(load_dict["settings"]["extinguisher_triggered"])
        model.set_acoustic_signals_off(load_dict["settings"]["acoustic_signals_off"])
        model.set_ue_off(load_dict["settings"]["ue_off"])
        model.set_fire_controls_off(load_dict["settings"]["fire_controls_off"])

    @staticmethod
    def retrieve_save_file(dialog, result):
        """Retrieve the save path from the file dialog."""
        file = dialog.save_finish(result)
        return file


    @staticmethod
    def save_to_file(file: Gio.File, save_dict: dict, message: str) -> None:
        """Save save_dict as JSON to the specified filepath."""
        file_path = file.get_path()
        print(f"Saving to: {file_path}")

        # Write save_dict to the file in JSON format
        with open(file_path, "w", encoding="utf-8") as file_dict:
            json.dump(save_dict, file_dict, sort_keys=True, indent=4)

        FileOperations.commit_changes(file, message)

        print("File saved successfully.")

    @staticmethod
    def commit_changes(file: Gio.File, message: str) -> None:
        """Commit changes to git."""
        # Get the repo
        file_path = Path(file.get_path()).resolve()
        repo_dir = file_path.parent
        try:
            repo = Repo(repo_dir, search_parent_directories=True)
        except InvalidGitRepositoryError:
            repo = Repo.init(repo_dir)

        # Stage all files in the directory
        repo.git.add(A=True)

        # Only commit if there is something to commit
        if repo.is_dirty(untracked_files=True):
            repo.index.commit(message or "Update files")

    @staticmethod
    def get_commits_for_dir(directory):
        """Returns a list of all commits for the provided directory containing tuples with commit date and message.
        Returns None if the directory is not a git repository."""
        try:
            repo = Repo(directory)
        except InvalidGitRepositoryError:
            return None

        commit_list = list(repo.iter_commits())
        return_list = []
        for commit in commit_list:
            parent = commit.parents[0] if commit.parents else None
            if parent:
                diffs = commit.diff(parent)
            else:
                # Initial commit (no parent): diff against empty tree
                diffs = commit.diff(NULL_TREE)

            diff_list = []
            for diff in diffs:
                diff_list.append((diff.a_path, diff.b_path, diff.change_type))

            return_list.append((commit.committed_date, diff_list, commit.message))
        return return_list

    @staticmethod
    def rollback(directory, commit_index):
        """Perform a hard reset of the specified directory to the specified index in the commit list."""
        repo = Repo(directory)
        commit_list = list(repo.iter_commits())
        commit = commit_list[commit_index]
        repo.head.reset(commit, index=True, working_tree=True)

    @staticmethod
    def create_building_save_dict(model) -> dict:
        """Create a dictionary that contains all information about the current building configuration."""
        save_dict = {"circuit_dict": {}, "building_description": model.get_building_description()}

        for circuit_number in model.get_circuits():
            save_dict["circuit_dict"][circuit_number] = {}

            for detector_number in model.get_detectors_for_circuit(circuit_number):
                save_dict["circuit_dict"][circuit_number][detector_number] = \
                    model.get_detector_description(circuit_number, detector_number)

        return save_dict


    @staticmethod
    def create_scenario_save_dict(model) -> dict:
        """Create a dictionary that contains a list of active detectors and a description."""
        save_dict = {"active_detector_list": model.get_active_detectors(),
                     "disabled_detector_list": model.get_disabled_detectors(),
                     "settings": {"extinguisher_triggered": model.get_extinguisher_triggered(),
                                  "acoustic_signals_off": model.get_acoustic_signals_off(),
                                  "ue_off": model.get_ue_off(),
                                  "fire_controls_off": model.get_fire_controls_off()},
                     "scenario_description": "Beschreibung"}
        return save_dict
