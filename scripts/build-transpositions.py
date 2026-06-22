"""
Build transposition PGN paths for each gambit using the Lichess Opening Explorer.

BFS from the initial position; at each node the Explorer is queried for the most
common continuations.  Every time a node's FEN matches a gambit's target position,
the move path taken to reach it is recorded as a transposition — unless the path is
identical to the gambit's own main-line PGN.

Transpositions are discovered from real game data, not theoretical permutations,
so only move orders that actually appear in many Lichess games are returned.

Usage (from the project root):
    python scripts/build-transpositions.py
    python scripts/build-transpositions.py --min-games 2000 --max-depth 10 --sleep 1.0

After this script completes, regenerate the JSON so transpositions are included:
    python scripts/generate-gambits-json.py

Output: scripts/transpositions.json
"""

import argparse
import json
import re
import ssl
import sys
import urllib.parse
from collections import deque
from time import sleep

import chess
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
_HTTP = urllib3.PoolManager(ssl_context=ssl._create_unverified_context())  # noqa: SLF001

GAMBITS_JSON = 'public/data/gambits.json'
OUTPUT_JSON = 'scripts/transpositions.json'

EXPLORER_URL = (
    'https://explorer.lichess.ovh/lichess'
    '?variant=standard'
    '&speeds=bullet,blitz,rapid,classical'
    '&ratings=1800,2000,2200,2500'
    '&topGames=0&recentGames=0'
    '&fen='
)


def _http_get(url: str, delay: float) -> dict:
    sleep(delay)
    try:
        resp = _HTTP.request('GET', url, timeout=15)
        if resp.status != 200:
            print(f'  Warning: HTTP {resp.status} from {url[:80]}', file=sys.stderr)
            return {}
        return json.loads(resp.data)
    except Exception as exc:
        print(f'  Warning: {exc}', file=sys.stderr)
        return {}


def fen_key(fen: str) -> str:
    """First 4 FEN fields: piece placement, side to move, castling rights, en-passant.
    Ignores the halfmove clock and fullmove counter so positions reached via
    different paths compare equal as long as the board state is the same."""
    return ' '.join(fen.split(' ')[:4])


def normalize_pgn(pgn: str) -> tuple:
    """'1. e4 e5 2. Nf3' → ('e4', 'e5', 'Nf3') — used to detect main-line duplicates."""
    return tuple(m for m in re.sub(r'\d+\.', '', pgn).split() if m)


def moves_to_pgn(san_moves: list) -> str:
    """['e4', 'e5', 'Nf3'] → '1. e4 e5 2. Nf3'"""
    parts = []
    for i, san in enumerate(san_moves):
        if i % 2 == 0:
            parts.append(f'{i // 2 + 1}. {san}')
        else:
            parts.append(san)
    return ' '.join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--min-games', type=int, default=1000,
        help='Minimum total games for a move to be explored in the BFS (default: 1000)',
    )
    parser.add_argument(
        '--max-depth', type=int, default=12,
        help='Maximum half-moves from the starting position (default: 12)',
    )
    parser.add_argument(
        '--sleep', type=float, default=0.5,
        help='Seconds to sleep between Explorer API calls (default: 0.5)',
    )
    args = parser.parse_args()

    with open(GAMBITS_JSON, encoding='utf-8') as f:
        gambits = json.load(f)

    # Index gambits by the first 4 FEN fields so multiple gambits that share
    # the same final position are all detected.
    gambit_by_fen: dict[str, list[dict]] = {}
    for g in gambits:
        key = fen_key(g['fen'])
        gambit_by_fen.setdefault(key, []).append(g)

    print(
        f'Loaded {len(gambits)} gambits '
        f'({len(gambit_by_fen)} unique FEN targets)\n'
        f'BFS: min_games={args.min_games}  max_depth={args.max_depth}  sleep={args.sleep}s\n'
    )

    # (eco, name, pgn) → set of transposition PGN strings
    transpositions: dict[tuple, set] = {
        (g['eco'], g['name'], g['pgn']): set()
        for g in gambits
    }

    initial_board = chess.Board()
    queue: deque = deque([(initial_board, [])])  # (board, san_moves_so_far)
    visited: set[str] = {fen_key(initial_board.fen())}
    positions_checked = 0

    while queue:
        board, san_moves = queue.popleft()
        depth = len(san_moves)

        if depth >= args.max_depth:
            continue

        positions_checked += 1
        if positions_checked % 100 == 0:
            total_found = sum(len(v) for v in transpositions.values())
            print(
                f'  [{positions_checked} positions | '
                f'queue={len(queue)} | '
                f'transpositions={total_found}]'
            )

        url = EXPLORER_URL + urllib.parse.quote(board.fen())
        data = _http_get(url, args.sleep)

        for move_data in data.get('moves', []):
            san = move_data.get('san', '')
            move_total = (
                move_data.get('white', 0)
                + move_data.get('draws', 0)
                + move_data.get('black', 0)
            )

            if not san or move_total < args.min_games:
                continue

            try:
                new_board = board.copy()
                new_board.push_san(san)
            except Exception:
                continue

            new_fkey = fen_key(new_board.fen())
            new_moves = san_moves + [san]

            if new_fkey in gambit_by_fen:
                path_norm = normalize_pgn(moves_to_pgn(new_moves))
                for g in gambit_by_fen[new_fkey]:
                    if path_norm != normalize_pgn(g['pgn']):
                        pgn_str = moves_to_pgn(new_moves)
                        key = (g['eco'], g['name'], g['pgn'])
                        if pgn_str not in transpositions[key]:
                            transpositions[key].add(pgn_str)
                            print(f'  ✓ {g["name"]}: {pgn_str}  ({move_total:,} games)')

            if new_fkey not in visited:
                visited.add(new_fkey)
                queue.append((new_board, new_moves))

    result = [
        {
            'eco': eco,
            'name': name,
            'pgn': pgn,
            'transpositions': sorted(pgn_set),
        }
        for (eco, name, pgn), pgn_set in transpositions.items()
        if pgn_set
    ]

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    total = sum(len(r['transpositions']) for r in result)
    print(
        f'\nDone!  Checked {positions_checked} positions.\n'
        f'Found {total} transpositions across {len(result)} gambits.\n'
        f'Output: {OUTPUT_JSON}'
    )


if __name__ == '__main__':
    main()
