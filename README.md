# Hardware

Die BMA-Steuerung ist dafür ausgelegt, auf einem Raspberry Pi ausgeführt zu werden. 
FAT und FBF werden über 5V, 3.3V und GND mit Strom versorgt und per I2C über die serielle Schnittstelle angesteuert. 
Die Platinen können anhand der beiliegenden KiCAD-Dateien hergestellt werden. 
Zusatzmodule wie eine Blitzleuchte oder ein FSD können nach Belieben hinzugefügt und in die Steuerung eingebunden werden.

# Software

## Abhängigkeiten

Zum Ausführen des Python-Scripts müssen Python 3.13 oder neuer und alle in requirements.txt 
definierten Abhängigkeiten installiert sein. 

Zusätzlich ist, wie im Kommentar in requirements.txt erwähnt, 
Okular notwendig, um die Hilfedatei anzeigen zu können. Dabei muss okular-extra-backends installiert werden, 
um Markdown-Dateien anzeigen zu können. Natürlich kann auch ein anderer Markdown-Viewer verwendet werden, 
wenn in Application.py die Konstante markdown-viewer entsprechend angepasst wird.  
Falls die Hilfedatei nach PDF konvertiert wird, bieten sich natürlich noch mehr Möglichkeiten. 
Markdown wurde lediglich aufgrund der besseren Integration in das Versionskontrollsystem ausgewählt.

## Konfiguration von labwc

Falls Raspberry Pi OS (oder ein anderes Betriebssystem mit labwc als Compositor) verwendet wird, 
sollten für ein einheitliches Design der Anwendung Client-Side-Decorations bevorzugt werden. 
Dazu muss in der labwc-Konfigurationsdatei (in der Regel /etc/xdg/labwc/rc.xml) 
die Variable <core><decorations> auf client gesetzt werden. 
Weitere Informationen dazu sind unter https://labwc.github.io/labwc-config.5.html#entry_core_decoration zu finden.  
In diesem Fall empfiehlt es sich auch, in /etc/xdg/labwc/environment die Umgebungsvariable 
QT_WAYLAND_DISABLE_WINDOWDECORATION=0 zu setzen, da ansonsten für Qt-Anwendungen wie Okular 
keine Kopfleiste mehr angezeigt wird.