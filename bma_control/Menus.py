# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import gi

gi.require_version('GLib', '2.0')
from gi.repository import Gio, GLib


class TupleAddMenu(Gio.Menu):
    """Helper class to easily add menu items"""

    def __init__(self, items: tuple) -> None:
        super().__init__()
        for item in items:
            self.append(*item)


class PrimaryMenu(TupleAddMenu):
    """Menu model for the primary menu"""

    def __init__(self):
        super().__init__((("Hilfe", "app.help"),
                          ("Über BMA-Simulator", "app.about"),
                          ("Speicherfunktionen freischalten", "app.unlock"),
                          ("Einstellungen", "app.settings"),
                          ("Bearbeitungsmodus", "app.edit_mode")))


class SaveMenu(TupleAddMenu):
    """Menu model for the "Save" MenuButton in the header bar"""

    def __init__(self):
        super().__init__((("Gebäudekonfiguration speichern.", "app.save_building"),
                          ("Szenario speichern", "app.save_scenario"),
                          ("Szenario-Tags verwalten...", "app.define_tags"),
                          ("Dateistand wiederherstellen...", "app.rollback")))


class OpenMenu(TupleAddMenu):
    """Menu model for the "Open" MenuButton in the header bar"""

    def __init__(self):
        super().__init__((("Datei öffnen...", "app.open"),
                          ("Szenario-Browser", "app.launch_scenario_browser")))


class EditMenu(TupleAddMenu):
    """Menu model for the "Bearbeiten" MenuButton in the header bar"""

    def __init__(self):
        super().__init__((("Meldergruppe hinzufügen...", "edit.create_circuit"),
                          ("Gebäudebeschreibung bearbeiten...", "edit.edit_building"),
                          ("FBF...", "edit.edit_fbf"),
                          ("Abschaltung leeren", "edit.clear_disabled"),
                          ("Historie leeren", "edit.clear_history"),
                          ("Leere Datei erstellen", "edit.clear_all")))


class CircuitContextMenu(Gio.Menu):
    """Menu model for the context menu that appears when right-clicking on a circuit"""

    def __init__(self, circuit_number):
        super().__init__()
        create_detector_item = Gio.MenuItem.new("Melder hinzufügen...", "edit.create_detector")
        create_detector_item.set_attribute_value("target", GLib.Variant("i", circuit_number))
        self.append_item(create_detector_item)
        delete_circuit_item = Gio.MenuItem.new("Meldergruppe löschen", "edit.delete_circuit")
        delete_circuit_item.set_attribute_value("target", GLib.Variant("i", circuit_number))
        self.append_item(delete_circuit_item)


class DetectorContextMenu(Gio.Menu):
    """Menu model for the context menu that appears when right-clicking on a detector"""

    def __init__(self, circuit_number, detector_number):
        super().__init__()
        edit_detector_item = Gio.MenuItem.new("Beschreibung bearbeiten...", "edit.edit_detector")
        edit_detector_item.set_attribute_value("target", GLib.Variant("s", f"{circuit_number}, {detector_number}"))
        self.append_item(edit_detector_item)
        disable_detector_item = Gio.MenuItem.new("Abschaltung",
                                                 f"detector.enable_detector_{circuit_number}_{detector_number}")
        self.append_item(disable_detector_item)
        history_detector_item = Gio.MenuItem.new("In Historie",
                                                 f"detector.in_history_{circuit_number}_{detector_number}")
        self.append_item(history_detector_item)
        delete_detector_item = Gio.MenuItem.new("Melder löschen", "edit.delete_detector")
        delete_detector_item.set_attribute_value("target", GLib.Variant("s", f"{circuit_number}, {detector_number}"))
        self.append_item(delete_detector_item)
