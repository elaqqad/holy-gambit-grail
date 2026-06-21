"""
One-time migration: generate scripts/gambits-delta.csv from the current
public/data/gambits.json compared against the live Lichess TSV.

The produced delta, when fed to build-gambits.py, reconstructs the current
gambits.json faithfully (same gambits, same PGN corrections).

Run once, review the output, commit gambits-delta.csv, then use
build-gambits.py for all future refreshes.
"""

import csv
import json
import sys

import requests
import urllib3

# Python on Windows often can't verify github.com certs through corporate proxies.
# These are local dev scripts — suppressing verification is acceptable here.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CHESS_OPENINGS_URL = 'https://raw.githubusercontent.com/lichess-org/chess-openings/master'
OPENINGS_FILES = ['a', 'b', 'c', 'd', 'e']
JSON_PATH = 'public/data/gambits.json'
DELTA_PATH = 'scripts/gambits-delta.csv'
DELTA_FIELDS = ['action', 'eco', 'name', 'pgn', 'new_pgn', 'comment']


def is_gambit(name: str) -> bool:
    return name.strip().lower().endswith('gambit')


def load_tsv() -> list[tuple[str, str, str]]:
    """Returns all (eco, name, pgn) tuples from the Lichess gambit TSV files."""
    print('Downloading Lichess TSV files...')
    result: list[tuple[str, str, str]] = []
    for letter in OPENINGS_FILES:
        resp = requests.get(f'{CHESS_OPENINGS_URL}/{letter}.tsv', timeout=30, verify=False)
        resp.encoding = 'utf-8'
        for i, line in enumerate(resp.iter_lines(decode_unicode=True)):
            if i == 0:
                continue
            parts = line.split('\t')
            if len(parts) >= 3 and is_gambit(parts[1]):
                result.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    print(f'  {len(result)} gambits in Lichess TSV')
    return result


def main() -> None:
    lichess_list = load_tsv()
    lichess_full = set(lichess_list)  # set of (eco, name, pgn) for O(1) lookup

    print(f'Loading {JSON_PATH}...')
    with open(JSON_PATH, encoding='utf-8') as f:
        our_gambits: list[dict] = json.load(f)
    print(f'  {len(our_gambits)} entries in current JSON')

    rows: list[dict] = []
    accounted: set[tuple[str, str, str]] = set()

    # Pass 1: handle entries with original_pgn (PGN corrections).
    # Track which Lichess slots are consumed by modify actions so we don't
    # accidentally treat those same slots as "exact matches" for other entries.
    modify_sources: set[tuple[str, str, str]] = set()
    for g in our_gambits:
        if not g.get('original_pgn'):
            continue
        eco, name, pgn = g['eco'], g['name'], g['pgn']
        original_pgn = g['original_pgn']
        lichess_key = (eco, name, original_pgn)

        if lichess_key in lichess_full:
            # Lichess still has the original entry; emit a modify to replace it.
            modify_sources.add(lichess_key)
            accounted.add(lichess_key)
            rows.append({
                'action':  'modify',
                'eco':     eco,
                'name':    name,
                'pgn':     original_pgn,
                'new_pgn': pgn,
                'comment': g.get('comment', ''),
            })
        else:
            # Lichess no longer has the original PGN (TSV updated since we
            # corrected this entry). Treat our version as a custom add.
            rows.append({
                'action':  'add',
                'eco':     eco,
                'name':    name,
                'pgn':     pgn,
                'new_pgn': '',
                'comment': g.get('comment', ''),
            })

    # Pass 2: handle entries without original_pgn.
    for g in our_gambits:
        if g.get('original_pgn'):
            continue
        eco, name, pgn = g['eco'], g['name'], g['pgn']
        key = (eco, name, pgn)

        if key in lichess_full and key not in modify_sources:
            # Exact Lichess match whose slot isn't already consumed by a modify.
            accounted.add(key)
        else:
            # Either not in Lichess, or its Lichess slot is consumed by a modify
            # (the Lichess entry is being transformed away and won't appear in
            # the build output, so we need an explicit add for this entry).
            rows.append({
                'action':  'add',
                'eco':     eco,
                'name':    name,
                'pgn':     pgn,
                'new_pgn': '',
                'comment': g.get('comment', ''),
            })

    # Removals: Lichess gambits not accounted for above.
    for eco, name, pgn in lichess_list:
        if (eco, name, pgn) not in accounted:
            rows.append({
                'action':  'remove',
                'eco':     eco,
                'name':    name,
                'pgn':     pgn,
                'new_pgn': '',
                'comment': '',
            })

    # Sort: removes first (by eco/name), then modifies, then adds.
    order = {'remove': 0, 'modify': 1, 'add': 2}
    rows.sort(key=lambda r: (order[r['action']], r['eco'], r['name']))

    with open(DELTA_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=DELTA_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    n_remove = sum(1 for r in rows if r['action'] == 'remove')
    n_modify = sum(1 for r in rows if r['action'] == 'modify')
    n_add    = sum(1 for r in rows if r['action'] == 'add')
    print(f'Written {DELTA_PATH}:')
    print(f'  {n_remove} removes  (Lichess gambits we exclude)')
    print(f'  {n_modify} modifies (PGN corrections with original_pgn)')
    print(f'  {n_add} adds     (custom or sub-variation entries)')
    print()
    print('Next steps:')
    print('  1. Review gambits-delta.csv — especially the "remove" rows.')
    print('  2. Run: python scripts/build-gambits.py --no-stats')
    print('  3. Verify: npm run gambits:generate && npm test')
    print('  4. Commit gambits-delta.csv alongside any changes.')


if __name__ == '__main__':
    main()
