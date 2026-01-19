import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
from functools import partial

from Menus import DataMenu, AddMenu
from FileOpenDialog import FileOpenDialog
from FileSaveDialog import FileSaveDialog
from DefineObjectWindows import DefineCircuitWindow, DefineDetectorWindow
from EditWindows import EditBuildingWindow, EditDetectorWindow


class MainWindow(Gtk.ApplicationWindow):
    """Main Window of the application. Displays Detectors grouped in circuits as well as menus to access all
    application functionality."""

    def __init__(self, data_action_group, edit_action_group, hidden_action_group, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Steuerung Übungs-BMA")

        # Create a box that contains all other widgets in this window
        self.outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.outer_box)

        # Box that contains all circuits and detectors
        self.main_box = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, vexpand=True)
        self.main_box.set_margin_top(5)
        self.main_box.set_margin_bottom(5)
        self.main_box.set_margin_start(5)
        self.main_box.set_margin_end(5)
        self.main_box.set_row_spacing(20)
        self.main_box.set_column_spacing(20)
        self.main_box.set_size_request(-1, 400)
        self.outer_box.append(self.main_box)

        # Console to print information about active detectors to
        self.console_buffer = Gtk.TextBuffer()
        self.console = Gtk.TextView(editable=False,
                                    buffer=self.console_buffer,
                                    cursor_visible=False,
                                    left_margin=10,
                                    top_margin=10,
                                    monospace=True)
        self.console_frame = Gtk.Frame(child=self.console, label="Aktive Melder")
        self.outer_box.insert_child_after(self.console_frame, self.main_box)

        # Definition of the window header
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)

        # MenuButton to handle data operations
        self.data_menu = DataMenu()
        self.data_menubutton = Gtk.MenuButton(label="Datei", direction=Gtk.ArrowType.DOWN)
        self.data_menubutton.set_menu_model(self.data_menu)
        self.header.pack_start(self.data_menubutton)

        # MenuButton to add a circuit or edit the building description
        self.add_menu = AddMenu()
        self.add_menubutton = Gtk.MenuButton(label="+", direction=Gtk.ArrowType.DOWN)
        self.add_menubutton.set_menu_model(self.add_menu)
        self.add_menubutton.set_visible(False)
        self.header.pack_start(self.add_menubutton)

        # Buttons to control the LCD
        self.clear_alarms_button = Gtk.Button(label="Rücksetzen", action_name="hidden_actions.clear_alarms")
        self.header.pack_end(self.clear_alarms_button)
        self.next_alarm_button = Gtk.Button(label=">", action_name="hidden_actions.next_alarm")
        self.header.pack_end(self.next_alarm_button)
        self.previous_alarm_button = Gtk.Button(label="<", action_name="hidden_actions.previous_alarm")
        self.header.pack_end(self.previous_alarm_button)


        # Bind the action groups to the window
        self.insert_action_group("data", data_action_group)
        self.insert_action_group("edit", edit_action_group)
        self.insert_action_group("hidden_actions", hidden_action_group)

    def show_open_dialog(self, open_response_callback):
        """Show a FileOpenDialog."""
        file_open_dialog = FileOpenDialog()
        file_open_dialog.open(self, None, open_response_callback)

    def show_save_dialog(self, save_response_callback, file_type):
        """Show a FileSaveDialog."""
        file_save_dialog = FileSaveDialog(file_type)
        file_save_dialog.save(self, None, partial(save_response_callback, file_type=file_type))

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