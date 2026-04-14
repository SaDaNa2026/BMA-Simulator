from RPLCD.i2c import CharLCD

class LCDController(CharLCD):
    def __init__(self, model):
        super().__init__('PCF8574', 0x25)
        self.model = model
        self.current_screen: int = 0
        self.visible_dict: dict = {}
        self._write_building_description()

    def _write_building_description(self):
        """Write the building description to the LCD."""
        self.clear()
        self.cursor_pos = (0, 0)
        self.write_string(self.model.get_building_description())

    def _write_message(self, detector: tuple, position, message_type: str) ->None:
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
        elif message_type == "history":
            self.write_string("      Feuer")
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

    def _write_disabled_detectors(self):
        """Set visible_dict according to the disabled detectors and refresh"""
        disabled_detectors = self.model.get_disabled_detectors()
        if self.current_screen == 2 and len(disabled_detectors) > 0:
            self.visible_dict.clear()
            self.visible_dict["bottom"] = disabled_detectors[-1]

            if len(disabled_detectors) > 1:
                self.visible_dict["top"] = disabled_detectors[0]

        self.refresh()

    def _write_history_detectors(self):
        """Set visible_dict according to the history detectors and refresh"""
        history_detectors = self.model.get_history_detectors()
        if self.current_screen == 3:
            self.clear()
            if len(history_detectors) > 0:
                self.visible_dict.clear()
                self.visible_dict["bottom"] = history_detectors[-1]

        self.refresh()

    def reset(self):
        """Resets the LCD to display the first and last alarm, if available. Displays the building description otherwise."""
        self.visible_dict.clear()
        self.clear()
        active_detector_list = self.model.get_active_detectors()
        if len(active_detector_list) > 0:
            self.current_screen = 1
            self.add_alarm(active_detector_list[0])
            if len(active_detector_list) > 1:
                self.add_alarm(active_detector_list[-1])

        else:
            self.current_screen = 0
            self._write_building_description()


    def previous_message(self) -> bool:
        """Set the scrollable to the previous alarm. Returns true if the operation was successful, otherwise false"""
        message_list = self._get_message_list()
        if not message_list:
            return False

        if self.current_screen == 3:
            position = "bottom"
            shown_detectors = 1
        else:
            position = "top"
            shown_detectors = 2

        # Check if there are enough alarms to scroll
        if not len(message_list) > shown_detectors or self.visible_dict[position] not in message_list:
            return False
        current_index = message_list.index(self.visible_dict[position])
        if current_index == 0:
            return False

        new_index = current_index - 1
        self.visible_dict[position] = message_list[new_index]
        self.refresh()
        return True

    def next_message(self) -> bool:
        """Set the scrollable alarm to the next alarm. Returns true if the operation was successful, otherwise false"""
        message_list = self._get_message_list()
        if not message_list:
            return False

        if self.current_screen == 3:
            position = "bottom"
            shown_detectors = 1
        else:
            position = "top"
            shown_detectors = 2

        # Check if there are enough alarms to scroll
        if not len(message_list) > shown_detectors or self.visible_dict[position] not in message_list:
            return False
        current_index = message_list.index(self.visible_dict[position])
        if message_list[current_index] == message_list[-shown_detectors]:
            return False
        new_index = current_index + 1
        self.visible_dict[position] = message_list[new_index]
        self.refresh()
        return True

    def _get_message_list(self) -> list|bool:
        if self.current_screen == 1:
            return self.model.get_active_detectors()
        elif self.current_screen == 2:
            return self.model.get_disabled_detectors()
        elif self.current_screen == 3:
            return self.model.get_history_detectors()
        else:
            return False

    def first_message_shown(self) -> bool:
        """Checks if the first message is shown on the LCD. Return True if current_screen == 0 (home screen)"""
        match self.current_screen:
            case 1:
                if len(self.visible_dict) < 2:
                    return True
                return self.visible_dict["top"] == self.model.get_active_detectors()[0]
            case 2:
                if len(self.visible_dict) < 2:
                    return True
                return self.visible_dict["top"] == self.model.get_disabled_detectors()[0]
            case 3:
                return self.visible_dict["bottom"] == self.model.get_history_detectors()[0]
            case _:
                return True

    def last_message_shown(self) -> bool:
        """Checks if the last scrollable (second to last) message is shown on the LCD. Returns
        True if current_screen == 0 (home screen)"""
        match self.current_screen:
            case 1:
                if len(self.visible_dict) < 2:
                    return True
                return self.visible_dict["top"] == self.model.get_active_detectors()[-2]
            case 2:
                if len(self.visible_dict) < 2:
                    return True
                return self.visible_dict["top"] == self.model.get_disabled_detectors()[-2]
            case 3:
                return self.visible_dict["bottom"] == self.model.get_history_detectors()[-1]
            case _:
                return True

    def toggle_view_level(self):
        """Switch between alarms and disabled detectors"""
        match self.current_screen:
            case 0:
                if len(self.model.get_active_detectors()) > 0:
                    self.current_screen = 1
                    self.reset()

                elif len(self.model.get_disabled_detectors()) > 0:
                    self.current_screen = 2
                    self._write_disabled_detectors()

            case 1:
                if len(self.model.get_disabled_detectors()) > 0:
                    self.current_screen = 2
                    self._write_disabled_detectors()

            case 2:
                if len(self.model.get_active_detectors()) > 0:
                    self.current_screen = 1
                    self.reset()
                else:
                    self.current_screen = 0
                    self.reset()

            case 3:
                if len(self.model.get_active_detectors()) > 0:
                    self.current_screen = 1
                    self.reset()
                else:
                    self.current_screen = 0
                    self.reset()

    def show_history(self):
        """Switch to the history screen if there are detectors in the history"""
        if len(self.model.get_history_detectors()) > 0:
            self.current_screen = 3
            self._write_history_detectors()

    def refresh(self):
        """Refresh the LCD according to visible_alarm_dict."""
        if len(self.visible_dict) > 2:
            raise ValueError("visible_dict may not have more than 2 entries")

        if self.current_screen == 1:
            self.clear()
            for position in self.visible_dict:
                self._write_message(self.visible_dict[position], position, "alarm")

        elif self.current_screen == 2:
            self.clear()
            for position in self.visible_dict:
                self._write_message(self.visible_dict[position], position, "disabled")

        elif self.current_screen == 3:
            self.clear()
            self.cursor_pos = (0, 12)
            self.write_string("Historie")
            self.cursor_pos = (1, 15)
            self.write_string(self.model.get_history_time_string())
            self._write_message(self.visible_dict["bottom"], "bottom", "history")

    def test(self):
        """Fill the screen with blocks to test all pixels"""
        for row in range(4):
            self.cursor_pos = (row, 0)
            self.write_string('\xff' * 20)
