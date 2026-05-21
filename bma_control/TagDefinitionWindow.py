import random
from time import time
from enum import Enum

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gio

import json
from json import JSONDecodeError
from ModalWindow import ModalWindow
from ConfirmationBox import ConfirmationBox


class ActionType(Enum):
    DO = 1
    UNDO = 2
    REDO = 3


class TagBox(Gtk.Box):
    def __init__(self, tag_id: str, list_index: int, text: str, move_func, delete_func) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL,
                         spacing=5,
                         focusable=False,
                         margin_top=10,
                         margin_bottom=10,
                         margin_start=20,
                         margin_end=20)
        self.tag_id = tag_id
        self.list_index = list_index
        self.entry = Gtk.Entry(text=text,
                               margin_end=60,
                               width_chars=15)
        self.append(self.entry)
        self.down_button = Gtk.Button(icon_name="go-down-symbolic")
        self.down_button.connect("clicked", move_func, "down")
        self.append(self.down_button)
        self.up_button = Gtk.Button(icon_name="go-up-symbolic")
        self.up_button.connect("clicked", move_func, "up")
        self.append(self.up_button)
        self.remove_button = Gtk.Button(icon_name="edit-delete-symbolic")
        self.remove_button.connect("clicked", delete_func)
        self.append(self.remove_button)


class TagDefinitionWindow(ModalWindow):
    def __init__(self, parent, tag_file_path: str, error_dialog_function, tag_selector) -> None:
        """A Window for editing the tag file"""
        super().__init__(parent, title="Szenario-Tags verwalten")
        # Set the random seed for ID generation when tags are added
        random.seed(time())

        self.tag_file_path = tag_file_path
        self.tag_selector = tag_selector

        # Set up undo/redo actions
        self.undo_stack: list = []
        self.redo_stack: list = []

        action_entries = [("undo", self.undo, None),
                          ("redo", self.redo, None)]
        self.actions = Gio.SimpleActionGroup.new()
        self.actions.add_action_entries(action_entries)
        self.insert_action_group("tag_actions", self.actions)
        
        # Disable undo/redo actions until entries are pushed to the respective stack
        for name in self.actions.list_actions():
            action = self.actions.lookup_action(name)
            if isinstance(action, Gio.SimpleAction):
                action.set_enabled(False)

        self.undo_shortcut = Gtk.Shortcut(action=Gtk.NamedAction.new("tag_actions.undo"),
                                          trigger=Gtk.ShortcutTrigger.parse_string("<Ctrl>Z"))
        self.add_shortcut(self.undo_shortcut)
        self.redo_shortcut = Gtk.Shortcut(action=Gtk.NamedAction.new("tag_actions.redo"),
                                          trigger=Gtk.ShortcutTrigger.parse_string("<Ctrl><Shift>Z|<Ctrl>Y"))
        self.add_shortcut(self.redo_shortcut)

        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)

        self.undo_button = Gtk.Button(icon_name="edit-undo-symbolic", action_name="tag_actions.undo", tooltip_text="Undo")
        self.header.pack_start(self.undo_button)
        self.redo_button = Gtk.Button(icon_name="edit-redo-symbolic", action_name="tag_actions.redo", tooltip_text="Redo")
        self.header.pack_start(self.redo_button)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.main_box)

        self.listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE,
                                   focusable=False,
                                   show_separators=True)
        self.listbox.set_sort_func(self._sort_tag_list)
        self.scroll_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.scroll_box.append(self.listbox)
        self.scrolled_window = Gtk.ScrolledWindow(child=self.scroll_box,
                                                  hscrollbar_policy=Gtk.PolicyType.NEVER,
                                                  vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                                  max_content_height=600,
                                                  propagate_natural_height=True,
                                                  margin_bottom=10)
        self.main_box.append(self.scrolled_window)

        try:
            with open(tag_file_path, "r") as tag_file:
                tag_dict = json.load(tag_file)

        except JSONDecodeError:
            GLib.idle_add(error_dialog_function("Invalides Dateiformat",
                                                f"Stellen Sie sicher, dass {tag_file_path} existiert und dem "
                                                f"JSON-Standard entspricht.",
                                                parent))
            self.destroy()
            return

        except FileNotFoundError:
            GLib.idle_add(error_dialog_function("Tag-Datei nicht gefunden",
                                                f"Stellen Sie sicher, dass unter {tag_file_path} eine JSON-Datei im Format "
                                                f"'Tag-ID': [list_index, tag_description] vorhanden ist.",
                                                parent))
            self.destroy()
            return

        # Keep track of the list indexes already added to check if an index exists more than once
        list_indexes: list = []
        # Keep references to the TagBox objects added to listbox
        self.tag_boxes: list = []
        for tag_id in tag_dict:
            tag_values = tag_dict[tag_id]
            if not type(tag_values) == list:
                error_dialog_function("Falsches Tag-Format",
                                      f"Tag-ID {tag_id} entspricht nicht einer Liste. Folgendes Format "
                                      f"muss eingehalten werden: 'Tag-ID': [list_index, tag_name]\n"
                                      f"Tag-Datei: {tag_file_path}",
                                      self)
                continue

            if not len(tag_values) == 2:
                error_dialog_function("Falsches Tag-Format",
                                      f"Tag-ID {tag_id} entspricht nicht einer Liste mit 2 Einträgen. Folgendes Format "
                                      f"muss eingehalten werden: 'Tag-ID': [list_index, tag_name]\n"
                                      f"Tag-Datei: {tag_file_path}",
                                      self)
                continue

            list_index = tag_values[0]
            if not type(list_index) == int:
                error_dialog_function("Falsches Tag-Format",
                                      f"list_index von Tag {tag_id} ist keine natürliche Zahl. Folgendes Format muss "
                                      f"eingehalten werden: 'Tag-ID': [list_index, tag_name]\n"
                                      f"Tag-Datei: {tag_file_path}",
                                      self)
                continue

            if list_index in list_indexes:
                error_dialog_function("Doppelter Listen-Index",
                                      f"list_index {list_index} kommt in {tag_file_path} mehr als einmal vor, was nicht "
                                      f"erlaubt ist.\nFormat der Datei: 'Tag-ID': [list_index, tag_name]",
                                      self)

            tag_name = tag_values[1]
            if not type(tag_name) == str:
                error_dialog_function("Falsches Tag-Format",
                                      f"tag_name von Tag {tag_id} ist kein String. Folgendes Format muss "
                                      f"eingehalten werden: 'Tag-ID': [list_index, tag_name]\n"
                                      f"Tag-Datei: {tag_file_path}",
                                      self)
                continue

            tag_box = TagBox(tag_id, list_index, tag_name, self.move_tag, self.delete_tag)
            self.listbox.append(tag_box)
            self.tag_boxes.append(tag_box)
            list_indexes.append(list_index)

        self.make_list_indexes_continuous()

        # Button for adding a new Tag
        add_button_label = Gtk.Label(margin_top=10, margin_bottom=10)
        add_button_label.set_markup("<span size='large'>Tag hinzufügen</span>")
        self.add_button = Gtk.Button()
        self.add_button.connect("clicked", lambda button, *args: self.add_tag())
        self.add_button.set_child(add_button_label)
        self.scroll_box.append(self.add_button)

        # Confirm and Cancel buttons
        self.confirmation_box = ConfirmationBox(self.destroy, self.write_changes, "Speichern")
        self.main_box.append(self.confirmation_box)

    def _sort_tag_list(self, child1, child2):
        """Sorting function for the tags in listbox"""
        tag1 = child1.get_child()
        tag2 = child2.get_child()

        if tag1.list_index < tag2.list_index:
            return -1
        elif tag1.list_index > tag2.list_index:
            return 1
        else:
            return 0

    def get_sorted_list_indexes(self) -> list:
        """Returns a sorted list of the list indexes of all tag boxes"""
        number_list: list = []
        for tag_box in self.tag_boxes:
            number_list.append(tag_box.list_index)
        number_list.sort()

        return number_list

    def make_list_indexes_continuous(self) -> None:
        """Makes sure that there are no 'holes' in list_indexes, i.e. every value in list_indexes is equal to its index
        as long as list_indexes is sorted"""
        number_list = self.get_sorted_list_indexes()

        # Every list index now is the index of the previous list index in number_list. Yes, I know this is stupid.
        for tag_box in self.tag_boxes:
            old_list_index = tag_box.list_index
            tag_box.list_index = number_list.index(old_list_index)


    def move_tag(self, button, direction: str, action_type: ActionType = ActionType.DO) -> None:
        """Move the tag box which is the parent of the clicked button in the specified direction, if possible"""
        tag_box = button.get_parent()
        old_list_index = tag_box.list_index
        match direction:
            case "up":
                if tag_box.list_index == 0:
                    return
                tag_box.list_index -= 1
                reverse_direction = "down"

            case "down":
                if not any(tag_box.list_index < other_tag.list_index for other_tag in self.tag_boxes):
                    return
                tag_box.list_index += 1
                reverse_direction = "up"

            case _:
                return

        for other_tag_box in self.tag_boxes:
            if other_tag_box.tag_id == tag_box.tag_id:
                continue

            if other_tag_box.list_index == tag_box.list_index:
                other_tag_box.list_index = old_list_index

        self.listbox.invalidate_sort()

        match action_type:
            case ActionType.DO:
                self.append_undo((self.move_tag, (button, reverse_direction)))
                self.clear_redo()
            case ActionType.UNDO:
                self.append_redo((self.move_tag, (button, reverse_direction)))
            case ActionType.REDO:
                self.append_undo((self.move_tag, (button, reverse_direction)))

    def delete_tag(self, button, action_type: ActionType = ActionType.DO) -> None:
        """Remove the tag box which is the parent of the clicked button"""
        tag_box = button.get_parent()

        # Get data for undo
        tag_id = tag_box.tag_id
        list_index = tag_box.list_index
        text = tag_box.entry.get_text()

        # Remove tag_box
        self.tag_boxes.remove(tag_box)
        listbox_row = tag_box.get_parent()
        self.listbox.remove(listbox_row)
        self.make_list_indexes_continuous()
        self.listbox.invalidate_sort()

        match action_type:
            case ActionType.DO:
                self.append_undo((self.add_tag, (tag_id, list_index, text)))
                self.clear_redo()
            case ActionType.UNDO:
                self.append_redo((self.add_tag, (tag_id, list_index, text)))
            case ActionType.REDO:
                self.append_undo((self.add_tag, (tag_id, list_index, text)))

    def add_tag(self,
                tag_id: str | None = None,
                list_index: int | None = None,
                text: str = "",
                action_type: ActionType = ActionType.DO) -> None:
        """Add a tag, optionally with the specified tag_id and index (if possible)"""
        if tag_id is None:
            # Generate a random tag_id
            tag_id = str(random.randint(1000000000, 9999999999))

        # Verify this tag_id does not already exist
        while any(tag_id == tag_box.tag_id for tag_box in self.tag_boxes):
            tag_id = str(random.randint(1000000000, 9999999999))

        # Determine list index
        self.make_list_indexes_continuous()
        previous_indexes = self.get_sorted_list_indexes()
        if list_index is None:
            list_index = len(previous_indexes)

        # Increment all list indexes which are greater than or equal list_index by 1 to make room for the new tag
        for tag_box in self.tag_boxes:
            if tag_box.list_index >= list_index:
                tag_box.list_index += 1

        tag_box = TagBox(tag_id, list_index, text, self.move_tag, self.delete_tag)
        self.listbox.append(tag_box)
        self.tag_boxes.append(tag_box)
        self.listbox.invalidate_sort()

        match action_type:
            case ActionType.DO:
                self.append_undo((self.delete_tag, (tag_box.remove_button,)))
                self.clear_redo()
            case ActionType.UNDO:
                self.append_redo((self.delete_tag, (tag_box.remove_button,)))
            case ActionType.REDO:
                self.append_undo((self.delete_tag, (tag_box.remove_button,)))

    def write_changes(self):
        """Write the current configuration to disk"""
        save_dict: dict = {}
        for tag_box in self.tag_boxes:
            save_dict[tag_box.tag_id] = [tag_box.list_index, tag_box.entry.get_text()]

        with open(self.tag_file_path, "w") as tag_file:
            json.dump(save_dict, tag_file, indent=4)

        # Reset the tag selector in the main window
        selected_tag_ids = tuple(self.tag_selector.selected_tags_dict.keys())
        self.tag_selector.reset(selected_tag_ids)

    def undo(self, *args):
        """Pop last entry off the undo stack and execute it"""
        if len(self.undo_stack) > 0:
            action_tuple = self.undo_stack.pop()
            action_tuple[0](*action_tuple[1], ActionType.UNDO)

        if len(self.undo_stack) == 0:
            undo_action = self.actions.lookup_action("undo")
            if isinstance(undo_action, Gio.SimpleAction):
                undo_action.set_enabled(False)

    def redo(self, *args):
        """Pop last entry off the redo stack and execute it"""
        if len(self.redo_stack) > 0:
            action_tuple = self.redo_stack.pop()
            action_tuple[0](*action_tuple[1], ActionType.REDO)

        if len(self.redo_stack) == 0:
            redo_action = self.actions.lookup_action("redo")
            if isinstance(redo_action, Gio.SimpleAction):
                redo_action.set_enabled(False)

    def append_undo(self, entry: tuple) -> None:
        """Append the given entry to the undo stack and enable the undo action"""
        self.undo_stack.append(entry)
        undo_action = self.actions.lookup_action("undo")
        if isinstance(undo_action, Gio.SimpleAction):
            undo_action.set_enabled(True)

    def append_redo(self, entry: tuple) -> None:
        """Append the given entry to the redo stack and enable the redo action"""
        self.redo_stack.append(entry)
        redo_action = self.actions.lookup_action("redo")
        if isinstance(redo_action, Gio.SimpleAction):
            redo_action.set_enabled(True)

    def clear_redo(self) -> None:
        """Clear the undo stack"""
        self.redo_stack.clear()
        redo_action = self.actions.lookup_action("redo")
        if isinstance(redo_action, Gio.SimpleAction):
            redo_action.set_enabled(False)
