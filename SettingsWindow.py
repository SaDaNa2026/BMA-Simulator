import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gio, GLib

from ModalWindow import ModalWindow


class HistoryTimeFrame(Gtk.Frame):
    def __init__(self, history_time_mode: str, history_time_offset: int, history_time_absolute: tuple) -> None:
        super().__init__(label="Uhrzeit der Historie")
        # Convert time information to str for display in the entries
        offset_string = str(history_time_offset)
        # Add a leading zero to the hour and minute string if it's single-digit
        hour_string = str(history_time_absolute[0])
        if len(hour_string) == 1:
            hour_string = "0" + hour_string
        minute_string = str(history_time_absolute[1])
        if len(minute_string) == 1:
            minute_string = "0" + minute_string

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                margin_top=5,
                                margin_bottom=5,
                                spacing=5)
        self.set_child(self.main_box)

        # Box for the "automatic" option
        self.automatic_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                     margin_start=20)
        self.main_box.append(self.automatic_box)
        self.automatic_button = Gtk.CheckButton(label="Automatisch vor",
                                                action_name="settings.history_time_mode",
                                                action_target=GLib.Variant("s", "automatic"))
        self.automatic_box.append(self.automatic_button)

        self.offset_entry = Gtk.Entry(margin_start=5,
                                      max_length=2,
                                      input_purpose=Gtk.InputPurpose.DIGITS,
                                      max_width_chars=2,
                                      sensitive=True if history_time_mode == "automatic" else False,
                                      text=offset_string,
                                      xalign=0.5)
        self.offset_entry.connect_after("changed", self.validate_input, 99)
        self.automatic_box.append(self.offset_entry)

        self.offset_label = Gtk.Label(label="Minuten",
                                      margin_start=5)
        self.automatic_box.append(self.offset_label)


        # Box for the "user defined" option
        self.user_defined_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                        margin_start=20)
        self.main_box.append(self.user_defined_box)
        self.user_defined_button = Gtk.CheckButton(label="Benutzerdefiniert um",
                                                   group=self.automatic_button,
                                                   action_name="settings.history_time_mode",
                                                   action_target=GLib.Variant("s", "user_defined"))
        self.user_defined_box.append(self.user_defined_button)
        self.hour_entry = Gtk.Entry(margin_start=5,
                                    max_length=2,
                                    input_purpose=Gtk.InputPurpose.DIGITS,
                                    max_width_chars=2,
                                    sensitive=True if history_time_mode == "user_defined" else False,
                                    text=hour_string,
                                    xalign=0.5)
        self.hour_entry.connect("changed", self.validate_input, 23)
        self.user_defined_box.append(self.hour_entry)
        self.colon_label = Gtk.Label(label=":")
        self.user_defined_box.append(self.colon_label)
        self.minute_entry = Gtk.Entry(max_length=2,
                                      input_purpose=Gtk.InputPurpose.DIGITS,
                                      max_width_chars=2,
                                      sensitive=True if history_time_mode == "user_defined" else False,
                                      text=minute_string,
                                      xalign=0.5)
        self.minute_entry.connect("changed", self.validate_input, 59)
        self.user_defined_box.append(self.minute_entry)

    def validate_input(self, entry, limit):
        """Changes the CSS class of the entry to error if the input contains non-digit characters"""
        text = entry.get_text()
        if text.isdigit():
            if int(text) <= limit:
                entry.remove_css_class("error")
            else:
                entry.add_css_class("error")
        else:
            entry.add_css_class("error")


class SwitchFrame(Gtk.Frame):
    def __init__(self, action_name: str, switch_label: str) -> None:
        super().__init__()
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                spacing=5,
                                margin_top=5,
                                margin_bottom=5,
                                margin_start=5,
                                margin_end=5)
        self.set_child(self.main_box)
        self.switch = Gtk.Switch(action_name=action_name)
        self.main_box.append(self.switch)
        self.label = Gtk.Label(label=switch_label)
        self.main_box.append(self.label)


class SettingsWindow(ModalWindow):
    def __init__(self, parent, model, refresh_lcd, update_leds, **kwargs):
        super().__init__(parent, title="Einstellungen", **kwargs)
        self.model = model
        self.refresh_lcd = refresh_lcd
        self.update_leds = update_leds
        history_time_mode = self.model.get_history_time_mode()

        # Add an action to keep track of the radio buttons
        self.history_time_mode_action = Gio.SimpleAction.new_stateful("history_time_mode",
                                                                 GLib.VariantType("s"),
                                                                 GLib.Variant("s", history_time_mode))
        self.history_time_mode_action.connect("change-state", self.on_history_time_mode_changed)
        self.beeper_enabled_action = Gio.SimpleAction.new_stateful("beeper_enabled",
                                                                   None,
                                                                   GLib.Variant("b", self.model.get_beeper_enabled()))
        self.action_group = Gio.SimpleActionGroup.new()
        self.action_group.insert(self.history_time_mode_action)
        self.action_group.insert(self.beeper_enabled_action)
        self.insert_action_group("settings", self.action_group)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.main_box)

        self.list_box = Gtk.ListBox(show_separators=False,
                                    selection_mode=Gtk.SelectionMode.NONE,
                                    margin_top=5,
                                    margin_bottom=5)
        self.main_box.append(self.list_box)

        # Frame with settings for the history time
        self.history_time_frame = HistoryTimeFrame(history_time_mode, self.model.get_history_time_offset(), self.model.get_history_time_absolute())
        self.list_box.append(self.history_time_frame)

        # Switch to control beeper_enabled
        self.beeper_enabled_frame = SwitchFrame("settings.beeper_enabled", "Summer bei Alarm aktivieren")
        self.list_box.append(self.beeper_enabled_frame)

        # Box with buttons to cancel, apply or confirm
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                  spacing=10,
                                  margin_start=50,
                                  margin_end=5,
                                  margin_top=5,
                                  margin_bottom=5)
        self.main_box.append(self.button_box)

        self.cancel_button = Gtk.Button(label="Abbrechen", halign=Gtk.Align.END)
        self.cancel_button.connect("clicked", lambda button, *args: self.destroy())
        self.button_box.append(self.cancel_button)

        self.apply_button = Gtk.Button(label="Anwenden", halign=Gtk.Align.END)
        self.apply_button.connect("clicked", lambda button, *args: self.on_apply_clicked())
        self.button_box.append(self.apply_button)

        self.confirm_button = Gtk.Button(label="OK", halign=Gtk.Align.END)
        self.confirm_button.connect("clicked", lambda button, *args: self.on_confirm_clicked())
        self.button_box.append(self.confirm_button)

    def on_history_time_mode_changed(self, action, parameter, *args):
        action.set_state(parameter)

        if parameter.get_string() == "automatic":
            self.history_time_frame.offset_entry.set_sensitive(True)
            self.history_time_frame.hour_entry.set_sensitive(False)
            self.history_time_frame.minute_entry.set_sensitive(False)

        elif parameter.get_string() == "user_defined":
            self.history_time_frame.offset_entry.set_sensitive(False)
            self.history_time_frame.hour_entry.set_sensitive(True)
            self.history_time_frame.minute_entry.set_sensitive(True)

    def validate_settings(self) -> bool:
        entries = ((self.history_time_frame.offset_entry.get_text(), 99),
                   (self.history_time_frame.hour_entry.get_text(), 23),
                    (self.history_time_frame.minute_entry.get_text(), 59))

        for entry_tuple in entries:
            entry = entry_tuple[0]
            limit = entry_tuple[1]
            if not entry.isdigit():
                return False
            elif int(entry) < 0 or int(entry) > limit:
                return False

        return True

    def on_apply_clicked(self):
        """Apply settings and keep the window open"""
        self.apply_settings()

    def on_confirm_clicked(self):
        """Apply settings and close the window"""
        if self.apply_settings():
            self.destroy()

    def apply_settings(self) -> bool:
        if self.validate_settings():
            # Apply history time settings
            history_time_mode_action = self.action_group.lookup_action("history_time_mode")
            self.model.set_history_time_mode(history_time_mode_action.get_state().get_string())
            self.model.set_history_time_offset(int(self.history_time_frame.offset_entry.get_text()))
            hour = int(self.history_time_frame.hour_entry.get_text())
            minute = int(self.history_time_frame.minute_entry.get_text())
            self.model.set_history_time_absolute((hour, minute))

            # Apply beeper settings
            beeper_enabled_action = self.action_group.lookup_action("beeper_enabled")
            self.model.set_beeper_enabled(beeper_enabled_action.get_state().get_boolean())

            self.refresh_lcd()
            self.update_leds()
            return True
        else:
            return False
