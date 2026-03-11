import gi
gi.require_version('GLib', '2.0')
from gi.repository import Gio, GLib

class PrimaryMenu(Gio.Menu):
    """Menu model for the primary menu"""
    def __init__(self):
        super().__init__()
        help_item = Gio.MenuItem.new("Hilfe", "app.help")
        self.append_item(help_item)
        about_item = Gio.MenuItem.new("Über BMA-Steuerung", "app.about")
        self.append_item(about_item)

class DataMenu(Gio.Menu):
    """Menu model for the "Data" MenuButton in the header bar."""
    def __init__(self):
        super().__init__()
        save_building_item = Gio.MenuItem.new("Gebäudekonfiguration speichern...", "app.save_building")
        self.append_item(save_building_item)
        save_scenario_item = Gio.MenuItem.new("Szenario speichern...", "app.save_scenario")
        self.append_item(save_scenario_item)
        open_item = Gio.MenuItem.new("Datei öffnen...", "app.open")
        self.append_item(open_item)
        rollback_item = Gio.MenuItem.new("Dateistand wiederherstellen...", "app.rollback")
        self.append_item(rollback_item)
        edit_mode_item = Gio.MenuItem.new("Bearbeitungsmodus", "app.edit_mode")
        self.append_item(edit_mode_item)


class EditMenu(Gio.Menu):
    """Menu model for the "Bearbeiten" MenuButton in the header bar."""
    def __init__(self):
        super().__init__()
        create_circuit_item = Gio.MenuItem.new("Meldergruppe hinzufügen...", "edit.create_circuit")
        self.append_item(create_circuit_item)
        edit_building_item = Gio.MenuItem.new("Gebäudebeschreibung bearbeiten...", "edit.edit_building")
        self.append_item(edit_building_item)
        edit_fbf_item = Gio.MenuItem.new("FBF...", "edit.edit_fbf")
        self.append_item(edit_fbf_item)
        clear_disabled_item = Gio.MenuItem.new("Abschaltung leeren", "edit.clear_disabled")
        self.append_item(clear_disabled_item)
        clear_history_item = Gio.MenuItem.new("Historie leeren", "edit.clear_history")
        self.append_item(clear_history_item)


class CircuitContextMenu(Gio.Menu):
    """Menu model for the context menu that appears when right-clicking on a circuit."""
    def __init__(self, circuit_number):
        super().__init__()
        create_detector_item = Gio.MenuItem.new("Melder hinzufügen...", "edit.create_detector")
        create_detector_item.set_attribute_value("target", GLib.Variant("i", circuit_number))
        self.append_item(create_detector_item)
        delete_circuit_item = Gio.MenuItem.new("Meldergruppe löschen", "edit.delete_circuit")
        delete_circuit_item.set_attribute_value("target", GLib.Variant("i", circuit_number))
        self.append_item(delete_circuit_item)


class DetectorContextMenu(Gio.Menu):
    """Menu model for the context menu that appears when right-clicking on a detector."""
    def __init__(self, circuit_number, detector_number):
        super().__init__()
        edit_detector_item = Gio.MenuItem.new("Beschreibung bearbeiten...", "edit.edit_detector")
        edit_detector_item.set_attribute_value("target", GLib.Variant("s", f"{circuit_number}, {detector_number}"))
        self.append_item(edit_detector_item)
        disable_detector_item = Gio.MenuItem.new("Abschaltung", f"detector.enable_detector_{circuit_number}_{detector_number}")
        self.append_item(disable_detector_item)
        history_detector_item = Gio.MenuItem.new("In Historie", f"detector.in_history_{circuit_number}_{detector_number}")
        self.append_item(history_detector_item)
        delete_detector_item = Gio.MenuItem.new("Melder löschen", "edit.delete_detector")
        delete_detector_item.set_attribute_value("target", GLib.Variant("s", f"{circuit_number}, {detector_number}"))
        self.append_item(delete_detector_item)
