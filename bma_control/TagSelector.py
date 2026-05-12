import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
import json
from json import JSONDecodeError

import Model


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


class TagSelector(Gtk.Box):
    def __init__(self, tag_file_path: str, error_dialog_function, on_selected_tags_changed_callback):
        """
        A box containing:
            1. a menubutton for selecting from a scrollable listbox of available tags
            2. a horizontal scrollable list of selected tags, each with a button to remove that tag"""
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL,
                       spacing=5,
                       margin_start=5,
                       margin_end=5)
        # Keep track of available and selected tags
        self.available_tags_dict: dict = self._load_tag_file(tag_file_path)
        self.selected_tags_dict: dict = {}

        self.error_dialog_function = error_dialog_function
        self.on_selected_tags_changed_callback = on_selected_tags_changed_callback

        self.tag_menu_button = Gtk.MenuButton(label="Filter",
                                              margin_top=10,
                                              margin_bottom=10)
        self.tag_menu_button.set_create_popup_func(self._set_filter_popover)
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

    def _set_filter_popover(self, *args) -> None:
        """Create a popover for the filter menu button"""
        self.tag_list_box = Gtk.ListBox(show_separators=True,
                                   selection_mode=Gtk.SelectionMode.NONE)
        for tag_id in self.available_tags_dict:
            tag_button = Gtk.Button(label=str(self.available_tags_dict[tag_id]),
                                    has_frame=False)
            tag_button.connect("clicked", self._on_add_tag_clicked, tag_id)
            self.tag_list_box.append(tag_button)

        scrollable = Gtk.ScrolledWindow(child=self.tag_list_box,
                                        vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                        hscrollbar_policy=Gtk.PolicyType.NEVER,
                                        max_content_height=400,
                                        propagate_natural_height=True)
        popover = Gtk.Popover(child=scrollable)
        self.tag_menu_button.set_popover(popover)

    def _load_tag_file(self, tag_file_path: str) -> dict:
        """Try to open and load the tag file. Display an error message if this fails"""
        try:
            if not tag_file_path:
                raise FileNotFoundError

            with open(tag_file_path, "r") as tag_json:
                tag_dict = json.load(tag_json)

        except (FileNotFoundError, JSONDecodeError):
            self.error_dialog_function("Tag file not found",
                                       f"Make sure a json-formatted dictionary of tags and associated IDs to be "
                                       f"used for scenario filtering is located at {tag_file_path}.\n"
                                       f"In the current state, scenario filtering will be unavailable.",
                                       self.get_parent())
            tag_dict = {}

        # Convert str keys to int
        return_dict: dict = {}
        for key in tag_dict.keys():
            return_dict[int(key)] = tag_dict[key]

        return return_dict

    def _on_add_tag_clicked(self, button, tag_id: int) -> None:
        """Move the tag with the provided id from available_tags_dict to selected_tags_dict if possible.
        Append a filter button to the filter box"""
        if tag_id not in self.available_tags_dict or tag_id in self.selected_tags_dict:
            return

        self.selected_tags_dict[tag_id] = self.available_tags_dict.pop(tag_id)
        self.selected_tags_dict = Model.sort_dict_by_key(self.selected_tags_dict)

        tag_object = TagObject(tag_id, self.selected_tags_dict[tag_id], self._on_tag_remove_clicked)
        self.tag_box.append(tag_object)
        self.tag_list_box.remove(button.get_parent())
        self.on_selected_tags_changed_callback()

    def _on_tag_remove_clicked(self, button, tag_object) -> None:
        """Remove the tag object and move the tag from selected_tags_dict to available_tags_dict if possible"""
        tag_id = tag_object.tag_id
        self.available_tags_dict[tag_id] = self.selected_tags_dict.pop(tag_id)
        self.available_tags_dict = Model.sort_dict_by_key(self.available_tags_dict)
        self.tag_box.remove(tag_object)
        self.on_selected_tags_changed_callback()