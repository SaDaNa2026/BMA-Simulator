from RPLCD.i2c import CharLCD

class LCDController(CharLCD):
    def __init__(self, model):
        super().__init__('PCF8574', 0x25)
        self.model = model
        self.visible_alarm_dict: dict = {}

    def write_alarm(self, detector: tuple, position):
        """Write an alarm to the LCD at the specified position."""
        circuit_number = detector[0]
        detector_number = detector[1]
        detector_description = self.model.get_detector_description(circuit_number, detector_number)
        circuit_string = str(circuit_number)
        detector_string = str(detector_number)

        if position == "top":
            self.cursor_pos = (0, (5 - len(circuit_string)))
        elif position == "bottom":
            self.cursor_pos = (2, (5 - len(circuit_string)))
        else:
            raise ValueError("position must be top or bottom")

        # Write the alarm in the correct format
        self.write_string(circuit_string)
        self.write_string("/")
        self.write_string(detector_string)
        line = self.cursor_pos[0]
        self.cursor_pos = (line, 9)
        self.write_string("      Feuer")
        self.write_string(f"\r\n{detector_description}")

    def add_alarm(self, detector: tuple):
        """Add a new alarm."""
        if not isinstance(detector, tuple):
            raise TypeError("detector must be a tuple")
        if detector not in self.model.get_active_detectors():
            raise ValueError("tried to add an alarm for an inactive detector")

        self.visible_alarm_dict.clear()

        # Insert the new alarm at the bottom
        self.visible_alarm_dict["bottom"] = detector

        # Set the first alarm to the first detector
        first_alarm = self.model.get_active_detectors()[0]
        if not detector == first_alarm:
            self.visible_alarm_dict["top"] = first_alarm

        self.refresh()

    def clear_alarms(self):
        """Clear all alarms."""
        self.visible_alarm_dict.clear()
        self.refresh()

    def previous_alarm(self, *args):
        """Set the top alarm to the previous alarm."""
        # Check if there are enough alarms to scroll
        if not len(self.model.get_active_detectors()) > 2:
            return
        current_index = self.model.get_active_detectors().index(self.visible_alarm_dict["top"])
        # Return if the top alarm is already the first one
        if current_index == 0:
            return
        new_index = current_index - 1
        self.visible_alarm_dict["top"] = self.model.get_active_detectors()[new_index]
        self.refresh()

    def next_alarm(self, *args):
        """Set the top alarm to the previous alarm."""
        # Check if there are enough alarms to scroll
        if not len(self.model.get_active_detectors()) > 2:
            return
        current_index = self.model.get_active_detectors().index(self.visible_alarm_dict["top"])
        # Return if the top alarm is already the first one
        if self.model.get_active_detectors()[current_index] == self.model.get_active_detectors()[-2]:
            return
        new_index = current_index + 1
        self.visible_alarm_dict["top"] = self.model.get_active_detectors()[new_index]
        self.refresh()

    def switch_view_level(self):
        """Switch between alarms, errors and history. Currently a placeholder."""
        pass

    def refresh(self):
        """Refresh the LCD according to visible_alarm_dict."""
        if len(self.visible_alarm_dict) > 2:
            raise ValueError("visible_alarm_dict may not have more than 2 entries")

        self.clear()
        for position in self.visible_alarm_dict:
            self.write_alarm(self.visible_alarm_dict[position], position)