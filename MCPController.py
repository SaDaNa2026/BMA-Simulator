import smbus3
from mcp23017 import *
import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib


class MCPController(MCP23017):
    def __init__(self, address, button_list: list):
        super().__init__(address, smbus3.SMBus(1))

        self.button_list = button_list

        # Dictionary to keep track of the button state
        self.last_state: dict = {}
        for button_tuple in self.button_list:
            self.last_state[button_tuple[0]] = False

        for button_tuple in button_list:
            self.pin_mode(button_tuple[0], INPUT)

        GLib.timeout_add(100, self.poll_buttons)

    def poll_buttons(self):
        for button_tuple in self.button_list:
            pin_number = button_tuple[0]
            if self.digital_read(pin_number) and not self.last_state[pin_number]:
                print(pin_number)
                self.last_state[pin_number] = True
                button_tuple[1]()
            elif not self.digital_read(pin_number):
                self.last_state[pin_number] = False
        return True

