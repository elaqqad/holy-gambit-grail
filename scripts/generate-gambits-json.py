"""
Generate public/data/gambits.json: applies scripts/gambits-delta.csv on top
of the automated scripts/gambits.csv, merges in scripts/transpositions.json,
and writes the final artifact the app consumes.

This is pass 3 of the pipeline (see scripts/pipeline.py for the full chain):
  1. build-gambits.py          Lichess TSV + is_gambit() filter -> gambits.csv (fully automated)
  2. build-transpositions.py   BFS over the Explorer API -> transpositions.json
  3. generate-gambits-json.py  gambits.csv + gambits-delta.csv + transpositions.json -> gambits.json (this script)

The delta file (scripts/gambits-delta.csv) is the only place manual curation
happens:

    action  | columns used
    --------+----------------------------------------------------------
    remove  | eco, name, pgn                         exclude a gambit
    modify  | eco, name, pgn, new_pgn                 change PGN; pgn = the automated CSV's original
    add     | eco, name, pgn                          include a gambit not in the automated CSV

Every action's comment column is shown to site visitors, so it should read
as a chess explanation (what differs from Lichess's own PGN and why, or a
naming disambiguation) -- never an explanation of our own code.

add/modify rows carry their own stats cache (master, lichess, white, draws,
black) since their position isn't in the automated CSV at all (add) or isn't
the same position the automated CSV cached stats for (modify). Pass
--fetch-stats to fill in any of those that are still empty; the results are
written back into gambits-delta.csv so they're cached for next time.

Usage:
    python scripts/generate-gambits-json.py                # use cached delta stats only
    python scripts/generate-gambits-json.py --fetch-stats  # fetch missing add/modify stats
"""

import argparse
import csv
import json

from gambits_shared import color_and_move_from_pgn, fen_from_pgn, fetch_stats, set_lichess_token, uci_moves_from_pgn

CSV_PATH = 'scripts/gambits.csv'
DELTA_PATH = 'scripts/gambits-delta.csv'
JSON_PATH = 'public/data/gambits.json'
TRANSPOSITIONS_PATH = 'scripts/transpositions.json'
DELTA_FIELDS = ['action', 'eco', 'name', 'pgn', 'new_pgn', 'comment', 'master', 'lichess', 'white', 'draws', 'black']

EMPTY_STATS = {'white': 0, 'draws': 0, 'black': 0, 'lichess': '', 'master': ''}


def load_raw_csv() -> list[dict]:
    with open(CSV_PATH, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_delta() -> list[dict]:
    try:
        with open(DELTA_PATH, encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


def stats_from_delta_row(row: dict) -> dict | None:
    """None if this add/modify row hasn't had its stats fetched yet."""
    if not row.get('white'):
        return None
    return {
        'white': int(row.get('white') or 0),
        'draws': int(row.get('draws') or 0),
        'black': int(row.get('black') or 0),
        'lichess': row.get('lichess', '').strip(),
        'master': row.get('master', '').strip(),
    }


def stats_from_raw_row(row: dict) -> dict:
    return {
        'white': int(row.get('white') or 0),
        'draws': int(row.get('draws') or 0),
        'black': int(row.get('black') or 0),
        'lichess': row.get('lichess', '').strip(),
        'master': row.get('master', '').strip(),
    }


def fetch_and_cache_stats(delta_row: dict, pgn: str) -> dict:
    """Fetches live stats for a delta add/modify row and writes them back
    into delta_row in place, so the caller's later CSV write persists them."""
    color, _ = color_and_move_from_pgn(pgn)
    fen = fen_from_pgn(pgn)
    uci = uci_moves_from_pgn(pgn)
    print(f'  Fetching stats for {delta_row["name"]} ({pgn})...')
    stats = fetch_stats(fen, uci, color)
    delta_row['white'] = stats['white']
    delta_row['draws'] = stats['draws']
    delta_row['black'] = stats['black']
    delta_row['lichess'] = stats['lichess']
    delta_row['master'] = stats['master']
    return stats


def apply_delta(raw_rows: list[dict], delta_rows: list[dict], fetch_missing_stats: bool) -> list[dict]:
    """Merges the automated CSV with the delta, returning a curated list of
    dicts: eco, name, pgn, white, draws, black, lichess, master, and
    optionally original_pgn / comment. delta_rows entries may be mutated in
    place with freshly-fetched stats when fetch_missing_stats is set."""
    removes: set[tuple[str, str, str]] = set()
    modifies: dict[tuple[str, str, str], dict] = {}
    adds: list[dict] = []

    for row in delta_rows:
        action = row['action'].strip()
        key = (row['eco'].strip(), row['name'].strip(), row['pgn'].strip())
        if action == 'remove':
            removes.add(key)
        elif action == 'modify':
            modifies[key] = row
        elif action == 'add':
            adds.append(row)

    print(f'  Delta: {len(removes)} removes, {len(modifies)} modifies, {len(adds)} adds')

    seen: set[tuple[str, str, str]] = set()
    result: list[dict] = []

    for raw in raw_rows:
        key = (raw['eco'], raw['name'], raw['pgn'])
        if key in removes:
            continue

        if key in modifies:
            delta_row = modifies[key]
            new_pgn = delta_row['new_pgn'].strip()
            item: dict = {'eco': raw['eco'], 'name': raw['name'], 'pgn': new_pgn, 'original_pgn': raw['pgn']}
            if delta_row.get('comment', '').strip():
                item['comment'] = delta_row['comment'].strip()
            stats = stats_from_delta_row(delta_row)
            if stats is None:
                stats = fetch_and_cache_stats(delta_row, new_pgn) if fetch_missing_stats else EMPTY_STATS
            item.update(stats)
        else:
            item = {'eco': raw['eco'], 'name': raw['name'], 'pgn': raw['pgn']}
            item.update(stats_from_raw_row(raw))

        dedup_key = (item['eco'], item['name'], item['pgn'])
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        result.append(item)

    for delta_row in adds:
        eco, name, pgn = delta_row['eco'].strip(), delta_row['name'].strip(), delta_row['pgn'].strip()
        key = (eco, name, pgn)
        if key in seen:
            continue
        seen.add(key)

        item = {'eco': eco, 'name': name, 'pgn': pgn}
        if delta_row.get('comment', '').strip():
            item['comment'] = delta_row['comment'].strip()
        stats = stats_from_delta_row(delta_row)
        if stats is None:
            stats = fetch_and_cache_stats(delta_row, pgn) if fetch_missing_stats else EMPTY_STATS
        item.update(stats)
        result.append(item)

    return result


def load_transpositions() -> dict[tuple[str, str, str], list[str]]:
    try:
        with open(TRANSPOSITIONS_PATH, encoding='utf-8') as f:
            data = json.load(f)
        return {(t['eco'], t['name'], t['pgn']): t['transpositions'] for t in data}
    except FileNotFoundError:
        return {}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--fetch-stats',
        action='store_true',
        help='Fetch stats for any delta add/modify rows that are missing them, and cache the results back into gambits-delta.csv',
    )
    parser.add_argument('--lichess-token', default='', metavar='TOKEN', help='Lichess API token for the Explorer API')
    args = parser.parse_args()
    if args.lichess_token:
        set_lichess_token(args.lichess_token)

    raw_rows = load_raw_csv()
    delta_rows = load_delta()

    curated = apply_delta(raw_rows, delta_rows, fetch_missing_stats=args.fetch_stats)
    print(f'  {len(curated)} gambits after applying delta')

    if args.fetch_stats:
        with open(DELTA_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=DELTA_FIELDS)
            writer.writeheader()
            writer.writerows(delta_rows)
        print(f'  Cached any newly-fetched stats back into {DELTA_PATH}')

    transpositions = load_transpositions()

    seen_keys: set[tuple[str, str, str]] = set()
    gambits: list[dict] = []
    warnings: list[str] = []

    for item in curated:
        key = (item['eco'], item['name'], item['pgn'])
        if key in seen_keys:
            warnings.append(f'Skipped duplicate: {key[0]} {key[1]}')
            continue
        seen_keys.add(key)

        color, move = color_and_move_from_pgn(item['pgn'])
        fen = fen_from_pgn(item['pgn'])

        entry: dict = {
            'eco': item['eco'],
            'name': item['name'],
            'pgn': item['pgn'],
            'move': move,
            'color': color,
            'fen': fen,
            'master': item.get('master') or '',
            'lichess': item.get('lichess') or '',
            'white': int(item.get('white') or 0),
            'draws': int(item.get('draws') or 0),
            'black': int(item.get('black') or 0),
        }

        if 'original_pgn' in item:
            entry['original_pgn'] = item['original_pgn']
            entry['original_fen'] = fen_from_pgn(item['original_pgn'])
        if 'comment' in item:
            entry['comment'] = item['comment']

        transp = transpositions.get(key, [])
        if transp:
            entry['transpositions'] = transp

        gambits.append(entry)

    # Sort by total games descending (most-played gambits first, matching Lichess
    # order), tie-broken by name so two entries with identical stats (the same
    # underlying position under two different Lichess names) sort deterministically
    # instead of swapping order between runs.
    gambits.sort(key=lambda g: (-(g['white'] + g['draws'] + g['black']), g['name']))

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(gambits, f, indent=4, ensure_ascii=False)

    print(f'Generated {len(gambits)} entries -> {JSON_PATH}')
    if warnings:
        print(f'\n{len(warnings)} warning(s):')
        for w in warnings:
            print(f'  {w}')


if __name__ == '__main__':
    main()
