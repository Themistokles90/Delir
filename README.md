# Delir
Datenextraktionstools
Hier die Installationsasnweisungen für das Statistik Tool mit dem ich das
gemacht habe. Schaut nach viel aus, ist

1) installation
‚R' installieren, also die 2 Sachen runterladen und erst das
obere dann das untere installieren:
https://cran.uni-muenster.de/bin/windows/base/R-3.5.1-win.exe
https://cran.uni-muenster.de/bin/windows/Rtools/Rtools35.exe

https://download1.rstudio.org/RStudio-1.1.456.exe

Das letzte ist eine grafische Benutzeroberfläche für das Statistik Tool.

2) Projekt einrichten
Erst mal das Archiv im Anhang an einen beliebigen Ort entpacken.
Dann Rstudio öffnen. Hier siehst Du unten rechts den File Browser -> hier
navigierst du zu dem entpackten Verzeichnis (über das '...' am rechten
Rand kannst Du direkt Verzeichnisse auswählen)

Hier solltest du jetzt nur 2 sachen sehen:
- eine Datei 'report.Rmd'
- eine Datei 'README'
- einen Ordner 'scripts'

Wenn Du das hast, dann auch in dem File Browser Bereich auf 'More'/'Mehr'
(das grüne Zahnrad) und da 'SET as working directory'/'Als
Arbeitsverzeichnis setzen' auswählen.

Dann mit einfach auf die report.Rmd klicken. Hier in Zeile 63/64 die 2
Pfade anpassen: ddata -> wo die XLSX Dateien liegen, fout -> in welche
Datei die Daten hingeschrieben werden sollen; dann speichern.

Jetzt nur noch auf den kleinen Pfeil oben neben 'Knit' -> dann 'knit to
HTML'
