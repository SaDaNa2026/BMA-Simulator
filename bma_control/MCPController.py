import smbus
from mcp23017 import *
import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib
import time


class MCPController(MCP23017):
    def __init__(self, address, button_list: list, led_dict: dict):
        """- address: I2C address of the MCP
            - button_list: [button pin, callback function, callback function for long press (set to None if maintained_action or to disable it), maintained_action, normally_closed]
            - led_dict: {led_name : led_pin}"""

        super().__init__(address, smbus.SMBus(1))
        self.button_list = button_list

        # Dictionary to keep track of the button state
        self.last_state: dict = {}
        # Dictionary to keep track of press start time
        self.press_start_time: dict = {}
        # Dictionary to keep track of long press timers
        self.long_press_timers: dict = {}

        for button_tuple in self.button_list:
            pin = button_tuple[0]
            self.last_state[pin] = False
            self.press_start_time[pin] = None
            self.long_press_timers[pin] = None
            self.pin_mode(pin, INPUT)

        for led_pin in led_dict.values():
            self.pin_mode(led_pin, OUTPUT)

        GLib.timeout_add(100, self.poll_buttons)

    def _on_long_press_timeout(self, pin, long_press_callback):
        """Called after 5 seconds if the button is still pressed."""
        if self.last_state[pin]:
            long_press_callback()
            self.press_start_time[pin] = None
            self.long_press_timers[pin] = None
        return False

    def poll_buttons(self):
        """Check the state of every button provided in the list. Execute callbacks for the pressed buttons."""
        for button_tuple in self.button_list:
            pin_number = button_tuple[0]
            callback = button_tuple[1]
            long_press_callback = button_tuple[2]
            maintained_action = button_tuple[3]
            normally_closed = button_tuple[4]
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
                    self.press_start_time[pin_number] = time.time()
                    if long_press_callback is not None:
                        # Schedule long press check after 5 seconds
                        self.long_press_timers[pin_number] = GLib.timeout_add(
                            5000, self._on_long_press_timeout, pin_number, long_press_callback
                        )
                elif not state and self.last_state[pin_number]:
                    self.last_state[pin_number] = False
                    if self.long_press_timers[pin_number] is not None:
                        # Cancel long press timer if button is released
                        GLib.source_remove(self.long_press_timers[pin_number])
                        self.long_press_timers[pin_number] = None
                    # Only call normal callback if not long pressed
                    if self.press_start_time[pin_number] is not None and (
                            time.time() - self.press_start_time[pin_number] < 5
                    ):
                        callback()
                    self.press_start_time[pin_number] = None
        return True

