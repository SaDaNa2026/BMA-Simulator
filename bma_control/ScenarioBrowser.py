import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio
from gi.repository.Gio import File
from json import JSONDecodeError

from FileOperations import FileOperations
from ModalWindow import ModalWindow
from TagSelector import TagSelector


class BuildingFrame(Gtk.Frame):
    def __init__(self,
                 label: str,
                 scenario_files: list[File],
                 on_scenario_clicked_callback,
                 error_dialog_function,
                 tag_selector) -> None:
        super().__init__(label=label,
                         margin_start=5,
                         margin_end=5)
        self.error_dialog_function = error_dialog_function
        self.tag_selector = tag_selector
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.vbox)
        self.separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.vbox.append(self.separator)
        self.list_box = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE,
                                    show_separators=True)
        self.list_box.set_sort_func(self._sort_scenarios)
        self.list_box.set_filter_func(self._filter_scenarios)
        self.vbox.append(self.list_box)
        for scenario in scenario_files:
            scenario_path = scenario.get_path()
            if not scenario_path:
                return

            label = FileOperations.get_filename_without_extension(scenario_path)
            scenario_button = Gtk.Button(label=label,
                                         has_frame=False)
            scenario_button.connect("clicked", on_scenario_clicked_callback, scenario)
            scenario_button.scenario_file = scenario
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

    def get_scenario_tag_ids(self, scenario_file: File) -> list[str]:
        """Returns a list of the tag_ids of the given scenario"""
        try:
            open_value = FileOperations.open_file(scenario_file)
        except JSONDecodeError:
            self.error_dialog_function("Szenariodatei invalide",
                                       f"Stellen Sie sicher, dass {scenario_file.get_path()} dem "
                                       f"JSON-Standard entspricht",
                                       self.get_parent())
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


    def _filter_scenarios(self, row) -> bool:
        """Filter function for the scenarios in the listbox. Return True if the scenario contains all required tags"""
        scenario = row.get_child().scenario_file
        scenario_tags = self.get_scenario_tag_ids(scenario)

        return all(
            key in scenario_tags
            for key in self.tag_selector.selected_tags_dict.keys()
        )

    def contains_visible_scenarios(self) -> bool:
        """Check if list_box contains at least one scenario matching the filter"""
        for row in self.list_box:
            if self._filter_scenarios(row):
                return True

        return False


class ScenarioBrowser(ModalWindow):
    def __init__(self, parent, error_dialog_function, top_level_dir_path: str, tag_file_path: str, load_file_callback) -> None:
        """A window to browse through available scenarios grouped by building and view scenario descriptions.
        Filtering by tags is also available"""
        super().__init__(parent, resizable=True, title="Szenario-Browser", default_width=1000, default_height=600)
        self.error_dialog_function = error_dialog_function
        self.top_level_dir = Gio.File.new_for_path(top_level_dir_path)
        self.current_scenario_file: File | None = None
        self.load_file_callback = load_file_callback

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(self.main_box)

        # Add the file tree view in the left of the window
        self.filetree_frame = Gtk.Frame()
        self.filetree_frame_label = Gtk.Label()
        self.filetree_frame_label.set_markup("<span size='large'>Verfügbare Szenarien</span>")
        self.filetree_frame.set_label_widget(self.filetree_frame_label)
        self.main_box.append(self.filetree_frame)
        self.filetree_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.filetree_frame.set_child(self.filetree_box)
        self.separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.filetree_box.append(self.separator)
        # Search entry for filtering of building names
        self.search_entry = Gtk.SearchEntry(placeholder_text="Gebäudename...")
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.filetree_box.append(self.search_entry)
        # Scrollable ListBox for the BuildingFrames
        self.filetree_scrollable = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER,
                                                      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                                      vexpand=True)
        self.filetree_box.append(self.filetree_scrollable)
        self.filetree_listbox = Gtk.ListBox(show_separators=False,
                                            selection_mode=Gtk.SelectionMode.NONE,
                                            margin_top=5)
        self.filetree_listbox.set_sort_func(self._sort_filetree)
        self.filetree_listbox.set_filter_func(self._filter_filetree)
        self.filetree_scrollable.set_child(self.filetree_listbox)

        self.right_side_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.append(self.right_side_box)

        # Add a box for management of filter tags
        self.tag_selector = TagSelector(tag_file_path, error_dialog_function, self.reload_filetree)
        self.right_side_box.append(self.tag_selector)

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

        self._populate_filetree(self.top_level_dir)

    def _sort_filetree(self, child1, child2) -> int:
        """Sorting function for the building frames inside filetree_listbox"""
        building_label_1 = child1.get_child().get_label()
        building_label_2 = child2.get_child().get_label()

        if building_label_1 < building_label_2:
            return -1
        elif building_label_1 > building_label_2:
            return 1
        else:
            return 0

    def _filter_filetree(self, row) -> bool:
        """Filter function for the BuildingFrames inside filetree_listbox"""
        building_frame = row.get_child()
        building_frame.list_box.invalidate_filter()

        search_text = self.search_entry.get_text().lower()
        if not search_text:
            text_found = True
        else:
            # Frame is the child of the ListBoxRow. Convert the label to lowercase for case-insensitive filtering
            frame_label = building_frame.get_label().lower()
            text_found = search_text in frame_label

        return text_found and building_frame.contains_visible_scenarios()

    def _on_search_changed(self, entry) -> None:
        """Trigger refiltering when the search is changed"""
        self.filetree_listbox.invalidate_filter()

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

        building_frame = BuildingFrame(label,
                                       scenario_list,
                                       self._on_scenario_clicked,
                                       self.error_dialog_function,
                                       self.tag_selector)
        self.filetree_listbox.append(building_frame)

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

    def reload_filetree(self) -> None:
        """Clear filetree and repopulate it with the current filter selection. Clear the textview and current_file too"""
        self.description_textbuffer.set_text("")
        self.description_frame_label.set_text("")
        self.current_scenario_file = None
        self.confirm_button.set_sensitive(False)

        self.filetree_listbox.invalidate_filter()

    def _load_scenario(self, *args):
        """Load the selected scenario"""
        if self.current_scenario_file is None:
            return

        self.load_file_callback(self.current_scenario_file)
        self.destroy()
