# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
                                          f"Entwickler: Samuel Namyslo(sadana2026@tutamail.com)")
        self.main_box.append(self.info_label)
