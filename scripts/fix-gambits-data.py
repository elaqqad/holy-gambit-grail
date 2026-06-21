"""
Fix gambits.csv and gambits.json to establish CSV as source of truth.

Rule: gambit color = whoever plays the last move in the PGN.
  - PGN ends on White's move → color: white
  - PGN ends on Black's move → color: black

Changes applied:
  1. Add 4 entries present in JSON but missing from CSV.
  2. Truncate PGNs for 11 same-PGN color conflicts (Black's acceptance removed).
  3. Sync 6 entries where CSV had a longer/different PGN than JSON.
  4. Pollock Gambit: extend PGN with Black's gambit move (6...Nd4).
  5. User corrections: Young Gambit, Albin-Chatard (truncate), Haxo (new PGN).
"""

import csv
import json
import re
from io import StringIO
import chess.pgn
import chess

CSV_PATH = 'scripts/gambits.csv'
JSON_PATH = 'public/data/gambits.json'


def fen_from_pgn(pgn: str) -> str:
    game = chess.pgn.read_game(StringIO(pgn))
    node = game
    while not node.is_end():
        node = node.next()
    return node.board().fen()


def color_and_move_from_pgn(pgn: str) -> tuple[str, int]:
    """Derive color and half-move index from PGN using the downloader rule."""
    split = re.split(r'\d+\.', pgn)
    color = 'black' if ' ' in split[-1].strip() else 'white'
    n = len(split) - 1  # number of full move segments
    move = 2 * n if color == 'black' else 2 * n - 1
    return color, move


def truncate_pgn(pgn: str) -> str:
    """Remove Black's last response from a PGN (make it end on White's move)."""
    return pgn.rsplit(' ', 1)[0].strip()


def apply_pgn(entry: dict, pgn: str, master: str | None = None, lichess: str | None = None) -> dict:
    """Update entry with a new PGN, recomputing color, move, and FEN."""
    color, move = color_and_move_from_pgn(pgn)
    entry = dict(entry)
    entry['pgn'] = pgn
    entry['color'] = color
    entry['move'] = move
    entry['fen'] = fen_from_pgn(pgn)
    if master is not None:
        entry['master'] = master
    if lichess is not None:
        entry['lichess'] = lichess
    return entry


# ── Load files ────────────────────────────────────────────────────────────────

with open(JSON_PATH, encoding='utf-8') as f:
    gambits_json: list[dict] = json.load(f)

with open(CSV_PATH, encoding='utf-8') as f:
    gambits_csv: list[dict] = list(csv.DictReader(f))

json_by_name = {g['name']: g for g in gambits_json}
csv_by_name  = {r['name']: r for r in gambits_csv}

# ── Collect all changes ───────────────────────────────────────────────────────

# Maps name → updated entry (shared between CSV and JSON unless noted)
csv_updates:  dict[str, dict] = {}
json_updates: dict[str, dict] = {}

# ── 1. Four entries in JSON but not in CSV ────────────────────────────────────
missing_in_csv = [
    'A50 Indian Defense: Budapest Gambit',
    'A50 Indian Defense: Normal Variation, Wagon Gambit',
    'A51 Indian Defense: Budapest Defense, Fajarowicz Gambit',
    'Dutch Defense: Staunton Gambit, Lasker Variation',
]
for name in missing_in_csv:
    csv_updates[name] = dict(json_by_name[name])

# ── 2. Truncate PGNs: same PGN in both, JSON manually set color=white ─────────
#    These PGNs end with Black's acceptance; truncate to White's last move.
truncate_cases = [
    'Amar Gambit',
    'Bird Opening: Dutch Variation, Batavo Gambit',
    'French Defense: La Bourdonnais Variation, Reuter Gambit',
    'Hungarian Opening: Pachman Gambit',
    'Italian Game: Classical Variation, Greco Gambit',
    'Italian Game: Evans Gambit, Mortimer-Evans Gambit',
    'King\'s Gambit Accepted: Blachly Gambit',
    'King\'s Gambit Accepted: Kieseritzky Gambit, Rice Gambit',
    'Mikenas Defense: Pozarek Gambit',
    'Ruy Lopez: Closed, Center Attack, Basque Gambit',
    'Vienna Gambit, with Max Lange Defense: Hamppe-Muzio Gambit',
]
for name in truncate_cases:
    base = csv_by_name[name]
    new_pgn = truncate_pgn(base['pgn'])
    updated = apply_pgn(base, new_pgn)
    csv_updates[name] = updated
    json_updates[name] = apply_pgn(json_by_name[name], new_pgn)

# ── 3. Sync CSV to JSON's intentional PGN (only unambiguous single-name entries)
#    These have different PGNs between CSV and JSON. We skip any name that has
#    multiple CSV rows (legitimate sub-variations) to avoid collapsing them.
from collections import Counter as _Counter
_csv_name_counts = _Counter(r['name'] for r in gambits_csv)

use_json_pgn_cases = [
    # Benko Gambit: SKIP — CSV has A57+A59 sub-variations, keep both
    # Blackmar-Diemer Gambit: SKIP — CSV has offer+acceptance variants, keep both
    # Dutch Defense: Staunton Gambit: SKIP — CSV has A82+A83 sub-variations
    # Italian Game: Evans Gambit: SKIP — CSV has 3 sub-variations (C51×2, C52)
    # King's Gambit Accepted: King's Knight's Gambit: SKIP — CSV has 4 sub-variations
    "Bishop's Opening: Boden-Kieseritzky Gambit",  # single entry in CSV, different move order
]
for name in use_json_pgn_cases:
    assert _csv_name_counts[name] == 1, f'Expected single CSV entry for {name}'
    j = json_by_name[name]
    updated = apply_pgn(csv_by_name[name], j['pgn'])
    updated['master']  = j.get('master', '')
    updated['lichess'] = j.get('lichess', '')
    csv_updates[name] = updated
    json_updates[name] = apply_pgn(j, j['pgn'])

# ── 4. Pollock Gambit: extend CSV (and JSON) PGN with Black's gambit move ─────
#    After 6. exd5, Black plays 6...Nd4 (the Pollock Gambit counter-sacrifice).
pollock_name = 'Vienna Game: Paulsen Variation, Pollock Gambit'
pollock_pgn = csv_by_name[pollock_name]['pgn'] + ' Nd4'
csv_updates[pollock_name] = apply_pgn(csv_by_name[pollock_name], pollock_pgn)
json_updates[pollock_name] = apply_pgn(json_by_name[pollock_name], pollock_pgn)

# ── 5. User-specified corrections ─────────────────────────────────────────────

# Young Gambit: truncate PGN to end at 10. Nc3 (White's move → color: white)
young_name = "King's Gambit Accepted: Double Muzio Gambit, Young Gambit"
young_pgn  = '1. e4 e5 2. f4 exf4 3. Nf3 g5 4. Bc4 g4 5. O-O gxf3 6. Qxf3 Qf6 7. Bxf7+ Kxf7 8. d4 Qxd4+ 9. Be3 Qf6 10. Nc3'
csv_updates[young_name] = apply_pgn(csv_by_name[young_name], young_pgn,
                                    master=None, lichess='ikkJgIJv')
json_updates[young_name] = apply_pgn(json_by_name[young_name], young_pgn,
                                     master=None, lichess='ikkJgIJv')

# Albin-Chatard: truncate PGN to end at 7. hxg5 (White's move → color: white)
albin_name = 'French Defense: Alekhine-Chatard Attack, Albin-Chatard Gambit'
albin_pgn  = '1. e4 e6 2. d4 d5 3. Nc3 Nf6 4. Bg5 Be7 5. e5 Nfd7 6. h4 Bxg5 7. hxg5'
csv_updates[albin_name] = apply_pgn(csv_by_name[albin_name], albin_pgn,
                                    master='xbT1NZw6', lichess='gBRBbZ6f')
json_updates[albin_name] = apply_pgn(json_by_name[albin_name], albin_pgn,
                                     master='xbT1NZw6', lichess='gBRBbZ6f')

# Haxo Gambit: replace with the extended line where Black plays d3
haxo_name = 'Scotch Game: Haxo Gambit'
haxo_pgn  = '1. e4 e5 2. Nf3 Nc6 3. d4 exd4 4. Bc4 Bc5 5. c3 d3'
csv_updates[haxo_name] = apply_pgn(csv_by_name[haxo_name], haxo_pgn,
                                   master=None, lichess=None)
json_updates[haxo_name] = apply_pgn(json_by_name[haxo_name], haxo_pgn,
                                    master=None, lichess=None)
# Clear stale stats for Haxo (position changed)
for d in (csv_updates[haxo_name], json_updates[haxo_name]):
    d['white'] = 0
    d['draws'] = 0
    d['black'] = 0

# ── Helper: fix any remaining violations row-by-row ──────────────────────────

# Build a (name, eco) → intended_color lookup from JSON so we can align CSV
_json_by_name_eco = {(x['name'], x['eco']): x for x in gambits_json}

def fix_rule_violation(entry: dict) -> dict:
    """
    1. If color=white but PGN ends on Black's move, truncate the PGN.
    2. If CSV color disagrees with the JSON intended color for the same
       (name, eco) pair AND the PGN ends on Black's move, truncate the PGN
       to align with the JSON intent.
    (We never truncate color=black/PGN-ends-white entries — those are
    deliberate counter-gambit extensions like the Pollock Gambit.)
    """
    split = re.split(r'\d+\.', entry['pgn'])
    pgn_ends_black = ' ' in split[-1].strip()

    # Case 1: explicit rule violation — color says white but PGN ends on Black
    needs_truncation = entry['color'] == 'white' and pgn_ends_black

    # Case 2: CSV disagrees with JSON intent for the same (name, eco) pair
    if not needs_truncation and pgn_ends_black:
        json_peer = _json_by_name_eco.get((entry['name'], entry.get('eco', '')))
        if json_peer and json_peer['color'] == 'white' and entry['color'] == 'black':
            needs_truncation = True

    if needs_truncation:
        entry = dict(entry)
        new_pgn = truncate_pgn(entry['pgn'])
        entry['pgn']   = new_pgn
        entry['color'], entry['move'] = color_and_move_from_pgn(new_pgn)
        entry['fen']   = fen_from_pgn(new_pgn)
    return entry


# ── Apply changes and write CSV ───────────────────────────────────────────────

# Start from existing CSV rows, apply updates, then append missing entries
csv_fields = ['eco', 'name', 'pgn', 'move', 'color', 'fen',
              'master', 'lichess', 'white', 'draws', 'black']

new_csv_rows = []
for row in gambits_csv:
    name = row['name']
    if name in csv_updates:
        merged = dict(row)
        merged.update(csv_updates[name])
        new_csv_rows.append(fix_rule_violation(merged))
    else:
        new_csv_rows.append(fix_rule_violation(row))

# Append the 4 entries that were missing
existing_csv_names = {r['name'] for r in gambits_csv}
for name in missing_in_csv:
    if name not in existing_csv_names:
        new_csv_rows.append(csv_updates[name])

with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=csv_fields)
    writer.writeheader()
    writer.writerows(new_csv_rows)

print(f'CSV written: {len(new_csv_rows)} rows')

# ── Apply changes and write JSON ──────────────────────────────────────────────

new_json = []
for entry in gambits_json:
    name = entry['name']
    if name in json_updates:
        merged = dict(entry)
        merged.update(json_updates[name])
        new_json.append(fix_rule_violation(merged))
    else:
        new_json.append(fix_rule_violation(entry))

with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(new_json, f, indent=4, ensure_ascii=False)

print(f'JSON written: {len(new_json)} entries')

# ── Summary ───────────────────────────────────────────────────────────────────

print()
print('Changes applied:')
print(f'  Added to CSV:        {len(missing_in_csv)} entries')
print(f'  Truncated PGNs:      {len(truncate_cases)} entries (both files)')
print(f'  Synced to JSON PGN:  {len(use_json_pgn_cases)} entries (CSV only)')
print(f'  Pollock Gambit:      extended PGN (both files)')
print(f'  User corrections:    Young Gambit, Albin-Chatard, Haxo (both files)')
