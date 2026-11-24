# NMS Galaxie-Tracker

🇬🇧 [English version → README.md](README.md) · 🇩🇪 Deutsche Fassung (diese Datei)

Lokale Webseite mit Datenbank für **No Man's Sky**, um die eigenen Orte (Galaxien, Systeme, Basen, Raumstationen, Allianzen) schnell wiederzufinden. Typische Frage: *„Ich sehe in der Anomalie eine Basis in einer Galaxie. War ich da schon, habe ich dort etwas?“*

- Alle 256 Galaxien als farbiges Raster (Lush / Normal / Harsh / Empty), besucht ja/nein, Suche und Filter
- Systeme und Einträge (Basis, Mini-Basis, Raumstation, Portal) je Galaxie, mit Lebensform, Wealth und Konflikt
- Allianzen mit ihren Stationen über alle Galaxien
- Alle **Hitchhikers-of-the-Galaxy-Hubs** (HotG) aus dem NMS-Wiki, auch in noch nicht besuchten Galaxien, mit Portal-Glyphen
- Sicherung als Datenbankkopie, JSON und CSV

Läuft nur lokal, **ohne Login, ohne Konto, ohne Secrets**. Alle Daten liegen in einer einzigen SQLite-Datei. Die App lauscht nur auf dem eigenen Rechner (`127.0.0.1`), nicht im Netzwerk. Die Oberfläche ist **zweisprachig (Englisch und Deutsch)**. Standard ist Englisch bzw. die Browsersprache, oben rechts schaltet „Deutsch / English“ um (wird im Browser gemerkt).

Die vollständige Beschreibung (Ziele, Oberfläche, Importregeln) steht in [`NMS-Galaxie-Tracker-SPEC.md`](NMS-Galaxie-Tracker-SPEC.md). Diese Datei erklärt Installation, Bedienung und den Aufbau.

## Installation

Beim **ersten Start** legt die App die Datenbank selbst an: alle 256 Galaxien (Nummer, Name), alle als „nicht besucht“, dazu die Tabelle der HotG-Hubs und eine eigene Allianz namens „My Alliance“ (umbenennbar in der App). Danach rufst du `http://127.0.0.1:5050` im Browser auf.

### Variante A: Docker (empfohlen, nichts weiter nötig)

Voraussetzung: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (oder Docker Engine mit Compose) ist installiert und gestartet. Auf dem Mac geht auch [Colima](https://github.com/abiosoft/colima) (`brew install colima docker docker-compose`, dann `colima start`). Das Projekt muss dabei in deinem Home-Ordner liegen, damit der Ordner `data/` auf dem Mac sichtbar ist.

```
git clone https://github.com/sasilanz/NMS_GIA.git
cd NMS_GIA
docker compose up -d --build
```

Dann `http://127.0.0.1:5050` öffnen.

- Die Datenbank und alle Sicherungen liegen im Ordner **`./data`** neben `docker-compose.yml` (`data/nms.db`, `data/export/`). Dieser Ordner bleibt beim Neubauen und Aktualisieren erhalten. **Zum Sichern genügt es, ihn zu kopieren.**
- Stoppen: `docker compose down` (Daten bleiben). Starten: `docker compose up -d`. Logs: `docker compose logs -f`.
- Aktualisieren auf eine neue Version: `git pull && docker compose up -d --build`. Die Datenbank wird beim Start bei Bedarf automatisch erweitert.
- Port ändern: in `docker-compose.yml` die linke Zahl bei `ports` ändern, z. B. `"127.0.0.1:8080:5050"`.
- Der Port ist absichtlich nur an `127.0.0.1` gebunden. Es gibt keinen Login. Wer die App im Netzwerk freigibt, gibt auch jedem dort Schreibzugriff.

### Variante B: Python direkt

Voraussetzung: Python 3.10 oder neuer.

```
git clone https://github.com/sasilanz/NMS_GIA.git
cd NMS_GIA
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt      # Windows: .venv\Scripts\pip ...
.venv/bin/python app.py                        # Windows: .venv\Scripts\python app.py
```

Dann `http://127.0.0.1:5050` öffnen. Beenden mit Ctrl+C. Die Datenbank `nms.db` liegt im Projektordner.

**macOS-Komfort:** Doppelklick auf `start.command` startet den Server und öffnet den Browser, `stop.command` beendet ihn, `export.command` erstellt eine Sicherung. Beim ersten Mal ggf. Rechtsklick → „Öffnen“.

### Einstellungen (Umgebungsvariablen)

| Variable | Standard | Bedeutung |
|---|---|---|
| `NMS_DB` | `nms.db` | Pfad der Datenbankdatei |
| `NMS_EXPORT_DIR` | `export` | Ordner für Sicherungen |
| `NMS_HOST` | `127.0.0.1` | Adresse, auf der der Server lauscht (im Docker-Image `0.0.0.0`, von außen nur über die Port-Freigabe in `docker-compose.yml`) |
| `NMS_PORT` | `5050` | Port |

### Neu anfangen / Datenbank zurücksetzen

Datenbank-Datei (bzw. den Ordner `data/`) löschen und die App neu starten, dann entsteht eine frische. Oder gezielt: `python3 init_db.py --neu --allianz "Meine ABC"` (löscht alle Daten!).

### Eigene Numbers-Liste importieren (optional)

Wer bisher eine Tabelle in Numbers geführt hat: `export_numbers.py` exportiert sie als `galaxie_numbers.csv` (Spalten siehe unten, Abschnitt „Skripte“). Liegt diese Datei beim Anlegen der Datenbank im Projektordner, wird sie mit übernommen. Ohne die Datei startet alles leer, das ist der Normalfall.

### Datenquellen

- Galaxienliste (`galaxien_quelle_a.csv`): Nummern und Namen der 256 Galaxien. Einzelne Schreibweisen können abweichen, Namen lassen sich in der App korrigieren.
- HotG-Hubs: aus dem [NMS-Fandom-Wiki](https://nomanssky.fandom.com/wiki/Hitchhikers_of_the_Galaxy) (Text dort unter [CC BY-SA](https://www.fandom.com/licensing)). Die mitgelieferte `hotg_hubs.csv` ist ein Stand zum Start, auf der Seite „HotG-Hubs“ holt „↻ Von Fandom aktualisieren“ den aktuellen Stand.
- *No Man's Sky* ist eine Marke von Hello Games. Das Projekt ist inoffiziell.
- Lizenz: [MIT](LICENSE).

## Server starten und stoppen (macOS, Variante B)

Der Server startet **nicht von selbst**. Er läuft nur, solange du ihn gestartet hast. Nach einem Neustart des Macs oder wenn du das Terminalfenster schließt, ist er wieder aus.

**Starten:** Doppelklick auf `start.command` im Projektordner. Es öffnet sich ein Terminalfenster, und der Browser öffnet die Seite `http://127.0.0.1:5050`. Das Terminalfenster muss offen bleiben, solange du die App nutzt. Läuft der Server schon, öffnet der Doppelklick nur den Browser.

**Stoppen:** Eine dieser drei Möglichkeiten:
1. Im Terminalfenster Ctrl+C drücken.
2. Das Terminalfenster schließen.
3. Doppelklick auf `stop.command`.

**Von Hand im Terminal:**
```
cd NMS_GIA        # bzw. dein Projektordner
.venv/bin/python app.py          # starten, Beenden mit Ctrl+C
```
Läuft er im Hintergrund und du findest ihn nicht: `lsof -ti tcp:5050 -sTCP:LISTEN` zeigt die Prozessnummer, `kill <Nummer>` beendet ihn.

**Läuft er?** Antwortet `http://127.0.0.1:5050` im Browser nicht, ist der Server aus. Dann einfach `start.command` öffnen.

Falls macOS beim ersten Doppelklick meldet, die Datei sei von einem nicht verifizierten Entwickler: Rechtsklick auf `start.command`, „Öffnen“, dann „Öffnen“ bestätigen. Das ist nur beim ersten Mal nötig.

## Stand

| Schritt (laut Spec, Abschnitt 7) | Status |
|---|---|
| 1. Datenbank anlegen und Import | **fertig** |
| 2. Galaxie-Raster mit Farben, Suche, Filtern | **fertig** |
| 3. Galaxie-Ansicht | **fertig** |
| 4. Anlegen, Bearbeiten, Löschen | **fertig** |
| Allianz-Ansicht (aus Abschnitt 3.3 der Spec) | **fertig** |
| 5. Export und Backup | **fertig** |
| 5. Globale Suche | **fertig** |
| HotG-Hubs (Liste aus dem NMS-Wiki, mit Aktualisieren-Knopf) | **fertig** |
| Allianz-Übersicht und Allianz-Filter im Raster | **fertig** |
| Systemattribute (Lebensform, Wealth, Konflikt) | **fertig** |

### Welche Python-Funktion startet den Server?

Am Ende von `app.py` steht:

```python
if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=False)
```

- **`app.run(...)`** startet den eingebauten Flask-Webserver. Der Aufruf **blockiert**: Das Terminal bleibt belegt, und der Server läuft, bis du Ctrl+C drückst oder das Fenster schließt.
- **`HOST = '127.0.0.1'`** bedeutet: nur dieser Mac erreicht den Server, kein Zugriff aus dem WLAN.
- **`PORT = 5050`** ist die Portnummer. Beides steht oben in `app.py` (Konstanten `HOST` und `PORT`). Wer den Port ändert, muss auch die Adresse im Browser und in `start.command` und `stop.command` ändern.
- Die Zeile `if __name__ == '__main__'` sorgt dafür, dass der Server nur startet, wenn man `app.py` direkt aufruft (`.venv/bin/python app.py`), nicht wenn die Datei von woanders importiert wird.

### Läuft der Server? Port prüfen

Alle Befehle im Terminal:

```
lsof -nP -iTCP:5050 -sTCP:LISTEN     # lauscht etwas auf Port 5050? Zeigt Prozess und Nummer (PID)
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5050/    # 200 = läuft, sonst keine Antwort
ps aux | grep "[a]pp.py"             # läuft ein Python-Prozess mit app.py?
```

- Ausgabe von `lsof` mit einer Zeile (`Python ... 127.0.0.1:5050 (LISTEN)`): Der Server läuft. Keine Ausgabe: Er läuft nicht.
- `curl` gibt `200` aus, wenn die Startseite antwortet. Gibt es `000` aus (oder „Connection refused“), läuft der Server nicht.
- Meldung beim Start „Address already in use“: Auf Port 5050 läuft schon etwas, meist ein alter Server. Mit `lsof` die PID suchen und mit `kill <PID>` beenden.
- Am Mac ist Port 5000 vom AirPlay-Empfänger belegt, deshalb wurde 5050 gewählt.

## Bedienung der App

Adresse: `http://127.0.0.1:5050` (Server vorher starten, siehe oben).

**Startseite = Galaxie-Raster.** Alle Galaxien als Kacheln. Farbe der Kachel = Typ:

| Farbe | Typ |
|---|---|
| grün | Lush |
| türkis | Normal |
| rot-orange | Harsh |
| hellgrau | Empty |
| weiß-grau | Typ unbekannt |

**Schnellcheck „War ich in dieser Galaxie schon?“**
1. Seite öffnen. Das Suchfeld ist schon aktiv, einfach lostippen.
2. Nummer eingeben (z. B. `170`) oder Namen oder Kürzel (z. B. `ezd`).
3. Bei genau einem Treffer steht oben groß: „✓ schon besucht“ oder „noch nicht besucht“, plus die Zahl der Einträge.
4. **Escape** leert die Suche. Tippst du, ohne ins Feld zu klicken, springt der Cursor automatisch ins Suchfeld.

**Besucht setzen oder zurücknehmen:** Auf den Kreis oben rechts in der Kachel klicken. Besuchte Kacheln haben einen rosa Rahmen und ein gefülltes Häkchen. Die Änderung wird sofort in `nms.db` gespeichert, ein Speichern-Knopf ist nicht nötig.

**Filter** (Leiste unter dem Suchfeld, Klick schaltet ein und aus):
- Typ: Lush, Normal, Harsh, Empty, mehrere gleichzeitig möglich.
- **alle / besucht / nicht besucht:** Eines davon ist immer aktiv. „alle“ zeigt alle Galaxien, auch die nicht besuchten.
- hat Basis / Station: zeigt nur Galaxien mit eingetragenen Einträgen.
- **🚀 HotG-Hub:** zeigt nur Galaxien, in denen es einen HotG-Hub gibt (auch nicht besuchte). Diese Kacheln tragen unten links eine gelbe „HotG“-Marke.
- **Allianz-Station …:** Auswahl einer Allianz (oder „irgendeine Allianz“). Zeigt nur Galaxien, in denen du eine Station dieser Allianz erfasst hast.
- Die Zahl „x von y“ neben dem Suchfeld zeigt, wie viele Kacheln gerade sichtbar sind. Suche und Filter wirken gemeinsam.

**Galaxie öffnen:** Auf eine Kachel klicken (nicht auf den Kreis, der schaltet nur „besucht“). Mit „← Raster“ oben links geht es zurück, mit „‹ 169“ und „171 ›“ zur vorherigen und nächsten Galaxie.

**Weitere Knöpfe oben:** „🤝 Allianzen“ (Übersicht aller Allianzen), „🚀 HotG-Hubs“ (alle HotG-Hubs), „🔍 Alles durchsuchen“, „Sicherung“. Einen Knopf „+ Galaxie“ gibt es nicht mehr, weil alle 256 Galaxien erfasst sind. Eine zusätzliche Galaxie ließe sich nur über die Schnittstelle `POST /api/galaxy` anlegen.

## Bedienung der Galaxie-Ansicht

Alles, was du änderst, wird **sofort gespeichert**, sobald du das Feld verlässt (Tab oder Klick daneben). Oben rechts steht kurz „✓ gespeichert“. Bei einem Fehler steht dort ein roter Hinweis, zum Beispiel wenn der Name leer ist.

**Kopf (farbig nach Typ):** Name, Kürzel, Typ, Bewertung (1 bis 5 Sterne), Notiz und der große Knopf „Besucht“. Hier korrigierst du falsche Galaxienamen. In der Notiz steht noch der Freitext aus der alten Numbers-Liste (Basen, Eigene Raumstation, Extras). Den kannst du von dort aus in Systeme und Einträge umwandeln und danach aus der Notiz löschen.

**Systeme:** „+ System“ legt ein neues System an. Name und Notiz sind direkt editierbar. Dazu gibt es drei optionale Dropdowns: **Lebensform** (Gek, Vy'keen, Korvax), **Wealth** (1 bis 3, niedrig bis hoch) und **Konflikt** (1 bis 3, niedrig bis hoch). „✕ System“ löscht das System **mit allen seinen Einträgen** (vorher kommt eine Rückfrage). Namensschema in den Platzhaltern: Kürzel + Merkname, z. B. `EZD Aibaba`.

**Einträge** (Basis, Mini-Basis, Raumstation, Portal, Sonstiges) liegen in einem System:
- „+ Basis / Eintrag“ legt einen Eintrag vom Typ Basis an, den Typ kannst du danach ändern.
- „+ Raumstation (Name deiner Allianz)“ legt gleich eine Raumstation deiner eigenen Allianz an.
- Felder: Typ, Name (Schema Kürzel + Typ + Merkmal, z. B. `EZD Basis Insel`, wie im Teleporter), Planet (nur Text), Allianz, Notiz. **Bei Typ „Raumstation“ gibt es kein Planetenfeld**, weil eine Station keinen Planeten hat. Ein früher eingetragener Planet bleibt in der Datenbank erhalten und erscheint wieder, wenn der Typ zurückgestellt wird.
- **Allianz:** „keine (persönlich)“ für eigene Basen, sonst die Allianz auswählen. ★ markiert deine eigene Allianz. Einträge mit Allianz haben links einen farbigen Streifen (gelb = eigene Allianz, rosa = andere).
- „✕“ rechts löscht den Eintrag (mit Rückfrage).

**Galaxie löschen:** Ganz unten „Galaxie löschen …“. Löscht auch alle Systeme und Einträge darin (mit Rückfrage).

## Bedienung der Allianz-Ansicht

**Öffnen:** Der gelbe Knopf „★ Allianzname“ oben links ist auf jeder Seite da und führt direkt zu deiner eigenen Allianz. Alternativ in einem Eintrag auf „Allianz öffnen →“ klicken.

**Liste:** Alle Stationen der Allianz über alle Galaxien, sortiert nach Galaxie-Nummer: Galaxie, System, Typ, Name, Planet, Notiz. Das Suchfeld darüber filtert live. Ein Klick auf die Galaxie öffnet sie zum Bearbeiten. Hier in der Liste wird nichts bearbeitet.

**Übersicht:** Der Knopf „🤝 Allianzen“ (Startseite) oder „Alle Allianzen“ führt zu `/allianzen`: jede Allianz mit Zahl der Stationen und Galaxien, plus „+ Allianz“.

**Fremde Allianz-Station erfassen:** Allianz in der Übersicht anlegen, dann in der Galaxie einen Eintrag vom Typ Raumstation anlegen und dort die Allianz auswählen. Im Raster findest du sie mit dem Filter „Allianz-Station …“.

**Allianz wechseln:** Die Auswahl oben zeigt alle Allianzen mit der Zahl ihrer Stationen, ★ = eigene.

**Neue Allianz:** „+ Allianz“ und Namen eingeben. Danach kannst du sie bei Einträgen in der Galaxie-Ansicht auswählen.

**Name und Notiz** der Allianz sind direkt editierbar und werden sofort gespeichert.

**Eigene Allianz festlegen:** Bei einer anderen Allianz unten „Als meine eigene Allianz festlegen“. Es gibt immer genau eine eigene. Der gelbe Knopf oben zeigt danach auf die neue.

**Allianz löschen:** Unten „Allianz löschen …“ bei einer nicht eigenen Allianz. Die Stationen bleiben in ihren Galaxien erhalten, gehören dann aber keiner Allianz mehr. Die eigene Allianz lässt sich nicht löschen.

## Bedienung der HotG-Hubs („Hitchhikers of the Galaxy“)

Die Seite `/hotg` (Knopf „🚀 HotG-Hubs“) listet **alle Hubs der Community aus dem NMS-Wiki**, auch in Galaxien, die du noch nicht besucht hast: Nummer, Galaxie, Besucht-Status, Hub-System, Portal-Glyphen (Hex, mit „kopieren“-Knopf), Entdecker und deine eigenen Einträge in der Galaxie. Die Galaxie ist verlinkt. Galaxie 69 hat ein geheimes System ohne Glyphen, dort steht der Zugangshinweis.

- **Filter:** alle / nicht besucht / besucht, dazu eine Suche über Nummer, Galaxie, System und Entdecker. Der Filter wird im Browser gemerkt.
- **↻ Von Fandom aktualisieren:** holt die Liste jetzt frisch aus dem Wiki (Abschnitt „All HotG galactic hubs discovered so far“) und ersetzt die lokale Liste. Danach steht da, was neu, geändert oder entfernt ist. Der Abruf läuft über die MediaWiki-API, weil die normale Wiki-Seite für Skripte gesperrt ist. Der Besitzer der Community (Ronnie) lädt neue Galaxien dort selbst hoch, dein Stand erscheint also erst nach seinem Upload.
- Im Terminal: `.venv/bin/python hotg_import.py`.
- In der Galaxie-Ansicht steht oben ein gelber Hinweis mit Hub, Glyphen und Entdecker, wenn es dort einen Hub gibt.
- Die Daten liegen in der Tabelle `hotg_hub` und zusätzlich als Kopie in `hotg_hubs.csv` (wird beim Aktualisieren neu geschrieben). Ist die Tabelle beim Start leer, wird sie aus der CSV gefüllt. Hubs in Galaxien, die es in deiner Datenbank nicht gibt, werden übersprungen.

## Sicherung (Export) und Wiederherstellen

**Der Ordner `export/`** wird beim ersten Export automatisch angelegt, im Projektordner unter `export/` (bei Docker `data/export/`). Jeder Export bekommt darin einen eigenen Unterordner mit Datum und Uhrzeit, z. B. `export/2026-11-06_144754/`. Alte Exporte werden nie automatisch gelöscht.

**Inhalt eines Exports:**

| Datei | Inhalt |
|---|---|
| `nms.db` | vollständige Kopie der Datenbank, **die wichtigste Datei** (zum Wiederherstellen) |
| `nms.json` | alle Daten als JSON (alle Tabellen, auch `hotg_hub`) |
| `galaxien.csv` | alle Galaxien (Nr, Name, Kürzel, Typ, Besucht, Bewertung, Notiz) |
| `systeme.csv` | alle Systeme mit Galaxie, Lebensform, Wealth und Konflikt |
| `eintraege.csv` | alle Einträge mit Galaxie, System und Allianz als Namen (lesbar, kein Nachschlagen nötig) |
| `allianzen.csv` | alle Allianzen |

Die CSV-Dateien öffnen sich in Numbers und Excel mit richtigen Umlauten.

**Export auslösen (drei Wege, alle funktionieren bei laufendem Server):**
1. **Im Browser:** Im Raster oben auf „Sicherung“, dann „Jetzt sichern“. Die Seite listet alle vorhandenen Exporte und lässt jede Datei einzeln herunterladen.
2. **Doppelklick auf `export.command`:** sichert und öffnet den neuen Ordner im Finder.
3. **Im Terminal:** `.venv/bin/python exporter.py`

**Wiederherstellen** (z. B. nach versehentlichem Löschen):
1. Server stoppen (`stop.command`).
2. Die aktuelle `nms.db` zur Sicherheit umbenennen, z. B. in `nms-kaputt.db`.
3. Die `nms.db` aus dem gewünschten Export-Ordner in den Projektordner kopieren (bei Docker nach `data/`).
4. Server starten (`start.command`).

**Wann sichern?** Vor größeren Änderungen, besonders vor dem Aufräumen der alten Freitexte und bevor du etwas löschst. Gelöschtes (✕) ist sonst nicht wiederherstellbar. Der Export ist nur eine Kopie auf demselben Mac. Für echten Schutz den Ordner `export/` gelegentlich auf eine externe Platte oder in die Cloud kopieren.

## Aufräumen der alten Freitexte

Der Import hat den Freitext aus der Numbers-Liste unverändert in die Notiz der Galaxie geschrieben, je eine Zeile pro Spalte (`Basen: …`, `Eigene Raumstation: …`, `Extras: …`, `Sternenystem: …`). Daraus sollen nach und nach echte Systeme und Einträge werden.

**Die Aufräum-Liste:** Im Raster oben auf „Aufräumen (39)“ (die Zahl ist die Menge der noch offenen Galaxien). Die Liste zeigt jede Galaxie mit altem Text, den Text lesbar nach Spalte getrennt, daneben „Öffnen →“. Filter: Suchfeld in den alten Texten, „noch ohne Systeme“, „besucht“.

**So gehst du pro Galaxie vor:**
1. „Öffnen →“ klicken. Oben in der Notiz steht der alte Text zum Abschreiben.
2. „+ System“ anlegen (Namensschema `Kürzel Merkname`, z. B. `EZD Aibaba`) und darin „+ Basis / Eintrag“ oder „+ Raumstation (Allianzname)“.
3. Typ, Name (wie im Teleporter, `Kürzel Typ Merkmal`), Planet und Notiz ausfüllen.
4. Die erledigten Zeilen aus der Galaxie-Notiz **löschen**. Andere Notizen (zum Beispiel „Bewertung (Original): ?“) kannst du behalten.

Eine Galaxie verschwindet aus der Liste, sobald in ihrer Notiz keine Zeile mehr mit `Basen:`, `Eigene Raumstation:`, `Extras:` oder `Sternenystem:` und Text dahinter steht. Die Liste ist also dein Fortschritt: Er ist von selbst erledigt, wenn die Zahl 0 ist. Der Knopf im Raster verschwindet dann ebenfalls.

**Tipp:** Vor dem Aufräumen einen Export machen, und zwischendurch wieder (siehe Abschnitt Sicherung). Beim Löschen von Zeilen aus der Notiz gibt es kein Rückgängig.

**Technik:** `alttext_zeilen(notiz)` in `app.py` erkennt die Zeilen des Imports mit einem Muster und zerlegt sie in Spalte und Text. `aufraeumen()` (Route `/aufraeumen`) baut daraus die Liste mit der Zahl der schon angelegten Systeme und Einträge je Galaxie.

## Bedienung der Suche („Wo ist meine Basis?“)

**Öffnen:** Im Raster oben auf „🔍 Alles durchsuchen“, oder in jeder Ansicht auf „🔍 Suche“. Wenn du im Raster etwas ins Suchfeld tippst, erscheint darunter ein Link, der dasselbe in allem sucht.

**Suchen:** Einfach lostippen, die Treffer erscheinen live. Gesucht wird in:
- **Einträgen** (Basen, Stationen …): Name, Planet, Notiz, Typ und Allianzname
- **Systemen:** Name und Notiz
- **Galaxien:** Nummer, Name, Kürzel und Notiz. Dazu gehören auch die **alten Texte aus der Numbers-Liste**, die noch in den Galaxie-Notizen stehen. So findest du auch Orte, die du noch nicht als eigenen Eintrag angelegt hast.

**Wie die Treffer aussehen:** Die Treffer sind gruppiert (Einträge, Systeme, Galaxien). Bei jedem Eintrag steht der ganze Weg: *Galaxie › System › Planet*, dazu ein Textausschnitt mit gelb markierten Treffern und die Angabe, in welchem Feld es gepasst hat. Ein Klick öffnet die Galaxie und springt direkt zum Eintrag oder System, das kurz gelb umrandet wird.

**Regeln:**
- Mehrere Wörter müssen **alle** vorkommen: „ezd insel“ findet nur Treffer mit beiden Wörtern.
- Groß/Klein ist egal. Umlaute: „ü“ wird wie „u“ behandelt, außerdem findet „ue“ ein „ü“ (also „blaugruen“ findet „Blaugrün“, „strasse“ findet „Straße“).
- Eine Zahl findet genau diese Galaxie (170 findet nur Galaxie 170, nicht 17 oder 1700).
- Angezeigt werden höchstens die ersten 300 Treffer.

**Technik:** `suche(anfrage)` in `app.py` liest alle Galaxien, Systeme und Einträge und vergleicht sie in Python mit den Wörtern. **`falten(text)`** macht Text klein und entfernt Akzente (Länge bleibt gleich, damit die gelbe Markierung an der richtigen Stelle sitzt), **`varianten(wort)`** erzeugt die Schreibweisen (ue→u, ss→s), **`schnipsel()`** schneidet den Textausschnitt um den Treffer. Schnittstelle: `GET /api/suche?q=…`. Bei deiner Datenmenge (einige hundert Zeilen) ist das sofort fertig, ohne eigenen Suchindex.

**Datensicherung:** Alle Daten liegen in der einen Datei `nms.db`. Zum Sichern bei gestopptem Server die Datei kopieren.

## Einrichtung und Port

Der Server ist nur lokal erreichbar. Port 5050, weil 5000 am Mac von AirPlay belegt ist.

Einmalig einrichten, falls `.venv` fehlt: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.

### Galaxie-Raster (Startseite)

- Alle Galaxien als Kacheln mit Nummer, Name, Kürzel, Farbe nach Typ.
- Besucht = rosa Rahmen und gefülltes Häkchen. Ein Klick auf das Häkchen schaltet um und speichert sofort in der Datenbank.
- Suchfeld ist beim Öffnen fokussiert. Eine Zahl zeigt genau diese Galaxie, Text sucht in Name und Kürzel. Bei genau einem Treffer steht oben groß „schon besucht“ oder „noch nicht besucht“. Escape leert die Suche.
- Filter: Typ (mehrere möglich), alle / besucht / nicht besucht (genau eines aktiv), hat Basis / Station.
- **Standard und Merken:** Beim allerersten Öffnen ist „besucht“ eingeschaltet, du siehst also nur deine besuchten Galaxien. **Alle Galaxien** siehst du mit dem Knopf „alle“ in der Filterleiste. Die Filter (Typ, besucht, hat Basis) merkt sich der Browser dauerhaft, die Suche und die Scrollposition bleiben für den offenen Tab erhalten. Kommst du aus einer Galaxie zurück, ist das Raster so wie du es verlassen hast. Ein neuer Tab oder ein neuer Tag startet mit leerem Suchfeld, aber mit deinen Filtern. „✕ Filter zurücksetzen“ neben der Zahl löscht die Suche und alle Filter und stellt auf „alle“.
- **Schnellcheck trotz Filter „besucht“:** Findet deine Suche unter den besuchten nichts (z. B. eine Galaxie, in der du noch nie warst), werden die Treffer trotzdem angezeigt, mit dem Hinweis, dass der Filter ignoriert wird. So bekommst du auch dort die Antwort „noch nicht besucht“, statt „nichts gefunden“.
- Das Zählersymbol (⌂) erscheint erst, wenn Einträge in der Datenbank stehen. Bisher stehen die Basen nur als Text in der Notiz, deshalb zeigt der Filter „hat Basis“ aktuell nichts an.

## Dateien

| Datei | Zweck |
|---|---|
| `NMS-Galaxie-Tracker-SPEC.md` | Spezifikation |
| `README.md` | diese Datei |
| `nms.db` | SQLite-Datenbank, **enthält alle Daten** (entsteht beim ersten Start, nicht im Git-Repo) |
| `Dockerfile`, `docker-compose.yml`, `.dockerignore` | Docker-Betrieb (Daten im Ordner `data/`) |
| `start.command` | Doppelklick: Server starten und Browser öffnen |
| `stop.command` | Doppelklick: Server beenden |
| `app.py` | Flask-Server: Raster-Seite und Besucht-Umschalter |
| `i18n.py`, `translations_en.py` | Zweisprachigkeit: deutsche Texte sind die Schlüssel, `translations_en.py` enthält das englische Wörterbuch |
| `check_translations.py` | prüft, dass jeder Text eine englische Übersetzung hat (`python3 check_translations.py`) |
| `templates/_sprache.html`, `templates/_js.html` | Sprachumschalter und JS-Übersetzungsfunktion `_()` für alle Seiten |
| `templates/index.html` | Raster-Seite (HTML, CSS, JavaScript) |
| `templates/galaxy.html` | Galaxie-Ansicht mit Bearbeiten (HTML, CSS, JavaScript) |
| `templates/allianz.html` | Allianz-Ansicht (HTML, CSS, JavaScript) |
| `templates/allianzen.html` | Allianz-Übersicht (HTML, CSS, JavaScript) |
| `templates/hotg.html` | HotG-Hubs (HTML, CSS, JavaScript) |
| `templates/suche.html` | Globale Suche (HTML, CSS, JavaScript) |
| `templates/aufraeumen.html` | Aufräum-Liste der alten Freitexte (HTML, CSS, JavaScript) |
| `requirements.txt` | Python-Abhängigkeiten (Flask) |
| `exporter.py` | Sicherung: erzeugt Exporte in `export/` (Terminal oder aus `app.py`) |
| `export.command` | Doppelklick: Export erstellen und Ordner im Finder öffnen |
| `export/` | die Exporte, ein Unterordner pro Sicherung (entsteht automatisch) |
| `hotg_import.py` | holt die HotG-Hub-Liste aus dem NMS-Wiki und speichert sie in `nms.db` und `hotg_hubs.csv` |
| `hotg_hubs.csv` | Kopie der HotG-Hub-Liste (Stand des letzten Abrufs) |
| `init_db.py` | legt `nms.db` an und importiert die Galaxien |
| `export_numbers.py` | exportiert die Numbers-Liste einmalig nach CSV |
| `galaxien_quelle_a.csv` | Quelle A: Galaxienliste (Nummer, Name, Typ) (ursprünglich per OCR aus einer gescannten Liste gelesen) |
| `galaxie_numbers.csv` | Quelle B (optional, nicht im Repo): eigene Numbers-Liste als CSV |

## Datenmodell

Fünf Tabellen, Hierarchie **Galaxie → System → Eintrag**. Planeten sind nur ein Textfeld am Eintrag.

- **`galaxy`**: `nr` (Primärschlüssel), `name`, `kuerzel`, `typ` (Lush/Normal/Harsh/Empty), `besucht` (0/1), `bewertung` (1–5), `notiz`
- **`system`**: `id`, `galaxy_nr` → galaxy, `name`, `lebensform` (Gek, Vy'keen, Korvax, leer erlaubt), `wealth` (1–3), `konflikt` (1–3), `notiz`
- **`eintrag`**: `id`, `system_id` → system, `typ` (Basis, Mini-Basis, Raumstation, Portal, Sonstiges), `name`, `planet`, `allianz_id` → allianz (leer = persönliche Basis), `notiz`
- **`allianz`**: `id`, `name`, `eigene` (1 = meine eigene Allianz, genau eine), `notiz`
- **`hotg_hub`**: `galaxy_nr` (Primärschlüssel, → galaxy), `system`, `entdeckt_von`, `glyphen` (Hex), `zugang` (Hinweis bei geheimen Systemen). Referenzdaten aus dem Wiki, keine eigenen Einträge. Die Tabelle wird beim Start angelegt, die drei Systemspalten werden bei einer älteren Datenbank automatisch nachgerüstet.

Löscht man eine Galaxie, werden ihre Systeme und deren Einträge mit gelöscht. Löscht man eine Allianz, bleiben ihre Einträge erhalten, nur der Verweis wird leer.

## Skripte

### `init_db.py`

Baut die Datenbank auf. Nur Standardbibliothek, kein `pip install` nötig.

```
python3 init_db.py          # bricht ab, wenn nms.db schon existiert
python3 init_db.py --neu    # löscht nms.db und baut sie neu auf (alle Daten weg!)
```

Wichtig: `--neu` löscht auch alles, was später in der App eingetragen wurde. Vor dem Aufruf vorher `nms.db` sichern.

Funktionen und Ablauf:

- **`lies(pfad)`** liest eine CSV-Datei und gibt eine Liste von Zeilen (als Dictionaries mit den Spaltennamen) zurück.
- **`main()`** macht der Reihe nach:
  1. Schutz: Existiert `nms.db`, bricht das Skript ab, außer es wird mit `--neu` gestartet.
  2. Legt die Tabellen an (Konstante `SCHEMA`).
  3. **Quelle A** einlesen: alle Galaxien (Nummer, Name, Typ), alle starten als nicht besucht.
  4. **Quelle B** (Numbers) einlesen und über die Nummer zuordnen:
     - **Name:** Der Numbers-Name hat Vorrang vor Quelle A. Abweichungen kommen in die Abweichungsliste.
     - **Typ:** `Kategorie` wird zu `typ`. Unbekannte Werte (z. B. `???`) werden gemeldet, der Typ aus Quelle A bleibt.
     - **Besucht:** `Entdeckt` = `X` oder `x` ergibt `besucht = 1`.
     - **Kürzel:** wird übernommen.
     - **Bewertung:** Die Anzahl der Sterne `*` bis `*****` ergibt 1 bis 5. Andere Werte (`?`, `???`, `Magenta`) ergeben `NULL`, der Originalwert steht in der Notiz.
     - **Freitexte:** `Sternenystem`, `Eigene Raumstation`, `Basen` und `Extras` landen unverändert in der Notiz der Galaxie, je eine Zeile mit der Spaltenbezeichnung davor. Sie werden **nicht** automatisch zerlegt.
     - Zeilen ohne Namen und die Zeile „NMS Freundescode“ werden ignoriert.
  5. Schreibt alle Galaxien in die Tabelle `galaxy` und legt die eigene Allianz (`--allianz`, Standard „My Alliance“) mit `eigene = 1` an.
  6. Gibt eine Kontrolle aus: Anzahl Galaxien, Anzahl besucht, Anzahl mit Notiz, Anzahl ohne Typ, die Abweichungsliste und Galaxien aus Numbers, die in Quelle A fehlen.

Konstanten am Dateianfang: `DB` (Dateiname der Datenbank), `QUELLE_A` und `QUELLE_B` (Pfade der CSV-Dateien), `TYPEN` (erlaubte Galaxientypen).

### `export_numbers.py`

Liest die Numbers-Datei und schreibt die Galaxienzeilen als CSV. Muss nur laufen, wenn sich die Numbers-Liste ändert. Braucht das Paket `numbers-parser`.

```
pip install numbers-parser
python3 export_numbers.py MeineListe.numbers galaxie_numbers.csv
```

Übernommen werden die Spalten Name, Kategorie, Entdeckt, Bewertung, Kürzel, Sternenystem, Eigene Raumstation, Basen und Extras. Nur Zeilen mit einer Nummer in der ersten Spalte werden exportiert, also keine Überschrift, kein Freundescode und keine Summenzeile.

## Datenquellen und bekannte Eigenheiten

- **Quelle A** (`galaxien_quelle_a.csv`) wurde ursprünglich per OCR aus einer gescannten Liste gelesen und mit einer weiteren Liste abgeglichen. Die Namen sind nur bei den Galaxien aus Numbers von mir geprüft, bei allen anderen kann die Schreibweise abweichen. Falsche Namen werden später in der App korrigiert.
- **256 Galaxien:** Die PDF-Liste führte 257, die Datenbank enthält die Galaxien 1 bis 256 (wie auch das HotG-Wiki). Eine Galaxie 257 gibt es nicht.
- **Typ von #256 und #257:** In den PDF-Listen „???“. Numbers hat #256 = Normal, bei #257 steht „???“, deshalb ist #257 ohne Typ.
- **Systemnamen** stehen in Numbers in der Spalte „Eigene Raumstation“, nicht in „Sternenystem“ (die ist leer).
- **Kernfarbe** („Core Color“, Farbe des Galaxienkerns) ist nicht Teil des Modells, kann später als Feld `kernfarbe` ergänzt werden.

## Datenbank ansehen

```
sqlite3 nms.db "SELECT nr, name, typ, besucht FROM galaxy WHERE besucht = 1 ORDER BY nr"
sqlite3 nms.db ".schema"
```

### `app.py`

- **`FARBEN`** enthält alle Farben der Oberfläche an einer Stelle (Lush, Normal, Harsh, Empty, ohne Typ, besucht). Sie werden als CSS-Variablen in die Seite geschrieben. Zum Ändern nur hier editieren.
- **`db()`** öffnet pro Anfrage eine Datenbankverbindung, **`close_db()`** schließt sie wieder.
- **`galaxien()`** liest alle Galaxien samt Zähler der Einträge (Systeme und Einträge werden per Join gezählt).
- **`raster()`** (Route `/`) liefert die Startseite.
- **`besucht_umschalten(nr)`** (Route `POST /api/galaxy/<nr>/besucht`) schaltet `besucht` um und antwortet mit dem neuen Wert, bei unbekannter Nummer mit 404.
- **`galaxie_ansicht(nr)`** (Route `/galaxy/<nr>`) liefert die Galaxie-Seite, **`galaxie_komplett(nr)`** holt Galaxie, Systeme, Einträge, Allianzen und die Nachbar-Nummern aus der Datenbank.
- **`aendern(tabelle, schluessel, id, daten, pruefer)`** ist die gemeinsame Speicherfunktion: Sie ändert nur erlaubte Felder, prüft jeden Wert und gibt die gespeicherte Zeile zurück. Die Prüfer **`pruefe_galaxy`**, **`pruefe_system`**, **`pruefe_eintrag`** legen fest, welche Felder änderbar sind und welche Werte gelten (z. B. Bewertung 1 bis 5, Eintragstypen). Leere Texte werden zu NULL, Namen dürfen nicht leer sein. Fehler kommen als Meldung zurück (`Eingabefehler`, HTTP 400).
- **Export:** Die Arbeit macht **`exporter.py`**. **`erstelle_export()`** legt den Zeitstempel-Ordner an, kopiert die Datenbank mit der SQLite-Backup-Funktion (konsistent, auch bei laufendem Server), schreibt JSON und CSV und gibt Ordner, Dateien und Zeilenzahlen zurück. **`liste_exporte()`** listet die vorhandenen Exporte. In `app.py`: Seite `/export`, `POST /api/export` (erstellt einen Export) und `/export/datei/<ordner>/<datei>` (Download, nur echte Export-Ordner und die bekannten Dateinamen).
- **HotG:** **`hotg_vorbereiten()`** legt beim Start `hotg_hub` an, füllt sie bei Bedarf aus `hotg_hubs.csv` und rüstet die Systemspalten nach. **`hotg_seite()`** (Route `/hotg`), **`hotg_aktualisieren()`** (`POST /api/hotg/aktualisieren`) ruft **`hotg_import.py`** auf (`lade_wikitext()`, `parse()`, `speichern()`).
- **Allianz-Übersicht:** **`allianzen_uebersicht()`** (Route `/allianzen`) zählt Stationen und Galaxien je Allianz. Im Raster trägt jede Kachel die IDs ihrer Allianzen (`data-al`) für den Allianz-Filter.
- **Allianz:** **`allianz_komplett(aid)`** holt die Allianz, ihre Stationen (Join über Eintrag, System und Galaxie) und die Auswahlliste mit Anzahl. Routen: `/allianz` (leitet zur eigenen Allianz weiter), `/allianz/<id>`. **`eigene_allianz_fuer_alle_seiten()`** (Context-Processor) stellt die eigene Allianz allen Seiten für den festen Link bereit. Schnittstellen: `POST /api/allianz`, `PATCH` und `DELETE /api/allianz/<id>`, `POST /api/allianz/<id>/eigene` (setzt die eigene Allianz, die anderen werden zurückgesetzt).
- **Schnittstellen (alle JSON):** `POST /api/galaxy` (anlegen), `PATCH` und `DELETE /api/galaxy/<nr>`, `POST /api/galaxy/<nr>/system`, `PATCH` und `DELETE /api/system/<id>`, `POST /api/system/<id>/eintrag`, `PATCH` und `DELETE /api/eintrag/<id>`, `GET /api/galaxy/<nr>`. Löschen einer Galaxie oder eines Systems löscht die darunterliegenden Daten mit (Datenbank-Kaskade).

Die Suche und die Filter laufen komplett im Browser (JavaScript in `index.html`), damit sie ohne Verzögerung reagieren.

## Technik

Python mit Flask, SQLite, einfache HTML-Seiten mit etwas JavaScript. Läuft nur lokal am Mac mini (`127.0.0.1`), ohne Login. Export als JSON oder CSV zur Sicherung kommt in Schritt 5.
