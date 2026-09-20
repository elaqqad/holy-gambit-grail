# Curation notes

A running log of judgment calls made about the gambit data that aren't
obvious from the diff alone -- so nobody (including future us) has to
re-derive _why_ a color was flipped, an entry was removed, or a comment says
what it says. Keep appending to this file; don't overwrite past entries.

## Background: why colors sometimes need a human

`color_and_move_from_pgn()` (in `build-gambits.py` and
`generate-gambits-json.py`) derives a gambit's `color` from one rule only:
whoever plays the textually **last** move in the recorded PGN. That's a
convenient proxy, not a chess judgment -- it has no idea who actually offered
material. It fails in two directions:

-   **Lichess's own PGN runs past the real sacrifice.** The trailing move is a
    quiet follow-up by the _other_ side, which flips the derived color. Caught
    by `scripts/check-gambit-colors.py`; fixed by truncating the PGN (as a
    delta `modify`) to end back on the real gambiteer's move.
-   **The is_gambit() filter's name-suffix check.** It only keeps Lichess
    opening names that literally end in the word "Gambit", so names with a
    trailing qualifier ("... Deferred", "..., Traditional Line") get silently
    dropped even though they're real gambits. Not fixed wholesale (too many
    false positives among the ~667 other "contains gambit but doesn't end in
    it" names -- most of those genuinely aren't gambits, e.g. "X Gambit
    Declined"); specific reported cases get added back via delta `add`.

`scripts/check-gambit-colors.py` screens for the first failure mode
automatically (see its own docstring for how, and its documented blind
spots), but it's a screen, not a verdict -- every flag needs a human to
actually look at the position. The tool that made this fast: publish an
Artifact table with the exact stored PGN per entry plus a
`lichess.org/analysis/pgn/...` link, so the reviewer plays through the real
line rather than trusting a move order remembered from elsewhere online
(chess.com and Lichess don't always agree, and neither always agrees with
what's actually a few characters different in our own CSV).

## Session: gambit-color-audit (this session)

Ran `check-gambit-colors.py`, got a review Artifact built, went through it
with the site owner move by move. Decisions:

**Kept as-is, no data change** (the check flagged these, but the color is
correct once you look at the actual idea):

-   **Corkscrew Gambit / Corkscrew Countergambit** (both stay Black) -- the
    imbalance both lines grow from is Black's `2...f5`; more specifically,
    Black's `4...fxe4` (grabbing a pawn back into a wide-open position instead
    of playing safe) is the real offer, and White's `5.Nf7!?` is White
    _accepting_ the complications Black proposed, not offering their own. The
    Gambit's recorded final move (`6...d5`) is forced and comes too late to be
    "the" gambit move in any strict sense, but truncating further isn't worth
    it here -- noted in each entry's `comment` field instead.
-   **Philidor Gambit / Philidor Countergambit** (both stay Black) -- the pawn
    actually left hanging in both is Black's own `e5` (attacked by White's
    `3.d4` since move 2, never defended); the two entries just differ in _how_
    Black declines to save it (`3...f5` vs `3...Bd7`).
-   **Grob/Fritz/Romford Countergambit** (stays Black) -- the real gambiting
    choice is several moves before the recorded final move: `2...Bxg4` and
    `3...d4` keep grabbing material instead of giving it back or defending
    b7/a8, which forces the sequence into White netting a rook by `5.Bxa8`. We
    keep the PGN at `5...Qxa8` (Black's forced recapture) by convention; see
    the entry's `comment`.
-   **Maróczy Gambit, Nimzowitsch Gambit, Ruisdonk Gambit, Chandler Gambit,
    Zilbermints-Benoni Gambit** (all stay White) -- these all leave a central
    pawn structurally underdefended from early on; Black eventually wins it
    several moves later, and White's recorded final move just develops instead
    of immediately trying to get it back. `check-gambit-colors.py` can't see
    this "slow leak" pattern (the threat builds up over several of Black's
    moves, not one), but it's a real, deliberate White gambit in each case.
-   **Zilbermints Double Gambit / Countergambit** (both stay Black) -- both end
    on a further, deliberate Black pawn push (`2...g5` / `4...g5`); a
    consistent idea in both, unlike the Corkscrew pair.

**Fixed** (delta `modify` rows added in `gambits-delta.csv`, with the
per-entry reasoning in each entry's `comment` field in `gambits.json`):

-   `Queen's Gambit Declined: Chigorin Defense, Modern Gambit`: White, not
    Black. Truncated to end on `4. Nf3`.
-   `Latvian Gambit: Clam Gambit`: Black, not White. Truncated to end on
    `3...f5`.
-   `Queen's Gambit Accepted: Slav Gambit`: White, not Black. Truncated to end
    on `3. Nf3`. Caveat kept in the comment: this is only really a _further_
    gambit if Black plays the (uncommon) `3...b5` to hold the pawn -- most QGA
    lines are just better for White regardless.

**Removed** (delta `remove`, reason in the delta row's `comment`):

-   `English Opening: ... Nei Gambit` -- not a real gambit. No material ever
    changes hands in the line; Black is simply forced to retreat a knight
    (`4...Ng8`) after White's space-gaining `4.e5`.

Regression tests for the three color fixes and the removal live in
`tests/gambit-detection.test.ts` (see the `color fixes from the
gambit-color-audit session` describe block).
