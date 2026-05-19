import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

import json
from json import JSONDecodeError
from ModalWindow import ModalWindow
from ConfirmationBox import ConfirmationBox
from random import randint


class TagBox(Gtk.Box):
    def __init__(self, list_index: int, text: str) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL,
                         spacing=5,
                         focusable=False,
                         margin_top=10,
                         margin_bottom=10,
                         margin_start=20,
                         margin_end=20)
        self.list_index = list_index
        self.entry = Gtk.Entry(text=text,
                               margin_end=60,
                               width_chars=15)
        self.append(self.entry)
        self.down_button = Gtk.Button(icon_name="go-down-symbolic")
        self.append(self.down_button)
        self.up_button = Gtk.Button(icon_name="go-up-symbolic")
        self.append(self.up_button)
        self.remove_button = Gtk.Button(icon_name="edit-delete-symbolic")
        self.append(self.remove_button)


class TagDefinitionWindow(ModalWindow):
    def __init__(self, parent, tag_file_path: str, error_dialog_function) -> None:
        super().__init__(parent, title="Szenario-Tags verwalten")
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
            error_dialog_function("Invalides Dateiformat",
                                  f"Stellen Sie sicher, dass {tag_file_path} existiert und dem JSON-Standard entspricht.")
            self.destroy()
            return

        for tag_id in tag_dict:
            tag_values = tag_dict[tag_id]
            if not type(tag_values) == list:
                error_dialog_function("Falsches Tag-Format",
                                      f"Tag-ID {tag_id} entspricht nicht einer Liste. Folgendes Format muss "
                                      f"eingehalten werden: 'Tag-ID': [list_index, tag_description]")
                continue

            tag_row = TagBox(tag_values[0], tag_values[1])
            self.listbox.append(tag_row)

        # Button for adding a new Tag
        add_button_label = Gtk.Label(margin_top=10, margin_bottom=10)
        add_button_label.set_markup("<span size='large'>Tag hinzufügen</span>")
        self.add_button = Gtk.Button()
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
    
    def write_changes(self):
        """Write the current configuration to disk and destroy self"""
        pass
