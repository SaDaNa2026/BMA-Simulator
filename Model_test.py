import unittest
from Model import BuildingModel, sort_dict_by_key


class TestBuildingModel(unittest.TestCase):
    """Test suite for BuildingModel."""

    def setUp(self):
        """Create a fresh BuildingModel for each test."""
        self.model = BuildingModel()
        self.model.clear_data()

    def assert_circuits_equal(self, expected):
        """Helper to compare circuit lists without relying on order."""
        self.assertCountEqual(self.model.get_circuits(), expected)

    def assert_detectors_equal(self, circuit_number, expected):
        """Helper to compare detector lists for a circuit."""
        self.assertCountEqual(
            self.model.get_detectors_for_circuit(circuit_number),
            expected
        )

    def test_sort_dict_by_key(self):
        # Invalid type
        with self.assertRaises(TypeError):
            sort_dict_by_key(None)

        # Verify correct sorting
        test_dict = {5 : [1, 2], 3 : {4 : 2}, 1 : ""}
        sorted_test_dict = {1 : "", 3 : {4 : 2}, 5 : [1, 2]}
        self.assertEqual(sort_dict_by_key(test_dict), sorted_test_dict)

    def test_building_description(self):
        """Test getter, setter, and invalid inputs for building_description."""
        # Default value
        self.assertEqual(self.model.get_building_description(), "Gebäudebeschreibung")

        # Valid update
        self.model.set_building_description("Neue Beschreibung")
        self.assertEqual(self.model.get_building_description(), "Neue Beschreibung")

        # Type validation
        with self.assertRaises(TypeError):
            BuildingModel(5)
        with self.assertRaises(TypeError):
            self.model.set_building_description(True)

        # circuit_dict must be empty on init
        with self.assertRaises(ValueError):
            BuildingModel(circuit_dict={1: "a"})

    def test_circuit_lifecycle(self):
        """Test adding, listing, deleting, and clearing circuits."""
        # Initially no circuits
        self.assert_circuits_equal([])

        # Add valid circuit numbers
        for number in (1, 99999):
            self.model.add_circuit(number)
            self.assertIn(number, self.model.get_circuits())

        self.assert_circuits_equal([1, 99999])

        # Reject duplicates and invalid numbers
        with self.assertRaises(ValueError):
            self.model.add_circuit(1)
        with self.assertRaises(ValueError):
            self.model.add_circuit(0)
        with self.assertRaises(ValueError):
            self.model.add_circuit(100000)

        # Reject non-int circuit numbers
        with self.assertRaises(TypeError):
            self.model.add_circuit("1")

        # Delete existing circuit
        self.model.delete_circuit(1)
        self.assert_circuits_equal([99999])

        # Delete non-existing circuit
        with self.assertRaises(KeyError):
            self.model.delete_circuit(5)

        # Reject non-int deletes
        with self.assertRaises(TypeError):
            self.model.delete_circuit("1")

        # Clear resets everything
        self.model.clear_data()
        self.assert_circuits_equal([])
        self.assertEqual(
            self.model.get_building_description(),
            "Gebäudebeschreibung"
        )

    def test_detector_lifecycle(self):
        """Test adding, updating, and deleting detectors."""
        self.model.add_circuit(1)

        # Add valid detectors
        self.model.add_detector(1, 1, "Rauchmelder EG")
        self.assert_detectors_equal(1, [1])
        self.assertEqual(
            self.model.get_detector_description(1, 1),
            "Rauchmelder EG"
        )

        # Reject duplicates and invalid numbers
        with self.assertRaises(ValueError):
            self.model.add_detector(1, 1)
        with self.assertRaises(ValueError):
            self.model.add_detector(1, 0)
        with self.assertRaises(ValueError):
            self.model.add_detector(1, 100)

        # Reject wrong types and length
        with self.assertRaises(TypeError):
            self.model.add_detector("1", 1)
        with self.assertRaises(TypeError):
            self.model.add_detector(1, "1")
        with self.assertRaises(TypeError):
            self.model.add_detector(1, 10, 42)
        with self.assertRaises(ValueError):
            self.model.add_detector(1, 9, "Diese Beschreibung ist zu lang")
        with self.assertRaises(ValueError):
            self.model.add_detector(1, 8, f"Newline test\n")

        # Add another detector
        self.model.add_detector(1, 99, "Heizung")
        self.assert_detectors_equal(1, [1, 99])

        # Update description
        self.model.set_detector_description(1, 1, "Rauchmelder OG")
        self.assertEqual(
            self.model.get_detector_description(1, 1),
            "Rauchmelder OG"
        )
        with self.assertRaises(TypeError):
            self.model.set_detector_description(1, 1, 123)
        with self.assertRaises(ValueError):
            self.model.set_detector_description(1, 1, "Diese Beschreibung ist zu lang")
        with self.assertRaises(ValueError):
            self.model.set_detector_description(1, 1, f"Newline test\n")

        # Update alarm status
        self.model.set_detector_alarm_status(1, 1, True)
        self.assertTrue(self.model.get_detector_alarm_status(1, 1))
        with self.assertRaises(TypeError):
            self.model.set_detector_alarm_status(1, 1, "True")
        with self.assertRaises(KeyError):
            self.model.set_detector_alarm_status(5, 6, False)
        with self.assertRaises(KeyError):
            self.model.set_detector_alarm_status(1, 6, False)

        # Delete detector
        self.model.delete_detector(1, 1)
        self.assert_detectors_equal(1, [99])

        # Reject wrong types for delete
        with self.assertRaises(TypeError):
            self.model.delete_detector("1", 1)
        with self.assertRaises(TypeError):
            self.model.delete_detector(1, "1")

        # Deleting circuit also removes its detectors
        self.model.delete_circuit(1)
        self.assert_circuits_equal([])

    def test_get_active_detectors(self):
        """Verify that get_active_detectors returns only alarms with status True."""
        self.model.add_circuit(1)
        self.model.add_detector(1, 1, "Sensor A")
        self.model.add_detector(1, 2, "Sensor B")
        self.model.add_detector(1, 3, "Sensor C")

        # Initially no active detectors
        self.assertEqual(self.model.get_active_detectors(), [])

        # Activate one detector
        self.model.set_detector_alarm_status(1, 1, True)
        self.assertEqual(self.model.get_active_detectors(), [(1, 1)])

        # Activate second and third detector
        self.model.set_detector_alarm_status(1, 2, True)
        self.model.set_detector_alarm_status(1, 3, True)
        self.assertCountEqual(
            self.model.get_active_detectors(),
            [(1, 1), (1, 2), (1, 3)]
        )

        # Deactivate second detector
        self.model.set_detector_alarm_status(1, 2, False)
        self.assertEqual(self.model.get_active_detectors(), [(1, 1), (1, 3)])

        # Delete first detector
        self.model.delete_detector(1, 1)
        self.assertEqual(self.model.get_active_detectors(), [(1, 3)])

    def test_enable_detector(self):
        """Test enabling/disabling of detectors."""
        # Test adding, setting and getting the enabled state
        self.model.add_circuit(1)
        self.model.add_detector(1, 1)
        self.assertEqual(self.model.get_detector_enabled(1, 1), True)
        self.model.set_detector_enabled(1, 1, False)
        self.assertEqual(self.model.get_detector_enabled(1, 1), False)

        # Test getting the disabled list
        self.model.add_detector(1, 2)
        self.model.set_detector_enabled(1, 2, True)
        self.assertEqual(self.model.get_disabled_detectors(), [(1, 1)])

        # Test the removal of disabled detectors from active_detector_list
        with self.assertRaises(ValueError):
            self.model.set_detector_alarm_status(1, 1, True)
        self.model.set_detector_alarm_status(1, 2, True)
        self.assertEqual(self.model.get_detector_alarm_status(1, 2), True)
        self.model.set_detector_enabled(1, 2, False)
        self.assertEqual(self.model.get_detector_alarm_status(1, 2), False)

        # Test removal of detectors
        self.model.delete_detector(1, 1)
        self.model.set_detector_enabled(1, 2, False)
        self.assertEqual(self.model.get_disabled_detectors(), [(1, 2)])
        self.model.delete_circuit(1)
        self.assertEqual(self.model.get_disabled_detectors(), [])

        # Test invalid syntax
        with self.assertRaises(KeyError):
            self.model.set_detector_enabled(2, 1, True)
        with self.assertRaises(KeyError):
            self.model.get_detector_enabled(2, 1)

        self.model.add_circuit(1)
        self.model.add_detector(1, 1)
        with self.assertRaises(KeyError):
            self.model.set_detector_enabled(1, 2, True)
        with self.assertRaises(KeyError):
            self.model.get_detector_enabled(1, 2)

        with self.assertRaises(TypeError):
            self.model.set_detector_enabled(1, 1, 1)

        with self.assertRaises(TypeError):
            self.model.add_detector(1, 2, enabled="test")

    def test_detector_history(self):
        self.model.add_circuit(1)
        self.model.add_detector(1, 1)

        self.model.set_detector_in_history(1, 1, True)
        self.assertEqual(self.model.get_detector_in_history(1, 1), True)

        self.model.add_detector(1, 2)
        self.assertEqual(self.model.get_detector_in_history(1, 2), False)

        self.assertEqual(self.model.get_history_detectors(), [(1, 1)])

        with self.assertRaises(KeyError):
            self.model.set_detector_in_history(2, 1, True)

        with self.assertRaises(KeyError):
            self.model.set_detector_in_history(1, 3, True)

        with self.assertRaises(KeyError):
            self.model.get_detector_in_history(45, 1)

        with self.assertRaises(KeyError):
            self.model.get_detector_in_history(1, 4)

        with self.assertRaises(TypeError):
            self.model.set_detector_in_history(1, 1, "string")

    def test_error_scenarios(self):
        """Ensure error cases are properly raised."""
        # Setting circuit_dict or active_detector_list when instantiating
        with self.assertRaises(ValueError):
            circuit_building = BuildingModel(circuit_dict={1: 3})
        with self.assertRaises(ValueError):
            detector_building = BuildingModel(active_detector_list=[(1, 1), (2, 3)])

        # Non-existing circuit or detector
        with self.assertRaises(KeyError):
            self.model.delete_circuit(1)
        self.model.add_circuit(1)
        with self.assertRaises(KeyError):
            self.model.delete_detector(1, 1)

        # Invalid building description type
        with self.assertRaises(TypeError):
            self.model.set_building_description(None)

        # Invalid circuit/detector numbers
        with self.assertRaises(ValueError):
            self.model.add_circuit(0)
        with self.assertRaises(ValueError):
            self.model.add_detector(1, 0)

        # Invalid types for circuit/detector operations
        with self.assertRaises(TypeError):
            self.model.add_detector("1", 1)
        with self.assertRaises(TypeError):
            self.model.delete_detector(1, "1")

    def test_history_time_functions(self):
        with self.assertRaises(TypeError):
            self.model.set_history_time_mode(1)
        with self.assertRaises(ValueError):
            self.model.set_history_time_mode("test")

        self.model.set_history_time_mode("user_defined")
        self.assertEqual(self.model.get_history_time_mode(), "user_defined")

        with self.assertRaises(TypeError):
            self.model.set_history_time_absolute("15:13")
        with self.assertRaises(ValueError):
            self.model.set_history_time_absolute((15, 34, 12))
        with self.assertRaises(TypeError):
            self.model.set_history_time_absolute(("12", 19))
        with self.assertRaises(TypeError):
            self.model.set_history_time_absolute((12, "19"))
        with self.assertRaises(ValueError):
            self.model.set_history_time_absolute((24, 12))
        with self.assertRaises(ValueError):
            self.model.set_history_time_absolute((12, 60))

        self.model.set_history_time_absolute((0, 0))
        self.assertEqual(self.model.get_history_time_absolute(), (0, 0))
        self.assertEqual(self.model.get_history_time_string(), "00:00")

        self.model.set_history_time_mode("automatic")
        self.assertEqual(self.model.get_history_time_mode(), "automatic")

        with self.assertRaises(TypeError):
            self.model.set_history_time_offset("3")
        with self.assertRaises(ValueError):
            self.model.set_history_time_offset(100)

        self.model.set_history_time_offset(42)
        self.assertEqual(self.model.get_history_time_offset(), 42)

if __name__ == '__main__':
    unittest.main()
