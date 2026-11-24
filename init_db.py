"""Legt nms.db an und importiert die Galaxien (Quelle A + Numbers-Liste).
Aufruf: python init_db.py                      (bricht ab, wenn die Datenbank schon existiert)
        python init_db.py --neu                (löscht die Datenbank und baut sie neu auf)
        python init_db.py --allianz "Meine ABC" (Name der eigenen Allianz, Standard: "Meine Allianz")
Quelle B (galaxie_numbers.csv, eigene Numbers-Liste) ist optional: Fehlt die Datei, starten alle
Galaxien als „nicht besucht“. Der Datenbankpfad lässt sich mit der Umgebungsvariable NMS_DB ändern.
Nur Standardbibliothek."""
import csv, os, sqlite3, sys

DB = os.environ.get('NMS_DB', 'nms.db')
QUELLE_A = 'galaxien_quelle_a.csv'
QUELLE_B = 'galaxie_numbers.csv'
TYPEN = {'Lush', 'Normal', 'Harsh', 'Empty'}

SCHEMA = """
CREATE TABLE galaxy (
    nr INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    kuerzel TEXT,
    typ TEXT CHECK (typ IN ('Lush','Normal','Harsh','Empty')),
    besucht INTEGER NOT NULL DEFAULT 0,
    bewertung INTEGER CHECK (bewertung BETWEEN 1 AND 5),
    notiz TEXT
);
CREATE TABLE allianz (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    eigene INTEGER NOT NULL DEFAULT 0,
    notiz TEXT
);
CREATE TABLE system (
    id INTEGER PRIMARY KEY,
    galaxy_nr INTEGER NOT NULL REFERENCES galaxy(nr) ON DELETE CASCADE,
    name TEXT NOT NULL,
    lebensform TEXT CHECK (lebensform IN ('Gek','Vy''keen','Korvax')),
    wealth INTEGER CHECK (wealth BETWEEN 1 AND 3),
    konflikt INTEGER CHECK (konflikt BETWEEN 1 AND 3),
    notiz TEXT
);
CREATE TABLE eintrag (
    id INTEGER PRIMARY KEY,
    system_id INTEGER NOT NULL REFERENCES system(id) ON DELETE CASCADE,
    typ TEXT NOT NULL CHECK (typ IN ('Basis','Mini-Basis','Raumstation','Portal','Sonstiges')),
    name TEXT NOT NULL,
    planet TEXT,
    allianz_id INTEGER REFERENCES allianz(id) ON DELETE SET NULL,
    notiz TEXT
);
CREATE INDEX idx_system_galaxy ON system(galaxy_nr);
CREATE INDEX idx_eintrag_system ON eintrag(system_id);
CREATE INDEX idx_eintrag_allianz ON eintrag(allianz_id);
"""


def lies(pfad):
    with open(pfad, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def main(db=None, allianz=None, still=False):
    """Baut die Datenbank auf. db und allianz überschreiben Voreinstellung bzw. Kommandozeile."""
    db = db or DB
    if allianz is None:
        allianz = sys.argv[sys.argv.index('--allianz') + 1] if '--allianz' in sys.argv else 'Meine Allianz'
    if os.path.exists(db):
        if '--neu' not in sys.argv:
            sys.exit(f'{db} existiert schon. Mit --neu neu aufbauen (löscht alle Daten!).')
        os.remove(db)
    ordner = os.path.dirname(db)
    if ordner:
        os.makedirs(ordner, exist_ok=True)
    quellen = os.path.dirname(os.path.abspath(__file__))
    qa, qb = os.path.join(quellen, QUELLE_A), os.path.join(quellen, QUELLE_B)

    con = sqlite3.connect(db)
    con.execute('PRAGMA foreign_keys = ON')
    con.executescript(SCHEMA)

    # Quelle A: Nummer, Name, Typ (alle starten als nicht besucht)
    a = {int(r['nr']): r for r in lies(qa)}
    galaxien = {n: dict(name=r['name'], typ=r['typ'] or None, kuerzel=None,
                        besucht=0, bewertung=None, notiz=None) for n, r in a.items()}

    abweichungen, nicht_in_a = [], []

    # Quelle B: Numbers-Liste
    for r in (lies(qb) if os.path.exists(qb) else []):
        n = int(r['Nr'])
        name = r['Name'].strip()
        if not name or name == 'NMS Freundescode':
            continue
        if n not in galaxien:
            nicht_in_a.append((n, name))
            continue
        g = galaxien[n]
        if name != g['name']:
            abweichungen.append(f"#{n}: Numbers '{name}' | Quelle A '{g['name']}' -> Numbers gilt")
        g['name'] = name  # Numbers-Name hat Vorrang

        kat = r['Kategorie'].strip()
        if kat in TYPEN:
            g['typ'] = kat
        elif kat:
            abweichungen.append(f"#{n} {name}: Kategorie '{kat}' unbekannt -> Typ bleibt '{g['typ']}'")

        if r['Entdeckt'].strip().lower() == 'x':
            g['besucht'] = 1
        g['kuerzel'] = r['Kürzel'].strip() or None

        notizen = []
        bew = r['Bewertung'].strip()
        if bew and set(bew) == {'*'} and len(bew) <= 5:
            g['bewertung'] = len(bew)
        elif bew:
            notizen.append(f'Bewertung (Original): {bew}')
        for spalte in ('Sternenystem', 'Eigene Raumstation', 'Basen', 'Extras'):
            wert = r[spalte].strip()
            if wert:
                notizen.append(f'{spalte}: {wert}')
        g['notiz'] = '\n'.join(notizen) or None

    con.executemany(
        'INSERT INTO galaxy (nr,name,kuerzel,typ,besucht,bewertung,notiz) VALUES (?,?,?,?,?,?,?)',
        [(n, g['name'], g['kuerzel'], g['typ'], g['besucht'], g['bewertung'], g['notiz'])
         for n, g in sorted(galaxien.items())])
    con.execute("INSERT INTO allianz (name, eigene) VALUES (?, 1)", (allianz,))
    con.commit()

    if still:
        con.close()
        return
    # Kontrolle
    z = lambda sql: con.execute(sql).fetchone()[0]
    print(f"Galaxien: {z('SELECT COUNT(*) FROM galaxy')}, besucht: {z('SELECT SUM(besucht) FROM galaxy')}, "
          f"mit Notiz: {z('SELECT COUNT(*) FROM galaxy WHERE notiz IS NOT NULL')}, "
          f"ohne Typ: {z('SELECT COUNT(*) FROM galaxy WHERE typ IS NULL')}")
    print('Allianz:', con.execute('SELECT name, eigene FROM allianz').fetchall())
    print('\nAbweichungen Numbers <-> Quelle A:')
    for x in abweichungen:
        print(' ', x)
    print('\nIn Numbers, aber nicht in Quelle A:', nicht_in_a or 'keine')
    con.close()


if __name__ == '__main__':
    main()
