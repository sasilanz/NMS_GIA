"""Fetches the list "All HotG galactic hubs discovered so far" from the NMS Fandom wiki
(via the MediaWiki API; the normal page blocks scripts) and stores it in nms.db.
Standard library only.   From a terminal:  .venv/bin/python hotg_import.py"""
import csv
import json
import re
import sqlite3
import urllib.request

API = ('https://nomanssky.fandom.com/api.php?action=parse&page=Hitchhikers_of_the_Galaxy'
       '&prop=wikitext&format=json')
ABSCHNITT = '===All HotG galactic hubs discovered so far==='
FELDER = ['galaxy_nr', 'system', 'entdeckt_von', 'glyphen', 'zugang', 'wiki_galaxie']


class ImportFehler(Exception):
    pass


def lade_wikitext():
    req = urllib.request.Request(API, headers={'User-Agent': 'Mozilla/5.0 (NMS-Tracker, lokal)'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)['parse']['wikitext']['*']
    except Exception as e:
        raise ImportFehler(f'{e}')


def parse(wikitext):
    """Gibt die Hubs als Liste von Dicts zurück (Reihenfolge wie im Wiki)."""
    if ABSCHNITT not in wikitext:
        raise ImportFehler('section "All HotG galactic hubs" not found in the wiki page')
    abschnitt = wikitext.split(ABSCHNITT)[1].split('\n==')[0]
    entf = lambda t: re.sub(r'</?nowiki>', '', t).strip()
    hubs = []
    for block in abschnitt.split('\n|-\n')[1:]:
        zellen = [z.strip() for z in re.split(r'\n\|\s|\s\|\|\s', '\n' + block.strip())][1:]
        if len(zellen) < 4:
            continue
        m = re.search(r'\((\d+)\)', zellen[1])
        if not m:
            continue
        g = re.search(r'\{\{Gl\|([0-9A-Fa-f]+)\}\}', zellen[3])
        hubs.append(dict(
            galaxy_nr=int(m.group(1)), system=entf(zellen[0]).lstrip('| ').strip(),
            entdeckt_von=entf(zellen[2]), glyphen=g.group(1).upper() if g else '',
            zugang='' if g else re.sub(r'\|\}\s*$', '', entf(zellen[3])).strip(),
            wiki_galaxie=re.sub(r'\[\[|\]\]|\s*\(\d+\)', '', zellen[1]).strip()))
    if len(hubs) < 20:
        raise ImportFehler(f'only {len(hubs)} hubs found, looks wrong; nothing changed')
    return hubs


def speichern(hubs, db_pfad='nms.db', csv_pfad='hotg_hubs.csv'):
    """Ersetzt die Tabelle hotg_hub komplett. Gibt (neu, entfernt, geaendert, uebersprungen) zurück."""
    con = sqlite3.connect(db_pfad)
    try:
        con.execute('PRAGMA foreign_keys = ON')
        con.execute("""CREATE TABLE IF NOT EXISTS hotg_hub (
            galaxy_nr INTEGER PRIMARY KEY REFERENCES galaxy(nr) ON DELETE CASCADE,
            system TEXT NOT NULL, entdeckt_von TEXT, glyphen TEXT, zugang TEXT)""")
        alt = {r[0]: r[1:] for r in con.execute(
            'SELECT galaxy_nr, system, entdeckt_von, glyphen, zugang FROM hotg_hub')}
        vorhanden = {r[0] for r in con.execute('SELECT nr FROM galaxy')}
        neu_daten, uebersprungen = {}, []
        for h in hubs:
            if h['galaxy_nr'] in vorhanden:
                neu_daten[h['galaxy_nr']] = (h['system'], h['entdeckt_von'] or None, h['glyphen'] or None, h['zugang'] or None)
            else:
                uebersprungen.append(h['galaxy_nr'])
        con.execute('DELETE FROM hotg_hub')
        con.executemany('INSERT INTO hotg_hub VALUES (?,?,?,?,?)', [(n, *d) for n, d in neu_daten.items()])
        con.commit()
    finally:
        con.close()
    with open(csv_pfad, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=FELDER)
        w.writeheader()
        w.writerows(hubs)
    neu = sorted(set(neu_daten) - set(alt))
    weg = sorted(set(alt) - set(neu_daten))
    geaendert = sorted(n for n in set(alt) & set(neu_daten) if tuple(alt[n]) != neu_daten[n])
    return neu, weg, geaendert, uebersprungen


def aktualisieren(db_pfad='nms.db', csv_pfad='hotg_hubs.csv'):
    return speichern(parse(lade_wikitext()), db_pfad, csv_pfad)


if __name__ == '__main__':
    neu, weg, geaendert, uebersprungen = aktualisieren()
    print(f'new: {neu or "-"}  removed: {weg or "-"}  changed: {geaendert or "-"}  skipped: {uebersprungen or "-"}')
