import gi

gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk, Gio, GLib, Gdk

from functools import partial
from json import JSONDecodeError

from Model import BuildingModel
from FileOperations import FileOperations
from MainWindow import MainWindow
from Circuit import Circuit
from Detector import Detector
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

        # Actions for all buttons to connect to
        app_action_entries = [("save_building", self.on_save_building_clicked, None),
                               ("save_scenario", self.on_save_scenario_clicked, None),
                               ("open", self.on_open_clicked, None),
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
                             "switch_view_level": GPB6,
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

    def add_circuit(self, circuit_number: int) -> None:
        """Create a new Circuit instance and add it to the window."""
        circuit = Circuit(circuit_number)
        self.window.circuit_dict[circuit_number] = circuit
        # Connect the event handler that detects if the circuit is right-clicked
        circuit.click_controller.connect("pressed", partial(self.on_circuit_pressed, circuit_number=circuit_number))
        self.window.main_box.append(circuit)

    def delete_circuit(self, circuit_number: int) -> None:
        """Delete the specified circuit."""
        circuit = self.window.circuit_dict[circuit_number]
        self.window.main_box.remove(circuit)
        del self.window.circuit_dict[circuit_number]

    def add_detector(self, circuit_number: int, detector_number: int, description: str, alarm_status: bool = False, enabled: bool = True) -> None:
        """Create a new Detector instance and add it to the window."""
        detector = Detector(circuit_number, detector_number, description)

        # Create a new stateful action for the detector switch
        switch_action_name = f"detector_toggle_{circuit_number}_{detector_number}"
        switch_action = Gio.SimpleAction.new_stateful(switch_action_name,
                                                      None,
                                                      GLib.Variant.new_boolean(alarm_status))
        switch_action.set_enabled(enabled)
        switch_action.connect("change-state",
                              self.on_detector_switch_toggled,
                              circuit_number,
                              detector_number)
        self.hidden_action_group.add_action(switch_action)

        # Set the detector switch according to the alarm_status and connect it to its callback function
        detector.detector_switch.set_action_name(f"hidden_actions.{switch_action_name}")

        # Create a new stateful action for the enabled state of the detector
        enabled_action_name = f"enable_detector_{circuit_number}_{detector_number}"
        enabled_action = Gio.SimpleAction.new_stateful(enabled_action_name,
                                                       None,
                                                       GLib.Variant.new_boolean(not enabled))
        enabled_action.set_enabled(self.get_action_state("edit_mode").get_boolean())
        enabled_action.connect("change-state",
                               self.on_enable_detector_clicked,
                               circuit_number,
                               detector_number)
        self.edit_action_group.add_action(enabled_action)

        # Connect the event handler that detects if the circuit is right-clicked
        detector.click_controller.connect("pressed", partial(self.on_detector_pressed,
                                                             circuit_number=circuit_number,
                                                             detector_number=detector_number))

        # Add the detector to its circuit
        circuit = self.window.circuit_dict[circuit_number]
        circuit.detector_dict[detector_number] = detector
        circuit.main_box.append(detector)

    def delete_detector(self, circuit_number: int, detector_number: int) -> None:
        """Delete a specified detector."""
        # Get the corresponding objects
        circuit = self.window.circuit_dict[circuit_number]
        detector = self.window.circuit_dict[circuit_number].detector_dict[detector_number]

        # Remove the detector's actions
        switch_action_name = f"detector_toggle_{circuit_number}_{detector_number}"
        self.hidden_action_group.remove_action(switch_action_name)
        enable_action_name = f"enable_detector_{circuit_number}_{detector_number}"
        self.edit_action_group.remove_action(enable_action_name)

        # Remove the detector object and the reference to it
        circuit.main_box.remove(detector)
        del self.window.circuit_dict[circuit_number].detector_dict[detector_number]

    def write_to_console(self, text: str):
        if not isinstance(text, str):
            raise TypeError("Text must be of type string")
        self.window.console_buffer.set_text(text)

    def clear_view(self):
        delete_list = [num for num in self.window.circuit_dict]
        for circuit_number in delete_list:
            self.delete_circuit(circuit_number)
        self.update_view()

    def update_view(self):
        """Update the GUI according to the model."""
        circuit_list = [key for key in self.window.circuit_dict.keys()]
        for circuit_number in circuit_list:
            circuit = self.window.circuit_dict[circuit_number]
            if circuit_number not in self.model.get_circuits():
                self.delete_circuit(circuit_number)
            else:
                detector_list = [key for key in circuit.detector_dict.keys()]
                for detector_number in detector_list:
                    self.delete_detector(circuit_number, detector_number)

        for circuit_number in self.model.get_circuits():
            if circuit_number not in self.window.circuit_dict:
                self.add_circuit(circuit_number)
            for detector_number in self.model.get_detectors_for_circuit(circuit_number):
                description = self.model.get_detector_description(circuit_number, detector_number)
                alarm_status = self.model.get_detector_alarm_status(circuit_number, detector_number)
                enabled = self.model.get_detector_enabled(circuit_number, detector_number)
                self.add_detector(circuit_number, detector_number, description, alarm_status, enabled)

    def on_save_building_clicked(self, *args):
        """Create a FileSaveDialog to save the building configuration."""
        self.window.show_save_dialog(self.on_file_save_response, "building")

    def on_save_scenario_clicked(self, *args):
        """Create a FileSaveDialog to save the scenario."""
        self.window.show_save_dialog(self.on_file_save_response, "scenario")

    def on_file_save_response(self, dialog, result, file_type: str):
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

        FileOperations.save_to_file(file, save_dict)

    def on_open_clicked(self, *args):
        """Creates a FileOpenDialog."""
        self.window.show_open_dialog(self.on_file_open_response)

    def on_file_open_response(self, dialog, result):
        """Callback for the file dialog. Retrieves the file object and calls the load function."""
        try:
            file = FileOperations.retrieve_open_file(dialog, result)
        except GLib.Error as e:
            print(f"Open canceled or failed: {e.message}")
            if not e.message == "Dismissed by user":
                self.window.show_error_alert("Öffnen fehlgeschlagen", e.message)
            return
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
                FileOperations.load_building_config(self.model, load_dict)
                self.update_view()
                self.print_detector_state()
                self.update_leds()

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
            FileOperations.apply_scenario(scenario_load_dict, self.model)

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

        self.update_view()
        self.print_detector_state()
        for detector in self.model.get_active_detectors():
            self.lcd.add_alarm(detector)
        self.update_leds()

    def on_detector_switch_toggled(self, action, parameter, circuit_number: int, detector_number: int):
        """Callback function for detector_switch. Set the alarm_status of the detector according to the position of
        the switch and print debugging info."""
        # Toggle alarm status
        action.set_state(parameter)
        alarm_status = parameter.get_boolean()
        self.model.set_detector_alarm_status(circuit_number, detector_number, alarm_status)

        print(f"Melder {detector_number} in Melderlinie {circuit_number} {'aktiviert' if alarm_status else 'deaktiviert'}")
        self.print_detector_state()
        if alarm_status:
            self.lcd.add_alarm((circuit_number, detector_number))
        else:
            self.lcd.reset()

        self.update_leds()

    def on_enable_detector_clicked(self, action, parameter, circuit_number: int, detector_number: int):
        """Toggle the enabled state of the detector switch."""
        action.set_state(parameter)
        enabled = not parameter.get_boolean()
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
        self.window.show_define_circuit_window(self.add_circuit_callback)

    def on_add_detector_clicked(self, action, parameter, *args):
        """Creates a DefineDetectorWindow."""
        # Convert the action parameter to int
        circuit_number = parameter.get_int32()
        self.window.show_define_detector_window(circuit_number, self.add_detector_callback)

    def on_edit_detector_clicked(self, action, parameter, *args):
        """Create an EditDetectorWindow."""
        # Convert parameters to int
        parameter_string = parameter.get_string()
        parameter_list = parameter_string.split(", ")
        circuit_number = int(parameter_list[0])
        detector_number = int(parameter_list[1])
        current_description = self.model.get_detector_description(circuit_number, detector_number)

        self.window.show_edit_detector_window(circuit_number, detector_number, self.edit_detector_callback,
                                              current_description)

    def on_edit_building_clicked(self, *args):
        """Create an EditBuildingWindow."""
        current_description = self.model.get_building_description()
        self.window.show_edit_building_window(self.edit_building_callback, current_description)

    def on_delete_circuit_clicked(self, action, parameter, *args):
        """Convert parameter to int and call the delete_circuit method."""
        circuit_number = parameter.get_int32()
        self.model.delete_circuit(circuit_number)
        self.delete_circuit(circuit_number)
        self.print_detector_state()
        self.lcd.reset()
        self.update_leds()

    def on_delete_detector_clicked(self, action, parameter, *args):
        """Convert parameters to int and delete the specified detector."""
        parameter_string = parameter.get_string()
        parameter_list = parameter_string.split(", ")
        circuit_number = int(parameter_list[0])
        detector_number = int(parameter_list[1])

        self.model.delete_detector(circuit_number, detector_number)
        self.delete_detector(circuit_number, detector_number)
        self.print_detector_state()
        self.lcd.reset()
        self.update_leds()

    def on_previous_alarm_clicked(self, *args):
        self.lcd.previous_alarm()
        self.update_leds()

    def on_next_alarm_clicked(self, *args):
        self.lcd.next_alarm()
        self.update_leds()

    def on_clear_alarms_clicked(self, *args):
        """Clear all alarms."""
        self.model.clear_alarms()
        self.lcd.clear_alarms()
        self.update_view()
        self.print_detector_state()
        self.led_fat.shutdown()
        self.led_fat.turn_on("working")

    def add_circuit_callback(self, circuit_number):
        self.model.add_circuit(circuit_number)
        self.add_circuit(circuit_number)

    def add_detector_callback(self, circuit_number, detector_number, detector_description):
        self.model.add_detector(circuit_number, detector_number, detector_description)
        self.add_detector(circuit_number, detector_number, detector_description)

    def edit_building_callback(self, description: str):
        """Change the building description."""
        self.model.set_building_description(description)

    def edit_detector_callback(self, circuit_number: int, detector_number: int, description: str):
        """Change a specified detector's description."""
        self.model.set_detector_description(circuit_number, detector_number, description)
        detector = self.window.circuit_dict[circuit_number].detector_dict[detector_number]
        detector.detector_label.set_label(f"{detector_number}: {description}")
        self.print_detector_state()
        self.lcd.refresh()
        self.update_leds()

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

    def beeper_off(self):
        """Turns off the beeper. Currently a placeholder."""
        pass