import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from contextlib import redirect_stdout
import io
from gi.repository import GLib, Gio

from FileOperations import FileOperations


class TestSaveDicts(unittest.TestCase):
    def test_create_building_save_dict(self):
        """Verify correct format of the save_dict."""
        mock_model = Mock()
        mock_model.get_building_description.return_value = "Testbeschreibung"
        mock_model.get_circuits.return_value = [1, 2]
        mock_model.get_detectors_for_circuit.return_value = [34, 42]
        mock_model.get_detector_description.return_value = "test"
        save_dict = FileOperations.create_building_save_dict(mock_model)
        self.assertEqual(save_dict, {"building_description": "Testbeschreibung",
                                     "circuit_dict": {1: {34: "test", 42: "test"}, 2: {34: "test", 42: "test"}}})

    def test_create_scenario_save_dict(self):
        """Verify correct format of the save_dict."""
        mock_model = Mock()
        mock_model.get_active_detectors.return_value = [(1, 1), (1, 2), (3, 1)]
        mock_model.get_disabled_detectors.return_value = [(1, 3), (2, 1)]
        save_dict = FileOperations.create_scenario_save_dict(mock_model)
        self.assertEqual(save_dict, {"active_detector_list": [(1, 1), (1, 2), (3, 1)],
                                     "disabled_detector_list": [(1, 3), (2, 1)],
                                     "scenario_description": "Beschreibung"})


class TestSaveToFile(unittest.TestCase):
    def setUp(self):
        self.mock_file = MagicMock()
        self.test_path = "/tmp/save.json"
        self.mock_file.get_path.return_value = self.test_path

    @patch("builtins.open", new_callable=MagicMock)
    @patch("json.dump")
    def test_saves_dict_to_file(self, mock_json_dump, mock_open):
        test_data = {"key": "value", "number": 42}
        mock_file_handle = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file_handle

        FileOperations.save_to_file(self.mock_file, test_data)

        self.mock_file.get_path.assert_called_once()
        mock_open.assert_called_once_with(self.test_path, "w", encoding="utf-8")
        mock_json_dump.assert_called_once_with(
            test_data,
            mock_file_handle,
            sort_keys=True,
            indent=4,
        )

    @patch("builtins.print")
    def test_logs_save_path_and_success(self, mock_print):
        test_data = {"key": "value"}

        FileOperations.save_to_file(self.mock_file, test_data)

        mock_print.assert_any_call(f"Saving to: {self.test_path}")
        mock_print.assert_called_with("File saved successfully.")


class DummyScenarioModel:
    def __init__(self):
        self.alarm_calls = []
        self.enabled_calls = []
        self.raise_key_error = False

    def set_detector_alarm_status(self, circuit_number, detector_number, status):
        if self.raise_key_error:
            raise KeyError
        self.alarm_calls.append((circuit_number, detector_number, status))

    def set_detector_enabled(self, circuit_number, detector_number, enabled):
        if self.raise_key_error:
            raise KeyError
        self.enabled_calls.append((circuit_number, detector_number, enabled))

class TestApplyScenario(unittest.TestCase):
    def setUp(self):
        self.model = DummyScenarioModel()

    def test_valid_input_calls_model(self):
        load_dict = {"active_detector_list": [[1, 2], [3, 4]], "disabled_detector_list" : [[1, 1], [2, 2]]}
        FileOperations.apply_scenario(load_dict, self.model)
        self.assertEqual(self.model.alarm_calls, [(1, 2, True), (3, 4, True)])
        self.assertEqual(self.model.enabled_calls, [(1, 1, False), (2, 2, False)])

    def test_non_list_raises_type_error(self):
        load_dict = {"active_detector_list": ["not_a_list"]}
        with self.assertRaises(TypeError) as cm:
            FileOperations.apply_scenario(load_dict, self.model)
        self.assertIn("Inkorrektes Format der Meldernummer.", str(cm.exception))

    def test_wrong_length_raises_syntax_error(self):
        load_dict = {"active_detector_list": [[1, 2, 3]]}
        with self.assertRaises(SyntaxError) as cm:
            FileOperations.apply_scenario(load_dict, self.model)
        self.assertIn("Inkorrektes Format der Meldernummer.", str(cm.exception))

    def test_first_element_not_int_raises_type_error(self):
        load_dict = {"active_detector_list": [["a", 2]]}
        with self.assertRaises(TypeError) as cm:
            FileOperations.apply_scenario(load_dict, self.model)
        self.assertIn("Mindestens eine Meldergruppen-Nummer ist keine natürliche Zahl.", str(cm.exception))

    def test_second_element_not_int_raises_type_error(self):
        load_dict = {"active_detector_list": [[1, "b"]]}
        with self.assertRaises(TypeError) as cm:
            FileOperations.apply_scenario(load_dict, self.model)
        self.assertIn("Mindestens eine Melder-Nummer ist keine natürliche Zahl.", str(cm.exception))

    def test_key_error_propagates_with_custom_message(self):
        load_dict = {"active_detector_list": [[5, 6]]}
        self.model.raise_key_error = True
        with self.assertRaises(KeyError) as cm:
            FileOperations.apply_scenario(load_dict, self.model)
        self.assertIn("Melder 6 in Meldergruppe 5 ist im Szenario aktiv, aber nicht in der Gebäudekonfiguration "
                      "enthalten, die im selben Verzeichnis liegt.", str(cm.exception))

    def test_multiple_entries_mixed(self):
        # First entry valid, second raises KeyError
        self.model.raise_key_error = False
        FileOperations.apply_scenario({"active_detector_list" : [[1, 1]], "disabled_detector_list" : [[2, 1]]}, self.model)
        # now set to raise on second call
        self.model.raise_key_error = True
        with self.assertRaises(KeyError):
            FileOperations.apply_scenario({"active_detector_list": [[2, 2]], "disabled_detector_list" : [[3, 1]]}, self.model)


class DummyBuildingModel:
    def __init__(self):
        self.circuit_dict = {}
        self.building_description = ""
        self.clear_data_calls = 0

    def clear_data(self):
        self.circuit_dict = {}
        self.building_description = ""
        self.clear_data_calls += 1

    def add_circuit(self, circuit_number):
        self.circuit_dict[circuit_number] = {}

    def add_detector(self, circuit_number, detector_number, description):
        self.circuit_dict[circuit_number][detector_number] = description

    def set_building_description(self, description):
        self.building_description = description

class TestLoadBuildingConfig(unittest.TestCase):
    def setUp(self):
        self.model = DummyBuildingModel()

    def test_load_building_config_valid_data(self):
        """Load a valid configuration and assert the model is updated and success is printed."""
        load_dict = {
            "building_description": "HQ Tower",
            "circuit_dict": {
                "1": {
                    "101": "Lobby smoke",
                    "102": "Basement heat",
                },
                "2": {
                    "201": "Server room",
                },
            },
        }

        # Capture stdout to verify the success message is printed exactly once.
        printed = io.StringIO()
        with redirect_stdout(printed):
            FileOperations.load_building_config(self.model, load_dict)

        # Verify the model interactions.
        self.assertEqual(self.model.clear_data_calls, 1)
        self.assertEqual(self.model.building_description, "HQ Tower")

        expected_circuits = {
            1: {
                101: "Lobby smoke",
                102:  "Basement heat",
            },
            2: {
                201: "Server room",
            },
        }
        self.assertEqual(self.model.circuit_dict, expected_circuits)

        # Ensure the function printed the success message exactly once.
        self.assertEqual(printed.getvalue().strip(), "File loaded successfully")

    def test_load_building_config_non_digit_circuit(self):
        """Ensure non-digit circuit keys raise ValueError with a German message."""
        load_dict = {
            "building_description": "HQ Tower",
            "circuit_dict": {
                "FOO": {
                    "101": "Lobby smoke",
                },
            },
        }

        with self.assertRaises(ValueError) as exc_info:
            FileOperations.load_building_config(self.model, load_dict)

        self.assertIn("Mindestens eine Meldergruppen-Nummer ist keine natürliche Zahl.", str(exc_info.exception))


    def test_load_building_config_non_digit_detector(self):
        """Ensure non-digit detector keys raise ValueError referencing the circuit number."""
        load_dict = {
            "building_description": "HQ Tower",
            "circuit_dict": {
                "1": {
                    "BAR": "Lobby smoke",
                },
            },
        }

        with self.assertRaises(ValueError) as exc_info:
            FileOperations.load_building_config(self.model, load_dict)

        circuit_number = 1
        expected_message = f"Mindestens eine Meldernummer in Meldergruppe {circuit_number} ist keine natürliche Zahl."
        self.assertIn(expected_message, str(exc_info.exception))


class TestGetBuildingConfigForScenario(unittest.TestCase):
    def setUp(self):
        # We keep the shared mock objects in setUp so that each test
        # starts with a clean slate but still benefits from reusable fixtures.
        self.source = MagicMock()
        self.source.get_path.return_value = "/some/scenario/path"

        self.north_building = MagicMock()
        self.north_building.get_name.return_value = "north.building"
        self.south_building = MagicMock()
        self.south_building.get_name.return_value = "south.building"
        self.other_file = MagicMock()
        self.other_file.get_name.return_value = "other_file.json"

        self.load_scenario_callback = MagicMock()

        self.scenario_load_dict = {"test" : "data"}

    def test_happy_path(self):
        """Happy path: exactly one .building file triggers the callback once."""
        self.source.enumerate_children_finish.return_value = [self.north_building, self.other_file]

        FileOperations.get_building_config_for_scenario(
            self.source,
            None,  # result is unused in the callback
            self.scenario_load_dict,
            self.load_scenario_callback,
        )

        # Verify that the callback was invoked with a Gio.File instance
        # pointing at the discovered .building file.
        self.load_scenario_callback.assert_called_once()
        file_arg, payload_arg = self.load_scenario_callback.call_args[0]
        self.assertIsInstance(file_arg, Gio.File)
        self.assertEqual(file_arg.get_path(), "/some/scenario/path/north.building")
        self.assertIs(payload_arg, self.scenario_load_dict)

    def test_raises_when_no_building_file_exists(self):
        """Zero .building files -> GLib.Error with a clear message."""
        self.source.enumerate_children_finish.return_value = []

        with self.assertRaises(GLib.Error) as exc:
            FileOperations.get_building_config_for_scenario(
                self.source,
                None,
                self.scenario_load_dict,
                self.load_scenario_callback,
            )

        self.assertEqual(exc.exception.message, "Keine .building-Datei in diesem Verzeichnis gefunden.")
        self.load_scenario_callback.assert_not_called()

    def test_raises_when_multiple_building_files_exist(self):
        """More than one .building file -> GLib.Error enumerating the count."""
        self.source.enumerate_children_finish.return_value = [self.north_building, self.south_building, self.other_file]

        with self.assertRaises(GLib.Error) as exc:
            FileOperations.get_building_config_for_scenario(
                self.source,
                None,
                self.scenario_load_dict,
                self.load_scenario_callback,
            )

        expected = f"Es wurden 2 .building-Dateien gefunden.\nStellen Sie sicher, dass pro Ordner nur eine .building-Datei existiert."
        self.assertEqual(exc.exception.message, expected)
        self.load_scenario_callback.assert_not_called()


if __name__ == '__main__':
    unittest.main()
