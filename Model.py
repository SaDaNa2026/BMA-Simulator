from dataclasses import dataclass, field
from typing import Dict, List

def sort_dict_by_key(input_dict: dict) -> dict:
    if not type(input_dict) == dict:
        raise TypeError("input_dict must be dict")
    sorted_keys = sorted(input_dict.keys())
    output_dict = {key : input_dict[key] for key in sorted_keys}
    return output_dict


@dataclass
class Detector:
    description: str = field(default="")

    def set_description(self, description: str) -> None:
        if not isinstance(description, str):
            raise TypeError("detector_description must be a string")
        if len(description) > 20:
            raise ValueError("detector_description must be a maximum of 20 characters")
        if f"\n" in description:
            raise ValueError("No newlines allowed in a detector description")
        self.description = description


@dataclass
class Circuit:
    """Represents a circuit with its detectors."""
    detector_dict: Dict[int, Detector] = field(default_factory=dict)

    def add_detector(self, detector_number: int, detector_description: str) -> None:
        """Add a detector to this circuit."""
        if not isinstance(detector_number, int):
            raise TypeError("detector_number must be int")
        if not isinstance(detector_description, str):
            raise TypeError("detector_description must be a string")
        if detector_number < 1 or detector_number >= 100:
            raise ValueError("Die Meldernummer muss zwischen 1 und 99 liegen.")
        if detector_number in self.detector_dict:
            raise ValueError("Dieser Melder existiert bereits.")
        if len(detector_description) > 20:
            raise ValueError("Die Beschreibung darf höchstens 20 Zeichen lang sein.")
        if f"\n" in detector_description:
            raise ValueError("No newlines allowed in a detector description")

        self.detector_dict[detector_number] = Detector(detector_description)
        self.detector_dict = sort_dict_by_key(self.detector_dict)

    def delete_detector(self, detector_number: int) -> None:
        """Remove a detector by index."""
        del self.detector_dict[detector_number]


@dataclass
class BuildingModel:
    building_description: str = field(default="BMA-Simulator")
    circuit_dict: Dict[int, Circuit] = field(default_factory=dict)
    active_detector_list: List[tuple] = field(default_factory=list)
    disabled_detector_list: List[tuple] = field(default_factory=list)
    history_detector_list: List[tuple] = field(default_factory=list)
    extinguisher_triggered: bool = field(default=False)
    acoustic_signals_off: bool = field(default=False)
    ue_off: bool = field(default=False)
    fire_controls_off: bool = field(default=False)

    def __post_init__(self):
        if not isinstance(self.building_description, str):
            raise TypeError("building_description must be a string")
        if self.circuit_dict != {}:
            raise ValueError("circuit_dict must be empty upon initialization. Add circuits later via add_circuit.")
        if self.active_detector_list:
            raise ValueError("active_detector_list must be empty upon initialization. Activate detectors later using "
                             "set_detector_alarm_status.")
        if self.history_detector_list:
            raise ValueError("history_detector_list must be empty upon initialization. Add detectors to history later using "
                             "set_detector_in_history.")

    def clear_data(self):
        """Resets to init values."""
        self.set_building_description("Gebäudebeschreibung")
        self.circuit_dict.clear()
        self.active_detector_list.clear()
        self.disabled_detector_list.clear()
        self.extinguisher_triggered = False
        self.acoustic_signals_off = False
        self.ue_off = False
        self.fire_controls_off = False

    def set_building_description(self, description: str) -> None:
        if not isinstance(description, str):
            raise TypeError("building_description must be a string")
        if len(description) > 20:
            raise ValueError("building_description must be a maximum of 20 characters")
        self.building_description = description

    def get_building_description(self) -> str:
        return self.building_description

    def add_circuit(self, circuit_number: int):
        """Add a specific circuit."""
        if not isinstance(circuit_number, int):
            raise TypeError("circuit_number must be int")

        if circuit_number < 1 or circuit_number >= 100000:
            raise ValueError("Die Meldergruppen-Nummer muss zwischen 1 und 99999 liegen.")
        if circuit_number in self.circuit_dict:
            raise ValueError("Diese Meldergruppe existiert bereits.")

        self.circuit_dict[circuit_number] = Circuit()
        self.circuit_dict = sort_dict_by_key(self.circuit_dict)

    def delete_circuit(self, circuit_number: int):
        """Delete a specific circuit and all detectors in it."""
        if not isinstance(circuit_number, int):
            raise TypeError("circuit_number must be int")

        delete_list = [num for num in self.circuit_dict[circuit_number].detector_dict]
        for detector_number in delete_list:
            self.delete_detector(circuit_number, detector_number)
        del self.circuit_dict[circuit_number]

    def get_circuits(self) -> list[int]:
        """Returns a list containing the numbers of all existing circuits."""
        circuit_number_list = []
        for circuit_number in self.circuit_dict:
            circuit_number_list.append(circuit_number)
        return circuit_number_list

    def add_detector(self, circuit_number: int, detector_number: int, description: str = "") -> None:
        """Add a detector to a specific circuit."""
        if not isinstance(circuit_number, int):
            raise TypeError("circuit_number must be int")

        self.circuit_dict[circuit_number].add_detector(detector_number, description)

    def delete_detector(self, circuit_number: int, detector_number: int) -> None:
        """Remove a specific detector from a specific circuit."""
        if not isinstance(circuit_number, int):
            raise TypeError("circuit_number must be int")
        if not isinstance(detector_number, int):
            raise TypeError("detector_number must be int")

        detector_tuple = (circuit_number, detector_number)

        self.circuit_dict[circuit_number].delete_detector(detector_number)
        if detector_tuple in self.active_detector_list:
            self.active_detector_list.remove(detector_tuple)
        if detector_tuple in self.disabled_detector_list:
            self.disabled_detector_list.remove(detector_tuple)

    def set_detector_description(self, circuit_number: int, detector_number: int, description: str) ->None:
        self.circuit_dict[circuit_number].detector_dict[detector_number].set_description(description)

    def get_detector_description(self, circuit_number: int, detector_number: int) -> str:
        return self.circuit_dict[circuit_number].detector_dict[detector_number].description

    def set_detector_enabled(self, circuit_number: int, detector_number: int, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise TypeError("enabled must be bool")
        if not circuit_number in self.circuit_dict:
            raise KeyError("circuit does not exist")
        if not detector_number in self.circuit_dict[circuit_number].detector_dict:
            raise KeyError("detector does not exist")

        detector_tuple = (circuit_number, detector_number)

        if enabled:
            if detector_tuple in self.disabled_detector_list:
                self.disabled_detector_list.remove(detector_tuple)

        else:
            if detector_tuple not in self.disabled_detector_list:
                self.disabled_detector_list.append(detector_tuple)
            if detector_tuple in self.active_detector_list:
                self.active_detector_list.remove(detector_tuple)

    def get_detector_enabled(self, circuit_number: int, detector_number: int) -> bool:
        if not circuit_number in self.circuit_dict:
            raise KeyError("circuit does not exist")
        if not detector_number in self.circuit_dict[circuit_number].detector_dict:
            raise KeyError("detector does not exist")

        detector_tuple = (circuit_number, detector_number)

        if detector_tuple in self.disabled_detector_list:
            return False
        else:
            return True

    def get_disabled_detectors(self) -> list:
        return self.disabled_detector_list

    def set_detector_in_history(self, circuit_number: int, detector_number: int, in_history: bool) -> None:
        if not isinstance(in_history, bool):
            raise TypeError("in_history must be bool")
        if not circuit_number in self.circuit_dict:
            raise KeyError("circuit does not exist")
        if not detector_number in self.circuit_dict[circuit_number].detector_dict:
            raise KeyError("detector does not exist")

        detector_tuple = (circuit_number, detector_number)

        if in_history:
            if detector_tuple not in self.history_detector_list:
                self.history_detector_list.append(detector_tuple)
        else:
            if detector_tuple in self.history_detector_list:
                self.history_detector_list.remove(detector_tuple)

    def get_detector_in_history(self, circuit_number: int, detector_number: int) -> bool:
        if not circuit_number in self.circuit_dict:
            raise KeyError("circuit does not exist")
        if not detector_number in self.circuit_dict[circuit_number].detector_dict:
            raise KeyError("detector does not exist")

        detector_tuple = (circuit_number, detector_number)

        if detector_tuple in self.history_detector_list:
            return True
        else:
            return False

    def get_history_detectors(self) -> list:
        return self.history_detector_list

    def set_detector_alarm_status(self, circuit_number: int, detector_number: int, alarm_status: bool) -> None:
        if not isinstance(alarm_status, bool):
            raise TypeError("alarm_status must be bool")
        if not circuit_number in self.circuit_dict:
            raise KeyError("circuit does not exist")
        if not detector_number in self.circuit_dict[circuit_number].detector_dict:
            raise KeyError("detector does not exist")

        detector_tuple: tuple = (circuit_number, detector_number)

        if detector_tuple in self.disabled_detector_list:
            raise ValueError("cannot activate disabled detector")

        if alarm_status:
            if detector_tuple not in self.active_detector_list:
                self.active_detector_list.append(detector_tuple)
        else:
            if detector_tuple in self.active_detector_list:
                self.active_detector_list.remove(detector_tuple)

    def get_detector_alarm_status(self, circuit_number: int, detector_number: int) -> bool:
        detector_tuple: tuple = (circuit_number, detector_number)
        return detector_tuple in self.active_detector_list

    def get_active_detectors(self) -> list:
        return self.active_detector_list

    def get_detectors_for_circuit(self, circuit_number: int) -> list:
        """Get all detectors for a specific circuit."""
        circuit = self.circuit_dict[circuit_number]
        detector_list = [num for num in circuit.detector_dict.keys()]
        return detector_list

    def clear_alarms(self) -> None:
        """Clear active_detector_list."""
        self.active_detector_list.clear()

    def set_extinguisher_triggered(self, state: bool) -> None:
        if not isinstance(state, bool):
            raise TypeError("state must be bool")
        self.extinguisher_triggered = state

    def get_extinguisher_triggered(self) -> bool:
        return self.extinguisher_triggered

    def set_acoustic_signals_off(self, state: bool) -> None:
        if not isinstance(state, bool):
            raise TypeError("state must be bool")
        self.acoustic_signals_off = state

    def get_acoustic_signals_off(self) -> bool:
        return self.acoustic_signals_off

    def set_ue_off(self, state: bool) -> None:
        if not isinstance(state, bool):
            raise TypeError("state must be bool")
        self.ue_off = state

    def get_ue_off(self) -> bool:
        return self.ue_off

    def set_fire_controls_off(self, state: bool) -> None:
        if not isinstance(state, bool):
            raise TypeError("state must be bool")
        self.fire_controls_off = state

    def get_fire_controls_off(self) -> bool:
        return self.fire_controls_off