# NMS Galaxie-Tracker – Spezifikation

Lokale Webseite mit Datenbank, um meine eigenen No-Man's-Sky-Orte (Galaxien, Systeme, Basen, Raumstationen) schnell wiederzufinden. Ersetzt die Numbers-Liste `Galaxieliste_neu.numbers`, die mit Systemen, Planeten und Raumstationen nicht mehr passt.

## 1. Wozu das Ganze

**Hauptfall (muss in unter 5 Sekunden gehen):** Ich sehe in der Anomalie eine Basis eines anderen Spielers in einer Galaxie und muss sofort wissen: *War ich in dieser Galaxie schon? Habe ich dort etwas?*

**Zweitfall:** Ich weiß bei einer meiner Basen nur noch die Galaxie. Ich öffne die Galaxie und sehe alles, was ich dort habe (Systeme, Basen, Stationen).

**Nicht-Ziele:** Keine Erfassung fremder Basen. Kein vollständiges Planeteninventar. Kein Login, keine Mehrbenutzer-Funktion, kein Online-Hosting.

## 2. Datenmodell

Datenbank: SQLite (eine einzelne Datei).

### galaxy
| Feld | Typ | Bemerkung |
|---|---|---|
| nr | INTEGER, PK | Galaxie-Nummer, fester Schlüssel. Der Import legt 1–257 an (die Zahl der Galaxien ist in NMS nicht eindeutig; die Quellen führen 256 oder 257). Weitere Galaxien lassen sich in der App selbst anlegen. |
| name | TEXT | Name der Galaxie |
| kuerzel | TEXT, optional | z. B. `EZD`, `ODY`, `PL`; wird in den Namen meiner Basen verwendet |
| typ | TEXT | `Lush`, `Normal`, `Harsh`, `Empty` (steuert die Farbe) |
| besucht | BOOLEAN | Standard: falsch |
| bewertung | INTEGER, optional | 1–5 |
| notiz | TEXT, optional | |

### system
| Feld | Typ | Bemerkung |
|---|---|---|
| id | INTEGER, PK | |
| galaxy_nr | INTEGER, FK | → galaxy.nr |
| name | TEXT | Ich benenne Systeme im Spiel um, Schema: `Kürzel + Merkname`, z. B. `EZD Aibaba` |
| lebensform | TEXT, optional | `Gek`, `Vy'keen`, `Korvax` |
| wealth | INTEGER, optional | 1–3 (niedrig bis hoch) |
| konflikt | INTEGER, optional | 1–3 (niedrig bis hoch) |
| notiz | TEXT, optional | |

### eintrag (Basis, Station usw.)
| Feld | Typ | Bemerkung |
|---|---|---|
| id | INTEGER, PK | |
| system_id | INTEGER, FK | → system.id |
| typ | TEXT | `Basis`, `Mini-Basis`, `Raumstation`, `Portal`, `Sonstiges` |
| name | TEXT | Name im Spiel, identisch mit dem Namen im Teleporter. Schema: `Kürzel + Typ + Merkmal`, z. B. `EZD Basis Insel` |
| planet | TEXT, optional | Planet nur als Textfeld, **keine eigene Ebene**. Bei Typ `Raumstation` wird das Feld in der Oberfläche nicht angezeigt (Stationen haben keinen Planeten). |
| allianz_id | INTEGER, FK, optional | → allianz.id; gesetzt = Station gehört zu dieser Allianz (auch meine eigene Allianz), leer = persönliche Basis ohne Allianz |
| notiz | TEXT, optional | woran ich den Ort erkenne, Besonderheiten |

### allianz
| Feld | Typ | Bemerkung |
|---|---|---|
| id | INTEGER, PK | |
| name | TEXT | Name der Allianz |
| eigene | BOOLEAN | wahr = meine eigene Allianz (genau eine); ihre Stationen sind die wichtigsten |
| notiz | TEXT, optional | |

Meine eigene Allianz heißt `ASI_1` und enthält nur meine eigenen, übernommenen Raumstationen. Sie wird beim ersten Start automatisch mit `eigene = wahr` angelegt. Sie ist die Hauptallianz. Fremde Allianzen kommen nur dazu, falls ich später einer beitrete.

Allianzen werden in der Oberfläche angelegt und gepflegt (kleine Verwaltungsseite). Mehrere Allianzen sind möglich; beim Wechsel bleiben alte Einträge der früheren Allianz erhalten.

### hotg_hub (Referenzdaten)
| Feld | Typ | Bemerkung |
|---|---|---|
| galaxy_nr | INTEGER, PK, FK | → galaxy.nr, höchstens ein Hub je Galaxie |
| system | TEXT | Name des Hub-Systems |
| entdeckt_von | TEXT, optional | |
| glyphen | TEXT, optional | Portal-Adresse als 12 Hex-Zeichen |
| zugang | TEXT, optional | Hinweis bei geheimen Systemen ohne Glyphen (Galaxie 69) |

Quelle: Liste „All HotG galactic hubs discovered so far“ im NMS-Fandom-Wiki (Seite „Hitchhikers of the Galaxy"). Die Liste wird nicht von Hand gepflegt, sondern per Knopf aus dem Wiki geholt.

Hierarchie: **Galaxie → System → Eintrag**. Jede Galaxie kann beliebig viele Systeme haben, jedes System beliebig viele Einträge.

## 3. Oberfläche

### 3.1 Startseite: Galaxie-Raster (wichtigste Ansicht)
- Alle Galaxien (beim Start 257) als Kacheln, mit Nummer und Name.
- **Farbe nach Typ** (aus der Numbers-Liste übernommen, an **einer** Stelle im Code änderbar): Lush = grün (97/216/54), Normal = türkis (115/253/234), Harsh = rot-orange (255/100/78), Empty = hellgrau (213/213/213). Typ leer = neutral/weiß.
- **Besucht** muss auf einen Blick erkennbar sein (Anomalie-Fall): Rosa wie in der Numbers-Liste (255/149/202), weil Rot schon Harsh ist, **plus** ein Häkchen auf der Kachel, damit es nicht nur an der Farbe hängt. Die genaue Farbe ist egal. Nicht besucht = ohne Rosa und ohne Häkchen.
- Kleines Symbol oder Zähler auf der Kachel, wenn ich in der Galaxie Basen oder Stationen habe.
- **Suchfeld ganz oben, sofort fokussiert:** Eingabe von Nummer, Name oder Kürzel filtert das Raster live. Ein Treffer zeigt sofort besucht ja/nein und ob ich dort etwas habe.
- Filter: Typ (Lush/Normal/Harsh/Empty), besucht / nicht besucht, „hat Basis", „Allianz-Station" (Auswahl einer bestimmten Allianz oder irgendeine), „HotG-Hub".
- Kacheln mit HotG-Hub tragen eine kleine „HotG"-Marke. Es gibt keinen „+ Galaxie"-Knopf, weil alle 256 Galaxien erfasst sind.
- Besucht-Status lässt sich direkt in der Kachel mit einem Klick umschalten.

### 3.2 Galaxie-Ansicht
- Kopf: Nummer, Name, Kürzel, Typ, Bewertung, besucht-Schalter, Notiz. Gibt es in der Galaxie einen HotG-Hub, steht darüber ein Hinweis mit System, Glyphen und Entdecker.
- Je System: Lebensform, Wealth (1–3) und Konflikt (1–3) als Dropdowns.
- Darunter der Baum, aufklappbar: System → Einträge (Typ, Name, Planet, Notiz).
- Einträge, die zu einer Allianz gehören, sind erkennbar markiert, mit dem Allianznamen als Link zur Allianz-Ansicht.
- Hier lege ich neue Systeme und Einträge an und bearbeite oder lösche vorhandene. Name, Typ und die übrigen Felder der Galaxie sind editierbar, falsche Namen aus dem Import korrigiere ich selbst. Neue Galaxien kann ich über das Raster anlegen, nicht benötigte löschen.

### 3.3 Allianz-Ansicht
- Liste aller Stationen einer Allianz über alle Galaxien: Galaxie, System, Planet, Notiz. Klick führt zur Galaxie.
- Meine eigene Allianz hat einen festen Link in der Kopfzeile, auf jeder Seite erreichbar. Das ist der wichtigste Zugriff auf meine eigenen Raumstationen.
- Weitere Allianzen sind über eine Allianz-Auswahl erreichbar. Hier lege ich Allianzen an und bearbeite sie.

- **Allianz-Übersicht** (`/allianzen`): alle Allianzen mit Zahl der Stationen und Galaxien, Allianz anlegen. Eine Station einer fremden Allianz ist ein normaler Eintrag (Typ Raumstation) mit dieser Allianz.

### 3.3a HotG-Hubs
Seite `/hotg`: alle Hubs der Hitchhikers of the Galaxy aus dem Wiki, auch in nicht besuchten Galaxien. Spalten: Nummer, Galaxie, Besucht-Status, Hub-System, Portal-Glyphen (kopierbar), Entdecker, eigene Einträge. Filter alle / nicht besucht / besucht und Suche. Der Knopf „Von Fandom aktualisieren" holt die Liste frisch aus dem Wiki und meldet neue, geänderte und entfernte Hubs.

### 3.4 Globale Suche
Ein Suchfeld findet Treffer über Galaxien, Systeme und Einträge (Name, Planet, Notiz) und führt zur passenden Galaxie.

### 3.5 Gerät
Nur lokal am Mac mini im Browser. Der Server lauscht nur auf `127.0.0.1`, kein Zugriff aus dem WLAN, kein Handy/Tablet. Ich spiele auf der PS5 an einem eigenen Bildschirm. Die App kann daher den ganzen Mac-Bildschirm nutzen, ein Layout für ein kleines Fenster ist nicht nötig.

## 4. Technik

- Python mit Flask, SQLite als Datenbank, einfache HTML-Seiten mit etwas JavaScript. Kein aufwendiges Frontend-Framework nötig.
- Läuft lokal. Ein Startbefehl, danach im Browser aufrufen.
- Alle Daten liegen in einer einzigen Datei, damit ein Backup einfach ist.
- Export als JSON oder CSV (komplett) zur Sicherung.
- Schnell: Das Raster muss sofort laden und die Suche ohne Verzögerung filtern.

## 5. Datenimport

Beim ersten Start sollen zwei Quellen eingelesen werden.

**Quelle A: vollständige Galaxienliste (ursprünglich 257 Einträge laut PDF; Nr. 257 gibt es nicht und wurde entfernt, es bleiben 256).** Liegt als `galaxy-liste.pdf` im Projektordner (8 Seiten, gescanntes Bild ohne Text, daher OCR nötig, z. B. Tesseract; das Ergebnis danach mit mir prüfen). Daraus entstehen Nummer und Name aller Galaxien. Alle starten als nicht besucht.

**Quelle B: meine bisherige Numbers-Liste**, als CSV oder Excel exportiert. Spalten: `Name`, `Kategorie`, `Entdeckt`, `Bewertung`, `Kürzel`, `Sternenystem`, `Eigene Raumstation`, `Basen`, `Extras`. Sie enthält nur die besuchten oder geplanten Galaxien, vor allem Lush. Sie wird über den Galaxienamen mit Quelle A abgeglichen.

Regeln für die Übernahme:
- `Kategorie` → `typ`. Für Galaxien ohne Eintrag in Quelle B bleibt der Typ leer, bis ich ihn setze.
- `Entdeckt` (`X` oder `x`) → `besucht = wahr`.
- `Bewertung`: Anzahl der Sterne `*` bis `*****` → 1 bis 5. Werte wie `?`, `???` und `Magenta` ergeben `NULL`, der Originalwert landet in der Notiz.
- `Kürzel` → `kuerzel`.
- `Basen`, `Eigene Raumstation` und `Extras` sind Freitext in einer Zelle und sind **nicht automatisch sauber trennbar**. Sie werden als Notiz an der Galaxie übernommen, damit nichts verloren geht. Ich lege die einzelnen Einträge danach selbst an. Eine automatische Aufteilung ist nicht nötig.
- Zeilen ohne Galaxiename, Zeilen wie „NMS Freundescode" und die Summenzeile „Entdeckte Galaxien" werden ignoriert. Die Nummer in Spalte 1 der Numbers-Liste dient als Hauptschlüssel, der Name nur als Gegenprobe.
- #256 (Odyalutai) und #257 (Yilsrussimil) haben in den PDF-Listen den Typ „???". In Numbers ist #256 „Normal" und #257 „???". Der Typ aus Numbers gilt, sonst bleibt er leer, bis ich ihn setze.
- **Der Name aus der Numbers-Liste hat Vorrang** vor der Liste aus Quelle A, weil ich ihn dort geprüft und bei Bedarf korrigiert habe. Abgeglichen wird über die Nummer. Abweichungen kommen in die Abweichungsliste, z. B. #2 Hilbert / Hilbert Dimension, #5 Hyaden / Hyades, #19 Isdorajung / Isdoraijung, #21 Loychazing / Loychazinq, #50 Teyaypiny / Teyaypilny, #150 Zavailani / Zavainlani.
- Bei Galaxien ohne Eintrag in Numbers gilt der Name aus Quelle A (nicht geprüft, Schreibweise kann falsch sein).
- Die Spalte `Sternenystem` ist leer. Die Systeme stehen teils in anderen Spalten, z. B. „EZD Alibaba EZD Roshun" bei Ezdaranit (richtig ist `EZD Aibaba`, die Autokorrektur hat es in Numbers zu „Alibaba“ verändert). Alles geht als Notiz an die Galaxie.
- Nach dem Import soll eine kurze Liste ausgegeben werden: Galaxien aus Quelle B, die in Quelle A nicht gefunden wurden (Schreibweise abweichend).

## 6. Offene Punkte (vor oder beim Bauen klären)

1. ~~Farben~~ geklärt, siehe 3.1.
2. ~~Gerät~~ geklärt: nur lokal am Mac mini.
3. ~~Allianz-Stationen~~ geklärt: fester Bestandteil, eigene Tabelle `allianz` mit Kennzeichen `eigene`, eigene Allianz per festem Link erreichbar, weitere Allianzen möglich.
4. **Screenshots:** Pro Eintrag ein Bild? Aktuell nicht Teil der Spezifikation, das Datenmodell lässt sich später erweitern.

## 7. Vorgehen (schrittweise bauen)

1. Datenbank anlegen und Import aus Quelle A und B, danach Kontrolle des Ergebnisses mit mir.
2. Galaxie-Raster mit Farben, Besucht-Markierung, Suche und Filtern.
3. Galaxie-Ansicht mit dem Baum, noch nur lesend.
4. Anlegen, Bearbeiten und Löschen von Systemen und Einträgen.
5. Globale Suche, Export und Backup.

Nach jedem Schritt kurz erklären, was gebaut wurde, damit ich es nachvollziehen kann, bevor es weitergeht.
