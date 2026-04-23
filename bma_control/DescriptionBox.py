# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class DescriptionBox(Gtk.Box):
    """Contains a label and a textview. Can be used where the user can edit a description."""
    def __init__(self, default_text: str="", max_length: int=None, label: str="Beschreibung") -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.description_label = Gtk.Label(label=label)
        self.append(self.description_label)

        self.description_entry = Gtk.Entry(activates_default=True)
        if max_length is not None:
            self.description_entry.set_max_length(max_length)
            self.description_entry.set_max_width_chars(max_length)
        self.append(self.description_entry)
        self.description_entry.set_text(default_text)

    def get_description(self) -> str:
        """Get the content of the Entry"""
        return self.description_entry.get_text()