/**
 * End-to-end regression tests for gambit detection against the real, shipped
 * public/data/gambits.json — not synthetic fixtures — so a bad edit to the data
 * (a colliding PGN prefix, a broken transposition) fails a test instead of
 * silently breaking detection for real players.
 *
 * Two independent detection paths exist in the codebase and are both covered:
 *  - The TreeMap (js/utils/TreeMap.ts), built by App.vue's LoadGambits() and used
 *    live in the browser. It matches an exact SAN move-string prefix, so it only
 *    recognizes a transposition if that specific move order was pre-computed into
 *    the gambit's `transpositions` field (by scripts/build-transpositions.py).
 *  - findGambitsInMoves() (js/goals/gambit-openings.ts), used only by
 *    scripts/update-cache.ts. It replays the game with chess.js and matches by
 *    resulting FEN, so it recognizes *any* move order reaching the same position —
 *    no pre-computed transposition list needed.
 */

import { readFileSync } from 'node:fs'
import { describe, test, expect } from 'vitest'
import type { PgnMove } from '@mliebelt/pgn-types'
import { TreeMap } from '../js/utils/TreeMap'
import { pgnPrefix, pgnToMoves, buildGambitPositionIndex, findGambitsInMoves } from '../js/goals/gambit-openings'
import type { GambitOpening } from '../js/types/types'

const gambits = JSON.parse(readFileSync('public/data/gambits.json', 'utf8')) as GambitOpening[]

// Mirrors App.vue's LoadGambits(): index every gambit under its main-line PGN
// and every listed transposition.
function buildTree(entries: GambitOpening[]): TreeMap<string, GambitOpening> {
    const tree = new TreeMap<string, GambitOpening>()
    for (const gambit of entries) {
        tree.set(pgnPrefix(gambit), gambit)
        for (const transposition of gambit.transpositions ?? []) {
            tree.set(pgnToMoves(transposition), gambit)
        }
    }
    return tree
}

// Minimal PgnMove stand-ins — only `.notation.notation` (the SAN string) is read
// by either detection path.
function sanMoves(...sans: string[]): PgnMove[] {
    return sans.map(
        (san) =>
            ({
                notation: { notation: san, col: '', row: '' },
            }) as PgnMove
    )
}

function byName(entries: GambitOpening[], name: string, pgn?: string): GambitOpening {
    const match = entries.find((g) => g.name === name && (pgn === undefined || g.pgn === pgn))
    if (!match) throw new Error(`fixture gambit not found: ${name} ${pgn ?? ''}`)
    return match
}

describe('TreeMap detection against the real gambits.json', () => {
    const tree = buildTree(gambits)

    test('detects Blackmar-Diemer Gambit via its main line', () => {
        const bdg = byName(gambits, 'Blackmar-Diemer Gambit', '1. d4 d5 2. e4')
        const results = tree.getMap(sanMoves('d4', 'd5', 'e4'), (m) => m.notation.notation)
        expect(results).toContainEqual(bdg)
    })

    test('detects Blackmar-Diemer Gambit via its recorded Scandinavian transposition (1. e4 d5 2. d4)', () => {
        const bdg = byName(gambits, 'Blackmar-Diemer Gambit', '1. d4 d5 2. e4')
        const results = tree.getMap(sanMoves('e4', 'd5', 'd4'), (m) => m.notation.notation)
        expect(results).toContainEqual(bdg)
    })

    // Regression for a real reported miss: https://lichess.org/e5e8w91q (Oct 2023
    // feedback). The game reaches the position via 2...e6 3.dxe6 (a normal capture);
    // our canonical PGN uses 2...e5 3.dxe6 (en passant) -- same resulting FEN, but a
    // different SAN string, so the TreeMap missed it until this transposition was added.
    test('detects Boehnke Gambit via the en-passant/direct-capture transposition', () => {
        const boehnke = byName(gambits, 'Scandinavian Defense: Boehnke Gambit')
        const results = tree.getMap(sanMoves('e4', 'd5', 'exd5', 'e6', 'dxe6'), (m) => m.notation.notation)
        expect(results).toContainEqual(boehnke)
    })

    // Regression for the collision fixed in PR #7 ("Fix TreeMap collision crash
    // and runtime errors"): the Countergambit's line must never fire the Gambit's
    // trophy just because they share an opening move prefix, and vice versa.
    test('does not confuse the Corkscrew Gambit with the Corkscrew Countergambit', () => {
        const countergambit = byName(gambits, 'Latvian Gambit: Corkscrew Countergambit')
        const gambit = byName(gambits, 'Latvian Gambit: Corkscrew Gambit')

        const countergambitResults = tree.getMap(sanMoves(...pgnToMoves(countergambit.pgn)), (m) => m.notation.notation)
        expect(countergambitResults).toContainEqual(countergambit)
        expect(countergambitResults).not.toContainEqual(gambit)

        const gambitResults = tree.getMap(sanMoves(...pgnToMoves(gambit.pgn)), (m) => m.notation.notation)
        expect(gambitResults).toContainEqual(gambit)
        expect(gambitResults).not.toContainEqual(countergambit)
    })

    test('detects Sicilian Defense: Wing Gambit Deferred', () => {
        const wingDeferred = byName(gambits, 'Sicilian Defense: Wing Gambit Deferred')
        const results = tree.getMap(sanMoves(...pgnToMoves(wingDeferred.pgn)), (m) => m.notation.notation)
        expect(results).toContainEqual(wingDeferred)
    })

    test('detects Italian Game: Classical Variation, Greco Gambit, Traditional Line', () => {
        const tradLine = byName(gambits, 'Italian Game: Classical Variation, Greco Gambit, Traditional Line')
        const results = tree.getMap(sanMoves(...pgnToMoves(tradLine.pgn)), (m) => m.notation.notation)
        expect(results).toContainEqual(tradLine)
    })

    test('an unlisted transposition is NOT recognized by the TreeMap (documents its limitation)', () => {
        // Beyer Gambit's own transpositions field only lists "1. e4 d5 2. d4 e5" —
        // not this equally valid move order reaching the exact same position.
        const results = tree.getMap(sanMoves('d4', 'd5', 'e4', 'e5'), (m) => m.notation.notation)
        const beyer = byName(gambits, "King's Pawn Game: Beyer Gambit")
        expect(results).not.toContainEqual(beyer)
    })
})

describe('findGambitsInMoves (FEN-based, used by scripts/update-cache.ts)', () => {
    const gambitsByFen = buildGambitPositionIndex(gambits)

    test('detects a gambit via its main line', () => {
        const smithMorra = byName(gambits, 'Sicilian Defense: Smith-Morra Gambit', '1. e4 c5 2. d4')
        const found = findGambitsInMoves(sanMoves('e4', 'c5', 'd4'), gambitsByFen)
        expect(found.map((f) => f.gambit)).toContainEqual(smithMorra)
    })

    // Same position as the TreeMap test above, reached by a different, unlisted
    // move order — the FEN-based matcher gets this right without needing any
    // pre-computed transposition entry, unlike the TreeMap.
    test('detects a transposition that has no corresponding entry in `transpositions` at all', () => {
        const beyer = byName(gambits, "King's Pawn Game: Beyer Gambit")
        const found = findGambitsInMoves(sanMoves('d4', 'd5', 'e4', 'e5'), gambitsByFen)
        expect(found.map((f) => f.gambit)).toContainEqual(beyer)
    })

    test('does not confuse the Corkscrew Gambit with the Corkscrew Countergambit', () => {
        const countergambit = byName(gambits, 'Latvian Gambit: Corkscrew Countergambit')
        const gambit = byName(gambits, 'Latvian Gambit: Corkscrew Gambit')

        const countergambitFound = findGambitsInMoves(sanMoves(...pgnToMoves(countergambit.pgn)), gambitsByFen).map((f) => f.gambit)
        expect(countergambitFound).toContainEqual(countergambit)
        expect(countergambitFound).not.toContainEqual(gambit)
    })
})

// Regression for the color-audit session: check-gambit-colors.py flagged these
// because color_and_move_from_pgn() derives color from whoever plays the
// recorded last move, not from who actually offered the material. Confirmed
// by hand (with a live Lichess board) and fixed by truncating each PGN to end
// on the real gambiteer's move instead.
describe('color fixes from the gambit-color-audit session', () => {
    test('Chigorin Defense Modern Gambit is White (White offers 2.c4; Black only accepts it later)', () => {
        const g = byName(gambits, "Queen's Gambit Declined: Chigorin Defense, Modern Gambit")
        expect(g.color).toBe('white')
        expect(g.pgn).toBe('1. d4 d5 2. c4 Nc6 3. Nc3 dxc4 4. Nf3')
    })

    test('Clam Gambit is Black (Black offers 3...f5; White just accepts with 4.exf5)', () => {
        const g = byName(gambits, 'Latvian Gambit: Clam Gambit')
        expect(g.color).toBe('black')
        expect(g.pgn).toBe('1. e4 e5 2. Nf3 Nc6 3. d3 f5')
    })

    test('QGA Slav Gambit is White (White offers 2.c4; the recorded 3...b5 is just Black defending it)', () => {
        const g = byName(gambits, "Queen's Gambit Accepted: Slav Gambit")
        expect(g.color).toBe('white')
        expect(g.pgn).toBe('1. d4 d5 2. c4 dxc4 3. Nf3')
    })

    test('Nei Gambit was removed (no material ever changes hands in the line)', () => {
        expect(gambits.find((g) => g.name.includes('Nei Gambit'))).toBeUndefined()
    })
})
