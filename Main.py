import sys

import gi
gi.require_version('Gtk', '4.0')

from GtkApp import App

bma_control = App(application_id="com.BMA.EXAMPLE")
bma_control.run(sys.argv)
