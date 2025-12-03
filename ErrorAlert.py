import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class ErrorAlert:
    @staticmethod
    def show(parent, error_message, error_detail):
        """Display an error alert."""
        error_alert = Gtk.AlertDialog(message=error_message, detail=error_detail, modal=True)
        error_alert.show(parent)


