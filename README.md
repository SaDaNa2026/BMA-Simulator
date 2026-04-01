# Hardware

Die BMA-Steuerung ist dafür ausgelegt, auf einem Raspberry Pi ausgeführt zu werden. 
FAT und FBF werden über 5V, 3.3V und GND mit Strom versorgt und per I2C über die serielle Schnittstelle angesteuert. 
Die Platinen können anhand der beiliegenden KiCAD-Dateien hergestellt werden. 
Zusatzmodule wie eine Blitzleuchte können nach Belieben hinzugefügt und in die Steuerung eingebunden 
oder deaktiviert werden.

# Software

## Abhängigkeiten

Zum Ausführen des Python-Scripts müssen Python 3.13 oder neuer und alle in requirements.txt 
definierten Abhängigkeiten installiert sein. 

Zusätzlich ist Okular notwendig, um die Hilfedatei anzeigen zu können. Dabei muss okular-extra-backends installiert werden, 
um Markdown-Dateien anzeigen zu können. Natürlich kann auch ein anderer Markdown-Viewer verwendet werden, 
wenn in Application.py die Konstante MARKDOWN_VIEWER entsprechend angepasst wird.  
Falls die Hilfedatei nach PDF konvertiert wird, bieten sich natürlich noch mehr Möglichkeiten. 
Markdown wurde lediglich aufgrund der besseren Integration in das Versionskontrollsystem ausgewählt.

## Desktopeintrag

Es liegt ein Beispiel für eine passende Desktopeintrags-Datei bei. Wenn die in der Datei angegebenen Anpassungen 
erfolgt sind, kann die Datei im entsprechenden Ordner (z.B. /usr/local/share/applications/) abgelegt werden.  
Falls ein Autostart der App erwünscht ist, kann der Desktopeintrag zusätzlich noch in /etc/xdg/autostart/ abgelegt werden.

## Startskript

Da sich alle Python-Pakete und Skripte in einer virtuellen Umgebung befinden, muss diese beim Programmstart erst 
aktiviert werden. Daher ist ein Startskript nötig, das diese Aufgabe übernimmt. Ein entsprechendes Beispiel liegt bei, 
es muss nur der Pfad zum Anwendungsordner angepasst werden. Das Skript kann dann z.B. in /usr/local/bin abgelegt werden.

Für den Fall, dass alle Python-Pakete systemweit installiert sind (ohne virtuelle Umgebung), 
entfällt die Notwendigkeit des Startskripts. Man verliert dann aber natürlich auch alle Vorteile 
der Separierung durch virtuelle Umgebungen.

## Konfiguration von labwc

Falls Raspberry Pi OS (oder ein anderes Betriebssystem mit labwc als Compositor) verwendet wird, 
sollten für ein einheitliches Design der Anwendung Client-Side-Decorations bevorzugt werden. 
Dazu muss in der labwc-Konfigurationsdatei (in der Regel /etc/xdg/labwc/rc.xml) 
die Variable <core><decorations> auf client gesetzt werden. 
Weitere Informationen dazu sind unter https://labwc.github.io/labwc-config.5.html#entry_core_decoration zu finden.  
In diesem Fall empfiehlt es sich auch, in /etc/xdg/labwc/environment die Umgebungsvariable 
QT_WAYLAND_DISABLE_WINDOWDECORATION=0 zu setzen, da ansonsten für Qt-Anwendungen wie Okular 
keine Kopfleiste mehr angezeigt wird.

## Konstanten

In Application.py werden unterhalb der Imports einige Konstanten definiert, mit denen die Anwendung 
an die Umgebung angepasst werden kann. Verfügbar sind:

- Der Standard-Dateipfad
- Der Markdown-Viewer zur Anzeige der Hilfedatei (einzutragender Name entspricht dem in der Shell)
- GPIO-Pin und Pullup-Konfiguration für das Freischaltelement, das FSE kann hier auch abgeschaltet werden
- GPIO-Pin des Relais' für die Blitzleuchte, kann hier auch abgeschaltet werden