from dataclasses import dataclass, field
from typing import Dict

def sort_dict_by_key(input_dict: dict) -> dict:
    if not type(input_dict) == dict:
        raise TypeError("input_dict must be dict")
    sorted_keys = sorted(input_dict.keys())
    output_dict = {key : input_dict[key] for key in sorted_keys}
    return output_dict


@dataclass
class Detector:
    description: str
    alarm_status: bool = field(default=False)

    def set_description(self, description: str) -> None:
        if not isinstance(description, str):
            raise TypeError("Detector description must be a string")
        self.description = description

    def set_alarm_status(self, alarm_status) -> None:
        if not isinstance(alarm_status, bool):
            raise TypeError("alarm_status must be bool")
        self.alarm_status = alarm_status


@dataclass
class Circuit:
    """Represents a circuit with its detectors."""
    detector_dict: Dict[int, Detector] = field(default_factory=dict)

    def add_detector(self, detector_number: int, detector_description: str) -> None:
        """Add a detector to this circuit."""
        self.detector_dict[detector_number] = Detector(detector_description)
        self.detector_dict = sort_dict_by_key(self.detector_dict)

    def delete_detector(self, detector_number: int) -> None:
        """Remove a detector by index."""
        del self.detector_dict[detector_number]


@dataclass
class BuildingModel:
    building_description: str = field(default="Hier Gebäudebeschreibung einfügen")
    circuit_dict: Dict[int, Circuit] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.building_description, str):
            raise TypeError("building_description must be a string")
        if self.circuit_dict != {}:
            raise ValueError("circuit_dict must be empty upon initialization. Add circuits later via add_circuit")

    def clear_data(self):
        """Resets to init values."""
        self.set_building_description("Hier Gebäudebeschreibung einfügen")
        self.circuit_dict = {}

    def set_building_description(self, building_description: str) -> None:
        if not isinstance(building_description, str):
            raise TypeError("building_description must be a string")
        self.building_description = building_description

    def get_building_description(self) -> str:
        return self.building_description

    def add_circuit(self, circuit_number: int):
        """Add a specific circuit."""
        if not isinstance(circuit_number, int):
            raise TypeError("circuit_number must be int")

        if circuit_number < 1 or circuit_number >= 1000000000:
            raise ValueError("Die Meldergruppen-Nummer muss zwischen 1 und 999999999 liegen.")
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

    def add_detector(self, circuit_number: int, detector_number: int, detector_description: str = "") -> None:
        """Add a detector to a specific circuit."""
        if not isinstance(circuit_number, int):
            raise TypeError("circuit_number must be int")
        if not isinstance(detector_number, int):
            raise TypeError("detector_number must be int")
        if not isinstance(detector_description, str):
            raise TypeError("detector_description must be str")

        if detector_number < 1 or detector_number >= 1000000000:
            raise ValueError("Die Meldernummer muss zwischen 1 und 999999999 liegen.")
        if detector_number in self.circuit_dict[circuit_number].detector_dict:
            raise ValueError("Dieser Melder existiert bereits.")

        self.circuit_dict[circuit_number].add_detector(detector_number, detector_description)

    def delete_detector(self, circuit_number: int, detector_number: int) -> None:
        """Remove a specific detector from a specific circuit."""
        if not isinstance(circuit_number, int):
            raise TypeError("circuit_number must be int")
        if not isinstance(detector_number, int):
            raise TypeError("detector_number must be int")

        self.circuit_dict[circuit_number].delete_detector(detector_number)

    def set_detector_description(self, circuit_number: int, detector_number: int, detector_description: str) ->None:
        self.circuit_dict[circuit_number].detector_dict[detector_number].set_description(detector_description)

    def get_detector_description(self, circuit_number: int, detector_number: int) -> str:
        return self.circuit_dict[circuit_number].detector_dict[detector_number].description

    def set_detector_alarm_status(self, circuit_number: int, detector_number: int, alarm_status: bool) -> None:
        self.circuit_dict[circuit_number].detector_dict[detector_number].set_alarm_status(alarm_status)

    def get_detector_alarm_status(self, circuit_number: int, detector_number: int) -> bool:
        return self.circuit_dict[circuit_number].detector_dict[detector_number].alarm_status

    def get_active_detectors(self) -> list:
        active_detector_list = []
        for circuit_number in self.circuit_dict:
            circuit = self.circuit_dict[circuit_number]
            for detector_number in circuit.detector_dict:
                if circuit.detector_dict[detector_number].alarm_status:
                    active_detector_list.append((circuit_number, detector_number))
        return active_detector_list

    def get_detectors_for_circuit(self, circuit_number: int) -> list:
        """Get all detectors for a specific circuit."""
        circuit = self.circuit_dict[circuit_number]
        detector_list = [num for num in circuit.detector_dict.keys()]
        return detector_list
