"""Sicherung (Export) der kompletten Datenbank.

Jeder Export liegt in einem eigenen Ordner  export/JJJJ-MM-TT_HHMMSS/  mit:
  nms.db            vollständige Kopie der Datenbank (zum Wiederherstellen)
  nms.json          alle Daten als JSON
  galaxien.csv, systeme.csv, eintraege.csv, allianzen.csv    für Numbers/Excel
Alte Exporte werden nie automatisch gelöscht.

Aufruf im Terminal:  .venv/bin/python exporter.py
Wird auch von app.py (Seite „Sicherung“) benutzt.
"""
import csv
import datetime
import json
import os
import sqlite3

DB = os.environ.get('NMS_DB', 'nms.db')
EXPORT_DIR = os.environ.get('NMS_EXPORT_DIR', 'export')
TABELLEN = ('galaxy', 'system', 'eintrag', 'allianz', 'hotg_hub')


def _neuer_ordner(basis):
    """Legt einen neuen, noch nicht vorhandenen Zeitstempel-Ordner an."""
    stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    name, n = stamp, 1
    while os.path.exists(os.path.join(basis, name)):
        n += 1
        name = f'{stamp}-{n}'
    pfad = os.path.join(basis, name)
    os.makedirs(pfad)
    return name, pfad


def _csv_schreiben(pfad, kopf, zeilen):
    # utf-8-sig: Umlaute werden in Excel und Numbers richtig erkannt
    with open(pfad, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(kopf)
        w.writerows(zeilen)


def erstelle_export(db_pfad=DB, basis=EXPORT_DIR):
    """Erzeugt einen vollständigen Export und gibt Ordnername, Pfad und Dateien zurück."""
    os.makedirs(basis, exist_ok=True)
    name, ordner = _neuer_ordner(basis)

    src = sqlite3.connect(db_pfad)
    src.row_factory = sqlite3.Row
    try:
        # 1. Konsistente Kopie der Datenbank (auch bei laufendem Server sicher)
        dst = sqlite3.connect(os.path.join(ordner, 'nms.db'))
        src.backup(dst)
        dst.close()

        # 2. JSON mit allen Tabellen
        daten = {t: [dict(r) for r in src.execute(f'SELECT * FROM {t} ORDER BY 1')] for t in TABELLEN}
        daten['erstellt'] = datetime.datetime.now().isoformat(timespec='seconds')
        with open(os.path.join(ordner, 'nms.json'), 'w', encoding='utf-8') as f:
            json.dump(daten, f, ensure_ascii=False, indent=2)

        # 3. CSV-Dateien, lesbar mit Namen statt nur Nummern
        _csv_schreiben(os.path.join(ordner, 'galaxien.csv'),
                       ['Nr', 'Name', 'Kürzel', 'Typ', 'Besucht', 'Bewertung', 'Notiz'],
                       [(r['nr'], r['name'], r['kuerzel'], r['typ'], 'X' if r['besucht'] else '',
                         r['bewertung'], r['notiz'])
                        for r in src.execute('SELECT * FROM galaxy ORDER BY nr')])
        _csv_schreiben(os.path.join(ordner, 'systeme.csv'),
                       ['Galaxie Nr', 'Galaxie', 'System', 'Lebensform', 'Wealth', 'Konflikt', 'Notiz'],
                       [tuple(r) for r in src.execute("""
                           SELECT ga.nr, ga.name, s.name, s.lebensform, s.wealth, s.konflikt, s.notiz
                           FROM system s JOIN galaxy ga ON ga.nr = s.galaxy_nr
                           ORDER BY ga.nr, s.name COLLATE NOCASE""")])
        _csv_schreiben(os.path.join(ordner, 'eintraege.csv'),
                       ['Galaxie Nr', 'Galaxie', 'System', 'Typ', 'Name', 'Planet', 'Allianz', 'Notiz'],
                       [tuple(r) for r in src.execute("""
                           SELECT ga.nr, ga.name, s.name, e.typ, e.name, e.planet, a.name, e.notiz
                           FROM eintrag e
                           JOIN system s ON s.id = e.system_id
                           JOIN galaxy ga ON ga.nr = s.galaxy_nr
                           LEFT JOIN allianz a ON a.id = e.allianz_id
                           ORDER BY ga.nr, s.name COLLATE NOCASE, e.name COLLATE NOCASE""")])
        _csv_schreiben(os.path.join(ordner, 'allianzen.csv'),
                       ['Name', 'Eigene', 'Notiz'],
                       [(r['name'], 'ja' if r['eigene'] else '', r['notiz'])
                        for r in src.execute('SELECT * FROM allianz ORDER BY eigene DESC, name COLLATE NOCASE')])
        anzahl = {t: len(daten[t]) for t in TABELLEN}
    finally:
        src.close()

    dateien = sorted(os.listdir(ordner))
    return dict(name=name, pfad=os.path.abspath(ordner), dateien=dateien, anzahl=anzahl)


def liste_exporte(basis=EXPORT_DIR):
    """Alle vorhandenen Exporte, neueste zuerst, mit Dateigrößen."""
    if not os.path.isdir(basis):
        return []
    ergebnis = []
    for name in sorted(os.listdir(basis), reverse=True):
        ordner = os.path.join(basis, name)
        if not os.path.isdir(ordner):
            continue
        dateien = [(d, os.path.getsize(os.path.join(ordner, d))) for d in sorted(os.listdir(ordner))]
        ergebnis.append(dict(name=name, pfad=os.path.abspath(ordner), dateien=dateien))
    return ergebnis


if __name__ == '__main__':
    e = erstelle_export()
    print(f"Export fertig: {e['pfad']}")
    print('Dateien:', ', '.join(e['dateien']))
    print('Zeilen:', ', '.join(f'{t} {n}' for t, n in e['anzahl'].items()))
