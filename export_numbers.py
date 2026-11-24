"""Einmaliger Export der Numbers-Liste nach CSV (braucht: pip install numbers-parser).
Aufruf: python export_numbers.py Galaxieliste_neu.numbers galaxie_numbers.csv"""
import csv, sys
from numbers_parser import Document
src, dst = sys.argv[1], sys.argv[2]
t = Document(src).sheets[0].tables[0]
rows = t.rows(values_only=True)
header = [h or '' for h in rows[1]]
with open(dst, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Nr'] + header[1:10])
    for r in rows[2:]:
        if isinstance(r[0], float):
            w.writerow([int(r[0])] + [('' if c is None else c) for c in r[1:10]])
