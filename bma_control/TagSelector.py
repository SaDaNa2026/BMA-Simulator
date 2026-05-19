import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import json
from json import JSONDecodeError

import Model


class TagObject(Gtk.Frame):
    def __init__(self, tag_id: str, tag_name: str, remove_callback):
        super().__init__()
        self.tag_id = tag_id
        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin_start=5)
        self.set_child(self.box)
        self.label = Gtk.Label(label=tag_name, opacity=0.9)
        self.box.append(self.label)
        self.remove_button = Gtk.Button(icon_name="process-stop-symbolic", has_frame=False)
        self.remove_button.connect("clicked", remove_callback, self)
        self.box.append(self.remove_button)


class TagSelector(Gtk.Box):
    def __init__(self, tag_file_path: str, error_dialog_function, on_selected_tags_changed_callback=None):
        """
        A box containing:
            1. a menubutton for selecting from a scrollable listbox of available tags
            2. a horizontal scrollable list of selected tags, each with a button to remove that tag"""
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL,
                         spacing=5,
                         margin_start=5,
                         margin_end=5)
        self.error_dialog_function = error_dialog_function
        # Keep track of available and selected tags
        self.available_tags_dict: dict = self._load_tag_file(tag_file_path)
        self.selected_tags_dict: dict = {}
        # Keep track of the tag objects in tag_box
        self.tag_object_list: list = []

        self.tag_file_path = tag_file_path
        self.on_selected_tags_changed_callback = on_selected_tags_changed_callback

        self.tag_menu_button = Gtk.MenuButton(label="Filter-Tags",
                                              margin_top=10,
                                              margin_bottom=10)
        self.tag_menu_button.set_create_popup_func(self._set_tags_popover)
        self.append(self.tag_menu_button)
        self.append(Gtk.Separator())
        self.tag_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                               spacing=10,
                               margin_top=10,
                               margin_bottom=10)
        self.tag_box_scrollable = Gtk.ScrolledWindow(child=self.tag_box,
                                                     vscrollbar_policy=Gtk.PolicyType.NEVER,
                                                     hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                                     hexpand=True,
                                                     propagate_natural_width=True)
        self.append(self.tag_box_scrollable)

    def _set_tags_popover(self, *args) -> None:
        """Create a popover for the filter menu button"""
        self.tag_list_box = Gtk.ListBox(show_separators=True,
                                        selection_mode=Gtk.SelectionMode.NONE)
        self.tag_list_box.set_sort_func(self._sort_tags)
        for tag_id in self.available_tags_dict:
            tag_values = self.available_tags_dict[tag_id]
            tag_button = Gtk.Button(label=str(tag_values[1]),
                                    has_frame=False)
            tag_button.connect("clicked", self._on_add_tag_clicked, tag_id)
            tag_button.list_index = tag_values[0]
            self.tag_list_box.append(tag_button)

        scrollable = Gtk.ScrolledWindow(child=self.tag_list_box,
                                        vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                        hscrollbar_policy=Gtk.PolicyType.NEVER,
                                        max_content_height=400,
                                        propagate_natural_height=True)
        popover = Gtk.Popover(child=scrollable)
        self.tag_menu_button.set_popover(popover)

    def _sort_tags(self, child1, child2):
        """Sorting function for the tags in the listbox"""
        tag1 = child1.get_child()
        tag2 = child2.get_child()

        if tag1.list_index < tag2.list_index:
            return -1
        elif tag1.list_index > tag2.list_index:
            return 1
        else:
            return 0

    def _load_tag_file(self, tag_file_path: str) -> dict:
        """Try to open and load the tag file. Display an error message if this fails"""
        try:
            if not tag_file_path:
                raise FileNotFoundError

            with open(tag_file_path, "r") as tag_json:
                tag_dict = json.load(tag_json)

        except (FileNotFoundError, JSONDecodeError):
            GLib.idle_add(self.error_dialog_function, "Tag-Datei nicht gefunden",
                          f"Stellen Sie sicher, dass unter {tag_file_path} eine JSON-Datei im Format "
                          f"'Tag-ID': [list_index, tag_description] vorhanden ist.\n"
                          f"Im aktuellen Zustand kann nicht nach Szenario-Tags gefiltert werden.",
                          self.get_parent())
            tag_dict = {}

        return_dict = self.cleanse_tag_dict(tag_dict)

        return return_dict

    def _on_add_tag_clicked(self, button, tag_id: str) -> None:
        """Move the tag with the provided id from available_tags_dict to selected_tags_dict if possible.
        Append a filter button to the filter box"""
        if tag_id not in self.available_tags_dict or tag_id in self.selected_tags_dict:
            return

        self.selected_tags_dict[tag_id] = self.available_tags_dict.pop(tag_id)
        self.selected_tags_dict = Model.sort_dict_by_key(self.selected_tags_dict)

        tag_object = TagObject(tag_id, self.selected_tags_dict[tag_id][1], self._on_tag_remove_clicked)
        self.tag_box.append(tag_object)
        self.tag_object_list.append(tag_object)
        self.tag_list_box.remove(button.get_parent())
        if self.on_selected_tags_changed_callback:
            self.on_selected_tags_changed_callback()

    def _on_tag_remove_clicked(self, button, tag_object) -> None:
        """Remove the tag object and move the tag from selected_tags_dict to available_tags_dict if possible"""
        tag_id = tag_object.tag_id
        self.available_tags_dict[tag_id] = self.selected_tags_dict.pop(tag_id)
        self.available_tags_dict = Model.sort_dict_by_key(self.available_tags_dict)
        self.tag_box.remove(tag_object)
        self.tag_object_list.remove(tag_object)
        if self.on_selected_tags_changed_callback:
            self.on_selected_tags_changed_callback()

    def reset(self, selected_tag_ids_tuple: tuple = ()):
        """Reload available tags from disk. Select all provided tag_ids if available"""
        # Clear tag_box
        while len(self.tag_object_list) > 0:
            self.tag_box.remove(self.tag_object_list.pop())

        self.available_tags_dict = self._load_tag_file(self.tag_file_path)
        self.selected_tags_dict.clear()
        # Move selected tags and create tag objects
        for tag_id in selected_tag_ids_tuple:
            if tag_id in self.available_tags_dict.keys():
                self.selected_tags_dict[tag_id] = self.available_tags_dict.pop(tag_id)
                self.selected_tags_dict = Model.sort_dict_by_key(self.selected_tags_dict)

                tag_object = TagObject(tag_id, self.selected_tags_dict[tag_id][1], self._on_tag_remove_clicked)
                self.tag_box.append(tag_object)
                self.tag_object_list.append(tag_object)

        self._set_tags_popover()

    def cleanse_tag_dict(self, tag_dict: dict) -> dict:
        """Remove all key-value pairs in tag_dict with invalid syntax and return the resulting dict"""
        return_dict: dict = {}
        for tag_id in tag_dict.keys():
            if not type(tag_id) == str:
                continue

            tag_values = tag_dict[tag_id]

            if not type(tag_values) == list:
                continue

            if not len(tag_values) == 2:
                continue

            if not type(tag_values[0]) == int:
                continue

            if not type(tag_values[1]) == str:
                continue

            return_dict[tag_id] = tag_values

        return return_dict
