"""
Build scripts/gambits.csv: the fully automated, deterministic definition of
"what counts as a gambit" -- the Lichess openings database filtered by
is_gambit(), nothing else. Run from the project root.

This file is intentionally NOT curated. It contains no manual additions,
removals, or PGN overrides -- those live in scripts/gambits-delta.csv and are
applied on top of this file by generate-gambits-json.py, which is what
actually produces public/data/gambits.json. Think of this script as pass 1 of
the pipeline (see scripts/pipeline.py for the full chain: this script, then
build-transpositions.py, then generate-gambits-json.py, then an optional
cache refresh).

Usage:
    python scripts/build-gambits.py             # fetch fresh stats from Lichess API (~slow)
    python scripts/build-gambits.py --no-stats  # reuse stats from the existing gambits.csv
"""

import argparse
import csv
import ssl

import urllib3

from gambits_shared import (
    CHESS_OPENINGS_URL,
    OPENINGS_FILES,
    color_and_move_from_pgn,
    fen_from_pgn,
    fetch_stats,
    is_gambit,
    set_lichess_token,
    uci_moves_from_pgn,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# urllib3.PoolManager with a custom SSLContext bypasses the Windows certificate
# store that hangs/crashes on some corporate networks (the issue with plain
# requests.get(verify=False) or ssl.create_default_context()).
_HTTP = urllib3.PoolManager(ssl_context=ssl._create_unverified_context())  # noqa: SLF001

CSV_PATH = 'scripts/gambits.csv'
CSV_FIELDS = ['eco', 'name', 'pgn', 'move', 'color', 'fen', 'master', 'lichess', 'white', 'draws', 'black']


def load_tsv() -> list[dict]:
    print('Downloading Lichess TSV files...')
    gambits = []
    for letter in OPENINGS_FILES:
        resp = _HTTP.request('GET', f'{CHESS_OPENINGS_URL}/{letter}.tsv', timeout=30)
        reader = csv.reader(resp.data.decode('utf-8').splitlines(), delimiter='\t')
        next(reader)  # skip header
        for row in reader:
            if len(row) >= 3 and is_gambit(row[1]):
                gambits.append({'eco': row[0].strip(), 'name': row[1].strip(), 'pgn': row[2].strip()})
    print(f'  {len(gambits)} gambits in Lichess TSV (is_gambit() filter only, no delta)')
    return gambits


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


def build(no_stats: bool) -> None:
    tsv_gambits = load_tsv()
    existing_stats = load_existing_csv_stats() if no_stats else {}

    csv_rows: list[dict] = []
    total = len(tsv_gambits)

    for i, gambit in enumerate(tsv_gambits):
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

    # Sort by total games descending, tie-broken by name for deterministic
    # ordering (keeps git diffs clean; roughly matches Lichess order)
    csv_rows.sort(key=lambda r: (-(r['white'] + r['draws'] + r['black']), r['name']))

    with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f'Written {len(csv_rows)} rows -> {CSV_PATH}')
    print('Next: python scripts/generate-gambits-json.py  (applies scripts/gambits-delta.csv and writes public/data/gambits.json)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--no-stats',
        action='store_true',
        help='Reuse stats from the existing gambits.csv instead of calling the Lichess API',
    )
    parser.add_argument(
        '--lichess-token',
        default='',
        metavar='TOKEN',
        help='Lichess API token for the Explorer API (required if your network blocks the API)',
    )
    args = parser.parse_args()
    if args.lichess_token:
        set_lichess_token(args.lichess_token)
    build(no_stats=args.no_stats)
