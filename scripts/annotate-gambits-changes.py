"""
Add original_pgn, original_fen, and comment fields to gambits.json entries
that were modified from the Lichess source database.

These annotations record WHY a position differs from the upstream Lichess
chess-openings database, so the rationale is preserved and can optionally
be surfaced to users (e.g. as a hover tooltip on the gambit card).
"""

import json
import subprocess

JSON_PATH = 'public/data/gambits.json'

# ── Fetch original data from main branch ─────────────────────────────────────

result = subprocess.run(
    ['git', 'show', 'main:public/data/gambits.json'],
    capture_output=True, text=True, encoding='utf-8'
)
original_by_key = {(x['name'], x['eco']): x for x in json.loads(result.stdout)}

with open(JSON_PATH, encoding='utf-8') as f:
    gambits = json.load(f)

# ── Hand-written comments for each intentionally changed entry ────────────────
# Key: (name, eco)

COMMENTS = {
    ('Amar Gambit', 'A00'): (
        "Lichess attributes this gambit to the position after 4...exf4 (Black's acceptance). "
        "On this site we stop at 4. Bxh3, White's last gambit move, "
        "so the trophy goes to White who played the creative opening."
    ),
    ('Hungarian Opening: Pachman Gambit', 'A00'): (
        "Lichess includes Black's reply 3...g6 in the gambit PGN. "
        "On this site we stop at 3. Qh5+, White's last move, "
        "as the check itself is the gambit idea — Black's response does not define it. "
        "Note: the true sacrifice begins as early as 1. g3 f5 2. e4 but that position "
        "has its own name; we may revisit this boundary in a future update."
    ),
    ('Mikenas Defense: Pozarek Gambit', 'A40'): (
        "Lichess includes Black's 4...Nxc4 (acceptance) in the PGN. "
        "On this site we stop at 4. Nc3, White's last move before the capture."
    ),
    ('Bird Opening: Dutch Variation, Batavo Gambit', 'B21'): (
        "Lichess includes Black's 3...dxe4 (acceptance) in the PGN. "
        "On this site we stop at 3. Nf3, White's last move before Black takes."
    ),
    ('Sicilian Defense: Smith-Morra Gambit', 'B21'): (
        "Lichess classifies the Smith-Morra including Black's 3...cxd4 acceptance and then 3. c3. "
        "On this site we use the shorter offer position 1. e4 c5 2. d4, "
        "so the gambit is detected as soon as White plays d4 regardless of whether Black accepts."
    ),
    ('French Defense: La Bourdonnais Variation, Reuter Gambit', 'C00'): (
        "Lichess includes Black's 3...dxe4 in the PGN. "
        "On this site we stop at 3. Nf3, White's last move."
    ),
    ('French Defense: Alekhine-Chatard Attack, Albin-Chatard Gambit', 'C13'): (
        "Lichess includes Black's 7...Qxg5 (taking the bishop) in the PGN, "
        "which assigns the gambit to Black. "
        "On this site we stop at 7. hxg5, White's sacrifice of the h-pawn, "
        "so the trophy correctly goes to White who initiates the attack."
    ),
    ('Vienna Gambit, with Max Lange Defense: Hamppe-Muzio Gambit', 'C25'): (
        "Lichess includes Black's 6...gxf3 (acceptance) in the PGN. "
        "On this site we stop at 6. O-O, White's last move before Black takes."
    ),
    ('Vienna Game: Paulsen Variation, Pollock Gambit', 'C26'): (
        "Lichess stops at 6. exd5, a White move, which would assign the gambit to White. "
        "The Pollock Gambit is actually Black's counter-sacrifice: after 6. exd5 Black plays "
        "6...Nd4, the defining move. We extend the PGN to 6...Nd4 so the trophy goes to Black."
    ),
    ('King\'s Gambit Accepted: Greco Gambit', 'C34'): (
        "Lichess includes Black's 6...Bg7 in the PGN. "
        "On this site we stop at 6. h4, White's last move, "
        "as White is the gambiteer in the King's Gambit."
    ),
    ('King\'s Gambit Accepted: Cunningham Defense, Bertin Gambit', 'C35'): (
        "Lichess includes Black's 7. Kh1 response in the extended PGN. "
        "On this site we stop at 5. g3, White's last gambit move before Black responds."
    ),
    ('King\'s Gambit Accepted: Blachly Gambit', 'C37'): (
        "Lichess includes Black's 4...g5 in the PGN. "
        "On this site we stop at 4. Bc4, White's last move."
    ),
    ('King\'s Gambit Accepted: Double Muzio Gambit, Young Gambit', 'C37'): (
        "Lichess includes Black's 10...fxe3 in the PGN, assigning the gambit to Black. "
        "On this site we stop at 10. Nc3, White's last move in the long sacrificial sequence, "
        "so the trophy correctly goes to White."
    ),
    ('King\'s Gambit Accepted: Ghulam-Kassim Gambit', 'C37'): (
        "Lichess includes Black's 5...gxf3 in the PGN. "
        "On this site we stop at 5. d4, White's last gambit push."
    ),
    ('King\'s Gambit Accepted: Kieseritzky Gambit, Rice Gambit', 'C39'): (
        "Lichess includes Black's 8...Bxe5 in the PGN. "
        "On this site we stop at 8. O-O, White's last move before the capture."
    ),
    ('Scotch Game: Haxo Gambit', 'C44'): (
        "Lichess stops at 4...Bc5, a Black move, but without the actual gambit sacrifice. "
        "We extend the line to 5. c3 d3 where Black plays the pawn thrust d3 — "
        "the real gambit move — so Black is correctly identified as the gambiteer."
    ),
    ('Italian Game: Evans Gambit, Mortimer-Evans Gambit', 'C51'): (
        "Lichess includes Black's 13...Kxf7 in the PGN. "
        "On this site we stop at 13. Qc2, White's last move."
    ),
    ('Italian Game: Classical Variation, Greco Gambit', 'C53'): (
        "Lichess includes Black's 6...d5 in the PGN. "
        "On this site we stop at 6. e5, White's gambit thrust."
    ),
    ('Ruy Lopez: Closed, Center Attack, Basque Gambit', 'C84'): (
        "Lichess includes Black's 8...dxc3 (acceptance) in the PGN. "
        "On this site we stop at 8. c3, White's last move before Black takes."
    ),
}

# ── Apply annotations ─────────────────────────────────────────────────────────

annotated = 0
for entry in gambits:
    key = (entry['name'], entry['eco'])
    orig = original_by_key.get(key)
    comment = COMMENTS.get(key)

    if orig and comment:
        # Only annotate if the PGN or FEN actually changed
        if orig['pgn'] != entry['pgn'] or orig['fen'] != entry['fen']:
            entry['original_pgn'] = orig['pgn']
            entry['original_fen'] = orig['fen']
            entry['comment'] = comment
            annotated += 1

with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(gambits, f, indent=4, ensure_ascii=False)

print(f'Annotated {annotated} entries in {JSON_PATH}')
