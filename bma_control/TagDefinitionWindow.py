import random
from time import time

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

import json
from json import JSONDecodeError
from ModalWindow import ModalWindow
from ConfirmationBox import ConfirmationBox


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
                                                  margin_bottom=20)
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


    def move_tag(self, button, direction: str) -> None:
        """Move the tag box which is the parent of the clicked button in the specified direction, if possible"""
        tag_box = button.get_parent()
        old_list_index = tag_box.list_index
        match direction:
            case "up":
                if tag_box.list_index == 0:
                    return
                tag_box.list_index -= 1

            case "down":
                if not any(tag_box.list_index < other_tag.list_index for other_tag in self.tag_boxes):
                    return
                tag_box.list_index += 1

            case _:
                return

        for other_tag_box in self.tag_boxes:
            if other_tag_box.tag_id == tag_box.tag_id:
                continue

            if other_tag_box.list_index == tag_box.list_index:
                other_tag_box.list_index = old_list_index

        self.listbox.invalidate_sort()

    def delete_tag(self, button) -> None:
        """Remove the tag box which is the parent of the clicked button"""
        tag_box = button.get_parent()
        self.tag_boxes.remove(tag_box)
        listbox_row = tag_box.get_parent()
        self.listbox.remove(listbox_row)
        self.make_list_indexes_continuous()
        self.listbox.invalidate_sort()

    def add_tag(self, list_index: int | None = None) -> None:
        """Add a tag, optionally at the specified index (if possible)"""
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

        tag_box = TagBox(tag_id, list_index, "", self.move_tag, self.delete_tag)
        self.listbox.append(tag_box)
        self.tag_boxes.append(tag_box)
        self.listbox.invalidate_sort()

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
