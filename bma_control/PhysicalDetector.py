import gpiozero


class PhysicalDetector(gpiozero.Button):
    def __init__(self, gpio_pin: int, pull_up: bool, circuit_number: int, detector_number: int) -> None:
        super().__init__(gpio_pin, pull_up=pull_up)
        self.circuit_number: int = circuit_number
        self.detector_number: int = detector_number
        self.last_state: bool = False