import os
import subprocess
import sys
import gpiozero

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk, Gio, GLib, Gdk
from json import JSONDecodeError

from Operations import DetectorOps, CircuitOps, BuildingOps
from Model import BuildingModel
from FileOperations import FileOperations
from MainWindow import MainWindow
from LCDController import LCDController
from MCPController import MCPController
from mcp23017 import *
from LEDController import LEDController


# -----------------------------------------------CONSTANTS--------------------------------------------------------------
# Set this to the application used to view HELP.md
MARKDOWN_VIEWER: str = "okular"
# Set this to the GPIO pin that the relay for the flashing light (Blitzleuchte) is connected to.
# Setting it to None will disable all functionality regarding the flashing light.
FLASH_RELAY_PIN: int|None = 26


# ----------------------------------------------APPLICATION-------------------------------------------------------------
class App(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id="org.example.BMA-control", **kwargs)
        self.connect('activate', self.on_activate)
        self.connect('shutdown', self.on_shutdown)

        self.model = BuildingModel()
        self.lcd = LCDController(self.model)

        # Create a placeholder to memorize opened files
        self.last_file = Gio.File.new_for_path("/home/lfs-bma/git_test1")

        # Keep track if the reset button has been pressed. This is necessary to check if the alarm LED needs to light up
        # if there are detectors in the history. Resets when a new file is loaded
        self.is_reset: bool = False

        self.undo_stack: list = []
        self.redo_stack: list = []

        # Initialize the operations
        self.detector_ops = DetectorOps(self.model, self)
        self.circuit_ops = CircuitOps(self.model, self)
        self.building_ops = BuildingOps(self.model, self)

        # Actions for all buttons to connect to
        app_action_entries = [("save_building", self.on_save_clicked, None),
                              ("save_scenario", self.on_save_clicked, None),
                              ("open", self.on_open_clicked, None),
                              ("rollback", self.on_rollback_clicked, None),
                              ("edit_mode", None, None, "false", self.on_edit_mode_clicked),
                              ("undo", self.on_undo_clicked, None),
                              ("redo", self.on_redo_clicked, None),
                              ("help", self.on_help_clicked, None),
                              ("about", self.on_about_clicked, None),
                              ("settings", self.on_settings_clicked, None)]

        edit_action_entries = [("create_circuit", self.on_add_circuit_clicked, None),
                               ("delete_circuit", self.on_delete_circuit_clicked, "i"),
                               ("create_detector", self.on_add_detector_clicked, "i"),
                               ("delete_detector", self.on_delete_detector_clicked, "s"),
                               ("edit_detector", self.on_edit_detector_clicked, "s"),
                               ("edit_building", self.on_edit_building_clicked, None),
                               ("edit_fbf", self.on_edit_fbf_clicked, None),
                               ("clear_disabled", self.on_clear_disabled_clicked, None),
                               ("clear_history", self.on_clear_history_clicked, None)]

        hidden_action_entries = [("previous_alarm", self.on_previous_message_clicked, None),
                                 ("next_alarm", self.on_next_message_clicked, None)]

        # Add app actions to self
        self.add_action_entries(app_action_entries, None)

        # Disable undo and redo actions (will be enabled when the respective stack has entries)
        for action_name in ("undo", "redo"):
            action = self.lookup_action(action_name)
            if isinstance(action, Gio.SimpleAction):
                action.set_enabled(False)

        # Add the window's action entries to groups
        self.edit_action_group = Gio.SimpleActionGroup.new()
        self.edit_action_group.add_action_entries(edit_action_entries, None)

        self.hidden_action_group = Gio.SimpleActionGroup()
        self.hidden_action_group.add_action_entries(hidden_action_entries, None)

        # Create an empty action group.
        # Detector enable and history actions will be added dynamically as detectors are created
        self.detector_action_group = Gio.SimpleActionGroup.new()

        # Set edit actions disabled
        for name in self.edit_action_group.list_actions():
            action = self.edit_action_group.lookup_action(name)
            if isinstance(action, Gio.SimpleAction):
                action.set_enabled(False)

        # Add shortcuts to the actions
        self.accels_list = [
            ("app.help", ["F1"]),
            ("app.settings", ["<Ctrl>P"]),
            ("app.save_building", ["<Ctrl>G"]),
            ("app.save_scenario", ["<Ctrl>S"]),
            ("app.open", ["<Ctrl>O"]),
            ("app.edit_mode", ["<Ctrl>E"]),
            ("app.undo", ["<Ctrl>Z"]),
            ("app.redo", ["<Ctrl><Shift>Z", "<Ctrl>Y"]),
            ("edit.create_circuit", ["<Ctrl>I"]),
            ("edit.edit_building", ["<Ctrl>B"]),
            ("edit.edit_fbf", ["<Ctrl>L"])
        ]
        for accel in self.accels_list:
            self.set_accels_for_action(*accel)

        # Variables mirroring the state of the switches on the FBF
        self.acoustic_signals_off_switch: bool = False
        self.ue_off_switch: bool = False
        self.fire_controls_off_switch: bool = False

        # Set up the port expander on the FAT
        self.fat_led_dict = {"previous_alarm": GPB4,
                             "next_alarm": GPB0,
                             "view_level": GPB6,
                             "beeper_off": GPB2,
                             "beeper": GPA4,
                             "working": GPA3,
                             "alarm": GPA2,
                             "error": GPA1,
                             "turn_off": GPA0}

        self.mcp_fat = MCPController(0x27,
                                     [(GPB1, self.on_next_message_clicked, None, False, False),
                                      (GPB3, self.on_beeper_off_clicked, self.on_self_test_pressed, False, False),
                                      (GPB5, self.on_previous_message_clicked, None, False, False),
                                      (GPB7, self.on_view_level_clicked, self.on_history_pressed, False, False)],
                                     self.fat_led_dict)

        self.led_fat = LEDController(self.mcp_fat, self.fat_led_dict)

        # Set up the port expander on the FBF
        self.fbf_led_dict = {"working": GPA0,
                             "extinguisher_triggered": GPA1,
                             "acoustic_signals_off": GPA2,
                             "ue_off": GPA3,
                             "ue_triggered": GPB5,
                             "fire_controls_off": GPB4,
                             "alarm": GPB3}

        self.mcp_fbf = MCPController(0x26,
                                     [(GPA4, self.on_acoustic_signals_off_toggled, None, True, False),
                                      (GPA5, self.on_ue_off_toggled, None, True, False),
                                      (GPB2, self.on_fire_controls_off_toggled, None, True, True),
                                      (GPB1, self.on_clear_alarms_clicked, None, False, False),
                                      (GPB0, self.on_UE_test_clicked, None, False, False)],
                                     self.fbf_led_dict)

        self.led_fbf = LEDController(self.mcp_fbf, self.fbf_led_dict)

        # Turn on the green LEDs
        self.led_fat.on("working")
        self.led_fbf.on("working")

        # Set up the relay for the flashing light
        if FLASH_RELAY_PIN is not None:
            self.flash_relay = gpiozero.OutputDevice(pin=FLASH_RELAY_PIN, active_high=False)

        self.window = MainWindow(edit_action_group=self.edit_action_group,
                                 hidden_action_group=self.hidden_action_group,
                                 detector_action_group=self.detector_action_group)

    def on_activate(self, app):
        self.window.set_application(app)
        self.window.present()

    def on_shutdown(self, app):
        """Clean up the hardware interface when the application is closed."""
        self.lcd.clear()
        self.led_fat.shutdown()
        self.led_fbf.shutdown()
        if FLASH_RELAY_PIN is not None:
            self.flash_relay.off()

    def append_undo(self, entry: tuple) -> None:
        """Append the given entry to the undo stack and enable the undo action"""
        self.undo_stack.append(entry)
        undo_action = self.lookup_action("undo")
        if isinstance(undo_action, Gio.SimpleAction):
            undo_action.set_enabled(True)

    def append_redo(self, entry: tuple) -> None:
        """Append the given entry to the redo stack and enable the redo action"""
        self.redo_stack.append(entry)
        redo_action = self.lookup_action("redo")
        if isinstance(redo_action, Gio.SimpleAction):
            redo_action.set_enabled(True)

    def clear_undo(self):
        """Clear the undo stack"""
        self.undo_stack.clear()
        undo_action = self.lookup_action("undo")
        if isinstance(undo_action, Gio.SimpleAction):
            undo_action.set_enabled(False)

    def clear_redo(self):
        """Clear the undo stack"""
        self.redo_stack.clear()
        redo_action = self.lookup_action("redo")
        if isinstance(redo_action, Gio.SimpleAction):
            redo_action.set_enabled(False)

    def on_circuit_pressed(self, gesture, n_press, x, y, circuit_number: int) -> None:
        """Present a context menu on a circuit if edit mode is enabled."""
        # Don't respond if edit mode is disabled
        if not self.get_action_state("edit_mode").get_boolean():
            return

        # Get the circuit that was clicked
        circuit = self.window.circuit_dict[circuit_number]

        # Create an invisible rectangle at the position of the click that the context menu points to
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1

        circuit.context_menu_popover.set_pointing_to(rect)
        circuit.context_menu_popover.popup()

    def on_detector_right_pressed(self, gesture, n_press, x, y, circuit_number: int, detector_number: int) -> None:
        """Present a context menu on a detector"""
        # Get the detector that was clicked
        detector = self.window.circuit_dict[circuit_number].detector_dict[detector_number]

        # Create an invisible rectangle at the position of the click that the context menu points to
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1

        # Show the popover menu
        detector.context_menu_popover.set_pointing_to(rect)
        detector.context_menu_popover.popup()

    def on_detector_left_pressed(self, gesture, n_press, *args, circuit_number: int, detector_number: int) -> None:
        """Shortcuts for activating actions without the context menu"""
        modifier_state = gesture.get_current_event_state()

        if modifier_state == Gdk.ModifierType.CONTROL_MASK:
            enable_action = self.detector_action_group.lookup_action(f"enable_detector_{circuit_number}_{detector_number}")
            enable_action.activate()

        if modifier_state == Gdk.ModifierType.SHIFT_MASK:
            history_action = self.detector_action_group.lookup_action(f"in_history_{circuit_number}_{detector_number}")
            history_action.activate()

        if modifier_state == Gdk.ModifierType.ALT_MASK:
            # Activating this action only works if edit mode is active
            edit_action = self.edit_action_group.lookup_action("edit_detector")
            edit_action.activate(GLib.Variant.new_string(f"{circuit_number}, {detector_number}"))

    def toggle_edit_mode(self, action, *args) -> None:
        """Toggle between normal mode and edit mode."""
        # Update the action’s stored state
        current_state = action.get_state().get_boolean()
        new_state = not current_state
        action.set_state(GLib.Variant.new_boolean(new_state))

        # Update UI
        for name in self.edit_action_group.list_actions():
            action = self.edit_action_group.lookup_action(name)
            if isinstance(action, Gio.SimpleAction):
                action.set_enabled(new_state)

        self.window.edit_menubutton.set_visible(new_state)

        # Print debug info
        if new_state:
            print("Edit mode active")

        else:
            print("Edit mode inactive")

    def on_save_clicked(self, action, *args):
        """Show a dialog to enter a commit message."""
        action_name = action.get_name()
        if action_name == "save_building":
            self.window.show_commit_message_window(self.on_commit_message_defined, "building")
        elif action_name == "save_scenario":
            self.window.show_commit_message_window(self.on_commit_message_defined, "scenario")

    def on_commit_message_defined(self, message, file_type):
        """Create a FileSaveDialog to save the building configuration."""
        file_path = self.last_file.get_path().split(".")[0]
        last_name = file_path.split("/")[-1]
        last_dir = self.last_file.get_parent()
        self.window.show_save_dialog(self.on_file_save_response, message, file_type, last_dir, last_name)

    def on_file_save_response(self, dialog, result, message: str, file_type: str):
        try:
            file = FileOperations.retrieve_save_file(dialog, result)

        except GLib.Error as e:
            print(f"Save canceled or failed: {e.message}")
            if not e.message == "Dismissed by user":
                self.window.show_error_alert("Speichern fehlgeschlagen", e.message)
            return

        if file_type == "building":
            save_dict = FileOperations.create_building_save_dict(self.model)

        elif file_type == "scenario":
            start = self.window.scenario_buffer.get_start_iter()
            end = self.window.scenario_buffer.get_end_iter()
            scenario_description = self.window.scenario_buffer.get_text(start, end)
            save_dict = FileOperations.create_scenario_save_dict(self.model, scenario_description)

        else:
            self.window.show_error_alert("Invalide Dateiendung", "Dateien müssen auf .building oder .scenario enden")
            return

        self.last_file = file
        FileOperations.save_to_file(file, save_dict, message)

    def on_open_clicked(self, *args):
        """Creates a FileOpenDialog."""
        last_dir = self.last_file.get_parent()
        self.window.show_open_dialog(self.on_file_open_response, last_dir)

    def on_file_open_response(self, dialog, result):
        """Callback for the file dialog. Retrieves the file object and calls the load function."""
        try:
            file = FileOperations.retrieve_open_file(dialog, result)
        except GLib.Error as e:
            print(f"Open canceled or failed: {e.message}")
            if not e.message == "Dismissed by user":
                self.window.show_error_alert("Öffnen fehlgeschlagen", e.message)
            return
        self.last_file = file
        self.load_file(file)

    def load_file(self, file):
        try:
            load_dict, file_type = FileOperations.open_file(file)

        except JSONDecodeError:
            self.window.show_error_alert("Fehler beim Laden der Datei",
                                         f"Invalides Dateiformat von {file.get_path()}\nStellen Sie sicher, "
                                         f"dass die Datei dem JSON-Standard entspricht.")
            return True

        except RuntimeError as e:
            self.window.show_error_alert("Fehler beim Laden der Datei", e)
            return True

        if file_type == "building":
            try:
                self.delete_all()
                FileOperations.load_building_config(self.model, load_dict, self.circuit_ops.add, self.detector_ops.add)
                self.print_detector_state()
                self.lcd.reset()
                self.update_leds()
                self.clear_undo()
                self.clear_redo()
                self.is_reset = False

            except KeyError as e:
                print(f"KeyError: {e}")
                self.window.show_error_alert(".building-Datei invalide", f"Key {e} fehlt oder ist falsch geschrieben.")
                self.model.clear_data()
                return True

            except (ValueError, TypeError) as e:
                print(f"ValueError/TypeError: {e}")
                self.window.show_error_alert(".building-Datei invalide", e)
                self.model.clear_data()
                return True

        else:
            try:
                FileOperations.get_scenario_directory(file, load_dict, self.load_scenario_callback)

            except GLib.Error as error:
                print(f"Error listing directory: {error.message}")
                self.window.show_error_alert(f"Öffnen fehlgeschlagen", error.message)
                return True

    def load_scenario_callback(self, building_file, scenario_load_dict):
        building_error = self.load_file(building_file)
        if building_error:
            return

        try:
            FileOperations.apply_scenario(scenario_load_dict,
                                          self.window.circuit_dict,
                                          self.detector_action_group,
                                          self.model,
                                          self.window.scenario_buffer)
            self.clear_redo()
            self.clear_undo()

        except TypeError as e:
            self.window.show_error_alert("scenario-Datei invalide", f"TypeError: {e}")
            return

        except KeyError as e:
            self.window.show_error_alert(".scenario-Datei invalide", f"KeyError: {e}")
            return

        except SyntaxError as e:
            self.window.show_error_alert(".scenario-Datei invalide", f"SyntaxError: {e}")
            return

        except ValueError as e:
            self.window.show_error_alert(".scenario-Datei invalide", f"ValueError: {e}")
            return

        self.print_detector_state()
        self.lcd.reset()
        for detector in self.model.get_active_detectors():
            self.lcd.add_alarm(detector)
        self.update_leds()

    def on_rollback_clicked(self, *args):
        """Present a list of all commits for the current directory."""
        directory = self.last_file.get_parent().get_path()
        commit_list = FileOperations.get_commits_for_dir(directory)

        # Display an error if the directory is not a repository
        if commit_list is None:
            self.window.show_error_alert("Dateifehler",
                                         "Öffnen Sie eine Datei aus dem Ordner, den Sie zurücksetzen wollen")
            return

        self.window.show_commit_list(directory, commit_list, FileOperations.rollback)

    def on_edit_fbf_clicked(self, *args):
        self.window.show_fbf_window(self.model, self.update_leds)

    def on_detector_switch_toggled(self, action, parameter, circuit_number: int, detector_number: int):
        """Callback function for detector_switch. Set the alarm_status of the detector according to the position of
        the switch"""
        # Toggle alarm status
        action.set_state(parameter)
        alarm_status = parameter.get_boolean()
        self.detector_ops.set_alarm_status(circuit_number, detector_number, alarm_status)

    def on_enable_detector_clicked(self, action, parameter):
        """Toggle the enabled state of the detector switch"""
        action.set_state(parameter)
        enabled = not parameter.get_boolean()
        _, _, circuit_string, detector_string = action.get_name().split("_")
        circuit_number = int(circuit_string)
        detector_number = int(detector_string)
        self.detector_ops.set_enabled(circuit_number, detector_number, enabled)

    def on_detector_in_history_clicked(self, action, parameter):
        """Toggle the history state of the detector"""
        action.set_state(parameter)
        in_history = parameter.get_boolean()
        _, _, circuit_string, detector_string = action.get_name().split("_")
        circuit_number = int(circuit_string)
        detector_number = int(detector_string)
        self.detector_ops.set_in_history(circuit_number, detector_number, in_history)

    def on_edit_mode_clicked(self, action, *args):
        self.toggle_edit_mode(action, *args)

    def on_add_circuit_clicked(self, *args):
        """Create a DefineCircuitWindow."""
        self.window.show_define_circuit_window(self.circuit_ops.add)

    def on_add_detector_clicked(self, action, parameter, *args):
        """Creates a DefineDetectorWindow."""
        # Convert the action parameter to int
        circuit_number = parameter.get_int32()
        self.window.show_define_detector_window(circuit_number, self.detector_ops.add)

    def on_edit_detector_clicked(self, action, parameter, *args):
        """Create an EditDetectorWindow."""
        # Convert parameters to int
        parameter_string = parameter.get_string()
        parameter_list = parameter_string.split(", ")
        circuit_number = int(parameter_list[0])
        detector_number = int(parameter_list[1])
        current_description = self.model.get_detector_description(circuit_number, detector_number)

        self.window.show_edit_detector_window(circuit_number, detector_number, self.detector_ops.edit,
                                              current_description)

    def on_edit_building_clicked(self, *args):
        """Create an EditBuildingWindow."""
        current_description = self.model.get_building_description()
        self.window.show_edit_building_window(self.building_ops.edit, current_description)

    def on_delete_circuit_clicked(self, action, parameter, *args):
        """Convert parameter to int and call the delete_circuit method."""
        circuit_number = parameter.get_int32()
        self.circuit_ops.delete(circuit_number)

    def on_delete_detector_clicked(self, action, parameter, *args):
        """Convert parameters to int and delete the specified detector."""
        parameter_string = parameter.get_string()
        parameter_list = parameter_string.split(", ")
        circuit_number = int(parameter_list[0])
        detector_number = int(parameter_list[1])

        self.detector_ops.delete(circuit_number, detector_number)

    def on_previous_message_clicked(self, *args):
        self.lcd.previous_message()
        self.update_leds()

    def on_next_message_clicked(self, *args):
        self.lcd.next_message()
        self.update_leds()

    def on_view_level_clicked(self, *args):
        self.lcd.toggle_view_level()
        self.update_leds()

    def on_beeper_off_clicked(self):
        """Turns off the beeper until a new alarm is added"""
        self.model.set_beeper_off(True)
        self.update_leds()

    def on_clear_alarms_clicked(self, *args):
        """Schedule alarms to be cleared after a short delay"""
        GLib.timeout_add_seconds(3, self.clear_alarms)

    def clear_alarms(self):
        """Clear all alarms"""
        self.is_reset = True

        # Convert list to tuple to make it immutable for iteration
        active_detectors = tuple(self.model.get_active_detectors())

        for detector_tuple in active_detectors:
            detector = self.window.circuit_dict[detector_tuple[0]].detector_dict[detector_tuple[1]]
            detector.detector_switch.set_active(False)

        self.lcd.reset()
        self.update_leds()

    def on_clear_disabled_clicked(self, *args):
        self.detector_ops.clear_disabled()

    def on_clear_history_clicked(self, *args):
        self.detector_ops.clear_history()

    def on_undo_clicked(self, *args):
        """Pop the top entry of undo_stack and execute it"""
        if len(self.undo_stack) > 0:
            operation_tuple = self.undo_stack.pop(-1)
            if len(operation_tuple) == 2:
                operation_tuple[0](*operation_tuple[1])
            else:
                operation_tuple[0]()

        if len(self.undo_stack) == 0:
            undo_action = self.lookup_action("undo")
            if isinstance(undo_action, Gio.SimpleAction):
                undo_action.set_enabled(False)

    def on_redo_clicked(self, *args):
        """Pop the top entry of redo_stack and execute it"""
        if len(self.redo_stack) > 0:
            operation_tuple = self.redo_stack.pop(-1)
            if len(operation_tuple) == 2:
                operation_tuple[0](*operation_tuple[1])
            else:
                operation_tuple[0]()

        if len(self.redo_stack) == 0:
            redo_action = self.lookup_action("redo")
            if isinstance(redo_action, Gio.SimpleAction):
                redo_action.set_enabled(False)

    def on_help_clicked(self, *args):
        """Open HELP.md in Okular"""
        dir_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        readme_path = dir_path + "/HELP.md"
        subprocess.Popen([MARKDOWN_VIEWER, readme_path],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)

    def on_about_clicked(self, *args):
        """Open the about window"""
        self.window.show_about_window()

    def on_settings_clicked(self, *args):
        """Open the settings window"""
        self.window.show_settings_window(self.model, self.lcd.refresh, self.update_leds, self.print_detector_state)

    def on_acoustic_signals_off_toggled(self, state):
        """Update acoustic_signals_off"""
        self.acoustic_signals_off_switch = state
        self.update_leds()

    def on_ue_off_toggled(self, state):
        """Update ue_off"""
        self.ue_off_switch = state
        self.update_leds()

    def on_fire_controls_off_toggled(self, state):
        """Update fire_controls_off"""
        self.fire_controls_off_switch = state
        self.update_leds()

    def on_UE_test_clicked(self, *args):
        """Test the transmission unit (UE). Currently a placeholder."""
        if not (self.model.get_ue_off() or self.ue_off_switch):
            self.led_fbf.on("ue_triggered")
            GLib.timeout_add_seconds(10, self.update_leds)

    def on_history_pressed(self):
        """Display the history screen"""
        self.lcd.show_history()
        self.update_leds()

    def on_self_test_pressed(self):
        """Turn on all LEDs and all pixels on the LCD"""
        self.lcd.test()
        self.led_fat.test()
        self.led_fbf.test()
        GLib.timeout_add(5000, self.stop_test)

    def stop_test(self):
        self.lcd.reset()
        self.led_fat.shutdown()
        self.led_fbf.shutdown()
        self.update_leds()

    def print_detector_state(self):
        """Print the active and disabled detectors to the console."""
        active_detector_list = self.model.get_active_detectors()
        disabled_detector_list = self.model.get_disabled_detectors()
        history_detector_list = self.model.get_history_detectors()

        active_detector_text = self.generate_text(active_detector_list)
        disabled_detector_text = self.generate_text(disabled_detector_list)
        history_detector_text = f"{self.model.get_history_time_string()}\n\r" + self.generate_text(history_detector_list)

        self.window.active_console.buffer.set_text(active_detector_text)
        self.window.disabled_console.buffer.set_text(disabled_detector_text)
        self.window.history_console.buffer.set_text(history_detector_text)

    def generate_text(self, detector_list: list) -> str:
        detector_text = ""
        for reference in detector_list:
            circuit_number = reference[0]
            detector_number = reference[1]
            detector_description = self.model.get_detector_description(circuit_number, detector_number)
            for i in range(4 - len(str(circuit_number))):
                detector_text += " "
            detector_text += f"{circuit_number}/{detector_number}"
            for i in range(2 - len(str(detector_number))):
                detector_text += " "
            detector_text += f"        {detector_description}\n"

        return detector_text

    def delete_all(self):
        """Removes all circuits and detectors"""
        for circuit_number in self.window.circuit_dict:
            circuit = self.window.circuit_dict[circuit_number]
            self.window.main_box.remove(circuit)
            del circuit

    def update_leds(self):
        """Set the LED states according to the active detectors and contents of the LCD."""
        self.led_fat.on("working")
        self.led_fbf.on("working")

        if len(self.model.get_active_detectors()) > 0:
            self.led_fbf.on("alarm")
            if self.lcd.current_screen == 1:
                self.led_fat.stop_blink("alarm")
                self.led_fat.on("alarm")
                if (not self.model.get_beeper_off()) and self.model.get_beeper_enabled():
                    self.led_fat.on("beeper")
                else:
                    self.led_fat.off("beeper")
            else:
                self.led_fat.start_blink("alarm")

            if FLASH_RELAY_PIN is not None:
                self.flash_relay.on()

            if not (self.model.get_ue_off() or self.ue_off_switch):
                self.led_fbf.on("ue_triggered")

            if self.model.get_extinguisher_triggered():
                self.led_fbf.on("extinguisher_triggered")
            else:
                self.led_fbf.off("extinguisher_triggered")

        else:
            self.led_fat.off("alarm")
            self.led_fat.stop_blink("alarm")
            self.led_fat.off("beeper")
            self.led_fbf.off("alarm")
            if FLASH_RELAY_PIN is not None:
                self.flash_relay.off()

            self.led_fbf.off("ue_triggered")
            self.led_fbf.off("extinguisher_triggered")

        if len(self.model.get_history_detectors()) > 0 and not self.is_reset:
            self.led_fbf.on("alarm")

        if self.lcd.first_message_shown():
            self.led_fat.stop_blink("previous_alarm")
        else:
            self.led_fat.start_blink("previous_alarm")

        if self.lcd.last_message_shown():
            self.led_fat.stop_blink("next_alarm")
        else:
            self.led_fat.start_blink("next_alarm")

        if ((self.model.get_disabled_detectors() and not self.lcd.current_screen == 2)
                or (self.model.get_active_detectors() and not self.lcd.current_screen == 1)):
            self.led_fat.start_blink("view_level")
        else:
            self.led_fat.stop_blink("view_level")

        if self.model.get_disabled_detectors():
            self.led_fat.start_blink("turn_off")
        else:
            self.led_fat.stop_blink("turn_off")

        if self.model.get_ue_off() or self.ue_off_switch:
            self.led_fbf.on("ue_off")
        else:
            self.led_fbf.off("ue_off")

        if self.model.get_acoustic_signals_off() or self.acoustic_signals_off_switch:
            self.led_fbf.on("acoustic_signals_off")
        else:
            self.led_fbf.off("acoustic_signals_off")

        if self.model.get_fire_controls_off() or self.fire_controls_off_switch:
            self.led_fbf.on("fire_controls_off")
        else:
            self.led_fbf.off("fire_controls_off")

