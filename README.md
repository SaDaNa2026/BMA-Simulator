# Hardware

Die Steuerung des BMA-SImulators ist dafür ausgelegt, auf einem Raspberry Pi ausgeführt zu werden. 
Getestet wurde mit einem Raspberry Pi 5B mit 8 GB RAM, die Anwendung sollte allerdings auch ohne Probleme 
auf einem Modell 4 mit 2 GB RAM laufen.

FAT und FBF werden durch den Raspberry Pi über 5V, 3.3V und GND mit Strom versorgt 
und per I2C über die serielle Schnittstelle angesteuert. 
Die Platinen können anhand der beiliegenden KiCAD-Dateien hergestellt werden. 
Zusatzmodule wie eine Blitzleuchte, ein Freischaltelement oder physische Melder können nach Belieben hinzugefügt 
und in die Steuerung eingebunden oder deaktiviert werden.

# Software

## Abhängigkeiten

Zum Ausführen des Python-Scripts müssen Python 3.13 oder neuer und alle in requirements.txt 
definierten Abhängigkeiten installiert sein. 

Zusätzlich ist Okular notwendig, um die Hilfedatei anzeigen zu können. Dabei muss okular-extra-backends installiert werden, 
um Markdown-Dateien anzeigen zu können. Natürlich kann auch ein anderer Markdown-Viewer verwendet werden, 
wenn in Application.py die Konstante MARKDOWN_VIEWER entsprechend angepasst wird.  
Falls die Hilfedatei nach PDF konvertiert wird, bieten sich noch mehr Möglichkeiten für die Anzeige. 
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

- Der Standard-Dateipfad für das Öffnen und Speichern von Dateien. Der Pfad sollte existieren, 
    andernfalls funktioniert die Anwendung aber trotzdem.
- Der Markdown-Viewer zur Anzeige der Hilfedatei (einzutragender Name entspricht dem in der Shell).
- Die Standard-Gebäudebeschreibung. Der Zeilenumbruch ist mit \n zu setzen. Die maximale Länge 
    einer Zeile beträgt 20 Zeichen.
- Eine PIN, mit der potenziell destruktive Aktionen wie Speichern oder Rollback gesichert werden. 
    Dies bietet ganz ausdrücklich keine wirkliche Sicherheit, sondern soll nur gegen Fehlbedienung absichern.
- GPIO-Pin und Pullup-Konfiguration für das Freischaltelement, das FSE kann hier auch abgeschaltet werden.
- Ein Tupel aller physischen Melder, die angeschlossen sind. Kommentar im Code beachten!  
    Falls keine physischen Melder vorhanden sind, kann hier auch einfach eine leere Liste zugewiesen werden.
- GPIO-Pin des Relais' für die Blitzleuchte, kann hier auch abgeschaltet werden.

## Integration von Git

Um den Dateistand zurücksetzen zu können, ist Git als Versionskontrollsystem integriert. Bei jedem Speichern
einer Gebäudekonfiguration oder eines Szenarios wird im entsprechenden Verzeichnis ein Repository initialisiert,
falls es nicht bereits eines ist. Anschließend werden alle Änderungen gestaget und committet. 
Über die Funktion "Dateistand zurücksetzen" gibt es dann die Möglichkeit, einen Hard Reset durchzuführen. 
Natürlich ist auch eine manuelle Verwaltung des Repositorys mithilfe von Git möglich.

Diese Integration macht einige Annahmen, die erfüllt werden sollten, um unerwünschte Folgen zu vermeiden:

- Für jede Gebäudekonfiguration mitsamt den dazugehörigen Szenarien existiert ein eigenes Verzeichnis (Gebäudeverzeichnis).
   Dabei können für Szenario-Dateien beliebig viele Unterverzeichnisse mit beliebiger Verschachtelung angelegt werden.
   In diesen Unterverzeichnissen dürfen jedoch keine Gebäudeverzeichnisse enthalten sein, denn:
- Gebäudeverzeichnisse dürfen nicht verschachtelt werden: Dadurch werden alle Änderungen im höhergeordneten Verzeichnis
   der beiden committet, wodurch keine saubere Trennung der Gebäude in den Commit-Messages mehr existiert.
- Es sollte ein eigenes Verzeichnis angelegt werden, das alle Gebäudeverzeichnisse bzw. Verzeichnisse 
   von Gebäudeverzeichnissen enthält. Dieses Verzeichnis sollte der Konstante DEFAULT_FILE_PATH 
   in Application.py entsprechen, wodurch sich die Öffnen- und Speicher-Dialoge direkt im richtigen Verzeichnis befinden.  
   Die Abschottung verhindert, dass andere, "unbeteiligte" Dateien in das Repository 
   aufgenommen werden oder ein Repository in einem Verzeichnis initialisiert wird, wo dies unerwünscht ist.