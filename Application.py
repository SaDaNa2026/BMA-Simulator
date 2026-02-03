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


class App(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id="org.example.BMA-control", **kwargs)
        self.connect('activate', self.on_activate)
        self.connect('shutdown', self.on_shutdown)

        self.model = BuildingModel()
        self.lcd = LCDController(self.model)

        # Create a placeholder to memorize opened files
        self.last_file = Gio.File.new_for_path("/home/lfs-bma/git_test1")

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
                               ("edit_mode", None, None, "false", self.on_edit_mode_clicked)]

        edit_action_entries = [("create_circuit", self.on_add_circuit_clicked, None),
                               ("delete_circuit", self.on_delete_circuit_clicked, "i"),
                               ("create_detector", self.on_add_detector_clicked, "i"),
                               ("delete_detector", self.on_delete_detector_clicked, "s"),
                               ("edit_detector", self.on_edit_detector_clicked, "s"),
                               ("edit_building", self.on_edit_building_clicked, None)]

        hidden_action_entries = [("previous_alarm", self.on_previous_alarm_clicked, None),
                                 ("next_alarm", self.on_next_alarm_clicked, None),
                                 ("clear_alarms", self.on_clear_alarms_clicked, None)]

        self.add_action_entries(app_action_entries, None)

        # Add the window's action entries to groups
        self.edit_action_group = Gio.SimpleActionGroup.new()
        self.edit_action_group.add_action_entries(edit_action_entries, None)

        self.hidden_action_group = Gio.SimpleActionGroup()
        self.hidden_action_group.add_action_entries(hidden_action_entries, None)

        # Set edit actions disabled
        for name in self.edit_action_group.list_actions():
            action = self.edit_action_group.lookup_action(name)
            if isinstance(action, Gio.SimpleAction):
                action.set_enabled(False)

        # Add shortcuts to the actions
        self.set_accels_for_action("app.save_building", ["<Ctrl><Shift>S"])
        self.set_accels_for_action("app.save_scenario", ["<Ctrl>S"])
        self.set_accels_for_action("app.open", ["<Ctrl>O"])
        self.set_accels_for_action("app.edit_mode", ["<Ctrl>E"])

        self.fat_led_dict = {"previous_alarm": GPB4,
                             "next_alarm": GPB0,
                             "view_level": GPB6,
                             "beeper_off": GPB2,
                             "working": GPA3,
                             "alarm": GPA2,
                             "error": GPA1,
                             "turn_off": GPA0}

        # Set up the port expander
        self.mcp_fat = MCPController(0x27,
                                     [(GPB1, self.on_next_alarm_clicked),
                                      (GPB3, self.beeper_off),
                                      (GPB5, self.on_previous_alarm_clicked),
                                      (GPB7, self.lcd.switch_view_level)],
                                     self.fat_led_dict)

        self.led_fat = LEDController(self.mcp_fat, self.fat_led_dict)

        # Turn on the green LED
        self.mcp_fat.digital_write(self.fat_led_dict["working"], HIGH)

        self.window = MainWindow(edit_action_group=self.edit_action_group,
                                 hidden_action_group=self.hidden_action_group)

    def on_activate(self, app):
        self.window.set_application(app)
        self.window.present()

    def on_shutdown(self, app):
        """Clean up the hardware interface when the application is closed."""
        self.lcd.clear()
        self.led_fat.shutdown()

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

    def on_detector_pressed(self, gesture, n_press, x, y, circuit_number: int, detector_number: int) -> None:
        """Present a context menu on a detector if edit mode is enabled."""
        # Don't respond if edit mode is disabled
        if not self.get_action_state("edit_mode").get_boolean():
            return

        # Get the detector that was clicked
        detector = self.window.circuit_dict[circuit_number].detector_dict[detector_number]

        # Create an invisible rectangle at the position of the click that the context menu points to
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1

        detector.context_menu_popover.set_pointing_to(rect)
        detector.context_menu_popover.popup()

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

        self.window.add_menubutton.set_visible(new_state)

        # Print debug info
        if new_state:
            print("Edit mode active")

        else:
            print("Edit mode inactive")

    def write_to_console(self, text: str):
        if not isinstance(text, str):
            raise TypeError("Text must be of type string")
        self.window.console_buffer.set_text(text)

    def delete_all(self):
        """Removes all circuits and detectors"""
        for circuit_number in self.window.circuit_dict:
            circuit = self.window.circuit_dict[circuit_number]
            self.window.main_box.remove(circuit)
            del circuit

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
            save_dict = FileOperations.create_scenario_save_dict(self.model)

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
                self.undo_stack.clear()
                self.redo_stack.clear()

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
            FileOperations.apply_scenario(scenario_load_dict, self.window.circuit_dict, self.edit_action_group)

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

    def on_detector_switch_toggled(self, action, parameter, circuit_number: int, detector_number: int):
        """Callback function for detector_switch. Set the alarm_status of the detector according to the position of
        the switch"""
        # Toggle alarm status
        action.set_state(parameter)
        alarm_status = parameter.get_boolean()
        self.model.set_detector_alarm_status(circuit_number, detector_number, alarm_status)

        self.print_detector_state()
        if alarm_status:
            self.lcd.add_alarm((circuit_number, detector_number))
        else:
            self.lcd.reset()

        self.update_leds()

    def on_enable_detector_clicked(self, action, parameter):
        """Toggle the enabled state of the detector switch."""
        action.set_state(parameter)
        enabled = not parameter.get_boolean()
        _, _, circuit_string, detector_string = action.get_name().split("_")
        circuit_number = int(circuit_string)
        detector_number = int(detector_string)
        detector = self.window.circuit_dict[circuit_number].detector_dict[detector_number]

        if not enabled:
            detector.detector_switch.set_active(False)

        detector_switch_action = self.hidden_action_group.lookup_action(f"detector_toggle_{circuit_number}_{detector_number}")
        if isinstance(detector_switch_action, Gio.SimpleAction):
            detector_switch_action.set_enabled(enabled)

        self.model.set_detector_enabled(circuit_number, detector_number, enabled)
        self.print_detector_state()
        self.lcd.reset()
        self.update_leds()


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

    def on_previous_alarm_clicked(self, *args):
        self.lcd.previous_alarm()
        self.update_leds()

    def on_next_alarm_clicked(self, *args):
        self.lcd.next_alarm()
        self.update_leds()

    def on_clear_alarms_clicked(self, *args):
        """Clear all alarms."""
        # Convert list to tuple to make it immutable for iteration
        active_detectors = tuple(self.model.get_active_detectors())

        for detector_tuple in active_detectors:
            detector = self.window.circuit_dict[detector_tuple[0]].detector_dict[detector_tuple[1]]
            detector.detector_switch.set_active(False)

    def print_detector_state(self):
        """Print the active detectors to the console."""
        active_detector_list = self.model.get_active_detectors()
        active_detector_text = ""
        print("Aktive Melder:")

        # Generate active_detector_text
        for reference in active_detector_list:
            circuit_number = reference[0]
            detector_number = reference[1]
            detector_description = self.model.get_detector_description(circuit_number, detector_number)
            for i in range(4 - len(str(circuit_number))):
                active_detector_text += " "
            active_detector_text += f"{circuit_number}/{detector_number}"
            for i in range(2 - len(str(detector_number))):
                active_detector_text += " "
            active_detector_text += f"        {detector_description}\n"

        print(active_detector_text)
        self.write_to_console(active_detector_text)

    def update_leds(self):
        """Set the LED states according to the active detectors and contents of the LCD."""
        if len(self.model.get_active_detectors()) > 0:
            self.led_fat.turn_on("alarm")
        else:
            self.led_fat.turn_off("alarm")

        if self.lcd.first_alarm_shown():
            self.led_fat.stop_blink("previous_alarm")
        else:
            self.led_fat.start_blink("previous_alarm")

        if self.lcd.last_alarm_shown():
            self.led_fat.stop_blink("next_alarm")
        else:
            self.led_fat.start_blink("next_alarm")

        if self.model.get_disabled_detectors():
            self.led_fat.start_blink("view_level")
            self.led_fat.start_blink("turn_off")
        else:
            self.led_fat.stop_blink("view_level")
            self.led_fat.stop_blink("turn_off")

    def beeper_off(self):
        """Turns off the beeper. Currently a placeholder."""
        pass