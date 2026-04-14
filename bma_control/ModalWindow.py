# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

class ModalWindow(Gtk.Window):
    def __init__(self, parent, resizable=False, **kwargs):
        super().__init__(modal=True,
                         transient_for=parent,
                         resizable=resizable,
                         **kwargs)
        self.close_shortcut = Gtk.Shortcut(
                    action=Gtk.CallbackAction.new(self.close_callback),
                    trigger=Gtk.ShortcutTrigger.parse_string("<Ctrl>W|Escape")
                )
        self.add_shortcut(self.close_shortcut)

    def close_callback(self, *args) ->bool:
        self.destroy()
        return False