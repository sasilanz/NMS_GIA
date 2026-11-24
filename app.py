"""NMS Galaxie-Tracker: lokaler Flask-Server.
Start: .venv/bin/python app.py   ->   http://127.0.0.1:5050
"""
import csv
import datetime
import os
import re
import sqlite3
import unicodedata

from flask import (Flask, abort, g, jsonify, redirect, render_template, request,
                   send_from_directory, url_for)

import hotg_import
from exporter import EXPORT_DIR, erstelle_export, liste_exporte

# Einstellungen (Standard: nur lokal, Port 5050; 5000 ist am Mac von AirPlay belegt).
# Per Umgebungsvariable änderbar, z. B. für Docker: NMS_DB, NMS_HOST, NMS_PORT, NMS_EXPORT_DIR
DB = os.environ.get('NMS_DB', 'nms.db')
HOST = os.environ.get('NMS_HOST', '127.0.0.1')
PORT = int(os.environ.get('NMS_PORT', '5050'))

# Alle Farben der Oberfläche an EINER Stelle (werden als CSS-Variablen in die Seite geschrieben).
FARBEN = {
    'lush': '#61d836',     # grün
    'normal': '#73fdea',   # türkis
    'harsh': '#ff644e',    # rot-orange
    'empty': '#d5d5d5',    # hellgrau
    'ohne-typ': '#f4f4f4', # Typ unbekannt
    'besucht': '#ff95ca',  # rosa (Rot ist schon Harsh)
}
TYP_KLASSE = {'Lush': 'lush', 'Normal': 'normal', 'Harsh': 'harsh', 'Empty': 'empty'}

app = Flask(__name__)

# ---------------------------------------------------------------------------
# HotG-Hubs (Hitchhikers of the Galaxy): Referenzliste aus dem NMS-Wiki, auch für nicht besuchte Galaxien
# ---------------------------------------------------------------------------
HOTG_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hotg_hubs.csv')
HOTG_QUELLE = 'https://nomanssky.fandom.com/wiki/Hitchhikers_of_the_Galaxy#All_HotG_galactic_hubs_discovered_so_far'


def hotg_vorbereiten():
    """Legt die Tabelle hotg_hub an und füllt sie einmalig aus hotg_hubs.csv. Bestehende Daten bleiben unberührt.
    Neu einlesen (z. B. nach Wiki-Update): Tabelle hotg_hub leeren und App neu starten."""
    con = sqlite3.connect(DB)
    try:
        con.execute("""CREATE TABLE IF NOT EXISTS hotg_hub (
            galaxy_nr INTEGER PRIMARY KEY REFERENCES galaxy(nr) ON DELETE CASCADE,
            system TEXT NOT NULL, entdeckt_von TEXT, glyphen TEXT, zugang TEXT)""")
        if con.execute('SELECT COUNT(*) FROM hotg_hub').fetchone()[0] == 0 and os.path.exists(HOTG_CSV):
            with open(HOTG_CSV, newline='', encoding='utf-8') as f:
                zeilen = [(int(r['galaxy_nr']), r['system'], r['entdeckt_von'] or None,
                           r['glyphen'] or None, r['zugang'] or None) for r in csv.DictReader(f)]
            con.executemany("""INSERT OR IGNORE INTO hotg_hub (galaxy_nr, system, entdeckt_von, glyphen, zugang)
                               SELECT ?,?,?,?,? WHERE EXISTS (SELECT 1 FROM galaxy WHERE nr = ?)""",
                            [z + (z[0],) for z in zeilen])
        # Systemattribute (Lebensform, Wealth, Konflikt) nachrüsten, falls die DB noch ohne sie angelegt wurde
        spalten = {r[1] for r in con.execute('PRAGMA table_info(system)')}
        for spalte in ('lebensform TEXT', 'wealth INTEGER', 'konflikt INTEGER'):
            if spalte.split()[0] not in spalten:
                con.execute(f'ALTER TABLE system ADD COLUMN {spalte}')
        con.commit()
    finally:
        con.close()


if not os.path.exists(DB):  # erster Start: Datenbank mit allen Galaxien automatisch anlegen
    import init_db
    init_db.main(db=DB, still=True)
hotg_vorbereiten()


def db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    con = g.pop('db', None)
    if con is not None:
        con.close()


def galaxien():
    """Alle Galaxien fürs Raster, mit Zähler der Einträge (Basen, Stationen usw.)."""
    rows = db().execute("""
        SELECT ga.nr, ga.name, ga.kuerzel, ga.typ, ga.besucht,
               COUNT(e.id) AS eintraege,
               (SELECT 1 FROM hotg_hub h WHERE h.galaxy_nr = ga.nr) AS hotg,
               (SELECT GROUP_CONCAT(DISTINCT e2.allianz_id) FROM eintrag e2 JOIN system s2 ON s2.id = e2.system_id
                WHERE s2.galaxy_nr = ga.nr AND e2.allianz_id IS NOT NULL) AS allianzen
        FROM galaxy ga
        LEFT JOIN system s ON s.galaxy_nr = ga.nr
        LEFT JOIN eintrag e ON e.system_id = s.id
        GROUP BY ga.nr ORDER BY ga.nr
    """).fetchall()
    return [dict(r, klasse=TYP_KLASSE.get(r['typ'], 'ohne-typ'), besucht=bool(r['besucht']), hotg=bool(r['hotg']),
                 allianzen=r['allianzen'] or '')
            for r in rows]


@app.route('/')
def raster():
    al = db().execute('SELECT id, name, eigene FROM allianz ORDER BY eigene DESC, name COLLATE NOCASE').fetchall()
    return render_template('index.html', galaxien=galaxien(), farben=FARBEN, allianzen=[dict(a) for a in al])


@app.route('/hotg')
def hotg_seite():
    rows = db().execute("""
        SELECT h.galaxy_nr AS nr, h.system, h.entdeckt_von, h.glyphen, h.zugang,
               ga.name, ga.kuerzel, ga.typ, ga.besucht,
               (SELECT COUNT(*) FROM eintrag e JOIN system s ON s.id = e.system_id
                WHERE s.galaxy_nr = ga.nr) AS eintraege
        FROM hotg_hub h JOIN galaxy ga ON ga.nr = h.galaxy_nr ORDER BY h.galaxy_nr""").fetchall()
    hubs = [dict(r, klasse=TYP_KLASSE.get(r['typ'], 'ohne-typ'), besucht=bool(r['besucht'])) for r in rows]
    gesamt = db().execute('SELECT COUNT(*) FROM galaxy').fetchone()[0]
    stand = (datetime.datetime.fromtimestamp(os.path.getmtime(HOTG_CSV)).strftime('%d.%m.%Y %H:%M')
             if os.path.exists(HOTG_CSV) else None)
    return render_template('hotg.html', hubs=hubs, gesamt=gesamt, quelle=HOTG_QUELLE, stand=stand, farben=FARBEN)


@app.route('/api/hotg/aktualisieren', methods=['POST'])
def hotg_aktualisieren():
    """Holt die Hub-Liste frisch aus dem Wiki und ersetzt die lokale Liste."""
    try:
        neu, weg, geaendert, uebersprungen = hotg_import.aktualisieren(DB, HOTG_CSV)
    except hotg_import.ImportFehler as e:
        return jsonify(fehler=str(e)), 502
    return jsonify(neu=neu, entfernt=weg, geaendert=geaendert, uebersprungen=uebersprungen)


@app.route('/api/galaxy/<int:nr>/besucht', methods=['POST'])
def besucht_umschalten(nr):
    con = db()
    row = con.execute('SELECT besucht FROM galaxy WHERE nr = ?', (nr,)).fetchone()
    if row is None:
        abort(404)
    neu = 0 if row['besucht'] else 1
    con.execute('UPDATE galaxy SET besucht = ? WHERE nr = ?', (neu, nr))
    con.commit()
    return jsonify(nr=nr, besucht=bool(neu))


# ---------------------------------------------------------------------------
# Galaxie-Ansicht und Bearbeiten
# ---------------------------------------------------------------------------
GALAXIE_TYPEN = ('Lush', 'Normal', 'Harsh', 'Empty')
EINTRAG_TYPEN = ('Basis', 'Mini-Basis', 'Raumstation', 'Portal', 'Sonstiges')


class Eingabefehler(Exception):
    pass


@app.errorhandler(Eingabefehler)
def eingabefehler(e):
    return jsonify(fehler=str(e)), 400


def text_oder_none(wert):
    """Leerer Text wird zu NULL, sonst getrimmter Text."""
    if wert is None:
        return None
    wert = str(wert).strip()
    return wert or None


def pflicht_text(wert, feld):
    wert = text_oder_none(wert)
    if wert is None:
        raise Eingabefehler(f'{feld} darf nicht leer sein.')
    return wert


def pruefe_galaxy(feld, wert):
    if feld == 'name':
        return pflicht_text(wert, 'Name')
    if feld in ('kuerzel', 'notiz'):
        return text_oder_none(wert)
    if feld == 'typ':
        wert = text_oder_none(wert)
        if wert is not None and wert not in GALAXIE_TYPEN:
            raise Eingabefehler('Unbekannter Typ.')
        return wert
    if feld == 'bewertung':
        if wert in (None, ''):
            return None
        try:
            wert = int(wert)
        except (TypeError, ValueError):
            raise Eingabefehler('Bewertung muss 1 bis 5 sein.')
        if not 1 <= wert <= 5:
            raise Eingabefehler('Bewertung muss 1 bis 5 sein.')
        return wert
    if feld == 'besucht':
        return 1 if wert in (True, 1, '1', 'true') else 0
    raise Eingabefehler(f'Feld {feld} ist nicht änderbar.')


LEBENSFORMEN = ('Gek', "Vy'keen", 'Korvax')


def pruefe_system(feld, wert):
    if feld == 'name':
        return pflicht_text(wert, 'Systemname')
    if feld == 'notiz':
        return text_oder_none(wert)
    if feld == 'lebensform':
        wert = text_oder_none(wert)
        if wert is not None and wert not in LEBENSFORMEN:
            raise Eingabefehler('Unbekannte Lebensform.')
        return wert
    if feld in ('wealth', 'konflikt'):
        if wert in (None, ''):
            return None
        try:
            wert = int(wert)
        except (TypeError, ValueError):
            raise Eingabefehler('Wert muss 1 bis 3 sein.')
        if not 1 <= wert <= 3:
            raise Eingabefehler('Wert muss 1 bis 3 sein.')
        return wert
    raise Eingabefehler(f'Feld {feld} ist nicht änderbar.')


def pruefe_eintrag(feld, wert):
    if feld == 'name':
        return pflicht_text(wert, 'Name')
    if feld in ('planet', 'notiz'):
        return text_oder_none(wert)
    if feld == 'typ':
        if wert not in EINTRAG_TYPEN:
            raise Eingabefehler('Unbekannter Eintragstyp.')
        return wert
    if feld == 'allianz_id':
        if wert in (None, ''):
            return None
        row = db().execute('SELECT id FROM allianz WHERE id = ?', (wert,)).fetchone()
        if row is None:
            raise Eingabefehler('Allianz gibt es nicht.')
        return row['id']
    raise Eingabefehler(f'Feld {feld} ist nicht änderbar.')


def aendern(tabelle, schluessel, wert_id, daten, pruefer):
    """Ändert die übergebenen Felder (nur erlaubte, geprüfte) und gibt die Zeile zurück."""
    con = db()
    if con.execute(f'SELECT 1 FROM {tabelle} WHERE {schluessel} = ?', (wert_id,)).fetchone() is None:
        abort(404)
    if not isinstance(daten, dict) or not daten:
        raise Eingabefehler('Keine Daten.')
    felder = {feld: pruefer(feld, wert) for feld, wert in daten.items()}
    sets = ', '.join(f'{feld} = ?' for feld in felder)
    con.execute(f'UPDATE {tabelle} SET {sets} WHERE {schluessel} = ?', (*felder.values(), wert_id))
    con.commit()
    return dict(con.execute(f'SELECT * FROM {tabelle} WHERE {schluessel} = ?', (wert_id,)).fetchone())


def galaxie_komplett(nr):
    con = db()
    ga = con.execute('SELECT * FROM galaxy WHERE nr = ?', (nr,)).fetchone()
    if ga is None:
        abort(404)
    systeme = []
    for s in con.execute('SELECT * FROM system WHERE galaxy_nr = ? ORDER BY name COLLATE NOCASE', (nr,)):
        eintraege = [dict(e) for e in con.execute(
            'SELECT * FROM eintrag WHERE system_id = ? ORDER BY typ, name COLLATE NOCASE', (s['id'],))]
        systeme.append(dict(s, eintraege=eintraege))
    ga = dict(ga, besucht=bool(ga['besucht']), klasse=TYP_KLASSE.get(ga['typ'], 'ohne-typ'))
    vorher = con.execute('SELECT MAX(nr) FROM galaxy WHERE nr < ?', (nr,)).fetchone()[0]
    nachher = con.execute('SELECT MIN(nr) FROM galaxy WHERE nr > ?', (nr,)).fetchone()[0]
    allianzen = [dict(a) for a in con.execute('SELECT * FROM allianz ORDER BY eigene DESC, name COLLATE NOCASE')]
    hub = con.execute('SELECT * FROM hotg_hub WHERE galaxy_nr = ?', (nr,)).fetchone()
    return dict(galaxy=ga, systeme=systeme, allianzen=allianzen, vorher=vorher, nachher=nachher,
                hotg=dict(hub) if hub else None)


@app.route('/galaxy/<int:nr>')
def galaxie_ansicht(nr):
    daten = galaxie_komplett(nr)
    return render_template('galaxy.html', daten=daten, farben=FARBEN,
                           galaxie_typen=GALAXIE_TYPEN, eintrag_typen=EINTRAG_TYPEN,
                           lebensformen=LEBENSFORMEN)


@app.route('/api/galaxy/<int:nr>')
def api_galaxie(nr):
    return jsonify(galaxie_komplett(nr))


@app.route('/api/galaxy', methods=['POST'])
def galaxie_anlegen():
    d = request.get_json(silent=True) or {}
    try:
        nr = int(d.get('nr'))
    except (TypeError, ValueError):
        raise Eingabefehler('Nummer fehlt oder ist keine Zahl.')
    if nr < 1:
        raise Eingabefehler('Nummer muss größer als 0 sein.')
    name = pflicht_text(d.get('name'), 'Name')
    typ = pruefe_galaxy('typ', d.get('typ'))
    con = db()
    if con.execute('SELECT 1 FROM galaxy WHERE nr = ?', (nr,)).fetchone():
        raise Eingabefehler(f'Galaxie {nr} gibt es schon.')
    con.execute('INSERT INTO galaxy (nr, name, typ) VALUES (?,?,?)', (nr, name, typ))
    con.commit()
    return jsonify(nr=nr), 201


@app.route('/api/galaxy/<int:nr>', methods=['PATCH'])
def galaxie_aendern(nr):
    return jsonify(aendern('galaxy', 'nr', nr, request.get_json(silent=True), pruefe_galaxy))


@app.route('/api/galaxy/<int:nr>', methods=['DELETE'])
def galaxie_loeschen(nr):
    con = db()
    if con.execute('SELECT 1 FROM galaxy WHERE nr = ?', (nr,)).fetchone() is None:
        abort(404)
    con.execute('DELETE FROM galaxy WHERE nr = ?', (nr,))  # Systeme und Einträge folgen per CASCADE
    con.commit()
    return jsonify(geloescht=nr)


@app.route('/api/galaxy/<int:nr>/system', methods=['POST'])
def system_anlegen(nr):
    con = db()
    if con.execute('SELECT 1 FROM galaxy WHERE nr = ?', (nr,)).fetchone() is None:
        abort(404)
    d = request.get_json(silent=True) or {}
    name = pflicht_text(d.get('name') or 'Neues System', 'Systemname')
    cur = con.execute('INSERT INTO system (galaxy_nr, name) VALUES (?,?)', (nr, name))
    con.commit()
    return jsonify(dict(con.execute('SELECT * FROM system WHERE id = ?', (cur.lastrowid,)).fetchone(),
                        eintraege=[])), 201


@app.route('/api/system/<int:sid>', methods=['PATCH'])
def system_aendern(sid):
    return jsonify(aendern('system', 'id', sid, request.get_json(silent=True), pruefe_system))


@app.route('/api/system/<int:sid>', methods=['DELETE'])
def system_loeschen(sid):
    con = db()
    if con.execute('SELECT 1 FROM system WHERE id = ?', (sid,)).fetchone() is None:
        abort(404)
    con.execute('DELETE FROM system WHERE id = ?', (sid,))
    con.commit()
    return jsonify(geloescht=sid)


@app.route('/api/system/<int:sid>/eintrag', methods=['POST'])
def eintrag_anlegen(sid):
    con = db()
    if con.execute('SELECT 1 FROM system WHERE id = ?', (sid,)).fetchone() is None:
        abort(404)
    d = request.get_json(silent=True) or {}
    typ = pruefe_eintrag('typ', d.get('typ') or 'Basis')
    name = pflicht_text(d.get('name') or 'Neuer Eintrag', 'Name')
    allianz_id = pruefe_eintrag('allianz_id', d.get('allianz_id'))
    cur = con.execute('INSERT INTO eintrag (system_id, typ, name, allianz_id) VALUES (?,?,?,?)',
                      (sid, typ, name, allianz_id))
    con.commit()
    return jsonify(dict(con.execute('SELECT * FROM eintrag WHERE id = ?', (cur.lastrowid,)).fetchone())), 201


@app.route('/api/eintrag/<int:eid>', methods=['PATCH'])
def eintrag_aendern(eid):
    return jsonify(aendern('eintrag', 'id', eid, request.get_json(silent=True), pruefe_eintrag))


@app.route('/api/eintrag/<int:eid>', methods=['DELETE'])
def eintrag_loeschen(eid):
    con = db()
    if con.execute('SELECT 1 FROM eintrag WHERE id = ?', (eid,)).fetchone() is None:
        abort(404)
    con.execute('DELETE FROM eintrag WHERE id = ?', (eid,))
    con.commit()
    return jsonify(geloescht=eid)


# ---------------------------------------------------------------------------
# Allianzen
# ---------------------------------------------------------------------------
@app.context_processor
def eigene_allianz_fuer_alle_seiten():
    """Macht die eigene Allianz in allen Seiten verfügbar (fester Link in der Kopfzeile)."""
    row = db().execute('SELECT id, name FROM allianz WHERE eigene = 1 LIMIT 1').fetchone()
    return dict(eigene_allianz=dict(row) if row else None)


def pruefe_allianz(feld, wert):
    if feld == 'name':
        return pflicht_text(wert, 'Allianzname')
    if feld == 'notiz':
        return text_oder_none(wert)
    raise Eingabefehler(f'Feld {feld} ist nicht änderbar.')


def allianz_komplett(aid):
    con = db()
    al = con.execute('SELECT * FROM allianz WHERE id = ?', (aid,)).fetchone()
    if al is None:
        abort(404)
    stationen = [dict(r) for r in con.execute("""
        SELECT e.id, e.typ, e.name, e.planet, e.notiz,
               s.id AS system_id, s.name AS system_name,
               ga.nr AS galaxy_nr, ga.name AS galaxy_name
        FROM eintrag e
        JOIN system s ON s.id = e.system_id
        JOIN galaxy ga ON ga.nr = s.galaxy_nr
        WHERE e.allianz_id = ?
        ORDER BY ga.nr, s.name COLLATE NOCASE, e.name COLLATE NOCASE""", (aid,))]
    alle = [dict(r) for r in con.execute("""
        SELECT a.id, a.name, a.eigene, COUNT(e.id) AS anzahl
        FROM allianz a LEFT JOIN eintrag e ON e.allianz_id = a.id
        GROUP BY a.id ORDER BY a.eigene DESC, a.name COLLATE NOCASE""")]
    return dict(allianz=dict(al, eigene=bool(al['eigene'])), stationen=stationen, alle=alle)


@app.route('/allianzen')
def allianzen_uebersicht():
    rows = db().execute("""
        SELECT a.id, a.name, a.eigene, a.notiz, COUNT(e.id) AS stationen,
               COUNT(DISTINCT s.galaxy_nr) AS galaxien
        FROM allianz a
        LEFT JOIN eintrag e ON e.allianz_id = a.id
        LEFT JOIN system s ON s.id = e.system_id
        GROUP BY a.id ORDER BY a.eigene DESC, a.name COLLATE NOCASE""").fetchall()
    return render_template('allianzen.html', allianzen=[dict(r, eigene=bool(r['eigene'])) for r in rows],
                           farben=FARBEN)


@app.route('/allianz')
def allianz_eigene():
    row = db().execute('SELECT id FROM allianz WHERE eigene = 1 LIMIT 1').fetchone()
    if row is None:
        row = db().execute('SELECT id FROM allianz ORDER BY id LIMIT 1').fetchone()
    if row is None:
        abort(404)
    return redirect(url_for('allianz_ansicht', aid=row['id']))


@app.route('/allianz/<int:aid>')
def allianz_ansicht(aid):
    return render_template('allianz.html', daten=allianz_komplett(aid), farben=FARBEN)


@app.route('/api/allianz', methods=['POST'])
def allianz_anlegen():
    d = request.get_json(silent=True) or {}
    name = pflicht_text(d.get('name'), 'Allianzname')
    con = db()
    cur = con.execute('INSERT INTO allianz (name, eigene) VALUES (?, 0)', (name,))
    con.commit()
    return jsonify(id=cur.lastrowid), 201


@app.route('/api/allianz/<int:aid>', methods=['PATCH'])
def allianz_aendern(aid):
    return jsonify(aendern('allianz', 'id', aid, request.get_json(silent=True), pruefe_allianz))


@app.route('/api/allianz/<int:aid>/eigene', methods=['POST'])
def allianz_als_eigene(aid):
    """Macht diese Allianz zur eigenen. Es gibt immer genau eine."""
    con = db()
    if con.execute('SELECT 1 FROM allianz WHERE id = ?', (aid,)).fetchone() is None:
        abort(404)
    con.execute('UPDATE allianz SET eigene = CASE WHEN id = ? THEN 1 ELSE 0 END', (aid,))
    con.commit()
    return jsonify(eigene=aid)


@app.route('/api/allianz/<int:aid>', methods=['DELETE'])
def allianz_loeschen(aid):
    con = db()
    row = con.execute('SELECT eigene FROM allianz WHERE id = ?', (aid,)).fetchone()
    if row is None:
        abort(404)
    if row['eigene']:
        raise Eingabefehler('Die eigene Allianz lässt sich nicht löschen. Lege zuerst eine andere als eigene fest.')
    con.execute('DELETE FROM allianz WHERE id = ?', (aid,))  # Einträge bleiben, allianz_id wird leer
    con.commit()
    return jsonify(geloescht=aid)


# ---------------------------------------------------------------------------
# Sicherung (Export), die eigentliche Arbeit macht exporter.py
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Globale Suche über Galaxien, Systeme und Einträge
# ---------------------------------------------------------------------------
MAX_TREFFER = 300


def falten(text):
    """Klein schreiben und Akzente/Umlaute auf den Grundbuchstaben bringen (ä -> a), ohne die Länge zu ändern."""
    return ''.join('s' if c == 'ß' else unicodedata.normalize('NFKD', c)[0].lower() for c in (text or ''))


def varianten(wort):
    """Schreibweisen eines Suchworts: 'ueber' findet auch 'über' (im Text ist ü zu u gefaltet), 'strasse' auch 'straße'."""
    ersatz = {'ae': 'a', 'oe': 'o', 'ue': 'u', 'ss': 's'}
    return {wort, re.sub('ae|oe|ue|ss', lambda m: ersatz[m.group()], wort)}


def schnipsel(text, woerter, breite=70):
    """Kurzer Textausschnitt um den ersten Treffer, mit … an abgeschnittenen Enden."""
    if not text:
        return None
    gefaltet = falten(text)
    pos = [gefaltet.find(w) for w in woerter if gefaltet.find(w) >= 0]
    if not pos:
        return None
    start = max(0, min(pos) - breite // 2)
    ende = min(len(text), start + breite * 2)
    return ('…' if start > 0 else '') + text[start:ende].replace('\n', ' · ') + ('…' if ende < len(text) else '')


def suche(anfrage):
    """Alle Wörter der Anfrage müssen vorkommen (UND). Gibt Treffer geordnet zurück:
    zuerst Einträge, dann Systeme, dann Galaxien, jeweils nach Galaxie-Nummer."""
    woerter = [w for w in falten(anfrage).split() if w]
    if not woerter:
        return []
    varianten_je_wort = [varianten(w) for w in woerter]
    alle_varianten = sorted({v for gruppe in varianten_je_wort for v in gruppe})
    con = db()

    def pruefe(felder, nr=None):
        """felder: Liste (Bezeichnung, Text). Gibt (passt, [Bezeichnungen mit Treffer]) zurück."""
        gefaltet = [(b, falten(t)) for b, t in felder]
        alle = '\n'.join(t for _, t in gefaltet)
        for w, gruppe in zip(woerter, varianten_je_wort):
            if w.isdigit() and nr is not None and w == str(nr):
                continue  # genau diese Galaxie-Nummer
            if not any(v in alle for v in gruppe):
                return False, []
        treffer_in = [b for b, t in gefaltet if any(v in t for v in alle_varianten)]
        if nr is not None and str(nr) in woerter:
            treffer_in.insert(0, 'Nummer')
        return True, treffer_in

    ergebnisse = []
    for r in con.execute("""
            SELECT e.id, e.typ, e.name, e.planet, e.notiz, a.name AS allianz, a.eigene,
                   s.id AS system_id, s.name AS system_name, ga.nr, ga.name AS galaxy_name, ga.typ AS galaxy_typ
            FROM eintrag e
            JOIN system s ON s.id = e.system_id
            JOIN galaxy ga ON ga.nr = s.galaxy_nr
            LEFT JOIN allianz a ON a.id = e.allianz_id
            ORDER BY ga.nr, s.name COLLATE NOCASE, e.name COLLATE NOCASE"""):
        ok, wo = pruefe([('Name', r['name']), ('Planet', r['planet']), ('Notiz', r['notiz']),
                         ('Typ', r['typ']), ('Allianz', r['allianz'])])
        if ok:
            ergebnisse.append(dict(art='eintrag', id=r['id'], galaxy_nr=r['nr'], galaxy_name=r['galaxy_name'],
                                   galaxy_klasse=TYP_KLASSE.get(r['galaxy_typ'], 'ohne-typ'),
                                   system_id=r['system_id'], system_name=r['system_name'],
                                   typ=r['typ'], titel=r['name'], planet=r['planet'], allianz=r['allianz'],
                                   eigene=bool(r['eigene']), treffer_in=wo,
                                   auszug=schnipsel(r['notiz'], alle_varianten) if 'Notiz' in wo else None))
    for r in con.execute("""
            SELECT s.id, s.name, s.notiz, ga.nr, ga.name AS galaxy_name, ga.typ AS galaxy_typ
            FROM system s JOIN galaxy ga ON ga.nr = s.galaxy_nr
            ORDER BY ga.nr, s.name COLLATE NOCASE"""):
        ok, wo = pruefe([('Name', r['name']), ('Notiz', r['notiz'])])
        if ok:
            ergebnisse.append(dict(art='system', id=r['id'], galaxy_nr=r['nr'], galaxy_name=r['galaxy_name'],
                                   galaxy_klasse=TYP_KLASSE.get(r['galaxy_typ'], 'ohne-typ'),
                                   titel=r['name'], treffer_in=wo,
                                   auszug=schnipsel(r['notiz'], alle_varianten) if 'Notiz' in wo else None))
    for r in con.execute('SELECT * FROM galaxy ORDER BY nr'):
        ok, wo = pruefe([('Name', r['name']), ('Kürzel', r['kuerzel']), ('Notiz', r['notiz'])], nr=r['nr'])
        if ok:
            ergebnisse.append(dict(art='galaxie', id=r['nr'], galaxy_nr=r['nr'], galaxy_name=r['name'],
                                   galaxy_klasse=TYP_KLASSE.get(r['typ'], 'ohne-typ'),
                                   titel=r['name'], kuerzel=r['kuerzel'], besucht=bool(r['besucht']),
                                   treffer_in=wo,
                                   auszug=schnipsel(r['notiz'], alle_varianten) if 'Notiz' in wo else None))
    return ergebnisse


@app.route('/suche')
def suche_seite():
    return render_template('suche.html', farben=FARBEN, q=request.args.get('q', ''))


@app.route('/api/suche')
def suche_api():
    treffer = suche(request.args.get('q', ''))
    return jsonify(treffer=treffer[:MAX_TREFFER], gesamt=len(treffer))


# ---------------------------------------------------------------------------
# Aufräumen: Galaxien, deren Notiz noch alten Freitext aus Numbers enthält
# ---------------------------------------------------------------------------
# Der Import schreibt jede Freitext-Spalte als Zeile "Spaltenname: Text" in die Notiz.
ALTTEXT_ZEILE = re.compile(r'^(Sternenystem|Eigene Raumstation|Basen|Extras): ?(.*)$')


def alttext_zeilen(notiz):
    """Zerlegt eine Notiz in (Spalte, Text)-Zeilen mit altem Freitext. Andere Zeilen zählen nicht."""
    zeilen = []
    for zeile in (notiz or '').split('\n'):
        m = ALTTEXT_ZEILE.match(zeile)
        if m and m.group(2).strip():
            zeilen.append((m.group(1), m.group(2).strip()))
    return zeilen


@app.route('/aufraeumen')
def aufraeumen():
    rows = db().execute("""
        SELECT ga.nr, ga.name, ga.kuerzel, ga.typ, ga.besucht, ga.notiz,
               (SELECT COUNT(*) FROM system s WHERE s.galaxy_nr = ga.nr) AS systeme,
               (SELECT COUNT(*) FROM eintrag e JOIN system s ON s.id = e.system_id WHERE s.galaxy_nr = ga.nr) AS eintraege
        FROM galaxy ga WHERE ga.notiz IS NOT NULL ORDER BY ga.nr""").fetchall()
    offen = []
    for r in rows:
        zeilen = alttext_zeilen(r['notiz'])
        if zeilen:
            offen.append(dict(r, klasse=TYP_KLASSE.get(r['typ'], 'ohne-typ'), zeilen=zeilen))
    gesamt_galaxien_mit_daten = db().execute(
        'SELECT COUNT(DISTINCT galaxy_nr) FROM system').fetchone()[0]
    return render_template('aufraeumen.html', offen=offen, farben=FARBEN,
                           mit_systemen=gesamt_galaxien_mit_daten)


@app.context_processor
def aufraeum_zaehler():
    """Zahl der noch offenen Galaxien für den Knopf im Raster."""
    n = sum(1 for (notiz,) in db().execute('SELECT notiz FROM galaxy WHERE notiz IS NOT NULL') if alttext_zeilen(notiz))
    return dict(aufraeumen_offen=n)


EXPORT_ORDNER_MUSTER = re.compile(r'\d{4}-\d{2}-\d{2}_\d{6}(-\d+)?')
EXPORT_DATEIEN = {'nms.db', 'nms.json', 'galaxien.csv', 'systeme.csv', 'eintraege.csv', 'allianzen.csv'}


@app.route('/export')
def export_seite():
    return render_template('export.html', exporte=liste_exporte(EXPORT_DIR), farben=FARBEN)


@app.route('/api/export', methods=['POST'])
def export_erstellen():
    try:
        return jsonify(erstelle_export(DB, EXPORT_DIR)), 201
    except (OSError, sqlite3.Error) as e:
        return jsonify(fehler=f'Export fehlgeschlagen: {e}'), 500


@app.route('/export/datei/<ordner>/<datei>')
def export_datei(ordner, datei):
    # Nur echte Export-Ordner (Zeitstempel) und nur die bekannten Dateinamen, sonst 404.
    if not EXPORT_ORDNER_MUSTER.fullmatch(ordner) or datei not in EXPORT_DATEIEN:
        abort(404)
    return send_from_directory(os.path.join(EXPORT_DIR, ordner), datei, as_attachment=True)


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=False)
