# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
from pathlib import Path
from git import Repo, InvalidGitRepositoryError, NULL_TREE
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gio, GLib


class FileOperations:
    @staticmethod
    def get_file_extension(file_path: str):
        # Find the last dot in the file path
        dot_pos = file_path.rfind('.')
        # The extension is everything after the last dot. Return empty string if there is no dot
        file_extension = file_path[dot_pos + 1:] if dot_pos != -1 else ""

        return file_extension

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
                raise ValueError("Es können nur Dateien geladen werden, die auf .building oder .scenario enden")

            return load_dict, file_extension

    @staticmethod
    def get_building_config_for_scenario(scenario_file, scenario_load_dict, load_scenario_callback):
        """Callback for get_scenario_directory. Finds the .building files in the directory and returns the file path.
        Throws an error if there is not exactly one .building file."""
        directory = Gio.file_new_for_path(scenario_file.get_parent().get_path())
        building_file_found = False

        # Check directory for building file. If none is found, check parent directories recursively
        while not building_file_found:
            # Stop recursing when reaching the user's home directory
            if directory == Path.home():
                raise FileNotFoundError("Es wurde keine .building-Datei gefunden. Stellen Sie sicher, dass im selben "
                                        "oder einem übergeordneten Verzeichnis wie die gewählte .scenario-Datei "
                                        "eine .building-Datei existiert.")

            children = directory.enumerate_children(
                'standard::name',
                Gio.FileQueryInfoFlags.NONE,
                None
            )

            # A list to store the paths to the ".building" files in the directory
            building_file_list = []

            for child_info in children:
                child_name = child_info.get_name()
                child_extension = FileOperations.get_file_extension(child_name)

                if child_extension == "building":
                    # Get the filepath of the child and add it to building_file_list
                    file_path = str(directory.get_path()) + "/" + child_name
                    building_file_list.append(file_path)

            # Check if exactly one .building file was found
            match len(building_file_list):
                case 0:
                    directory = directory.get_parent()

                case 1:
                    building_file_found = True
                    # Load the building_config file that has been found
                    building_file = Gio.file_new_for_path(building_file_list[0])
                    load_scenario_callback(building_file, scenario_load_dict)

                case _:
                    raise FileNotFoundError(f"Es wurden {len(building_file_list)} .building-Dateien gefunden.\nStellen Sie "
                                     f"sicher, dass pro Verzeichnis nur eine .building-Datei existiert.")

    @staticmethod
    def load_building_config(model, load_dict, add_circuit_function, add_detector_function):
        """Delete the current configuration, then parse the data from the load_dict."""
        model.clear_data()
        model.set_building_description(load_dict["building_description"])

        for circuit_string in load_dict["circuit_dict"]:
            if not circuit_string.isdigit():
                raise ValueError("Mindestens eine Meldergruppen-Nummer ist keine natürliche Zahl.")

            circuit_number = int(circuit_string)
            try:
                add_circuit_function(circuit_number)
            except ValueError as e:
                raise ValueError(f"Fehler beim Hinzufügen von Meldergruppe {circuit_number}: {e}")

            for detector_string in load_dict["circuit_dict"][circuit_string]:
                if not detector_string.isdigit():
                    raise ValueError(
                        f"Mindestens eine Meldernummer in Meldergruppe {circuit_number} ist keine natürliche Zahl.")

                detector_number = int(detector_string)
                detector_description = load_dict["circuit_dict"][circuit_string][detector_string]
                try:
                    add_detector_function(circuit_number, detector_number,
                                    description=detector_description)
                except ValueError as e:
                    raise ValueError(f"Fehler beim Hinzufügen von Melder {detector_number}: {e}")

        print("File loaded successfully")

    @staticmethod
    def apply_scenario(load_dict, circuit_dict, detector_action_group, model, scenario_description_textbuffer):
        """Set all detectors listed in load_dict to active"""
        # Add extinguisher alarm support
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

            enable_action = detector_action_group.lookup_action(f"enable_detector_{circuit_number}_{detector_number}")
            if not isinstance(enable_action, Gio.SimpleAction):
                raise KeyError(
                    f"Melder {detector_number} in Meldergruppe {circuit_number} ist im Szenario abgeschaltet, "
                    f"aber nicht in der Gebäudekonfiguration enthalten, die im selben Verzeichnis liegt.")

            enable_action.change_state(GLib.Variant.new_boolean(True))

        for number_list in load_dict["history_detector_list"]:
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

            history_action = detector_action_group.lookup_action(f"in_history_{circuit_number}_{detector_number}")
            if not isinstance(history_action, Gio.SimpleAction):
                raise KeyError(
                    f"Melder {detector_number} in Meldergruppe {circuit_number} ist im Szenario in der Historie, "
                    f"aber nicht in der Gebäudekonfiguration enthalten, die im selben Verzeichnis liegt.")

            history_action.change_state(GLib.Variant.new_boolean(True))

        # Set the scenario description
        scenario_description_textbuffer.set_text(load_dict["scenario_description"])

        # Set LEDs
        extinguisher_triggered = load_dict["settings"]["extinguisher_triggered"]
        model.set_extinguisher_triggered(extinguisher_triggered)
        model.set_acoustic_signals_off(load_dict["settings"]["acoustic_signals_off"])
        model.set_ue_off(load_dict["settings"]["ue_off"])
        model.set_fire_controls_off(load_dict["settings"]["fire_controls_off"])

        # Set alarm status of the hidden extinguisher detector
        model.set_detector_alarm_status(0, 1, extinguisher_triggered)

        # Apply history time settings
        model.set_history_time_mode(load_dict["settings"]["history_time_mode"])
        model.set_history_time_offset(load_dict["settings"]["history_time_offset"])
        model.set_history_time_absolute(tuple(load_dict["settings"]["history_time_absolute"]))

    @staticmethod
    def retrieve_save_file(dialog, result):
        """Retrieve the save path from the file dialog."""
        file = dialog.save_finish(result)
        return file


    @staticmethod
    def save_to_file(file: Gio.File, save_dict: dict, message: str) -> None:
        """Save save_dict as JSON to the specified filepath."""
        file_path = str(file.get_path())
        print(f"Saving to: {file_path}")

        # Write save_dict to the file in JSON format
        with open(file_path, "w", encoding="utf-8") as file_dict:
            json.dump(save_dict, file_dict, indent=4)

        FileOperations.commit_changes(file, message)

        print("File saved successfully.")

    @staticmethod
    def commit_changes(file: Gio.File, message: str) -> None:
        """Commit changes to git."""
        # Get the repo
        file_path = Path(str(file.get_path())).resolve()
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
    def get_commits_for_dir(directory, recursion_limit):
        """Returns a list of all commits for the provided directory containing tuples with commit date and message.
        Recursively tries parent directories until the provided limit (or the home directory) is reached.
        Returns None if the directory is not a git repository."""
        repo = None
        while (not (directory == Path.home() or directory == recursion_limit.get_parent())) and repo is None:
            try:
                print(directory)
                repo = Repo(directory)
            except InvalidGitRepositoryError:
                directory = directory.get_parent()

        if repo is None:
            return None

        # Get a list of all commits of the current directory
        commit_list = list(repo.iter_commits())
        return_list = []
        for commit in commit_list:
            parent = commit.parents[0] if commit.parents else None
            if parent:
                # Diff parent against commit. Other way around returns flipped values for adding/deleting files
                diffs = parent.diff(commit)
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
        commit = str(commit_list[commit_index])
        repo.head.reset(commit, index=True, working_tree=True)

    @staticmethod
    def create_building_save_dict(model) -> dict:
        """Create a dictionary that contains all information about the current building configuration."""
        save_dict = {"circuit_dict": {}, "building_description": model.get_building_description()}

        for circuit_number in model.get_circuits():
            save_dict["circuit_dict"][circuit_number] = {}
            circuit_detectors = 0
            for detector_number in model.get_detectors_for_circuit(circuit_number):
                detector_description = model.get_detector_description(circuit_number, detector_number)
                # Only add detector if it's not physical
                if not (circuit_number, detector_number, detector_description) in model.permanent_detectors:
                    circuit_detectors += 1
                    save_dict["circuit_dict"][circuit_number][detector_number] = detector_description
            # Only add circuit if it contains detectors
            if circuit_detectors == 0:
                del save_dict["circuit_dict"][circuit_number]

        return save_dict


    @staticmethod
    def create_scenario_save_dict(model, scenario_description: str) -> dict:
        """Create a dictionary that contains a list of active detectors and a description."""
        save_dict = {"active_detector_list": model.get_active_detectors(),
                     "disabled_detector_list": model.get_disabled_detectors(),
                     "history_detector_list": model.get_history_detectors(),
                     "settings": {"extinguisher_triggered": model.get_extinguisher_triggered(),
                                  "acoustic_signals_off": model.get_acoustic_signals_off(),
                                  "ue_off": model.get_ue_off(),
                                  "fire_controls_off": model.get_fire_controls_off(),
                                  "history_time_mode": model.get_history_time_mode(),
                                  "history_time_offset": model.get_history_time_offset(),
                                  "history_time_absolute": model.get_history_time_absolute()},
                     "scenario_description": scenario_description}
        return save_dict
