"""Zweisprachige Oberfläche (Englisch = Standard, Deutsch per Schalter).

Die deutschen Texte sind zugleich die Schlüssel: _('Deutscher Text') liefert in der englischen
Oberfläche die Übersetzung aus EN (siehe translations_en.py), in der deutschen den Text selbst.
Platzhalter: _('{n} Treffer', n=3). Die Sprache steht im Cookie 'lang' ('en' oder 'de').
Fehlt eine Übersetzung, erscheint der deutsche Text (und ein Test findet die Lücke).
"""
from flask import request

from translations_en import EN

SPRACHEN = ('en', 'de')
STANDARD = 'en'


def sprache():
    wahl = request.cookies.get('lang')
    if wahl in SPRACHEN:
        return wahl
    # erster Besuch: Browsersprache beachten, sonst Englisch
    return 'de' if request.accept_languages.best_match(SPRACHEN) == 'de' and \
        request.accept_languages.quality('de') > request.accept_languages.quality('en') else STANDARD


def _(text, **werte):
    if sprache() == 'en':
        text = EN.get(text, text)
    return text.format(**werte) if werte else text


def js_woerterbuch():
    """Wörterbuch für das JavaScript der Seiten (leer in der deutschen Oberfläche)."""
    return EN if sprache() == 'en' else {}
