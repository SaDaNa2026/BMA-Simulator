import gi
gi.require_version("GLib", "2.0")
from gi.repository import GLib
from mcp23017 import *
from functools import partial


class LEDController:
    def __init__(self, mcp_object, led_pins):
        self.mcp = mcp_object
        self.led_pins = led_pins
        self.blink_interval = 500

        self.led_status = {}
        for key in self.led_pins.keys():
            self.led_status[key] = LOW
            self.mcp.digital_write(self.led_pins[key], LOW)

        self.led_blinking = {}
        for key in self.led_pins.keys():
            self.led_blinking[key] = False


    def blink(self, led: str):
        print("blink")
        if self.led_blinking[led] and self.led_status[led] == LOW:
                self.led_status[led] = HIGH
                self.mcp.digital_write(self.led_pins[led], HIGH)
                return True
        else:
            self.led_status[led] = LOW
            self.mcp.digital_write(self.led_pins[led], LOW)
            if self.led_blinking[led]:
                return True
            else:
                return False

    def start_blink(self, led: str):
        self.led_blinking[led] = True
        GLib.timeout_add(self.blink_interval, partial(self.blink, led))

    def stop_blink(self, led: str):
        self.led_blinking[led] = False

    def shutdown(self):
        for led in self.led_pins:
            self.stop_blink(led)
            self.led_status[led] = LOW
            self.mcp.digital_write(self.led_pins[led], LOW)
