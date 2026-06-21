"""
Build public/data/gambits.json from the Lichess TSV files + scripts/gambits-delta.csv.

This replaces download-gambits.py. Run from the project root.

Usage:
    python scripts/build-gambits.py             # fetch fresh stats from Lichess API (~slow)
    python scripts/build-gambits.py --no-stats  # reuse stats from existing gambits.csv

The delta file (scripts/gambits-delta.csv) records curated overrides on top of the
raw Lichess opening database:

    action  | columns used
    --------+-------------------------------------------------------
    remove  | eco, name, pgn           exclude a Lichess gambit
    modify  | eco, name, pgn, new_pgn  change PGN; pgn = Lichess original
    add     | eco, name, pgn           include a gambit not in Lichess

The comment column on any row documents why the decision was made.

After updating gambits.csv the script calls generate-gambits-json.py to rebuild
the JSON, so both files end up in sync.
"""

import argparse
import csv
import json
import re
import subprocess
import sys
import urllib.parse
from io import StringIO
from time import sleep

import chess
import chess.pgn
import requests
import urllib3

# Python on Windows often can't verify GitHub/Lichess certs through corporate proxies.
# These are local dev scripts — suppressing verification is acceptable here.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CHESS_OPENINGS_URL = 'https://raw.githubusercontent.com/lichess-org/chess-openings/master'
LICHESS_EXPLORER = (
    'https://explorer.lichess.ovh/lichess'
    '?variant=standard&speeds=bullet,blitz,rapid,classical'
    '&ratings=1800,2000,2200,2500&fen='
)
MASTERS_EXPLORER = 'https://explorer.lichess.ovh/masters?play='
OPENINGS_FILES = ['a', 'b', 'c', 'd', 'e']

DELTA_PATH = 'scripts/gambits-delta.csv'
CSV_PATH = 'scripts/gambits.csv'
JSON_PATH = 'public/data/gambits.json'
CSV_FIELDS = ['eco', 'name', 'pgn', 'move', 'color', 'fen', 'master', 'lichess', 'white', 'draws', 'black']


# ── Helpers ───────────────────────────────────────────────────────────────────

def is_gambit(name: str) -> bool:
    return name.strip().lower().endswith('gambit')


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


def uci_moves_from_pgn(pgn: str) -> list[str]:
    game = chess.pgn.read_game(StringIO(pgn))
    node = game
    moves = []
    while not node.is_end():
        node = node.next()
        moves.append(node.move.uci())
    return moves


# ── API calls ─────────────────────────────────────────────────────────────────

def _get(url: str) -> dict:
    sleep(1)
    try:
        resp = requests.get(url, headers={'Accept': 'application/json'}, timeout=15, verify=False)
        return resp.json()
    except Exception as exc:
        print(f'  Warning: API error for {url[:80]}: {exc}', file=sys.stderr)
        return {}


def fetch_stats(fen: str, uci_moves: list[str], color: str) -> dict:
    lichess_data = _get(f'{LICHESS_EXPLORER}{urllib.parse.quote(fen)}')
    top_lichess = lichess_data.get('topGames', [])
    lichess_game = next((g['id'] for g in top_lichess if g.get('winner') == color), None)

    masters_data = _get(f'{MASTERS_EXPLORER}{",".join(uci_moves)}')
    top_masters = masters_data.get('topGames', [])
    master_game = next((g['id'] for g in top_masters if g.get('winner') == color), None)

    return {
        'white': lichess_data.get('white', 0),
        'draws': lichess_data.get('draws', 0),
        'black': lichess_data.get('black', 0),
        'lichess': lichess_game or '',
        'master': master_game or '',
    }


# ── Load data sources ─────────────────────────────────────────────────────────

def load_tsv() -> list[dict]:
    print('Downloading Lichess TSV files...')
    gambits = []
    for letter in OPENINGS_FILES:
        resp = requests.get(f'{CHESS_OPENINGS_URL}/{letter}.tsv', timeout=30, verify=False)
        resp.encoding = 'utf-8'
        reader = csv.reader(resp.iter_lines(decode_unicode=True), delimiter='\t')
        next(reader)  # skip header
        for row in reader:
            if len(row) >= 3 and is_gambit(row[1]):
                gambits.append({'eco': row[0].strip(), 'name': row[1].strip(), 'pgn': row[2].strip()})
    print(f'  {len(gambits)} gambits in Lichess TSV')
    return gambits


def load_delta() -> tuple[set, dict, list]:
    """
    Returns:
        removes  – set of (eco, name, pgn) to exclude
        modifies – {(eco, name, pgn): {'new_pgn': str, 'comment': str}}
        adds     – [{'eco', 'name', 'pgn', 'comment'}]
    """
    removes: set[tuple[str, str, str]] = set()
    modifies: dict[tuple[str, str, str], dict] = {}
    adds: list[dict] = []

    try:
        with open(DELTA_PATH, encoding='utf-8') as f:
            for row in csv.DictReader(f):
                action = row['action'].strip()
                eco = row['eco'].strip()
                name = row['name'].strip()
                pgn = row['pgn'].strip()
                key = (eco, name, pgn)

                if action == 'remove':
                    removes.add(key)
                elif action == 'modify':
                    modifies[key] = {
                        'new_pgn': row['new_pgn'].strip(),
                        'comment': row.get('comment', '').strip(),
                    }
                elif action == 'add':
                    adds.append({
                        'eco': eco,
                        'name': name,
                        'pgn': pgn,
                        'comment': row.get('comment', '').strip(),
                    })
    except FileNotFoundError:
        print(f'Warning: {DELTA_PATH} not found — run bootstrap-delta.py first', file=sys.stderr)

    print(f'  Delta: {len(removes)} removes, {len(modifies)} modifies, {len(adds)} adds')
    return removes, modifies, adds


def load_existing_csv_stats() -> dict[tuple[str, str, str], dict]:
    """Read stats columns from the current CSV to avoid API calls with --no-stats."""
    stats: dict[tuple[str, str, str], dict] = {}
    try:
        with open(CSV_PATH, encoding='utf-8') as f:
            for row in csv.DictReader(f):
                key = (row['eco'].strip(), row['name'].strip(), row['pgn'].strip())
                stats[key] = {
                    'white': int(row.get('white') or 0),
                    'draws': int(row.get('draws') or 0),
                    'black': int(row.get('black') or 0),
                    'lichess': row.get('lichess', '').strip(),
                    'master': row.get('master', '').strip(),
                }
    except FileNotFoundError:
        pass
    return stats


# ── Build pipeline ────────────────────────────────────────────────────────────

def apply_delta(
    tsv_gambits: list[dict],
    removes: set,
    modifies: dict,
    adds: list,
) -> list[dict]:
    """
    Returns the merged gambit list with annotations attached.
    Each entry may have: eco, name, pgn, original_pgn, comment.
    """
    seen: set[tuple[str, str, str]] = set()
    result: list[dict] = []

    for entry in tsv_gambits:
        key = (entry['eco'], entry['name'], entry['pgn'])

        if key in removes:
            continue

        item: dict = {'eco': entry['eco'], 'name': entry['name']}

        if key in modifies:
            mod = modifies[key]
            item['pgn'] = mod['new_pgn']
            item['original_pgn'] = entry['pgn']
            if mod['comment']:
                item['comment'] = mod['comment']
        else:
            item['pgn'] = entry['pgn']

        dedup_key = (item['eco'], item['name'], item['pgn'])
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        result.append(item)

    for entry in adds:
        key = (entry['eco'], entry['name'], entry['pgn'])
        if key in seen:
            continue
        seen.add(key)
        item = {'eco': entry['eco'], 'name': entry['name'], 'pgn': entry['pgn']}
        if entry.get('comment'):
            item['comment'] = entry['comment']
        result.append(item)

    return result


def build(no_stats: bool) -> None:
    tsv_gambits = load_tsv()
    removes, modifies, adds = load_delta()
    existing_stats = load_existing_csv_stats() if no_stats else {}

    gambits = apply_delta(tsv_gambits, removes, modifies, adds)
    print(f'  {len(gambits)} gambits after applying delta')

    csv_rows: list[dict] = []
    # annotations stored separately — picked up by generate-gambits-json.py
    total = len(gambits)

    for i, gambit in enumerate(gambits):
        pgn = gambit['pgn']
        color, move = color_and_move_from_pgn(pgn)
        fen = fen_from_pgn(pgn)

        csv_key = (gambit['eco'], gambit['name'], pgn)

        if no_stats:
            s = existing_stats.get(csv_key, {'white': 0, 'draws': 0, 'black': 0, 'lichess': '', 'master': ''})
        else:
            print(f'  [{i + 1}/{total}] {gambit["name"]}')
            uci = uci_moves_from_pgn(pgn)
            s = fetch_stats(fen, uci, color)

        csv_rows.append({
            'eco':     gambit['eco'],
            'name':    gambit['name'],
            'pgn':     pgn,
            'move':    move,
            'color':   color,
            'fen':     fen,
            'master':  s['master'],
            'lichess': s['lichess'],
            'white':   s['white'],
            'draws':   s['draws'],
            'black':   s['black'],
        })

    # Sort by total games descending (matches JSON order; keeps git diffs clean)
    csv_rows.sort(key=lambda r: -(r['white'] + r['draws'] + r['black']))

    # Write CSV (stats cache + curated PGNs)
    with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f'Written {len(csv_rows)} rows -> {CSV_PATH}')

    # Rebuild JSON via generate-gambits-json.py so annotations are applied
    # (that script reads original_pgn/comment from the existing JSON)
    print('Regenerating JSON...')
    result = subprocess.run(
        [sys.executable, 'scripts/generate-gambits-json.py'],
        capture_output=True, text=True
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(result.returncode)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--no-stats',
        action='store_true',
        help='Reuse stats from the existing gambits.csv instead of calling the Lichess API',
    )
    args = parser.parse_args()
    build(no_stats=args.no_stats)
