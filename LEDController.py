import gi
gi.require_version("GLib", "2.0")
from gi.repository import GLib
from mcp23017 import *


class LEDController:
    def __init__(self, mcp_object, led_pins):
        self.mcp = mcp_object
        self.led_pins = led_pins

        self.led_status = {}
        for key in self.led_pins.keys():
            self.led_status[key] = LOW
            self.mcp.digital_write(self.led_pins[key], LOW)

        self.led_blinking = {}
        for key in self.led_pins.keys():
            self.led_blinking[key] = False

        # Keep track of blinking LED's state and start the blinking function
        self.blink_on = False
        GLib.timeout_add(500, self.blink)

    def turn_on(self, led: str):
        self.mcp.digital_write(self.led_pins[led], HIGH)

    def turn_off(self, led: str):
        self.mcp.digital_write(self.led_pins[led], LOW)

    def blink(self):
        """Checks which LEDs need to blink and toggles their state."""
        for led in self.led_pins:
            if self.led_blinking[led]:
                if self.blink_on:
                    self.led_status[led] = LOW
                    self.turn_off(led)
                else:
                    self.led_status[led] = HIGH
                    self.turn_on(led)
        self.blink_on = not self.blink_on
        return True


    def start_blink(self, led: str):
        """Set the specified LED to blink."""
        self.led_blinking[led] = True

    def stop_blink(self, led: str):
        """Turn off blinking for the specified LED."""
        self.led_blinking[led] = False
        self.turn_off(led)

    def shutdown(self):
        """Turn off all LEDs."""
        for led in self.led_pins:
            self.stop_blink(led)
            self.led_status[led] = LOW
            self.turn_off(led)
