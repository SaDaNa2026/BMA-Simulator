from typing import Any

import gi

gi.require_version('GLib', '2.0')
from gi.repository import GLib, Gio
from functools import partial
from Detector import Detector
from Circuit import Circuit


class Operation:
    def __init__(self, model, app):
        self.model = model
        self.app = app


class DetectorOps(Operation):
    def add(self,
            circuit_number: int,
            detector_number: int,
            description: str,
            alarm_status: bool = False,
            enabled: bool = True,
            in_history: bool = False) -> None:
        """Create a new Detector instance and add it to the window."""
        self.model.add_detector(circuit_number, detector_number, description)
        circuit = self.app.window.circuit_dict[circuit_number]

        detector = Detector(circuit_number, detector_number, description)

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

        # Connect the event handler that detects if the circuit is right-clicked
        detector.click_controller.connect("pressed", partial(self.app.on_detector_pressed,
                                                             circuit_number=circuit_number,
                                                             detector_number=detector_number))

        # Get the previous detector to add this one in the correct position (default None => top position)
        previous_detector = None
        for other_detector_number in self.model.get_detectors_for_circuit(circuit_number):
            if detector_number > other_detector_number:
                previous_detector = circuit.detector_dict[other_detector_number]

        # Add the detector to its circuit
        circuit.detector_dict[detector_number] = detector
        circuit.button_box.insert_child_after(detector, previous_detector)

        self.app.clear_redo()
        self.app.append_undo((self.undo_add, (circuit_number, detector_number)))

    def undo_add(self, circuit_number: int, detector_number: int) -> None:
        readd_args = self.remove_detector(circuit_number, detector_number)

        self.app.append_redo((self.redo_add, readd_args))

    def redo_add(self,
                 circuit_number: int,
                 detector_number: int,
                 description: str,
                 alarm_status: bool,
                 enabled: bool,
                 in_history: bool,
                 detector: Any) -> None:
        self.readd_detector(circuit_number, detector_number, description, alarm_status, enabled, in_history, detector)

        self.app.append_undo((self.undo_add, (circuit_number, detector_number)))

    def delete(self, circuit_number: int, detector_number: int) -> None:
        """Remove a detector from the view and model and keep a reference to it"""
        readd_args = self.remove_detector(circuit_number, detector_number)
        self.app.clear_redo()
        self.app.append_undo((self.undo_delete, readd_args))

    def undo_delete(self,
                    circuit_number: int,
                    detector_number: int,
                    description: str,
                    alarm_status: bool,
                    enabled: bool,
                    in_history: bool,
                    detector: Any) -> None:
        self.readd_detector(circuit_number, detector_number, description, alarm_status, enabled, in_history, detector)
        self.app.append_redo((self.redo_delete, (circuit_number, detector_number)))

    def redo_delete(self, circuit_number: int, detector_number: int) -> None:
        readd_args = self.remove_detector(circuit_number, detector_number)
        self.app.append_undo((self.undo_delete, readd_args))

    def edit(self, circuit_number: int, detector_number: int, description: str) -> None:
        """Change a specified detector's description if it differs from the previous one."""
        previous_description = self.model.get_detector_description(circuit_number, detector_number)
        if description != previous_description:
            self._set_description(circuit_number, detector_number, description)
            self.app.clear_redo()
            self.app.append_undo((self.undo_edit, (circuit_number, detector_number, previous_description)))

    def undo_edit(self, circuit_number: int, detector_number: int, description: str) -> None:
        self._set_description(circuit_number, detector_number, description)
        self.app.append_redo((self.redo_edit, (circuit_number, detector_number, description)))

    def redo_edit(self, circuit_number: int, detector_number: int, description: str) -> None:
        self._set_description(circuit_number, detector_number, description)
        self.app.append_undo((self.undo_edit, (circuit_number, detector_number, description)))

    def set_enabled(self, circuit_number: int, detector_number: int, enabled: bool) -> None:
        """Set the enabled status of a detector"""
        previous_alarm_status = self.model.get_detector_alarm_status(circuit_number, detector_number)

        self.enable_detector_switch(circuit_number, detector_number, enabled)

        self.app.clear_redo()
        self.app.append_undo(
            (self.undo_set_enabled, (circuit_number, detector_number, not enabled, previous_alarm_status)))

    def undo_set_enabled(self, circuit_number: int, detector_number: int, enabled: bool, alarm_status: bool) -> None:
        previous_alarm_status = self.model.get_detector_alarm_status(circuit_number, detector_number)
        self.enable_detector_switch(circuit_number, detector_number, enabled)

        detector = self.app.window.circuit_dict[circuit_number].detector_dict[detector_number]
        if alarm_status:
            detector.detector_switch.set_active(True)

        enable_action = self.app.detector_action_group.lookup_action(
            f"enable_detector_{circuit_number}_{detector_number}"
        )
        enable_action.set_state(GLib.Variant.new_boolean(not enabled))

        self.app.append_redo(
            (self.redo_set_enabled, (circuit_number, detector_number, not enabled, previous_alarm_status)))

    def redo_set_enabled(self, circuit_number: int, detector_number: int, enabled: bool, alarm_status: bool) -> None:
        previous_alarm_status = self.model.get_detector_alarm_status(circuit_number, detector_number)
        self.enable_detector_switch(circuit_number, detector_number, enabled)

        detector = self.app.window.circuit_dict[circuit_number].detector_dict[detector_number]
        if alarm_status:
            detector.detector_switch.set_active(True)

        enable_action = self.app.detector_action_group.lookup_action(
            f"enable_detector_{circuit_number}_{detector_number}"
        )
        enable_action.set_state(GLib.Variant.new_boolean(not enabled))

        self.app.append_undo(
            (self.undo_set_enabled, (circuit_number, detector_number, not enabled, previous_alarm_status)))

    def set_in_history(self, circuit_number: int, detector_number: int, in_history: bool) -> None:
        previous_in_history = self.model.get_detector_in_history(circuit_number, detector_number)
        self.in_history_setter(circuit_number, detector_number, in_history)
        self.app.append_undo((self.undo_set_in_history, (circuit_number, detector_number, previous_in_history)))

    def undo_set_in_history(self, circuit_number: int, detector_number: int, in_history: bool) -> None:
        previous_in_history = self.model.get_detector_in_history(circuit_number, detector_number)

        in_history_action = self.app.detector_action_group.lookup_action(
            f"in_history_{circuit_number}_{detector_number}"
        )
        in_history_action.set_state(GLib.Variant.new_boolean(in_history))

        self.in_history_setter(circuit_number, detector_number, in_history)
        self.app.append_redo((self.redo_set_in_history, (circuit_number, detector_number, previous_in_history)))

    def redo_set_in_history(self, circuit_number: int, detector_number: int, in_history: bool) -> None:
        previous_in_history = self.model.get_detector_in_history(circuit_number, detector_number)

        in_history_action = self.app.detector_action_group.lookup_action(
            f"in_history_{circuit_number}_{detector_number}"
        )
        in_history_action.set_state(GLib.Variant.new_boolean(in_history))

        self.in_history_setter(circuit_number, detector_number, in_history)
        self.app.append_undo((self.undo_set_in_history, (circuit_number, detector_number, previous_in_history)))

    def enable_detector_switch(self, circuit_number: int, detector_number: int, enabled: bool) -> None:
        detector = self.app.window.circuit_dict[circuit_number].detector_dict[detector_number]
        if not enabled:
            detector.detector_switch.set_active(False)

        detector_switch_action = self.app.detector_action_group.lookup_action(
            f"detector_toggle_{circuit_number}_{detector_number}")
        if isinstance(detector_switch_action, Gio.SimpleAction):
            detector_switch_action.set_enabled(enabled)

        self.model.set_detector_enabled(circuit_number, detector_number, enabled)
        print(self.model.get_disabled_detectors())
        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

    def _set_description(self, circuit_number: int, detector_number: int, description: str) -> None:
        self.model.set_detector_description(circuit_number, detector_number, description)
        detector = self.app.window.circuit_dict[circuit_number].detector_dict[detector_number]
        detector.detector_label.set_label(f"{detector_number}: {description}")
        self.app.print_detector_state()
        self.app.lcd.refresh()

    def in_history_setter(self, circuit_number: int, detector_number: int, in_history: bool) -> None:
        self.model.set_detector_in_history(circuit_number, detector_number, in_history)
        self.app.print_detector_state()
        self.app.lcd.reset()

    def readd_detector(self,
                       circuit_number: int,
                       detector_number: int,
                       description: str,
                       alarm_status: bool,
                       enabled: bool,
                       in_history: bool,
                       detector: Any) -> None:
        circuit = self.app.window.circuit_dict[circuit_number]

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

        # Get the previous detector to add this one in the correct position (default None => top position)
        previous_detector = None
        for other_detector_number in self.model.get_detectors_for_circuit(circuit_number):
            if detector_number > other_detector_number:
                previous_detector = circuit.detector_dict[other_detector_number]

        # Add the detector object and the reference to it
        circuit.detector_dict[detector_number] = detector
        self.model.add_detector(circuit_number, detector_number, description)
        self.model.set_detector_alarm_status(circuit_number, detector_number, alarm_status)
        self.model.set_detector_enabled(circuit_number, detector_number, enabled)
        circuit.button_box.insert_child_after(detector, previous_detector)

        # Update state
        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

    def remove_detector(self, circuit_number: int, detector_number: int) -> tuple[str, bool, bool, bool, Any]:
        # Get the corresponding objects
        circuit = self.app.window.circuit_dict[circuit_number]
        detector = self.app.window.circuit_dict[circuit_number].detector_dict[detector_number]
        description = self.model.get_detector_description(circuit_number, detector_number)
        alarm_status = self.model.get_detector_alarm_status(circuit_number, detector_number)
        enabled = self.model.get_detector_enabled(circuit_number, detector_number)
        in_history = self.model.get_detector_in_history(circuit_number, detector_number)

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

        # Update state
        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

        return description, alarm_status, enabled, in_history, detector


class CircuitOps(Operation):
    def __init__(self, model, app):
        super().__init__(model, app)
        self.detector_ops = DetectorOps(model, app)

    def add(self, circuit_number: int) -> None:
        """Create a new Circuit instance and add it to the window."""
        self.model.add_circuit(circuit_number)

        circuit = Circuit(circuit_number)
        self.app.window.circuit_dict[circuit_number] = circuit
        # Connect the event handler that detects if the circuit is right-clicked
        circuit.click_controller.connect("pressed", partial(self.app.on_circuit_pressed, circuit_number=circuit_number))
        self.app.window.main_box.append(circuit)

        self.app.clear_redo()
        self.app.append_undo((self.undo_add, (circuit_number,)))

    def undo_add(self, circuit_number: int) -> None:
        circuit, detectors = self._remove_circuit(circuit_number)
        self.app.append_redo((self.redo_add, (circuit_number, circuit, detectors)))

    def redo_add(self, circuit_number: int, circuit: Any, detectors: Any) -> None:
        self._readd_circuit(circuit_number, circuit, detectors)
        self.app.append_undo((self.undo_add, (circuit_number,)))

    def delete(self, circuit_number: int) -> None:
        circuit, detectors = self._remove_circuit(circuit_number)
        self.app.clear_redo()
        self.app.append_undo((self.undo_delete, (circuit_number, circuit, detectors)))

    def undo_delete(self, circuit_number: int, circuit: Any, detectors: list) -> None:
        self._readd_circuit(circuit_number, circuit, detectors)
        self.app.append_redo((self.redo_delete, (circuit_number,)))

    def redo_delete(self, circuit_number: int) -> None:
        circuit, detectors = self._remove_circuit(circuit_number)
        self.app.append_undo((self.undo_delete, (circuit_number, circuit, detectors)))

    def _remove_circuit(self, circuit_number: int) -> tuple[Any, list]:
        circuit = self.app.window.circuit_dict[circuit_number]

        detector_list = [detector_number for detector_number in circuit.detector_dict]
        detectors = []
        for detector_number in detector_list:
            detector_props = [circuit_number, detector_number]
            for value in self.detector_ops.remove_detector(circuit_number, detector_number):
                detector_props.append(value)
            detectors.append(detector_props)

        self.model.delete_circuit(circuit_number)
        self.app.window.main_box.remove(circuit)
        del self.app.window.circuit_dict[circuit_number]

        return circuit, detectors

    def _readd_circuit(self, circuit_number: int, circuit: Any, detectors: list) -> None:
        self.model.add_circuit(circuit_number)
        self.app.window.circuit_dict[circuit_number] = circuit
        self.app.window.main_box.append(circuit)

        for detector in detectors:
            self.detector_ops.readd_detector(*detector)


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
