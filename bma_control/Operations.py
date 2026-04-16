# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Any

import gi

gi.require_version('GLib', '2.0')
from gi.repository import GLib, Gio
from functools import partial
from Detector import Detector
from Circuit import Circuit
from Model import sort_dict_by_key


class Operation:
    def __init__(self, model, app):
        self.model = model
        self.app = app


class DetectorOps(Operation):
    def __init__(self, model, app):
        super().__init__(model, app)
        # Variable to block set_alarm_status so the switch can be flipped without activating the method
        self.block_set_alarm_status = False

    def add(self,
            circuit_number: int,
            detector_number: int,
            description: str,
            alarm_status: bool = False,
            enabled: bool = True,
            in_history: bool = False) -> None:
        self.create_detector(circuit_number,
                             detector_number,
                             description,
                             False,
                             alarm_status,
                             None,
                             enabled,
                             None,
                             in_history,
                             None)

        self.app.clear_redo()
        self.app.append_undo((self.undo_add, (circuit_number, detector_number)))

    def undo_add(self, circuit_number: int, detector_number: int) -> None:
        readd_args = self.remove_detector(circuit_number, detector_number)

        # Update state
        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

        self.app.append_redo((self.redo_add, readd_args))

    def redo_add(self,
                 circuit_number: int,
                 detector_number: int,
                 description: str,
                 switch_active: bool,
                 alarm_status: bool,
                 alarm_index: int | None,
                 enabled: bool,
                 disabled_index: int | None,
                 in_history: bool,
                 history_index: int | None
                 ) -> None:
        self._readd_detector(circuit_number,
                             detector_number,
                             description,
                             switch_active,
                             alarm_status,
                             alarm_index,
                             enabled,
                             disabled_index,
                             in_history,
                             history_index)

        self.app.append_undo((self.undo_add, (circuit_number, detector_number)))

    def delete(self, circuit_number: int, detector_number: int) -> None:
        """Remove a detector from the view and model and keep a reference to it"""
        readd_args = self.remove_detector(circuit_number, detector_number)

        # Update state
        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

        self.app.clear_redo()
        self.app.append_undo((self.undo_delete, readd_args))

    def undo_delete(self,
                    circuit_number: int,
                    detector_number: int,
                    description: str,
                    switch_active: bool,
                    alarm_status: bool,
                    alarm_index: int | None,
                    enabled: bool,
                    disabled_index: int | None,
                    in_history: bool,
                    history_index: int | None
                    ) -> None:
        self._readd_detector(circuit_number,
                             detector_number,
                             description,
                             switch_active,
                             alarm_status,
                             alarm_index,
                             enabled,
                             disabled_index,
                             in_history,
                             history_index)
        self.app.append_redo((self.redo_delete, (circuit_number, detector_number)))

    def redo_delete(self, circuit_number: int, detector_number: int) -> None:
        readd_args = self.remove_detector(circuit_number, detector_number)

        # Update state
        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

        self.app.append_undo((self.undo_delete, readd_args))

    def create_detector(self,
                        circuit_number: int,
                        detector_number: int,
                        description: str,
                        switch_active: bool = False,
                        alarm_status: bool = False,
                        alarm_index: int | None = None,
                        enabled: bool = True,
                        enabled_index: int | None = None,
                        in_history: bool = False,
                        history_index: int | None = None
                        ) -> None:
        """Create a new Detector instance and add it to the window."""
        self.model.add_detector(circuit_number, detector_number, description)
        self.model.set_detector_alarm_status(circuit_number, detector_number, alarm_status, alarm_index)
        self.model.set_detector_enabled(circuit_number, detector_number, enabled, enabled_index)
        self.model.set_detector_in_history(circuit_number, detector_number, in_history, history_index)

        circuit = self.app.window.circuit_dict[circuit_number]
        detector = Detector(circuit_number, detector_number, description)

        # Set switch according to parameter
        detector.detector_switch.set_active(switch_active)

        # Create a new stateful action for the detector switch
        switch_action_name = f"detector_toggle_{circuit_number}_{detector_number}"
        switch_action = Gio.SimpleAction.new_stateful(switch_action_name,
                                                      None,
                                                      GLib.Variant.new_boolean(alarm_status))
        switch_action.set_enabled(enabled)
        switch_action.connect("change-state",
                              self.app.on_detector_switch_toggled,
                              circuit_number,
                              detector_number)
        self.app.detector_action_group.add_action(switch_action)

        # Connect the detector switch to its callback function
        detector.detector_switch.set_action_name(f"detector.{switch_action_name}")

        # Create a new stateful action for the enabled state of the detector
        enabled_action_name = f"enable_detector_{circuit_number}_{detector_number}"
        enabled_action = Gio.SimpleAction.new_stateful(enabled_action_name,
                                                       None,
                                                       GLib.Variant.new_boolean(not enabled))
        enabled_action.connect("change-state", self.app.on_enable_detector_clicked)
        self.app.detector_action_group.add_action(enabled_action)

        # Create a new stateful action for the history state of the detector
        history_action_name = f"in_history_{circuit_number}_{detector_number}"
        history_action = Gio.SimpleAction.new_stateful(history_action_name,
                                                       None,
                                                       GLib.Variant.new_boolean(in_history))
        history_action.connect("change-state", self.app.on_detector_in_history_clicked)
        self.app.detector_action_group.add_action(history_action)

        # Connect the click event handlers
        detector.right_click_controller.connect("pressed", partial(self.app.on_detector_right_pressed,
                                                                   circuit_number=circuit_number,
                                                                   detector_number=detector_number))
        detector.left_click_controller.connect("pressed", partial(self.app.on_detector_left_pressed,
                                                                  circuit_number=circuit_number,
                                                                  detector_number=detector_number))

        # Highlight detector if it's in the history
        detector.set_highlight(in_history, description)

        # Get the previous detector to add this one in the correct position (default None => top position)
        previous_detector = None
        # Sort dict to make sure the for loop works as intended
        circuit.detector_dict = sort_dict_by_key(circuit.detector_dict)
        for other_detector_number in circuit.detector_dict:
            if detector_number > other_detector_number:
                previous_detector = circuit.detector_dict[other_detector_number]

        # Add the detector to its circuit
        circuit.detector_dict[detector_number] = detector
        circuit.button_box.insert_child_after(detector, previous_detector)

    def _readd_detector(self,
                        circuit_number: int,
                        detector_number: int,
                        description: str,
                        switch_active: bool,
                        alarm_status: bool,
                        alarm_index: int | None,
                        enabled: bool,
                        disabled_index: int | None,
                        in_history: bool,
                        history_index: int | None) -> None:
        self.create_detector(circuit_number,
                             detector_number,
                             description,
                             switch_active,
                             alarm_status,
                             alarm_index,
                             enabled,
                             disabled_index,
                             in_history,
                             history_index)

        # Update state
        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

    def remove_detector(self, circuit_number: int, detector_number: int) -> tuple[
        int, int, str, bool, bool, int | None, bool, int | None, bool, int | None]:
        # Get the corresponding objects
        circuit = self.app.window.circuit_dict[circuit_number]
        detector = self.app.window.circuit_dict[circuit_number].detector_dict[detector_number]
        description = self.model.get_detector_description(circuit_number, detector_number)
        switch_active = detector.detector_switch.get_state()
        alarm_status = (circuit_number, detector_number) in self.model.active_detector_list
        if alarm_status:
            alarm_index = self.model.active_detector_list.index((circuit_number, detector_number))
        else:
            alarm_index = None
        enabled = self.model.get_detector_enabled(circuit_number, detector_number)
        if not enabled:
            disabled_index = self.model.disabled_detector_list.index((circuit_number, detector_number))
        else:
            disabled_index = None
        in_history = self.model.get_detector_in_history(circuit_number, detector_number)
        if in_history:
            history_index = self.model.history_detector_list.index((circuit_number, detector_number))
        else:
            history_index = None

        # Remove the detector object and the reference to it
        circuit.button_box.remove(detector)
        del self.app.window.circuit_dict[circuit_number].detector_dict[detector_number]
        self.model.delete_detector(circuit_number, detector_number)

        # Remove the detector's actions
        switch_action_name = f"detector_toggle_{circuit_number}_{detector_number}"
        self.app.detector_action_group.remove_action(switch_action_name)
        enable_action_name = f"enable_detector_{circuit_number}_{detector_number}"
        self.app.detector_action_group.remove_action(enable_action_name)
        history_action_name = f"in_history_{circuit_number}_{detector_number}"
        self.app.detector_action_group.remove_action(history_action_name)

        return circuit_number, detector_number, description, switch_active, alarm_status, alarm_index, enabled, disabled_index, in_history, history_index

    def edit(self, circuit_number: int, detector_number: int, description: str) -> None:
        """Change a specified detector's description if it differs from the previous one."""
        previous_description = self.model.get_detector_description(circuit_number, detector_number)
        if description != previous_description:
            self._set_description(circuit_number, detector_number, description)
            self.app.clear_redo()
            self.app.append_undo((self.undo_edit, (circuit_number, detector_number, previous_description)))

    def undo_edit(self, circuit_number: int, detector_number: int, description: str) -> None:
        previous_description = self.model.get_detector_description(circuit_number, detector_number)
        self._set_description(circuit_number, detector_number, description)
        self.app.append_redo((self.redo_edit, (circuit_number, detector_number, previous_description)))

    def redo_edit(self, circuit_number: int, detector_number: int, description: str) -> None:
        previous_description = self.model.get_detector_description(circuit_number, detector_number)
        self._set_description(circuit_number, detector_number, description)
        self.app.append_undo((self.undo_edit, (circuit_number, detector_number, previous_description)))

    def _set_description(self, circuit_number: int, detector_number: int, description: str) -> None:
        self.model.set_detector_description(circuit_number, detector_number, description)
        detector = self.app.window.circuit_dict[circuit_number].detector_dict[detector_number]
        detector.set_highlight(self.model.get_detector_in_history(circuit_number, detector_number), description)
        self.app.print_detector_state()
        self.app.lcd.refresh()

    def set_alarm_status(self, circuit_number: int, detector_number: int, alarm_status: bool) -> None:
        if not self.block_set_alarm_status:
            undo_args = self._active_setter(circuit_number, detector_number, alarm_status, None)

            self.app.clear_redo()
            self.app.append_undo((self.undo_set_alarm_status, undo_args))

    def undo_set_alarm_status(self, circuit_number: int, detector_number: int, alarm_status: bool, alarm_index: int|None) -> None:
        self.block_set_alarm_status = True
        detector = self.app.window.circuit_dict[circuit_number].detector_dict[detector_number]
        detector.detector_switch.set_active(alarm_status)
        redo_args = self._active_setter(circuit_number, detector_number, alarm_status, alarm_index)
        self.block_set_alarm_status = False

        self.app.append_redo((self.redo_set_alarm_status, redo_args))

    def redo_set_alarm_status(self, circuit_number: int, detector_number: int, alarm_status: bool, alarm_index: int|None) -> None:
        self.block_set_alarm_status = True
        detector = self.app.window.circuit_dict[circuit_number].detector_dict[detector_number]
        detector.detector_switch.set_active(alarm_status)
        undo_args = self._active_setter(circuit_number, detector_number, alarm_status, alarm_index)
        self.block_set_alarm_status = False

        self.app.append_undo((self.undo_set_alarm_status, undo_args))

    def _active_setter(self, circuit_number: int, detector_number: int, alarm_status: bool, alarm_index: int|None) -> tuple[int, int, bool, int|None]:
        previous_alarm_status = self.model.get_detector_alarm_status(circuit_number, detector_number)
        if previous_alarm_status:
            previous_alarm_index = self.model.active_detector_list.index((circuit_number, detector_number))
        else:
            previous_alarm_index = None

        self.model.set_detector_alarm_status(circuit_number, detector_number, alarm_status, alarm_index)

        self.app.print_detector_state()
        if alarm_status:
            self.app.lcd.add_alarm((circuit_number, detector_number))
        else:
            self.app.lcd.reset()
        self.app.update_leds()

        return circuit_number, detector_number, previous_alarm_status, previous_alarm_index

    def set_enabled(self, circuit_number: int, detector_number: int, enabled: bool) -> None:
        """Set the enabled status of a detector"""
        previous_disabled_index = self.enable_detector_switch(circuit_number, detector_number,
                                                                                  enabled, None)

        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

        self.app.clear_redo()
        self.app.append_undo(
            (self.undo_set_enabled,
             (circuit_number, detector_number, not enabled, previous_disabled_index)))

    def undo_set_enabled(self,
                         circuit_number: int,
                         detector_number: int,
                         enabled: bool,
                         disabled_index: int|None) -> None:
        previous_disabled_index = self.enable_detector_switch(circuit_number, detector_number,
                                                                                  enabled, disabled_index)

        enable_action = self.app.detector_action_group.lookup_action(
            f"enable_detector_{circuit_number}_{detector_number}"
        )
        enable_action.set_state(GLib.Variant.new_boolean(not enabled))

        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

        self.app.append_redo(
            (self.redo_set_enabled,
             (circuit_number, detector_number, not enabled, previous_disabled_index)))

    def redo_set_enabled(self,
                         circuit_number: int,
                         detector_number: int,
                         enabled: bool,
                         disabled_index: int | None) -> None:
        previous_disabled_index = self.enable_detector_switch(
            circuit_number, detector_number, enabled, disabled_index)

        enable_action = self.app.detector_action_group.lookup_action(
            f"enable_detector_{circuit_number}_{detector_number}"
        )
        enable_action.set_state(GLib.Variant.new_boolean(not enabled))

        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

        self.app.append_undo((self.undo_set_enabled,
                              (circuit_number, detector_number, not enabled, previous_disabled_index)))

    def enable_detector_switch(self, circuit_number: int, detector_number: int, enabled: bool, disabled_index: int|None) -> int | None:
        if not self.model.get_detector_enabled(circuit_number, detector_number):
            previous_disabled_index = self.model.disabled_detector_list.index((circuit_number, detector_number))
        else:
            previous_disabled_index = None

        detector_switch_action = self.app.detector_action_group.lookup_action(
            f"detector_toggle_{circuit_number}_{detector_number}")
        if isinstance(detector_switch_action, Gio.SimpleAction):
            detector_switch_action.set_enabled(enabled)

        self.model.set_detector_enabled(circuit_number, detector_number, enabled, disabled_index)

        return previous_disabled_index

    def clear_disabled(self) -> None:
        # Return if no detectors are disabled
        if len(self.model.get_disabled_detectors()) == 0:
            return

        previous_disabled_detector_list = self._disabled_clearer(False)

        self.app.clear_redo()
        self.app.append_undo((self.undo_clear_disabled, (previous_disabled_detector_list,)))

    def undo_clear_disabled(self, disabled_detector_list: list) -> None:
        for detector_tuple in disabled_detector_list:
            circuit_number = detector_tuple[0]
            detector_number = detector_tuple[1]
            self.enable_detector_switch(circuit_number, detector_number, False, None)

            enable_action = self.app.detector_action_group.lookup_action(
                f"enable_detector_{circuit_number}_{detector_number}"
            )
            enable_action.set_state(GLib.Variant.new_boolean(True))

        self.app.append_redo((self.redo_clear_disabled,))

    def redo_clear_disabled(self) -> None:
        previous_disabled_detector_list = self._disabled_clearer(False)

        self.app.append_undo((self.undo_clear_disabled, (previous_disabled_detector_list,)))

    def _disabled_clearer(self, is_undo: bool) -> list:
        disabled_tuple = tuple(self.model.get_disabled_detectors())
        previous_disabled_detector_list: list = []
        for detector_tuple in disabled_tuple:
            circuit_number = detector_tuple[0]
            detector_number = detector_tuple[1]
            self.enable_detector_switch(circuit_number, detector_number, True, None)
            previous_disabled_detector_list.append((circuit_number, detector_number))

            enable_action = self.app.detector_action_group.lookup_action(
                f"enable_detector_{circuit_number}_{detector_number}"
            )
            enable_action.set_state(GLib.Variant.new_boolean(is_undo))

        # Reverse detector order so undo operates correctly
        previous_disabled_detector_list.reverse()

        self.model.disabled_detector_list.clear()
        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

        return previous_disabled_detector_list

    def set_in_history(self, circuit_number: int, detector_number: int, in_history: bool) -> None:
        previous_in_history, previous_history_index = self.in_history_setter(circuit_number, detector_number, in_history, None)

        self.app.clear_redo()
        self.app.append_undo((self.undo_set_in_history, (circuit_number, detector_number, previous_in_history, previous_history_index)))

    def undo_set_in_history(self, circuit_number: int, detector_number: int, in_history: bool, history_index: int|None) -> None:
        previous_in_history, previous_history_index = self.in_history_setter(circuit_number, detector_number, in_history, history_index)

        in_history_action = self.app.detector_action_group.lookup_action(
            f"in_history_{circuit_number}_{detector_number}"
        )
        in_history_action.set_state(GLib.Variant.new_boolean(in_history))

        self.app.append_redo((self.redo_set_in_history, (circuit_number, detector_number, previous_in_history, previous_history_index)))

    def redo_set_in_history(self, circuit_number: int, detector_number: int, in_history: bool, history_index: int|None) -> None:
        previous_in_history, previous_history_index = self.in_history_setter(circuit_number, detector_number,
                                                                             in_history, history_index)
        in_history_action = self.app.detector_action_group.lookup_action(
            f"in_history_{circuit_number}_{detector_number}"
        )
        in_history_action.set_state(GLib.Variant.new_boolean(in_history))

        self.app.append_undo((self.undo_set_in_history, (circuit_number, detector_number, previous_in_history, previous_history_index)))

    def in_history_setter(self, circuit_number: int, detector_number: int, in_history: bool, history_index: int|None) -> tuple[bool, int|None]:
        previous_in_history = self.model.get_detector_in_history(circuit_number, detector_number)
        if previous_in_history:
            previous_history_index = self.model.history_detector_list.index((circuit_number, detector_number))
        else:
            previous_history_index = None

        self.model.set_detector_in_history(circuit_number, detector_number, in_history, history_index)
        detector = self.app.window.circuit_dict[circuit_number].detector_dict[detector_number]
        detector.set_highlight(in_history, self.model.get_detector_description(circuit_number, detector_number))
        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

        return previous_in_history, previous_history_index

    def clear_history(self):
        # Return if there are no detectors in the history
        if len(self.model.get_history_detectors()) == 0:
            return

        history_tuple: tuple = tuple(detector_tuple for detector_tuple in self.model.get_history_detectors())
        self._history_action_setter(history_tuple, False)

        self.model.history_detector_list.clear()
        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

        self.app.clear_redo()
        self.app.append_undo((self.undo_clear_history, (history_tuple,)))

    def undo_clear_history(self, history_tuple: tuple):
        self.model.history_detector_list = list(history_tuple)
        self._history_action_setter(history_tuple, True)

        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

        self.app.append_redo((self.redo_clear_history,))

    def redo_clear_history(self):
        history_tuple: tuple = tuple(detector_tuple for detector_tuple in self.model.get_history_detectors())
        self._history_action_setter(history_tuple, False)

        self.model.history_detector_list.clear()
        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

        self.app.append_undo((self.undo_clear_history, (history_tuple,)))

    def _history_action_setter(self, history_tuple: tuple, is_undo: bool) -> None:
        for detector_tuple in history_tuple:
            circuit_number = detector_tuple[0]
            detector_number = detector_tuple[1]
            action = self.app.detector_action_group.lookup_action(f"in_history_{circuit_number}_{detector_number}")
            if isinstance(action, Gio.SimpleAction):
                action.set_state(GLib.Variant.new_boolean(is_undo))

            detector = self.app.window.circuit_dict[detector_tuple[0]].detector_dict[detector_tuple[1]]
            detector.set_highlight(is_undo, self.model.get_detector_description(circuit_number, detector_number))


class CircuitOps(Operation):
    def __init__(self, model, app):
        super().__init__(model, app)
        self.detector_ops = DetectorOps(model, app)

    def add(self, circuit_number: int) -> None:
        """Create a new Circuit instance and add it to the window."""
        self._create_circuit(circuit_number)

        self.app.clear_redo()
        self.app.append_undo((self.undo_add, (circuit_number,)))

    def undo_add(self, circuit_number: int) -> None:
        detectors = self._remove_circuit(circuit_number)
        self.app.append_redo((self.redo_add, (circuit_number, detectors)))

    def redo_add(self, circuit_number: int, detectors: Any) -> None:
        self._readd_circuit(circuit_number, detectors)
        self.app.append_undo((self.undo_add, (circuit_number,)))

    def delete(self, circuit_number: int) -> None:
        detectors = self._remove_circuit(circuit_number)
        self.app.clear_redo()
        self.app.append_undo((self.undo_delete, (circuit_number, detectors)))

    def undo_delete(self, circuit_number: int, detectors: list) -> None:
        self._readd_circuit(circuit_number, detectors)
        self.app.append_redo((self.redo_delete, (circuit_number,)))

    def redo_delete(self, circuit_number: int) -> None:
        detectors = self._remove_circuit(circuit_number)
        self.app.append_undo((self.undo_delete, (circuit_number, detectors)))

    def _create_circuit(self, circuit_number: int) -> None:
        if not circuit_number in self.model.circuit_dict:
            self.model.add_circuit(circuit_number)
        circuit = Circuit(circuit_number)
        self.app.window.circuit_dict[circuit_number] = circuit
        # Connect the event handler that detects if the circuit is right-clicked
        circuit.click_controller.connect("pressed", partial(self.app.on_circuit_pressed, circuit_number=circuit_number))
        self.app.window.main_box.append(circuit)

    def _remove_circuit(self, circuit_number: int) -> list:
        circuit = self.app.window.circuit_dict[circuit_number]

        # Remove detectors and save their properties for readding
        detector_list = [detector_number for detector_number in circuit.detector_dict]
        detectors = []
        for detector_number in detector_list:
            detector_props = self.detector_ops.remove_detector(circuit_number, detector_number)
            detectors.append(detector_props)

        # Reverse detectors so they are added correctly
        detectors.reverse()

        if circuit_number in self.model.circuit_dict:
            self.model.delete_circuit(circuit_number)
        self.app.window.main_box.remove(circuit)
        del self.app.window.circuit_dict[circuit_number]

        # Update state
        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

        return detectors

    def _readd_circuit(self, circuit_number: int, detectors: list) -> None:
        self._create_circuit(circuit_number)

        for detector in detectors:
            self.detector_ops.create_detector(*detector)

        # Update state
        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()


class BuildingOps(Operation):
    def edit(self, description: str) -> None:
        """Set the building description if it differs from the previous one."""
        previous_description = self.model.get_building_description()
        if description != previous_description:
            self.model.set_building_description(description)
            self.app.lcd.reset()
            self.app.clear_redo()
            self.app.append_undo((self.undo_edit, (previous_description,)))

    def undo_edit(self, description: str) -> None:
        previous_description = self.model.get_building_description()
        self.model.set_building_description(description)
        self.app.lcd.reset()
        self.app.append_redo((self.redo_edit, (previous_description,)))

    def redo_edit(self, description: str) -> None:
        previous_description = self.model.get_building_description()
        self.model.set_building_description(description)
        self.app.lcd.reset()
        self.app.append_undo((self.undo_edit, (previous_description,)))
