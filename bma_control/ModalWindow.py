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