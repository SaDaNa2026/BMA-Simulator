import unittest
from Model import BuildingModel


class TestBuildingModel(unittest.TestCase):
    def setUp(self):
        self.building_model = BuildingModel()

    def test_building_description(self):
        with self.assertRaises(TypeError):
            invalid_description_type = BuildingModel(5)
        with self.assertRaises(ValueError):
            passing_circuit_dict = BuildingModel(circuit_dict={1: "a"})
        with self.assertRaises(TypeError):
            self.building_model.set_building_description(True)

        self.building_model.set_building_description("Test description")
        self.assertEqual(self.building_model.get_building_description(), "Test description")

    def test_circuit_functions(self):
        with self.assertRaises(KeyError):
            self.building_model.delete_circuit(1)

        with self.assertRaises(TypeError):
            self.building_model.add_circuit("1")
        for test_number in (-1, 0, 1000000000):
            with self.assertRaises(ValueError):
                self.building_model.add_circuit(test_number)

        self.building_model.add_circuit(1)
        self.assertEqual(self.building_model.get_circuits(), [1])

        with self.assertRaises(ValueError):
            self.building_model.add_circuit(1)

        self.building_model.add_circuit(999999999)
        self.assertEqual(self.building_model.get_circuits(), [1, 999999999])

        with self.assertRaises(TypeError):
            self.building_model.delete_circuit("1")
        with self.assertRaises(KeyError):
            self.building_model.delete_circuit(5)

        self.building_model.delete_circuit(1)
        self.assertEqual(self.building_model.get_circuits(), [999999999])
        self.building_model.delete_circuit(999999999)

    def test_detector_functions(self):
        with self.assertRaises(KeyError):
            self.building_model.delete_detector(1, 1)
        self.building_model.add_circuit(1)
        with self.assertRaises(KeyError):
            self.building_model.delete_detector(1, 1)

        with self.assertRaises(TypeError):
            self.building_model.add_detector("a", 1)
        with self.assertRaises(TypeError):
            self.building_model.add_detector(1, "1")
        with self.assertRaises(TypeError):
            self.building_model.add_detector(1, 1, 1)
        with self.assertRaises(KeyError):
            self.building_model.add_detector(2, 1)
        for test_number in (-1, 0, 1000000000):
            with self.assertRaises(ValueError):
                self.building_model.add_detector(1, test_number)

        self.building_model.add_detector(1, 1, "Test description")
        self.assertEqual(self.building_model.get_detectors_for_circuit(1), [1])
        self.assertEqual(self.building_model.get_detector_description(1,1), "Test description")

        with self.assertRaises(ValueError):
            self.building_model.add_detector(1,1)

        self.building_model.add_detector(1, 999999999)
        self.assertEqual(self.building_model.get_detectors_for_circuit(1), [1, 999999999])

        with self.assertRaises(TypeError):
            self.building_model.set_detector_description(1, 1, 1)
        self.building_model.set_detector_description(1, 1, "Changed description")
        self.assertEqual(self.building_model.get_detector_description(1, 1), "Changed description")

        with self.assertRaises(TypeError):
            self.building_model.set_detector_alarm_status(1, 1, 1)
        self.building_model.set_detector_alarm_status(1, 1, True)
        self.assertEqual(self.building_model.get_detector_alarm_status(1, 1), True)

        with self.assertRaises(TypeError):
            self.building_model.delete_detector("a", 1)
        with self.assertRaises(TypeError):
            self.building_model.delete_detector(1, "1")

        self.building_model.delete_detector(1,1)
        self.assertEqual(self.building_model.get_detectors_for_circuit(1), [999999999])
        self.building_model.delete_circuit(1)



if __name__ == '__main__':
    unittest.main()
