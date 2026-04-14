import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
from ModalWindow import ModalWindow

class AboutWindow(ModalWindow):
    def __init__(self, parent):
        super().__init__(parent,
                         title="Über BMA-Simulator")
        self.main_box = Gtk.Box(spacing=10,
                                orientation=Gtk.Orientation.VERTICAL,
                                margin_top=5,
                                margin_bottom=5,
                                margin_start=5,
                                margin_end=5)
        self.set_child(self.main_box)

        self.info_label = Gtk.Label(label=f"Diese App dient zur Steuerung der Übungs-BMA.\n"
                                          f"Für weitere Informationen öffnen Sie die Hilfedatei (F1 drücken). \n\n"
                                          f"Entwickler-Email: sadana2026@tutamail.com")
        self.main_box.append(self.info_label)
