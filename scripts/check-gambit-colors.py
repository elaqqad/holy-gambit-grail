"""
Screen public/data/gambits.json for color/PGN misattributions.

Each gambit's `color` is derived purely from whoever plays the textually-last
move in its PGN (see color_and_move_from_pgn() in build-gambits.py) -- it has
no actual understanding of chess. That heuristic is self-consistent by
construction (color always equals whoever plays the last move), so it can
never catch itself being wrong. But it silently assumes the PGN was truncated
at exactly the point of the real material offer -- and Lichess's own openings
database (or our delta overrides) don't always agree with that assumption:
sometimes the named "gambit" move is a few plies earlier than where the PGN
stops (a quiet trailing move from the other side gets included), and
sometimes it's later (the PGN stops before the actual sacrifice happens).

There is no way to fully automate "did this side actually offer material" --
it requires understanding chess ideas, not just piece counts. This script is
a SCREEN, not a verdict: it flags entries whose final move doesn't look like
a real material offer or capture, using two heuristics, and prints enough
context (move-by-move material balance) for a human to judge each one. Every
flagged entry needs a person to look at the PGN and decide whether the
color/truncation is right, wrong, or the heuristic is simply wrong for that
case (it will have false positives and negatives -- see the two known blind
spots documented above main()).

Usage:
    python scripts/check-gambit-colors.py                  # flags only
    python scripts/check-gambit-colors.py --all             # every entry, verbose
    python scripts/check-gambit-colors.py --family-pairs    # Gambit/Countergambit
                                                              same-color pairs only
"""

import argparse
import json
import re
import sys
from io import StringIO

import chess
import chess.pgn

JSON_PATH = 'public/data/gambits.json'

PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}


def material_balance(board: chess.Board) -> int:
    """White material minus Black material, in pawns."""
    total = 0
    for piece_type, value in PIECE_VALUES.items():
        total += value * len(board.pieces(piece_type, chess.WHITE))
        total -= value * len(board.pieces(piece_type, chess.BLACK))
    return total


def is_hanging(board: chess.Board, square: int, piece_color: bool) -> bool:
    """True if an enemy piece attacks `square` at all -- i.e. this piece is
    capturable right now, regardless of whether an "equal" recapture exists.

    A classical pawn gambit (Smith-Morra, Danish, Evans, ...) offers a pawn
    that IS adequately defended by material count -- the queen sitting on d1
    could recapture cxd4 for free after 1.e4 c5 2.d4 -- the entire point is
    that the gambiteer doesn't intend to take that "equal" recapture, trading
    the pawn permanently for development/lines instead. So checking whether
    the recapture is "worth it" misses almost every real gambit; simply being
    capturable at all is the actual signal of "material was offered here."
    """
    enemy = not piece_color
    return bool(board.attackers(enemy, square))




def analyze(pgn: str, gambiteer_white: bool) -> dict:
    game = chess.pgn.read_game(StringIO(pgn))
    if game is None or game.errors:
        return {'error': 'failed to parse PGN', 'errors': [str(e) for e in (game.errors if game else [])]}

    board = chess.Board()
    node = game
    trace = []
    last_move = None
    last_mover_white = None
    # Did the declared gambiteer color ever actually take a risk anywhere in
    # the line -- lose a piece to a capture, or leave one hanging -- rather
    # than just happening to play the textually-last move?
    risk_ply = None
    while not node.is_end():
        node = node.next()
        move = node.move
        mover_white = board.turn == chess.WHITE
        is_capture = board.is_capture(move)
        before = material_balance(board)
        board.push(move)
        after = material_balance(board)
        ply = len(trace) + 1

        if risk_ply is None:
            # Did the gambiteer just move a piece (quietly, or by capturing
            # somewhere) onto a square the opponent now attacks? A classical
            # pawn gambit (Smith-Morra, Danish, Evans, ...) offers a pawn that
            # IS "defended" by material count (a queen could recapture for
            # free), so we deliberately don't require the recapture to be
            # favorable: being attacked at all, right after voluntarily moving
            # there, is the actual signal of "material was offered here."
            #
            # Deliberately NOT "the gambiteer's piece got captured by the
            # opponent" on its own -- that fires on any routine pawn grab
            # anywhere in the game, whether or not it was ever offered as
            # part of this named line's idea (e.g. Corkscrew Gambit: White's
            # 3.Nxe5 simply nets an undefended central pawn Black never
            # specifically dangled; it says nothing about who took the real
            # risk later in the same line). Only the mover's own choice to
            # move into an attacked square counts; a capture that lands on an
            # attacked square is still covered, since it's still this move's
            # to_square being checked.
            if mover_white == gambiteer_white and is_hanging(board, move.to_square, gambiteer_white):
                risk_ply = ply

        trace.append(
            {
                'ply': ply,
                'mover': 'white' if mover_white else 'black',
                'capture': is_capture,
                'material_before': before,
                'material_after': after,
            }
        )
        last_move = move
        last_mover_white = mover_white

    final_square = last_move.to_square
    final_hanging = is_hanging(board, final_square, last_mover_white)
    final_capture = trace[-1]['capture'] if trace else False

    if risk_ply is None:
        # Catches the other common pattern the per-move check above misses:
        # the gambiteer never moves a piece INTO danger, they just decline to
        # rescue one the opponent's move put in danger (e.g. Tennison Gambit,
        # 1. e4 d5 2. Nf3 -- White's e4 pawn is attacked by Black's own d5,
        # not by anything White did, and White simply doesn't defend it).
        # Checked only at the final position, so it doesn't reintroduce the
        # "any piece, any ply" over-triggering the per-move check avoids.
        for square, piece in board.piece_map().items():
            if piece.color == gambiteer_white and piece.piece_type != chess.KING and is_hanging(board, square, gambiteer_white):
                risk_ply = len(trace)
                break

    return {
        'trace': trace,
        'final_capture': final_capture,
        'final_hanging': final_hanging,
        'final_material': trace[-1]['material_after'] if trace else 0,
        'last_mover': 'white' if last_mover_white else 'black',
        'gambiteer_ever_at_risk': risk_ply is not None,
        'risk_ply': risk_ply,
    }


def family_key(name: str) -> str:
    """Best-effort grouping key for spotting Gambit/Countergambit siblings,
    e.g. 'Latvian Gambit: Corkscrew Gambit' and
    'Latvian Gambit: Corkscrew Countergambit' -> both 'latvian gambit corkscrew'."""
    stripped = re.sub(r'\bcounter\s*gambit\b', 'gambit', name, flags=re.IGNORECASE)
    stripped = re.sub(r'\bgambit\b', '', stripped, flags=re.IGNORECASE)
    stripped = re.sub(r'[^a-z0-9]+', ' ', stripped.lower())
    return ' '.join(stripped.split())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--all', action='store_true', help='Print every entry, not just flagged ones')
    parser.add_argument('--family-pairs', action='store_true', help='Only print Gambit/Countergambit same-color family pairs')
    args = parser.parse_args()

    with open(JSON_PATH, encoding='utf-8') as f:
        gambits = json.load(f)

    if args.family_pairs:
        by_family: dict[str, list[dict]] = {}
        for g in gambits:
            by_family.setdefault(family_key(g['name']), []).append(g)
        found = 0
        for key, members in by_family.items():
            if len(members) < 2:
                continue
            has_counter = any('counter' in m['name'].lower() for m in members)
            has_plain = any('counter' not in m['name'].lower() for m in members)
            if not (has_counter and has_plain):
                continue
            colors = {m['color'] for m in members}
            if len(colors) == 1:
                found += 1
                print(f'SAME COLOR ({colors.pop()}) across "{key}" family:')
                for m in members:
                    print(f'    {m["name"]!r}: {m["pgn"]}')
                print()
        print(f'{found} Gambit/Countergambit families sharing one color (may be legitimate -- see PR description).')
        return

    flagged = 0
    for g in gambits:
        gambiteer_white = g['color'] == 'white'
        result = analyze(g['pgn'], gambiteer_white)
        if 'error' in result:
            print(f'PARSE ERROR: {g["name"]!r} {g["pgn"]!r}: {result["errors"]}')
            flagged += 1
            continue

        # Primary signal: across the WHOLE line, did the declared gambiteer
        # color ever actually risk something (lose a piece to capture, or
        # leave one hanging)? If never, the color is likely misattributed --
        # regardless of what the final move happens to be.
        suspicious = not result['gambiteer_ever_at_risk']
        if not suspicious and not args.all:
            continue

        flagged += 1 if suspicious else 0
        tag = 'SUSPICIOUS' if suspicious else 'ok'
        print(f'[{tag}] {g["name"]!r} (color={g["color"]}, move={g["move"]})')
        print(f'    pgn: {g["pgn"]}')
        print(
            f'    gambiteer ({g["color"]}) ever at risk: {result["gambiteer_ever_at_risk"]} (first at ply {result["risk_ply"]})  |  '
            f'final move by {result["last_mover"]}: capture={result["final_capture"]} hanging={result["final_hanging"]}  |  '
            f'material(white-black) at end={result["final_material"]}'
        )
        if suspicious:
            print(f'    -> {g["color"]} never loses or hangs anything anywhere in this line;')
            print('       the real sacrifice may belong to the other side, or my heuristic missed it -- check by hand.')
        print()

    total = len(gambits)
    print(f'{flagged} flagged out of {total} entries.')
    print('Every flagged entry needs a human to look at the PGN -- see the module docstring for known blind spots.')


if __name__ == '__main__':
    main()
