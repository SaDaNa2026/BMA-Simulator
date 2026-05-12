import json
from json import JSONDecodeError

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio
from gi.repository.Gio import File

from FileOperations import FileOperations
from ModalWindow import ModalWindow
import Model


class BuildingFrame(Gtk.Frame):
    def __init__(self, label: str, scenario_files: list[File], on_scenario_clicked_callback) -> None:
        super().__init__(label=label,
                         margin_start=5,
                         margin_end=5)
        self.list_box = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE,
                                    show_separators=True)
        self.list_box.set_sort_func(self._sort_scenarios)
        self.set_child(self.list_box)
        for scenario in scenario_files:
            scenario_path = scenario.get_path()
            if not scenario_path:
                return

            label = FileOperations.get_filename_without_extension(scenario_path)
            scenario_button = Gtk.Button(label=label,
                                         has_frame=False)
            scenario_button.connect("clicked", on_scenario_clicked_callback, scenario)
            self.list_box.append(scenario_button)

    def _sort_scenarios(self, child1, child2):
        """Sorting function for the scenarios inside list_box"""
        scenario1_label = child1.get_child().get_label()
        scenario2_label = child2.get_child().get_label()

        if scenario1_label < scenario2_label:
            return -1
        elif scenario1_label > scenario2_label:
            return 1
        else:
            return 0


class TagObject(Gtk.Frame):
    def __init__(self, tag_id: int, tag_name: str, remove_callback):
        super().__init__()
        self.tag_id = tag_id
        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin_start=5)
        self.set_child(self.box)
        self.label = Gtk.Label(label=tag_name, opacity=0.9)
        self.box.append(self.label)
        self.remove_button = Gtk.Button(icon_name="window-close-symbolic", has_frame=False)
        self.remove_button.connect("clicked", remove_callback, self)
        self.box.append(self.remove_button)


class ScenarioBrowser(ModalWindow):
    def __init__(self, parent, error_dialog_function, top_level_dir_path: str, tag_file_path: str, load_file_callback) -> None:
        """A window to browse through available scenarios grouped by building and view scenario descriptions.
        Filtering by tags is also available"""
        super().__init__(parent, resizable=True, title="Szenario-Browser", default_width=800, default_height=500)
        self.connect("activate-focus", self.test)
        self.error_dialog_function = error_dialog_function
        self.top_level_dir = Gio.File.new_for_path(top_level_dir_path)
        self.tag_file = Gio.File.new_for_path(tag_file_path)
        self.current_scenario_file: File | None = None
        self.available_tags_dict: dict = self._load_tag_file()
        self.selected_tags_dict: dict = {}
        self.filetree_children: list = []
        self.load_file_callback = load_file_callback

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(self.main_box)

        # Draw the file tree view in the left of the window
        self.filetree_frame = Gtk.Frame()
        self.filetree_frame_label = Gtk.Label()
        self.filetree_frame_label.set_markup("<span size='large'>Verfügbare Szenarien</span>")
        self.filetree_frame.set_label_widget(self.filetree_frame_label)
        self.main_box.append(self.filetree_frame)
        self.filetree_scrollable = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER,
                                                      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                                      vexpand=True)
        self.filetree_frame.set_child(self.filetree_scrollable)
        self.filetree_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                    margin_top=5,
                                    spacing=5)
        self.filetree_scrollable.set_child(self.filetree_box)
        self._populate_filetree(self.top_level_dir)

        self.right_side_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.append(self.right_side_box)

        # Add a box for management of filter tags
        self.filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                  spacing=5,
                                  margin_start=5,
                                  margin_end=5)
        self.right_side_box.append(self.filter_box)
        self.tag_menu_button = Gtk.MenuButton(label="Filter",
                                              margin_top=10,
                                              margin_bottom=10)
        self.tag_menu_button.set_create_popup_func(self._set_filter_popover)
        self.filter_box.append(self.tag_menu_button)
        self.filter_box.append(Gtk.Separator())
        self.tag_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                               spacing=10,
                               margin_top=10,
                               margin_bottom=10)
        self.tag_box_scrollable = Gtk.ScrolledWindow(child=self.tag_box,
                                                     vscrollbar_policy=Gtk.PolicyType.NEVER,
                                                     hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                                     hexpand=True,
                                                     propagate_natural_width=True)
        self.filter_box.append(self.tag_box_scrollable)

        # Prepare a frame for the scenario description
        self.description_frame = Gtk.Frame()
        self.description_frame_label = Gtk.Label()
        self.description_frame.set_label_widget(self.description_frame_label)
        self.right_side_box.append(self.description_frame)
        self.description_scrollable = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                                         vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                                         vexpand=True,
                                                         hexpand=True)
        self.description_frame.set_child(self.description_scrollable)
        self.description_textbuffer = Gtk.TextBuffer()
        self.description_text = Gtk.TextView(editable=False,
                                             buffer=self.description_textbuffer,
                                             margin_start=5,
                                             focusable=False,
                                             wrap_mode=Gtk.WrapMode.WORD)
        self.description_scrollable.set_child(self.description_text)

        # Buttons to Cancel or Load
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                  spacing=10,
                                  hexpand=True,
                                  halign=Gtk.Align.END,
                                  margin_top=5,
                                  margin_bottom=5,
                                  margin_start=10,
                                  margin_end=10)
        self.right_side_box.append(self.button_box)
        self.cancel_button = Gtk.Button(label="Abbrechen", halign=Gtk.Align.END)
        self.cancel_button.connect("clicked", lambda button, *args: self.destroy())
        self.button_box.append(self.cancel_button)
        self.confirm_button = Gtk.Button(label="Szenario laden", sensitive=False, halign=Gtk.Align.END)
        self.confirm_button.connect("clicked", self._load_scenario)
        self.button_box.append(self.confirm_button)

    def test(self):
        print("activated")

    def _populate_filetree(self, directory: File) -> None:
        """Recursively search directories for building files. Add a directory frame with all corresponding scenarios
        to the filetree for every directory containing a building file"""
        building_file_list = FileOperations.list_building_files(directory)

        # If more than one building file is found the file structure is invalid
        if len(building_file_list) > 1:
            self.error_dialog_function("Invalide Dateistruktur",
                                       f"Mehr als eine .building-Datei im Verzeichnis {directory.get_path()} gefunden",
                                       self)
            return

        # Recurse through child directories if no building files have been found
        if len(building_file_list) == 0:
            file_type = directory.query_file_type(
                Gio.FileQueryInfoFlags.NONE,
                None
            )
            # Do not recurse if the current file is not a directory
            if file_type != Gio.FileType.DIRECTORY:
                return

            children = directory.enumerate_children(
                'standard::name',
                Gio.FileQueryInfoFlags.NONE,
                None
            )
            # Recursive through child files
            for child in children:
                child_file = directory.get_child(child.get_name())
                self._populate_filetree(child_file)

            return

        # Remaining case is exactly one building file. Recursively get scenario files for this and all
        # child directories, filter for tags and add a directory frame with the filtered scenarios if there are any
        file_name = str(building_file_list[0].get_path())
        label = FileOperations.get_filename_without_extension(file_name)
        scenario_list = FileOperations.list_child_scenarios(directory)

        filtered_scenarios = self._filter_scenario_list(scenario_list, self.selected_tags_dict)
        if len(filtered_scenarios) > 0:
            building_frame = BuildingFrame(label, filtered_scenarios, self._on_scenario_clicked)
            self.filetree_box.append(building_frame)
            self.filetree_children.append(building_frame)

    def _load_tag_file(self) -> dict:
        """Try to open and load the tag file. Display an error message if this fails"""
        try:
            tag_file_path = self.tag_file.get_path()
            if not tag_file_path:
                raise FileNotFoundError

            with open(tag_file_path, "r") as tag_json:
                tag_dict = json.load(tag_json)

        except (FileNotFoundError, JSONDecodeError):
            self.error_dialog_function("Tag file not found",
                                       f"Make sure a json-formatted dictionary of tags and associated IDs to be "
                                       f"used for scenario filtering is located at {self.tag_file.get_path()}.\n"
                                       f"In the current state, scenario filtering will be unavailable.",
                                       self)
            tag_dict = {}

        # Convert str keys to int
        return_dict: dict = {}
        for key in tag_dict.keys():
            return_dict[int(key)] = tag_dict[key]

        return return_dict

    def get_scenario_tag_ids(self, scenario_file: File) -> list[str]:
        """Returns a list of the tag_ids of the given scenario"""
        try:
            open_value = FileOperations.open_file(scenario_file)
        except JSONDecodeError:
            self.error_dialog_function("Szenariodatei invalide",
                                       f"Stellen Sie sicher, dass {scenario_file.get_path()} dem "
                                       f"JSON-Standard entspricht",
                                       self)
            return []

        if open_value is None:
            return []
        load_dict = open_value[0]

        # Get tag_ids. Return an empty list if the key does not exist
        try:
            tag_id_list = load_dict["tag_ids"]
        except KeyError:
            tag_id_list = []

        return tag_id_list


    def _filter_scenario_list(self, scenario_list: list[File], tags_dict: dict) -> list[File]:
        """Remove scenarios that don't match the filter criteria"""
        return_list: list = []
        for scenario in scenario_list:
            not_found = False
            scenario_tags = self.get_scenario_tag_ids(scenario)
            # Iterate over provided keys. Only append scenario to return_list if it contains all keys
            for key in tags_dict.keys():
                if key not in scenario_tags:
                    not_found = True
                    break
            if not not_found:
                return_list.append(scenario)

        return return_list

    def _on_scenario_clicked(self, button, scenario_file: File) -> None:
        """Set the current scenario to the provided one and call the function to load the description"""
        self.current_scenario_file = scenario_file
        self._load_scenario_description()

    def _load_scenario_description(self) -> None:
        """Load the description of the current scenario file and display it"""
        if not self.current_scenario_file:
            return

        # Load the selected scenario file's contents via json
        try:
            open_result = FileOperations.open_file(self.current_scenario_file)
        except JSONDecodeError:
            self.error_dialog_function("Fehler beim Laden der Szenariobeschreibung",
                                       f"Stellen Sie sicher, dass {self.current_scenario_file.get_path()} "
                                       f"entsprechend dem JSON-Standard korrekt formatiert ist",
                                       self)
            return
        if open_result is None:
            return
        load_dict = open_result[0]

        # Set the description frame label to the scenario file name
        scenario_path = self.current_scenario_file.get_path()
        if scenario_path:
            scenario_name = FileOperations.get_filename_without_extension(scenario_path)
        else:
            scenario_name = ""
        self.description_frame_label.set_markup(f"<span size='large'>{scenario_name}</span>")

        # Get the description text from the selected scenario file
        try:
            self.description_textbuffer.set_text(load_dict["scenario_description"])

        except KeyError:
            self.error_dialog_function("Fehler beim Laden der Szenariobeschreibung",
                                       f"Stellen Sie sicher, dass {self.current_scenario_file.get_path()} korrekt"
                                       f"formatiert ist und den Schlüssel 'scenario_description' enthält",
                                       self)
            self.description_textbuffer.set_text("Konnte Beschreibung nicht laden")

        self.confirm_button.set_sensitive(True)

    def _set_filter_popover(self, menu_button) -> None:
        """Create a popover for the filter menu button"""
        tag_list_box = Gtk.ListBox(show_separators=True,
                                   selection_mode=Gtk.SelectionMode.NONE)
        for tag_id in self.available_tags_dict:
            tag_button = Gtk.Button(label=str(self.available_tags_dict[tag_id]),
                                    has_frame=False)
            tag_button.connect("clicked", self._on_tag_clicked, tag_id)
            tag_list_box.append(tag_button)

        scrollable = Gtk.ScrolledWindow(child=tag_list_box,
                                        vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                        hscrollbar_policy=Gtk.PolicyType.NEVER,
                                        max_content_height=300,
                                        propagate_natural_height=True)
        popover = Gtk.Popover(child=scrollable)
        self.tag_menu_button.set_popover(popover)

    def _on_tag_clicked(self, button, tag_id: int) -> None:
        """Move the tag with the provided id from available_tags_dict to selected_tags_dict if possible.
        Append a filter button to the filter box"""
        if tag_id not in self.available_tags_dict or tag_id in self.selected_tags_dict:
            return

        self.selected_tags_dict[tag_id] = self.available_tags_dict.pop(tag_id)
        self.selected_tags_dict = Model.sort_dict_by_key(self.selected_tags_dict)

        tag_object = TagObject(tag_id, self.selected_tags_dict[tag_id], self._on_tag_remove_clicked)
        self.tag_box.append(tag_object)
        self.reload_filetree()

    def _on_tag_remove_clicked(self, button, tag_object) -> None:
        """Remove the tag object and move the tag from selected_tags_dict to available_tags_dict if possible"""
        tag_id = tag_object.tag_id
        self.available_tags_dict[tag_id] = self.selected_tags_dict.pop(tag_id)
        self.available_tags_dict = Model.sort_dict_by_key(self.available_tags_dict)
        self.tag_box.remove(tag_object)
        self.reload_filetree()

    def reload_filetree(self) -> None:
        """Clear filetree and repopulate it with the current filter selection. Clear the textview and current_file too"""
        self.description_textbuffer.set_text("")
        self.description_frame_label.set_text("")
        self.current_scenario_file = None
        self.confirm_button.set_sensitive(False)

        while len(self.filetree_children) > 0:
            self.filetree_box.remove(self.filetree_children.pop())

        self._populate_filetree(self.top_level_dir)

    def _load_scenario(self, *args):
        """Load the selected scenario"""
        if self.current_scenario_file is None:
            return

        self.load_file_callback(self.current_scenario_file)
        self.destroy()
