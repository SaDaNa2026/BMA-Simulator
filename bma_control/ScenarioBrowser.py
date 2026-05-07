import json
from json import JSONDecodeError

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio
from gi.repository.Gio import File

from FileOperations import FileOperations
from ModalWindow import ModalWindow


class DirectoryFrame(Gtk.Frame):
    def __init__(self, label: str, scenario_files: list, on_scenario_clicked_callback) -> None:
        super().__init__(label=label)


class ScenarioBrowser(ModalWindow):
    def __init__(self, parent, error_dialog_function, top_level_dir_path: str, tag_file_path: str) -> None:
        """A window to browse through available scenarios grouped by building and view scenario descriptions.
        Filtering by tags is also available"""
        super().__init__(parent, resizable=True, title="Szenario-Browser")
        self.error_dialog_function = error_dialog_function
        self.top_level_dir = Gio.File.new_for_path(top_level_dir_path)
        self.tag_file = Gio.File.new_for_path(tag_file_path)
        self.current_scenario_file: File | None = None

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(self.main_box)

        # Draw the file tree view in the left of the window
        self.filetree_frame = Gtk.Frame(label="Verfügbare Szenarien")
        self.main_box.append(self.filetree_frame)
        self.filetree_scrollable = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER,
                                                      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                                      vexpand=True)
        self.filetree_frame.set_child(self.filetree_scrollable)
        self.filetree_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.filetree_scrollable.set_child(self.filetree_box)

    def _populate_filetree(self, directory: File) -> None:
        """Recursively search directories for building files. Add a directory frame with all corresponding scenarios
        to the filetree for every directory containing a building file"""
        building_file_list = FileOperations.list_building_files(directory)
        # If more than one building file is found the file structure is invalid
        if len(building_file_list) > 1:
            self.error_dialog_function("Invalide Dateistruktur",
                                       f"Mehr als eine .building-Datei im Verzeichnis {directory.get_path()} gefunden")
            return

        # Recurse through child directories if no building files have been found
        elif len(building_file_list) == 0:
            try:
                children = directory.enumerate_children(
                    'standard::name',
                    Gio.FileQueryInfoFlags.NONE,
                    None
                )
                for child in children:
                    self._populate_filetree(child)

            except Gio.IOErrorEnum.NOT_DIRECTORY:
                return

        # Remaining case is exactly one building file. Recursively get scenario files for this and all
        # child directories, filter for tags and add a directory frame with the filtered scenarios if there are any
        else:
            label = FileOperations.get_filename_without_extension(building_file_list[0].get_path())
            scenario_list = FileOperations.list_child_scenarios(directory)
            try:
                with open(str(self.tag_file.get_path()), "r") as tag_json:
                    tag_list = json.load(tag_json)
            except FileNotFoundError, JSONDecodeError:
                self.error_dialog_function("Tag file not found",
                                           f"Make sure a json-formatted dictionary of tags to be used for "
                                           f"scenario filtering is located at {self.tag_file.get_path()}.\n"
                                           f"In the current state, scenario filtering will be unavailable.")
                tag_list = []

            filtered_scenarios = self._filter_scenario_list(scenario_list, tag_list)
            if len(filtered_scenarios) > 0:
                directory_frame = DirectoryFrame(label, filtered_scenarios, self.on_scenario_clicked)

    def _filter_scenario_list(self, scenario_list: list[File], tag_id_list: list) -> list:
        """Remove scenarios that don't match the filter criteria"""
        # TODO
        return scenario_list

    def on_scenario_clicked(self, scenario_file: File) -> None:
        """Load the description of the provided scenario and display it.
        Also set the scenario that is loaded by the load button to the provided one"""
        # TODO
        self.current_scenario_file = scenario_file