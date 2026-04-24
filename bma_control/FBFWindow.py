# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio
from ModalWindow import ModalWindow


class FBFSettingsItem(Gtk.Frame):
    def __init__(self, label: str, action_name: str) -> None:
        super().__init__(hexpand=True,
                         vexpand=False,
                         margin_start=10,
                         margin_end=10,
                         margin_top=10,
                         margin_bottom=10
                         )

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                spacing=10,
                                margin_start=10,
                                margin_end=10,
                                margin_top=10,
                                margin_bottom=10,
                                homogeneous=True
                                )
        self.set_child(self.main_box)

        self.label = Gtk.Label(label=label, halign=Gtk.Align.START)
        self.main_box.append(self.label)

        self.switch = Gtk.Switch(action_name=action_name, halign=Gtk.Align.END)
        self.main_box.append(self.switch)


class FBFWindow(ModalWindow):
    def __init__(self, parent, model, app):
        super().__init__(parent, title="FBF-Einstellungen")
        self.model = model
        self.app = app

        action_entries = [("extinguisher_triggered", None, None, "true" if self.model.get_extinguisher_triggered() else "false", self.on_extinguisher_triggered_toggled),
                          ("acoustic_signals_off", None, None, "true" if self.model.get_acoustic_signals_off() else "false", self.on_acoustic_signals_off_toggled),
                          ("ue_off", None, None, "true" if self.model.get_ue_off() else "false", self.on_ue_off_toggled),
                          ("fire_controls_off", None, None, "true" if self.model.get_fire_controls_off() else "false", self.on_fire_controls_off_toggled)]

        self.actions = Gio.SimpleActionGroup.new()
        self.actions.add_action_entries(action_entries, None)
        self.insert_action_group("fbf_settings", self.actions)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=True)
        self.set_child(self.main_box)

        self.extinguisher_triggered_item = FBFSettingsItem("Löschanlage ausgelöst", "fbf_settings.extinguisher_triggered")
        self.main_box.append(self.extinguisher_triggered_item)
        self.acoustic_signals_off_item = FBFSettingsItem("Akustische Signale ab", "fbf_settings.acoustic_signals_off")
        self.main_box.append(self.acoustic_signals_off_item)
        self.ue_triggered_item = FBFSettingsItem("ÜE ab", "fbf_settings.ue_off")
        self.main_box.append(self.ue_triggered_item)
        self.fire_controls_off_item = FBFSettingsItem("Brandfallsteuerungen ab", "fbf_settings.fire_controls_off")
        self.main_box.append(self.fire_controls_off_item)

    def on_extinguisher_triggered_toggled(self, action, parameter, *args):
        action.set_state(parameter)
        state = parameter.get_boolean()
        self.model.set_extinguisher_triggered(state)
        # Activate the hidden detector belonging to the extinguishers
        self.model.set_detector_alarm_status(0, 1, state)
        self.app.print_detector_state()
        self.app.lcd.reset()
        self.app.update_leds()

    def on_acoustic_signals_off_toggled(self, action, parameter, *args):
        action.set_state(parameter)
        state = parameter.get_boolean()
        self.model.set_acoustic_signals_off(state)
        self.app.update_leds()

    def on_ue_off_toggled(self, action, parameter, *args):
        action.set_state(parameter)
        state = parameter.get_boolean()
        self.model.set_ue_off(state)
        self.app.update_leds()

    def on_fire_controls_off_toggled(self, action, parameter, *args):
        action.set_state(parameter)
        state = parameter.get_boolean()
        self.model.set_fire_controls_off(state)
        self.app.update_leds()
