from RPLCD.i2c import CharLCD

class LCDController(CharLCD):
    def __init__(self, model):
        super().__init__('PCF8574', 0x25)
        self.model = model
        self.current_screen: int = 0
        self.visible_dict: dict = {}
        self.write_building_description()

    def write_building_description(self):
        """Write the building description to the LCD."""
        self.clear()
        self.cursor_pos = (0, 0)
        self.write_string(self.model.get_building_description())

    def write_message(self, detector: tuple, position, message_type: str) ->None:
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
        if message_type == "alarm":
            self.write_string("      Feuer")
        elif message_type == "disabled":
            self.write_string("Abschaltung")
        self.write_string(f"\r\n{detector_description}")

    def add_alarm(self, detector: tuple):
        """Add a new alarm."""
        if not isinstance(detector, tuple):
            raise TypeError("detector must be a tuple")
        if detector not in self.model.get_active_detectors():
            raise ValueError("tried to add an alarm for an inactive detector")

        self.current_screen = 1
        self.visible_dict.clear()

        # Insert the new alarm at the bottom
        self.visible_dict["bottom"] = detector

        # Set the first alarm to the first detector
        first_alarm = self.model.get_active_detectors()[0]
        if not detector == first_alarm:
            self.visible_dict["top"] = first_alarm

        self.refresh()

    def reset(self):
        """Resets the LCD to display the first and last alarm, if available. Displays the building description otherwise."""
        self.visible_dict.clear()
        self.clear()
        active_detector_list = self.model.get_active_detectors()
        if len(active_detector_list) > 0:
            self.add_alarm(active_detector_list[0])
            if len(active_detector_list) > 1:
                self.add_alarm(active_detector_list[-1])

        else:
            self.current_screen = 0
            self.write_building_description()


    def previous_message(self) -> bool:
        """Set the top alarm to the previous alarm. Returns true if the operation was successful, otherwise false"""
        if self.current_screen == 1:
            active_detector_list = self.model.get_active_detectors()
            # Check if there are enough alarms to scroll
            if not len(active_detector_list) > 2 or self.visible_dict["top"] not in active_detector_list:
                return False
            current_index = active_detector_list.index(self.visible_dict["top"])
            # Return if the top alarm is already the first one
            if current_index == 0:
                return False
            new_index = current_index - 1
            self.visible_dict["top"] = active_detector_list[new_index]
            self.refresh()
            return True

        elif self.current_screen == 2:
            disabled_detector_list = self.model.get_disabled_detectors()
            return True
        else:
            return False


    def next_message(self) -> bool:
        """Set the top alarm to the next alarm. Returns true if the operation was successful, otherwise false"""
        active_detector_list = self.model.get_active_detectors()
        # Check if there are enough alarms to scroll
        if not len(active_detector_list) > 2 or self.visible_dict["top"] not in active_detector_list:
            return False
        current_index = active_detector_list.index(self.visible_dict["top"])
        # Return if the top alarm is already the first one
        if active_detector_list[current_index] == active_detector_list[-2]:
            return False
        new_index = current_index + 1
        self.visible_dict["top"] = active_detector_list[new_index]
        self.refresh()
        return True

    def first_message_shown(self) -> bool:
        """Checks if the first message is shown in the top position of the LCD. Return True if there are less than or
        equal to two alarms or current_screen == 0 (home screen)"""
        if self.current_screen == 0:
            return True
        if len(self.visible_dict) < 2 or len(self.model.get_active_detectors()) <= 2:
            return True
        return self.visible_dict["top"] == self.model.get_active_detectors()[0]

    def last_message_shown(self) -> bool:
        """Checks if the last scrollable (second to last) message is shown in the top position of the LCD. Returns
        True if there are less than or equal to 2 messages or current_screen == 0 (home screen)"""
        if len(self.visible_dict) < 2 or len(self.model.get_active_detectors()) <= 2:
            return True
        return self.visible_dict["top"] == self.model.get_active_detectors()[-2]

    def toggle_view_level(self):
        """Switch between alarms and disabled detectors"""
        if self.current_screen == (0 or 2):
            if len(self.model.get_active_detectors()) > 0:
                self.current_screen = 1
                self.reset()
        else:
            disabled_detectors = self.model.get_disabled_detectors()
            if len(disabled_detectors) > 0:
                self.current_screen=2
                self.visible_dict.clear()
                self.visible_dict["bottom"] = disabled_detectors[-1]

                if len(disabled_detectors) > 1:
                    self.visible_dict["top"] = disabled_detectors[0]

            self.refresh()

    def refresh(self):
        """Refresh the LCD according to visible_alarm_dict."""
        if len(self.visible_dict) > 2:
            raise ValueError("visible_dict may not have more than 2 entries")

        if self.current_screen == 1:
            self.clear()
            for position in self.visible_dict:
                self.write_message(self.visible_dict[position], position, "alarm")

        elif self.current_screen == 2:
            self.clear()
            for position in self.visible_dict:
                self.write_message(self.visible_dict[position], position, "disabled")