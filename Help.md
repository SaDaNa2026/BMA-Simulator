# Übersicht

Die BMA-Steuerung dient zur Steuerung und Konfiguration der Übungs-BMA an der Landesfeuerwehrschule 
Baden-Württemberg. 
Es können jederzeit dynamisch neue Meldergruppen und Melder erstellt oder gelöscht, 
Melder ausgelöst oder abgeschaltet und LEDs am FBF gesteuert werden.

Dabei können Gebäudekonfigurationen und Szenarien gespeichert und geladen werden. 
Die Gebäudekonfiguration speichert dabei, welche Meldergruppen und Melder existieren und 
welche Beschreibung diese haben. Das Szenario legt fest, welche Melder aktiviert oder abgeschaltet sind
und welche LEDs am FBF aktiv sind.

# Inhaltsverzeichnis

<!-- TOC -->
* [Übersicht](#übersicht)
* [Inhaltsverzeichnis](#inhaltsverzeichnis)
* [Dateistruktur](#dateistruktur)
* [Bedienung](#bedienung)
  * [Auslösen von Meldern](#auslösen-von-meldern)
  * [Laden von Dateien](#laden-von-dateien)
  * [Speichern](#speichern)
  * [Dateistand wiederherstellen](#dateistand-wiederherstellen)
  * [Bearbeitungsmodus](#bearbeitungsmodus)
    * [Button "Bearbeiten"](#button-bearbeiten)
    * [Rechtsklick auf Meldergruppen-Nummer](#rechtsklick-auf-meldergruppen-nummer)
    * [Rechtsklick auf Melder](#rechtsklick-auf-melder)
  * [Undo / Redo](#undo--redo)
<!-- TOC -->

# Dateistruktur

Für jedes Gebäude ist ein eigener Ordner anzulegen, in dem die Gebäudekonfiguration und alle 
dazugehörigen Szenarien gespeichert werden. Gebäudekonfigurationen haben die Endung ".building", 
Szenarien ".scenario". 
In jedem Ordner, in dem Szenarien gespeichert sind, muss genau eine Gebäudekonfiguration liegen. 
Ansonsten ist die Zuordnung eines Szenarios zur Konfiguration beim Laden nicht eindeutig und 
es wird eine Fehlermeldung angezeigt.

# Bedienung

## Auslösen von Meldern

Um einen Melder auszulösen, muss der Schalter neben der Meldernummer aktiviert (angeklickt) werden. 
Das versetzt die BMA in den Alarmzustand. Um mehrere Melder auszulösen, können diese 
in der gewünschten Reihenfolge angeklickt werden. Der Zustand der Melder wird im Szenario gespeichert.

Ausgelöste Melder können jederzeit über den Schalter wieder deaktiviert werden (hier: nicht abgeschaltet, 
sondern in einen nicht-ausgelösten Zustand versetzt). Im Gegensatz zur echten BMA verschwindet damit sofort 
die entsprechende Meldung vom FAT. Sobald keine Melder mehr aktiv sind, wechselt die BMA wieder in den Ruhezustand.

Informationen zur Abschaltung von Meldern finden sich im Abschnitt Bearbeitungsmodus - Rechtsklick auf Melder.

## Laden von Dateien

Zum Laden von vorkonfigurierten Gebäuden oder Szenarien kann die entsprechende Funktion 
unter dem Button "Datei" ausgewählt werden oder mit dem Tastenkürzel Strg+O aktiviert werden. 
Das Laden eines Szenarios lädt automatisch die entsprechende Gebäudekonfiguration.

## Speichern

Beim Speichern ist zwischen Gebäudekonfiguration (Strg+G) und Szenario (Strg+S) zu unterscheiden. 
Beide Optionen sind auch unter dem Button "Datei" verfügbar. 
Unabhängig davon müssen dann zuerst die Änderungen seit dem letzten Speichern beschrieben werden. 
Dies ist für ein eventuelles Zurücksetzen des Dateistands sehr wichtig, um Veränderungen nachvollziehen 
zu können, und sollte daher gewissenhaft betrieben werden.

Anschließend ist der Speicherort und Dateiname auszuwählen. Die Voreinstellung entspricht der letzten geöffneten Datei. 
Bei Veränderungen an einer Datei ist derselbe Dateiname wie zuvor zu wählen und die Warnung, 
dass eine gleichnamige Datei bereits existiert, mit "Ersetzen" zu bestätigen. 
Die Dateiendung ist bereits entsprechend der vorherigen Auswahl korrekt eingestellt; 
diese darf nicht verändert werden, da die Datei sonst nicht mehr geladen werden kann.

## Dateistand wiederherstellen

Diese Option findet sich unter dem Button "Datei". Falls ungewollte Änderungen 
an Dateien gespeichert wurden oder es anderweitig notwendig ist, lässt sich somit ein Ordner auf einen 
älteren Stand zurücksetzen. Dazu muss erst eine Datei aus dem betreffenden Ordner geladen werden, 
um festzulegen, welcher Ordner zurückgesetzt werden soll.

Wenn auf "Dateistand wiederherstellen" geklickt wird, erscheint ein Fenster, in dem alle bisherigen 
Speichervorgänge (Commits) im ausgewählten Ordner aufgelistet sind. Für jeden Commit wird die Zeit 
des Speicherns, die Veränderung und die beim Speichern eingegebene Beschreibung angezeigt. 
Durch Anklicken eines Listeneintrags wird dieser ausgewählt (angezeigt durch den blauen Hintergrund). 
Wenn nun auf "Wiederherstellen" geklickt wird, wird der Inhalt aller Dateien im Ordner 
auf den ausgewählten Stand zurückgesetzt.  
**Diese Aktion lässt sich nicht rückgängig machen.** 

Nach dem Zurücksetzen muss die Datei neu geladen werden, damit die Konfiguration die Änderungen reflektiert.

Anmerkung: Wenn manuelle Änderungen am Inhalt des Ordners durchgeführt werden 
(z.B. Umbenennen von Dateien), so werden diese gruppiert mit den in dieser Anwendung 
vorgenommenen Änderungen beim nächsten Speichervorgang im betreffenden Ordner als Commit aufgelistet.

## Bearbeitungsmodus

Um versehentliches Bearbeiten der Gebäudekonfiguration zu verhindern und die Benutzeroberfläche 
aufgeräumt zu halten, ist der Bearbeitungsmodus standardmäßig deaktiviert. Wenn der Bearbeitungsmodus 
deaktiviert ist, können als einzige Aktion Melder ausgelöst werden und natürlich alle Funktionen 
des FAT und FBF genutzt werden.

Der Bearbeitungsmodus kann unter dem Button "Datei" oder mit dem Tastenkürzel Strg+E aktiviert werden. 
Es stehen dann folgende Funktionen zur Verfügung:

### Button "Bearbeiten"

1. Meldergruppe hinzufügen:  
    Fügt eine Meldergruppe mit der definierten Nummer hinzu. Diese muss zwischen 1 und 99999 liegen.
2. Gebäudebeschreibung bearbeiten:  
    Die Gebäudebeschreibung wird im Ruhezustand im LCD des FAT angezeigt. 
    Mit dieser Funktion lässt sie sich ändern.
3. FBF:  
    Hier finden sich Schalter, um die LEDs auf dem FBF zu steuern. 
    Die Einstellung wird im Szenario gespeichert.
4. Historie leeren:  
    Löscht alle Einträge aus der Historie.

### Rechtsklick auf Meldergruppen-Nummer

1. Melder hinzufügen:  
    Fügt einen Melder mit der angegebenen Nummer (1-99) und Beschreibung hinzu.
2. Meldergruppe löschen

### Rechtsklick auf Melder

1. Beschreibung bearbeiten
2. Abschaltung:  
    Schaltet den Melder ab. Dadurch wird ein eventuell am Melder anliegender Alarm abgeschaltet und 
    der Melder in der Anzeigeebene der Abschaltung angezeigt. Diese Einstellung wird im Szenario gespeichert.
3. In Historie:  
    Legt fest, ob der Melder in der Historie erscheint. Diese Einstellung wird im Szenario gespeichert.
4. Melder löschen

Abschaltung und Historie sind auch bei ausgeschaltetem Bearbeitungsmodus verfügbar.

## Undo / Redo

Jede Aktion lässt sich per Strg+Z oder dem Undo-Button rückgängig machen, 
außer dem Auslösen von Meldern und den Einstellungen für das FBF
(hier kann man den Schalter einfach wieder umlegen).  
Per Strg+Y, Strg+Shift+Z oder dem Redo-Button kann man die rückgängig gemachte Aktion wiederherstellen.  
Falls keine Aktion mehr rückgängig gemacht oder wiederhergestellt werden kann, 
ist der entsprechende Button ausgegraut.

Das Laden einer Datei löscht alle bisherigen Einträge im undo/redo-Stack. 
Wenn die aktuelle Datei gespeichert wird, bleibt der Stack allerdings erhalten, sodass alle Änderungen 
seit dem letzten Laden rückgängig gemacht werden können.