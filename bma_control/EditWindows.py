# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
from ModalWindow import ModalWindow
from DescriptionBox import DescriptionBox

class EditWindow(ModalWindow):
    """Base class for a window that lets the user edit a description."""
    def __init__(self, edit_callback, parent, title, default_text: str="", max_length: int | None=None, description_box_label: str="Beschreibung", **kwargs):
        super().__init__(parent, default_width=350, default_height= 100, title=title, **kwargs)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                margin_top=5,
                                margin_bottom=5,
                                margin_start=5,
                                margin_end=5,
                                spacing=10)
        self.set_child(self.main_box)

        self.description_box = DescriptionBox(default_text, max_length, description_box_label)
        self.main_box.append(self.description_box)

        # Buttons to cancel or confirm
        self.confirmation_box = Gtk.CenterBox()
        self.main_box.append(self.confirmation_box)

        self.cancel_button = Gtk.Button(label="Abbrechen")
        self.cancel_button.connect("clicked", lambda button, *args: self.destroy())
        self.confirmation_box.set_start_widget(self.cancel_button)

        self.confirm_button = Gtk.Button(label="Bestätigen")
        self.confirm_button.connect("clicked", edit_callback)
        self.confirmation_box.set_end_widget(self.confirm_button)
        # Set the confirm button as default widget so it is activated when Enter is pressed inside the Entry
        self.set_default_widget(self.confirm_button)

        # Label to display an error if the description is too long
        self.warning_label = Gtk.Label()

    def get_description(self):
        """Remove old warnings and parse the description from description_box"""
        if self.warning_label.get_parent():
            self.main_box.remove(self.warning_label)

        description = self.description_box.get_description()
        return description



class EditDetectorWindow(EditWindow):
    """Window for editing the description of a detector"""
    def __init__(self, circuit_number, detector_number, current_description, edit_detector_callback, parent, **kwargs):
        self.circuit_number = circuit_number
        self.detector_number = detector_number
        title = f"Bearbeite Melder {detector_number} (Gruppe {circuit_number})"
        super().__init__(lambda button, *args: self.handle_edit(edit_detector_callback),
                         parent,
                         title,
                         current_description,
                         max_length=20,
                         **kwargs)

    def handle_edit(self, edit_detector_callback):
        description = self.get_description()
        try:
            edit_detector_callback(self.circuit_number, self.detector_number, description)
            self.destroy()
        except ValueError as e:
            self.warning_label.set_markup(f"<span foreground='red'>{e}</span>")
            self.main_box.insert_child_after(self.warning_label, self.description_box)


class EditBuildingWindow(EditWindow):
    """Window for editing the building description"""
    def __init__(self, current_description, edit_building_callback, parent, **kwargs):
        title = f"Gebäudebeschreibung bearbeiten"

        # Split the description into lines 0 and 1
        line_list: list = current_description.split("\n")
        line_0: str = line_list[0]
        if len(line_list) > 1:
            line_1: str = line_list[1]
        else:
            line_1: str = ""

        super().__init__(lambda button, *args: self.handle_edit(edit_building_callback),
                         parent,
                         title,
                         line_0,
                         max_length=20,
                         description_box_label="Zeile 1:",
                         **kwargs)

        # Add a second description box for the second line of the building description
        self.description_box_1 = DescriptionBox(line_1, 20, label="Zeile 2:")
        self.main_box.insert_child_after(self.description_box_1, self.description_box)

    def get_description(self):
        """Remove old warnings and parse the description from the description boxes"""
        if self.warning_label.get_parent():
            self.main_box.remove(self.warning_label)

        line_0: str = self.description_box.get_description()
        line_1: str = self.description_box_1.get_description()
        description: str = line_0 + "\n" + line_1
        return description

    def handle_edit(self, edit_building_callback):
        description = self.get_description()
        try:
            edit_building_callback(description)
            self.destroy()
        except ValueError as e:
            self.warning_label.set_markup(f"<span foreground='red'>{e}</span>")
            self.main_box.insert_child_after(self.warning_label, self.description_box_1)


class CodeInputWindow(EditWindow):
    def __init__(self, confirm_callback, parent, unlock_action):
        """Window for putting in a pin. confirm_callback should be the function that checks the pin and starts the
        protected functionality. It should return True to signal success and False to signal a wrong pin."""
        super().__init__(lambda button, *args: self.handle_edit(confirm_callback, unlock_action),
                         parent,
                         "PIN eingeben")

        self.description_box.description_entry.set_visibility(False)

    def handle_edit(self, confirm_callback, unlock_action):
        """Get the pin entry and pass it to confirm_callback.
        Destroy self if the pin was correct, display an error otherwise"""
        code = self.get_description()

        if confirm_callback(unlock_action, code):
            self.destroy()
        else:
            self.warning_label.set_markup("<span foreground='red'>Falsche PIN</span>")
            self.main_box.insert_child_after(self.warning_label, self.description_box)


class EditCommitMessageWindow(ModalWindow):
    """Window for entering a commit message."""
    def __init__(self, finish_callback, file_type, parent, **kwargs):
        title = "Änderungen beschreiben..."
        super().__init__(parent, title=title, resizable=True, **kwargs)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                margin_top=5,
                                margin_bottom=5,
                                margin_start=5,
                                margin_end=5,
                                spacing=10)
        self.set_child(self.main_box)

        self.description_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.main_box.append(self.description_box)

        self.description_label = Gtk.Label(label="Änderungen beschreiben:")

        # Use a scrollable TextView to allow multiline commit messages
        self.description_scrolled_window = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                                              vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                                              propagate_natural_width=True,
                                                              propagate_natural_height=True)
        self.description_box.append(self.description_scrolled_window)
        self.description_textview = Gtk.TextView(hexpand=True,
                                                 vexpand=True,
                                                 height_request=200,
                                                 width_request=500,
                                                 wrap_mode=Gtk.WrapMode.WORD)
        self.description_scrolled_window.set_child(self.description_textview)
        self.textbuffer = self.description_textview.get_buffer()

        # Buttons to cancel or confirm
        self.confirmation_box = Gtk.CenterBox()
        self.main_box.append(self.confirmation_box)

        self.cancel_button = Gtk.Button(label="Abbrechen")
        self.cancel_button.connect("clicked", lambda button, *args: self.destroy())
        self.confirmation_box.set_start_widget(self.cancel_button)

        self.confirm_button = Gtk.Button(label="Bestätigen")
        self.confirm_button.connect("clicked", lambda button, *args: self.handle_edit(finish_callback, file_type))
        self.confirmation_box.set_end_widget(self.confirm_button)

    def get_description(self):
        """Get the content of the TextView"""
        start = self.textbuffer.get_start_iter()
        end = self.textbuffer.get_end_iter()
        description = self.textbuffer.get_text(start, end, True)
        return description

    def handle_edit(self, commit_callback, file_type):
        message = self.get_description()
        commit_callback(message, file_type)
        self.destroy()