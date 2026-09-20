"""Shared helpers for the gambits data pipeline (build-gambits.py,
generate-gambits-json.py, build-transpositions.py). Not a standalone script."""

import json
import re
import ssl
import sys
import urllib.parse
from io import StringIO
from time import sleep

import chess
import chess.pgn
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# A custom SSLContext bypasses the Windows certificate store that hangs/crashes
# on some corporate networks (the issue with plain requests.get(verify=False)
# or ssl.create_default_context()).
_HTTP = urllib3.PoolManager(ssl_context=ssl._create_unverified_context())  # noqa: SLF001

CHESS_OPENINGS_URL = 'https://raw.githubusercontent.com/lichess-org/chess-openings/master'
OPENINGS_FILES = ['a', 'b', 'c', 'd', 'e']

LICHESS_EXPLORER = (
    'https://explorer.lichess.ovh/lichess'
    '?variant=standard&speeds=bullet,blitz,rapid,classical'
    '&ratings=1800,2000,2200,2500&fen='
)
MASTERS_EXPLORER = 'https://explorer.lichess.ovh/masters?play='

_LICHESS_TOKEN: str = ''  # set via set_lichess_token(); empty means no auth header


def set_lichess_token(token: str) -> None:
    global _LICHESS_TOKEN
    _LICHESS_TOKEN = token


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


def get(url: str, delay: float = 1.0) -> dict:
    """GET url as JSON, sleeping `delay` seconds first to stay polite to the Explorer API."""
    sleep(delay)
    headers = {'Accept': 'application/json'}
    if _LICHESS_TOKEN:
        headers['Authorization'] = f'Bearer {_LICHESS_TOKEN}'
    try:
        resp = _HTTP.request('GET', url, headers=headers, timeout=15)
        if resp.status == 401:
            print(
                f'  Warning: HTTP 401 from {url[:60]} — the Lichess Explorer API may'
                ' require a token. Pass --lichess-token <token> to authenticate.',
                file=sys.stderr,
            )
            return {}
        if resp.status != 200:
            print(f'  Warning: HTTP {resp.status} from {url[:80]}', file=sys.stderr)
            return {}
        return json.loads(resp.data)
    except Exception as exc:
        print(f'  Warning: API error for {url[:80]}: {exc}', file=sys.stderr)
        return {}


def fetch_stats(fen: str, uci_moves: list[str], color: str) -> dict:
    """Game counts plus one example Lichess game and one Masters game, each
    won by `color`, for the position reached by `fen`/`uci_moves`."""
    lichess_data = get(f'{LICHESS_EXPLORER}{urllib.parse.quote(fen)}')
    top_lichess = lichess_data.get('topGames', [])
    lichess_game = next((g['id'] for g in top_lichess if g.get('winner') == color), None)

    masters_data = get(f'{MASTERS_EXPLORER}{",".join(uci_moves)}')
    top_masters = masters_data.get('topGames', [])
    master_game = next((g['id'] for g in top_masters if g.get('winner') == color), None)

    return {
        'white': lichess_data.get('white', 0),
        'draws': lichess_data.get('draws', 0),
        'black': lichess_data.get('black', 0),
        'lichess': lichess_game or '',
        'master': master_game or '',
    }
