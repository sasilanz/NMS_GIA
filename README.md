# NMS Galaxy Tracker

🇬🇧 English (this file) · 🇩🇪 [Deutsche Fassung → README.de.md](README.de.md)

A small local web app for **No Man's Sky** players to keep track of their own places: galaxies, systems, bases, space stations and alliances. The typical question it answers in seconds:

> *"I see another player's base in the Anomaly. Have I been to that galaxy? Do I have anything there?"*

- All 256 galaxies as a colour-coded grid (Lush / Normal / Harsh / Empty), visited yes/no, instant search and filters
- Systems and entries (base, mini base, space station, portal) per galaxy, with life form, wealth and conflict level
- Alliances with their stations across all galaxies
- All **Hitchhikers of the Galaxy (HotG) hubs** from the NMS wiki, including galaxies you have not visited yet, with portal glyphs
- Backups as database copy, JSON and CSV
- **Bilingual UI: English and German** (switch in the top bar; English by default)

It runs **locally only, with no login, no account and no secrets**. All data lives in one SQLite file. The app listens on `127.0.0.1` only, not on your network.

## Installation

On first start the app creates its database itself: all 256 galaxies (number and name), all marked "not visited", plus the HotG hub table and an own alliance called "My Alliance" (rename it in the app). Then open **http://127.0.0.1:5050** in your browser.

### Option A: Docker (recommended, nothing else needed)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine with Compose), running. On macOS [Colima](https://github.com/abiosoft/colima) works too (`brew install colima docker docker-compose`, then `colima start`); keep the project inside your home folder so that `data/` is visible on the Mac.

```
git clone https://github.com/sasilanz/NMS_GIA.git
cd NMS_GIA
docker compose up -d --build
```

- The database and all backups live in the folder **`./data`** next to `docker-compose.yml` (`data/nms.db`, `data/export/`). It survives rebuilds and updates. **To back up, just copy that folder.**
- Stop: `docker compose down` (data is kept). Start: `docker compose up -d`. Logs: `docker compose logs -f`.
- Update: `git pull && docker compose up -d --build`. The database is upgraded automatically on start.
- Change the port: edit the left number under `ports` in `docker-compose.yml`, e.g. `"127.0.0.1:8080:5050"`.
- The port is deliberately bound to `127.0.0.1`. There is no login: anyone who can reach the app can edit your data, so do not expose it to a network.

### Option B: Python directly

Requires Python 3.10 or newer.

```
git clone https://github.com/sasilanz/NMS_GIA.git
cd NMS_GIA
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt      # Windows: .venv\Scripts\pip ...
.venv/bin/python app.py                        # Windows: .venv\Scripts\python app.py
```

Open http://127.0.0.1:5050. Stop with Ctrl+C. The database `nms.db` is created in the project folder.

**macOS shortcuts:** double-click `start.command` to start the server and open the browser, `stop.command` to stop it, `export.command` to create a backup (first time: right-click → Open).

### Settings (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `NMS_DB` | `nms.db` | path of the database file |
| `NMS_EXPORT_DIR` | `export` | folder for backups |
| `NMS_HOST` | `127.0.0.1` | address the server listens on (`0.0.0.0` inside the Docker image; from outside it is only reachable through the port mapping in `docker-compose.yml`) |
| `NMS_PORT` | `5050` | port |

### Start over / reset the database

Delete the database file (or the `data/` folder) and start the app again to get a fresh one. Or explicitly: `python3 init_db.py --neu --allianz "My ABC"` (deletes all data!).

### Import your own Numbers list (optional)

If you used to keep a Numbers table: `export_numbers.py` exports it as `galaxie_numbers.csv` (needs `pip install numbers-parser`; columns: Nr, Name, Kategorie, Entdeckt, Bewertung, Kürzel, Sternenystem, Eigene Raumstation, Basen, Extras). If that file is in the project folder when the database is created, it is imported too (visited flag, type, rating, abbreviation; free text goes into the galaxy note, and the "Clean up" page helps to turn it into systems and entries). Without the file everything starts empty, which is the normal case.

## Using the app

**Language:** the switch "Deutsch / English" is in the top bar of every page. Your choice is stored in a cookie; the first visit follows your browser language.

### Galaxy grid (start page)

- Every galaxy is a tile with number, name and abbreviation. Tile colour = type: green Lush, turquoise Normal, red-orange Harsh, grey Empty, light grey unknown.
- **Visited:** click the circle on a tile. Visited tiles get a pink border and a ticked circle. Saved instantly.
- **Quick check:** the search box is focused on load. Type a number (`170`), a name or an abbreviation. With exactly one match the status is shown in big letters: "already visited" / "not visited yet", plus the number of entries and whether a HotG hub exists. **Esc** clears the search.
- **Filters:** type (several at once), all / visited / not visited, "has base / station", "Alliance station …" (pick an alliance or any), "HotG hub". The filters are remembered by the browser. On the very first start the grid shows visited galaxies only (or all, if none is visited yet).
- Tiles with a HotG hub carry a yellow "HotG" badge. The "⌂ n" counter shows how many entries a galaxy has.
- "Search everything" searches bases, systems, planets and notes.

### Galaxy page

Click a tile. Everything is saved as soon as you leave a field ("✓ saved" appears top right).

- **Header (coloured by type):** name, abbreviation, type, rating (1–5 stars), note and the big "Visited" button. A yellow banner shows the HotG hub of this galaxy (system, glyphs, discoverer), if there is one.
- **Systems:** "+ System" adds a system. Each system has optional dropdowns for **life form** (Gek, Vy'keen, Korvax), **wealth** (1–3) and **conflict** (1–3), plus a note. "✕ System" deletes it with all its entries (after a confirmation). Naming scheme suggested by the placeholders: abbreviation + short name, e.g. `EZD Aibaba`.
- **Entries** (base, mini base, space station, portal, other) live inside a system: type, name (scheme abbreviation + type + feature, e.g. `EZD Base Island`, the same name as in your teleporter), planet (text only; space stations have no planet field), alliance and note. "+ Space station (alliance)" creates a station of your own alliance directly.
- **Alliance:** "none (personal)" for your own bases, otherwise pick the alliance. ★ marks your own alliance. Entries with an alliance get a coloured stripe (yellow = own alliance, pink = other).
- "Delete galaxy …" at the bottom deletes the galaxy with everything in it (after a confirmation).

### Alliances

- **Overview** (button "Alliances"): every alliance with number of stations and galaxies, plus "+ Alliance".
- **Alliance page:** all stations of an alliance across all galaxies, with a live filter. Click a galaxy to edit there. Name and note are editable. Exactly one alliance is "your own" (yellow button in the top bar of every page). You can switch it, and delete any other alliance (its stations stay, they just lose the alliance).
- **Recording a station of another alliance:** create the alliance in the overview, then create an entry of type space station in its galaxy and choose the alliance. In the grid, the filter "Alliance station …" finds it.

### HotG hubs

The page "HotG hubs" lists **all hubs of the Hitchhikers of the Galaxy community from the NMS wiki**, including galaxies you have not visited: galaxy, visited status, hub system, portal glyphs (hex, with a copy button), discoverer and your own entries. Filter by all / not visited / visited, or search by number, galaxy, system or discoverer. Galaxy 69 is a secret system without glyphs; the access note from the wiki is shown instead.

**"Update from Fandom"** fetches the current list from the wiki (section "All HotG galactic hubs discovered so far") and replaces the local list, then tells you what is new, changed or removed. From a terminal: `.venv/bin/python hotg_import.py`. The data is kept in the table `hotg_hub` and as a copy in `hotg_hubs.csv`; hubs for galaxies that do not exist in your database are skipped.

### Search

"Search everything" finds galaxies, systems and entries (name, planet, note, type, alliance). Several words narrow the result, case and accents do not matter. Each hit shows where it matched and jumps to the right place in the galaxy page.

### Backup and restore

Open "Backup" and click "Back up now". Every export is a folder `export/YYYY-MM-DD_HHMMSS/` (`data/export/` with Docker) containing:

| File | Content |
|---|---|
| `nms.db` | complete copy of the database, **the one that matters** (for restoring) |
| `nms.json` | all tables as JSON (including `hotg_hub`) |
| `galaxien.csv`, `systeme.csv`, `eintraege.csv`, `allianzen.csv` | readable tables for Numbers / Excel (names instead of IDs) |

Other ways: double-click `export.command`, or `.venv/bin/python exporter.py`. Old exports are never deleted automatically.

**Restore:** stop the server, rename the current `nms.db`, copy the `nms.db` from the export folder to the project folder (Docker: into `data/`), start the server. Back up before bigger changes: deletions (✕) cannot be undone, and an export on the same disk is only a copy, so copy `export/` somewhere else now and then.

## Data model

Five SQLite tables. Hierarchy **galaxy → system → entry**; planets are just a text field on the entry.

- `galaxy`: `nr` (primary key), `name`, `kuerzel` (abbreviation), `typ` (Lush/Normal/Harsh/Empty), `besucht` (0/1), `bewertung` (1–5), `notiz`
- `system`: `id`, `galaxy_nr` → galaxy, `name`, `lebensform` (Gek, Vy'keen, Korvax), `wealth` (1–3), `konflikt` (1–3), `notiz`
- `eintrag` (entry): `id`, `system_id` → system, `typ` (Basis, Mini-Basis, Raumstation, Portal, Sonstiges; stored in German and shown translated), `name`, `planet`, `allianz_id` → allianz (empty = personal), `notiz`
- `allianz`: `id`, `name`, `eigene` (1 = your own alliance, exactly one), `notiz`
- `hotg_hub`: `galaxy_nr` (key, → galaxy), `system`, `entdeckt_von`, `glyphen` (hex), `zugang` (access note for secret systems). Reference data from the wiki.

Deleting a galaxy deletes its systems and entries. Deleting an alliance keeps its entries and only clears the link. Older databases are upgraded automatically on start (new columns/tables are added). Look inside with `sqlite3 nms.db ".schema"`.

## Project layout

| File | Purpose |
|---|---|
| `app.py` | Flask server: all pages and the JSON API (`/api/...`) |
| `templates/` | pages (HTML, CSS and JavaScript in one file each): `index` (grid), `galaxy`, `allianz`, `allianzen`, `hotg`, `suche`, `export`, `aufraeumen` |
| `i18n.py`, `translations_en.py` | bilingual UI (see below) |
| `check_translations.py` | checks that every UI text has an English translation |
| `exporter.py` | backups (also used by the app) |
| `init_db.py` | creates the database and imports the galaxies |
| `hotg_import.py` | fetches the HotG hub list from the wiki |
| `galaxien_quelle_a.csv` | the 256 galaxies (number, name, type) |
| `hotg_hubs.csv` | snapshot of the hub list (rewritten on every update) |
| `export_numbers.py` | optional: Numbers list → CSV |
| `Dockerfile`, `docker-compose.yml` | Docker setup |
| `start.command`, `stop.command`, `export.command` | macOS double-click helpers |
| `NMS-Galaxie-Tracker-SPEC.md` | original specification (German) |
| `README.de.md` | this README in German |

Tech: Python + Flask, SQLite, plain HTML with a little JavaScript, no build step.

## Translations and contributing

The UI is bilingual. The German texts in the source are the keys: templates and code call `_('Deutscher Text')`, and `translations_en.py` maps each text to English (placeholders like `{n}` must match). JavaScript gets the same dictionary and its own `_()` (`templates/_js.html`). The language is chosen with the `lang` cookie (`/sprache/en`, `/sprache/de`).

- Add or change a text: edit the template/code and the entry in `translations_en.py`, then run `python3 check_translations.py` (it fails on missing translations or mismatching placeholders).
- Add another language: add a dictionary like `EN` and extend `i18n.py` (`SPRACHEN`, `_`, `js_woerterbuch`) and the switcher.
- The source code (identifiers and comments) is in German, because it started as a personal tool. Translations of code comments are welcome.

## Data sources and credits

- Galaxy list (`galaxien_quelle_a.csv`): numbers and names of the 256 galaxies, originally read by OCR from a scanned list and checked against another list. Some spellings may be off; rename galaxies in the app.
- HotG hubs: from the [NMS Fandom wiki](https://nomanssky.fandom.com/wiki/Hitchhikers_of_the_Galaxy) (text there is under [CC BY-SA](https://www.fandom.com/licensing)). The bundled `hotg_hubs.csv` is a snapshot; use "Update from Fandom" for the current state.
- *No Man's Sky* is a trademark of Hello Games. This project is unofficial and not affiliated with Hello Games or the HotG community.

## License

[MIT](LICENSE)
