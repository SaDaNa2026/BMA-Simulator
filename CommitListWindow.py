import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
from datetime import datetime


class ConfirmationAlert(Gtk.AlertDialog):
    def __init__(self):
        super().__init__()


class CommitBox(Gtk.Box):
    def __init__(self, commit: tuple, commit_index: int):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=20, homogeneous=True)
        self.commit_index = commit_index

        commit_date = str(datetime.fromtimestamp(commit[0]))
        self.date_label = Gtk.Label(label=commit_date)
        self.append(self.date_label)

        self.diff_list = commit[1]
        self.difference = ""
        for diff in self.diff_list:
            if len(self.difference) > 0:
                self.difference += f",\n"
            a_path = diff[0]
            b_path = diff[1]
            diff_type = diff[2]
            match diff_type:
                case 'A':
                    self.difference += f"{b_path} hinzugefügt"
                case 'D':
                    self.difference += f"{a_path} gelöscht"
                case 'M':
                    self.difference += f"{b_path} modifiziert"
                case 'R':
                    self.difference += f"{a_path} umbenannt in {b_path}"
                case 'T':
                    self.difference += f"{a_path}: Dateityp geändert"
                case 'C':
                    self.difference += f"{b_path} kopiert"
                case _:
                    self.difference += f"{a_path if a_path else b_path}: Unbekannte Änderung"

        self.diff_label = Gtk.Label(label=self.difference)
        self.append(self.diff_label)

        self.message_label = Gtk.Label(label=commit[2],
                                       width_chars=20,
                                       max_width_chars=30,
                                       wrap=True,
                                       halign=Gtk.Align.START)
        self.append(self.message_label)


class CommitListWindow(Gtk.Window):
    def __init__(self, parent, directory: str, commit_list: list, rollback_callback):
        super().__init__(modal=True, transient_for=parent, title=f"{directory} zurücksetzen...")
        self.rollback_callback = rollback_callback
        self.directory = directory

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                margin_top=5,
                                margin_bottom=5,
                                margin_start=5,
                                margin_end=5,
                                spacing=10)
        self.set_child(self.main_box)

        # ListBox to display all commits
        self.list_box = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE, show_separators=True)
        self.scrollable = Gtk.ScrolledWindow(child=self.list_box,
                                             vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                             hscrollbar_policy=Gtk.PolicyType.NEVER,
                                             vexpand=True,
                                             height_request=300)
        self.main_box.append(self.scrollable)

        # Add every commit to a new row in the ListBox
        index = 0
        for commit in commit_list:
            print(commit)
            commit_box = CommitBox(commit, index)
            self.list_box.append(commit_box)
            index += 1

        # Buttons to cancel or confirm
        self.confirmation_box = Gtk.CenterBox()
        self.main_box.append(self.confirmation_box)

        self.cancel_button = Gtk.Button(label="Schließen")
        self.cancel_button.connect("clicked", lambda button, *args: self.destroy())
        self.confirmation_box.set_start_widget(self.cancel_button)

        self.confirm_button = Gtk.Button(label="Zurücksetzen")
        self.confirm_button.connect("clicked", self.on_rollback_clicked)
        self.confirmation_box.set_end_widget(self.confirm_button)

    def on_rollback_clicked(self, *args):
        confirmation_alert = Gtk.AlertDialog(message="Dateistand zurücksetzen",
                                             detail=f"Wenn Sie fortfahren, gehen alle Änderungen\n"
                                                    f"nach dem ausgewählten Dateistand verloren.",
                                             buttons=["Abbrechen", "OK"])
        confirmation_alert.choose(self, None, self.on_confirm_clicked, None)

    def on_confirm_clicked(self, *args):
        selected_row = self.list_box.get_selected_row().get_child()
        if isinstance(selected_row, CommitBox):
            self.rollback_callback(self.directory, selected_row.commit_index)
            self.destroy()
        else:
            raise AttributeError