import smbus3
from mcp23017 import *
import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib


class MCPController(MCP23017):
    def __init__(self, address, button_list: list, led_dict: dict):
        """- address: I2C address of the MCP
            - button_list: [button pin, callback function, maintained_action, normally_closed]
            - led_dict: {led_name : led_pin}"""

        super().__init__(address, smbus3.SMBus(1))
        self.button_list = button_list

        # Dictionary to keep track of the button state
        self.last_state: dict = {}
        for button_tuple in self.button_list:
            self.last_state[button_tuple[0]] = False

        for button_tuple in button_list:
            self.pin_mode(button_tuple[0], INPUT)
        for led_pin in led_dict.values():
            self.pin_mode(led_pin, OUTPUT)

        GLib.timeout_add(100, self.poll_buttons)

    def poll_buttons(self):
        """Check the state of every button provided in the list. Execute callbacks for the pressed buttons."""
        for button_tuple in self.button_list:
            pin_number = button_tuple[0]
            callback = button_tuple[1]
            maintained_action = button_tuple[2]
            normally_closed = button_tuple[3]
            state = self.digital_read(pin_number)
            if normally_closed:
                state = not state

            if maintained_action:
                if state != self.last_state[pin_number]:
                    callback(state)
                    self.last_state[pin_number] = state

            else:
                if state and not self.last_state[pin_number]:
                    self.last_state[pin_number] = True
                    # Execute registered callback
                    callback()
                elif not state:
                    self.last_state[pin_number] = False
        return True

