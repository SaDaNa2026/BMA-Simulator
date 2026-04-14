# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gio, Gtk



class FileOpenDialog(Gtk.FileDialog):
    """A FileDialog configured for opening files."""
    def __init__(self, last_dir = Gio.File.new_for_path("/home/lfs-bma")):
        super().__init__(title="Konfiguration laden",
                       accept_label="Öffnen",
                       initial_folder=last_dir,
                       modal=True)

        # Add a file filter for the extensions used by this application
        extension_filter = Gtk.FileFilter()
        extension_filter.add_pattern("*.building")
        extension_filter.add_pattern("*.scenario")
        self.set_default_filter(extension_filter)