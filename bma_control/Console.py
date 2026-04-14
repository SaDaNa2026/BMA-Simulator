# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class Console(Gtk.Frame):
    def __init__(self, label):
        super().__init__(label=label, hexpand=True)
        self.buffer = Gtk.TextBuffer()
        self.console = Gtk.TextView(editable=False,
                                    buffer=self.buffer,
                                    cursor_visible=False,
                                    left_margin=10,
                                    top_margin=10,
                                    monospace=True)
        self.set_child(self.console)