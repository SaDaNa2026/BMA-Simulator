import unittest
from unittest.mock import Mock
from FileOperations import FileOperations


class MyTestCase(unittest.TestCase):
    def test_create_building_save_dict(self):
        mock_model = Mock()
        mock_model.get_building_description.return_value = "Testbeschreibung"
        mock_model.get_circuits.return_value = [1, 2]
        mock_model.get_detectors_for_circuit.return_value = [34, 42]
        mock_model.get_detector_description.return_value = "test"
        save_dict = FileOperations.create_building_save_dict(mock_model)
        self.assertEqual(save_dict, {"building_description": "Testbeschreibung",
                                     "circuit_dict": {1: {34: "test", 42: "test"}, 2: {34: "test", 42: "test"}}})

    def test_create_scenario_save_dict(self):
        mock_model = Mock()
        mock_model.get_active_detectors.return_value = [(1, 1), (1, 2), (3, 1)]
        save_dict = FileOperations.create_scenario_save_dict(mock_model)
        self.assertEqual(save_dict, {"active_detector_list": [(1, 1), (1, 2), (3, 1)], "scenario_description": "Beschreibung"})

if __name__ == '__main__':
    unittest.main()
