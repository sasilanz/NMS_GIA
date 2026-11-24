"""Prüft, dass jeder in Templates und app.py verwendete Text eine englische Übersetzung hat und dass
die Platzhalter ({n}, {name} …) übereinstimmen. Aufruf: python3 check_translations.py"""
import glob
import re
import sys

from translations_en import EN

DYNAMISCH = {'Basis', 'Mini-Basis', 'Raumstation', 'Portal', 'Sonstiges', 'niedrig', 'mittel', 'hoch',
            'Allianzname', 'Systemname', 'Nummer'}
muster = re.compile(r"""_\(\s*(?:'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)")""")
platz = lambda t: sorted(re.findall(r'\{(\w+)\}', t))

benutzt = set(DYNAMISCH)
for datei in glob.glob('templates/*.html') + ['app.py']:
    for m in muster.finditer(open(datei, encoding='utf-8').read()):
        k = m.group(1) if m.group(1) is not None else m.group(2)
        benutzt.add(k.replace("\\'", "'").replace('\\n', '\n'))
benutzt.discard('')

fehler = [f'fehlt: {k!r}' for k in sorted(benutzt) if k not in EN]
fehler += [f'Platzhalter verschieden: {k!r}' for k, v in EN.items() if platz(k) != platz(v)]
unbenutzt = sorted(set(EN) - benutzt)
for f in fehler:
    print(f)
if unbenutzt:
    print(f'Hinweis: {len(unbenutzt)} ungenutzte Übersetzungen:', unbenutzt[:5])
print('OK' if not fehler else f'{len(fehler)} Probleme')
sys.exit(1 if fehler else 0)
