from gi.repository import Gio, GLib


class DataMenu(Gio.Menu):
    """Menu model for the "Data" MenuButton in the header bar."""
    def __init__(self):
        super().__init__()
        save_building_item = Gio.MenuItem.new("Gebäudekonfiguration speichern", "win.save_building")
        self.append_item(save_building_item)
        save_scenario_item = Gio.MenuItem.new("Szenario speichern", "win.save_scenario")
        self.append_item(save_scenario_item)
        open_item = Gio.MenuItem.new("Datei öffnen", "win.open")
        self.append_item(open_item)
        edit_mode_item = Gio.MenuItem.new("Bearbeitungsmodus", "win.edit_mode")
        self.append_item(edit_mode_item)


class CircuitContextMenu(Gio.Menu):
    """Menu model for the context menu that appears when right-clicking on a circuit."""
    def __init__(self, circuit_number):
        super().__init__()
        create_detector_item = Gio.MenuItem.new("Melder hinzufügen", "win.create_detector")
        create_detector_item.set_attribute_value("target", GLib.Variant("i", circuit_number))
        self.append_item(create_detector_item)
        delete_circuit_item = Gio.MenuItem.new("Melderlinie löschen", "win.delete_circuit")
        delete_circuit_item.set_attribute_value("target", GLib.Variant("i", circuit_number))
        self.append_item(delete_circuit_item)


class DetectorContextMenu(Gio.Menu):
    """Menu model for the context menu that appears when right-clicking on a detector."""
    def __init__(self, circuit_number, detector_number):
        super().__init__()
        edit_detector_item = Gio.MenuItem.new("Melder bearbeiten", "win.edit_detector")
        edit_detector_item.set_attribute_value("target", GLib.Variant("s", f"{circuit_number}, {detector_number}"))
        self.append_item(edit_detector_item)
        delete_detector_item = Gio.MenuItem.new("Melder löschen", "win.delete_detector")
        delete_detector_item.set_attribute_value("target", GLib.Variant("s", f"{circuit_number}, {detector_number}"))
        self.append_item(delete_detector_item)
