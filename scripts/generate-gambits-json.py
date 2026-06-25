"""
Generate public/data/gambits.json from scripts/gambits.csv.

This is the canonical way to sync the JSON after any edit to the CSV.
Run: python scripts/generate-gambits-json.py

Rules applied:
  - gambit color = whoever plays the LAST move in the PGN
      PGN ends on White's move → color: white
      PGN ends on Black's move → color: black
  - move = half-move index of the last PGN move (1-indexed)
  - fen  = board position after the last PGN move (computed via python-chess)

Duplicate (eco, name, pgn) rows in the CSV are skipped with a warning.

Annotations (original_pgn, original_fen, comment) present in the existing
JSON are preserved so that hand-written explanations survive re-generation.
"""

import csv
import json
import re
from io import StringIO

import chess
import chess.pgn

CSV_PATH = 'scripts/gambits.csv'
JSON_PATH = 'public/data/gambits.json'
TRANSPOSITIONS_PATH = 'scripts/transpositions.json'


def fen_from_pgn(pgn: str) -> str:
    game = chess.pgn.read_game(StringIO(pgn))
    node = game
    while not node.is_end():
        node = node.next()
    return node.board().fen()


def color_and_move_from_pgn(pgn: str) -> tuple[str, int]:
    split = re.split(r'\d+\.', pgn)
    color = 'black' if ' ' in split[-1].strip() else 'white'
    n = len(split) - 1
    move = 2 * n if color == 'black' else 2 * n - 1
    return color, move


# ── Load existing annotations to preserve them ───────────────────────────────
# Keyed by (eco, name, pgn) so intentional same-name-different-pgn pairs
# are handled correctly.

try:
    with open(JSON_PATH, encoding='utf-8') as f:
        existing = json.load(f)
    annotations: dict[tuple[str, str, str], dict] = {}
    for entry in existing:
        ann = {k: entry[k] for k in ('original_pgn', 'original_fen', 'comment') if k in entry}
        if ann:
            annotations[(entry['eco'], entry['name'], entry['pgn'])] = ann
except FileNotFoundError:
    annotations = {}

try:
    with open(TRANSPOSITIONS_PATH, encoding='utf-8') as f:
        transpositions_data = json.load(f)
    transpositions: dict[tuple[str, str, str], list[str]] = {
        (t['eco'], t['name'], t['pgn']): t['transpositions']
        for t in transpositions_data
    }
except FileNotFoundError:
    transpositions = {}

# ── Read CSV and build JSON ───────────────────────────────────────────────────

seen_keys: set[tuple[str, str, str]] = set()
gambits: list[dict] = []
warnings: list[str] = []

with open(CSV_PATH, encoding='utf-8') as f:
    for row in csv.DictReader(f):
        key = (row['eco'], row['name'], row['pgn'])

        if key in seen_keys:
            warnings.append(f'Skipped duplicate: {key[0]} {key[1]}')
            continue
        seen_keys.add(key)

        pgn = row['pgn']
        color, move = color_and_move_from_pgn(pgn)
        fen = fen_from_pgn(pgn)

        # Warn when stored CSV values disagree with the computed values
        stored_color = row.get('color', '')
        stored_move  = row.get('move', '')
        stored_fen   = row.get('fen', '')
        if stored_color and stored_color != color:
            warnings.append(f'color mismatch {key[0]} {key[1]}: CSV={stored_color} computed={color}')
        if stored_move and int(stored_move) != move:
            warnings.append(f'move mismatch  {key[0]} {key[1]}: CSV={stored_move} computed={move}')
        if stored_fen and stored_fen != fen:
            warnings.append(f'fen mismatch   {key[0]} {key[1]}')

        entry: dict = {
            'eco':     row['eco'],
            'name':    row['name'],
            'pgn':     pgn,
            'move':    move,
            'color':   color,
            'fen':     fen,
            'master':  row.get('master')  or '',
            'lichess': row.get('lichess') or '',
            'white':   int(row.get('white')  or 0),
            'draws':   int(row.get('draws')  or 0),
            'black':   int(row.get('black')  or 0),
        }

        ann = annotations.get(key, {})
        entry.update(ann)

        transp = transpositions.get(key, [])
        if transp:
            entry['transpositions'] = transp

        gambits.append(entry)

# Sort by total games descending (most-played gambits first, matching Lichess order)
gambits.sort(key=lambda g: -(g['white'] + g['draws'] + g['black']))

with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(gambits, f, indent=4, ensure_ascii=False)

print(f'Generated {len(gambits)} entries -> {JSON_PATH}')
if warnings:
    print(f'\n{len(warnings)} warning(s):')
    for w in warnings:
        print(f'  {w}')
