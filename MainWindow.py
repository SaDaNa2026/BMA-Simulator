import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
from functools import partial

from Menus import DataMenu, EditMenu
from FileOpenDialog import FileOpenDialog
from FileSaveDialog import FileSaveDialog
from DefineObjectWindows import DefineCircuitWindow, DefineDetectorWindow
from EditWindows import EditBuildingWindow, EditDetectorWindow, EditCommitMessageWindow
from CommitListWindow import CommitListWindow
from Console import Console
from SettingsWindow import SettingsWindow


class MainWindow(Gtk.ApplicationWindow):
    """Main Window of the application. Displays Detectors grouped in circuits as well as menus to access all
    application functionality."""

    def __init__(self, edit_action_group, hidden_action_group, *args, **kwargs):
        super().__init__(*args, **kwargs, maximized=True)
        self.set_title("Steuerung Übungs-BMA")

        # A dictionary to keep track of the circuits in this window.
        self.circuit_dict: dict = {}

        # Create a box that contains all other widgets in this window
        self.outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.outer_box)

        # Box that contains all circuits and detectors
        self.scrollable = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                             vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        self.outer_box.append(self.scrollable)
        self.main_box = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE,
                                    vexpand=True,
                                    homogeneous=True,
                                    margin_top=5,
                                    margin_bottom=5,
                                    margin_start=5,
                                    margin_end=5,
                                    column_spacing=5)
        self.main_box.set_sort_func(self.sort_circuits, None)
        self.scrollable.set_size_request(-1, 400)
        self.scrollable.set_child(self.main_box)


        # Consoles that display information about active and disabled detectors
        self.console_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.console_box.set_size_request(600, -1)
        self.outer_box.insert_child_after(self.console_box, self.scrollable)
        self.active_console = Console("Ausgelöste Melder")
        self.console_box.append(self.active_console)
        self.disabled_console = Console("Abgeschaltete Melder")
        self.console_box.append(self.disabled_console)

        # Definition of the window header
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)

        # MenuButton to handle data operations
        self.data_menu = DataMenu()
        self.data_menubutton = Gtk.MenuButton(label="Datei", direction=Gtk.ArrowType.DOWN)
        self.data_menubutton.set_menu_model(self.data_menu)
        self.header.pack_start(self.data_menubutton)

        # MenuButton to add a circuit or edit the building description
        self.add_menu = EditMenu()
        self.add_menubutton = Gtk.MenuButton(label="Bearbeiten", direction=Gtk.ArrowType.DOWN)
        self.add_menubutton.set_menu_model(self.add_menu)
        self.add_menubutton.set_visible(False)
        self.header.pack_start(self.add_menubutton)

        # Buttons for undo/redo
        self.undo_button = Gtk.Button(icon_name="edit-undo", action_name="app.undo", tooltip_text="Undo")
        self.header.pack_start(self.undo_button)
        self.redo_button = Gtk.Button(icon_name="edit-redo", action_name="app.redo", tooltip_text="Redo")
        self.header.pack_start(self.redo_button)

        # Bind the action groups to the window
        self.insert_action_group("edit", edit_action_group)
        self.insert_action_group("hidden_actions", hidden_action_group)

    def show_settings_window(self, model, update_led_func):
        """Show the settings window"""
        settings_window = SettingsWindow(self, model, update_led_func)
        settings_window.present()

    def show_open_dialog(self, open_response_callback, last_dir):
        """Show a FileOpenDialog."""
        file_open_dialog = FileOpenDialog(last_dir)
        file_open_dialog.open(self, None, open_response_callback)

    def show_commit_message_window(self, finish_callback, file_type):
        self.commit_message_window = EditCommitMessageWindow(finish_callback, file_type, self)
        self.commit_message_window.present()

    def show_save_dialog(self, save_response_callback, message, file_type, last_dir, last_name):
        """Show a FileSaveDialog."""
        file_save_dialog = FileSaveDialog(file_type, last_dir, last_name)
        file_save_dialog.save(self, None, partial(save_response_callback, message=message, file_type=file_type))

    def show_commit_list(self, directory, commit_list, rollback_callback):
        commit_list_window = CommitListWindow(self, directory, commit_list, rollback_callback)
        commit_list_window.show()

    def show_error_alert(self, error_message, error_detail):
        """Display an error alert."""
        error_alert = Gtk.AlertDialog(message=error_message, detail=error_detail, modal=True)
        error_alert.show(self)

    def show_define_circuit_window(self, create_circuit_callback):
        self.define_circuit_window = DefineCircuitWindow(create_circuit_callback, self)
        self.define_circuit_window.present()

    def show_define_detector_window(self, circuit_number, create_detector_callback):
        self.define_detector_window = DefineDetectorWindow(circuit_number, create_detector_callback, self)
        self.define_detector_window.present()

    def show_edit_building_window(self, edit_building_callback, current_description):
        self.edit_building_window = EditBuildingWindow(current_description, edit_building_callback, self)
        self.edit_building_window.present()

    def show_edit_detector_window(self, circuit_number, detector_number, edit_detector_callback, current_description):
        self.edit_detector_window = EditDetectorWindow(circuit_number, detector_number, current_description, edit_detector_callback, self)
        self.edit_detector_window.present()

    def sort_circuits(self, child1, child2, user_data) -> int:
        """Sorting function for the circuits inside main_box."""
        circuit1 = child1.get_child()
        circuit2 = child2.get_child()

        if circuit1.circuit_number < circuit2.circuit_number:
            return -1
        elif circuit1.circuit_number > circuit2.circuit_number:
            return 1
        else:
            return 0