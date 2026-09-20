/**
 * Validates that public/data/gambits.json is exactly what the pipeline should
 * produce from scripts/gambits.csv (the automated, deterministic is_gambit()
 * filter over the Lichess openings TSV) with scripts/gambits-delta.csv (the
 * only place manual curation happens) applied on top -- see
 * scripts/generate-gambits-json.py, which this test mirrors.
 *
 * gambits.csv is NOT expected to match gambits.json entry-for-entry anymore:
 * the CSV is the raw automated set, the JSON is the curated one. These tests
 * instead reconstruct the expected curated key set from CSV + delta and catch
 * drift -- e.g. after editing the delta without regenerating the JSON, or a
 * bug in how removes/modifies/adds are applied. A modify row may leave
 * new_pgn blank to attach a comment without changing the position -- such a
 * row keeps the raw CSV's own key and stats (see generate-gambits-json.py).
 */

import { readFileSync } from 'node:fs'
import { describe, test, expect } from 'vitest'

// ── Minimal CSV parser that handles quoted fields containing commas ───────────

function parseCSVLine(line: string): string[] {
    const result: string[] = []
    let field = ''
    let inQuotes = false
    for (const ch of line) {
        if (ch === '"') {
            inQuotes = !inQuotes
        } else if (ch === ',' && !inQuotes) {
            result.push(field)
            field = ''
        } else {
            field += ch
        }
    }
    result.push(field)
    return result
}

function parseCSV(content: string): Record<string, string>[] {
    const lines = content.split('\n').filter((l) => l.trim())
    const headers = parseCSVLine(lines[0]).map((h) => h.trim())
    return lines.slice(1).map((line) => {
        const values = parseCSVLine(line).map((v) => v.trim())
        return Object.fromEntries(headers.map((h, i) => [h, values[i] ?? '']))
    })
}

type Key = string
const keyOf = (eco: string, name: string, pgn: string): Key => `${eco}|${name}|${pgn}`

// ── Load raw CSV, delta, and the generated JSON ────────────────────────────────

const rawRows = parseCSV(readFileSync('scripts/gambits.csv', 'utf8'))
const deltaRows = parseCSV(readFileSync('scripts/gambits-delta.csv', 'utf8'))
const jsonEntries = JSON.parse(readFileSync('public/data/gambits.json', 'utf8')) as Record<string, unknown>[]
const jsonByKey = new Map(jsonEntries.map((g) => [keyOf(g.eco as string, g.name as string, g.pgn as string), g]))

const removes = new Set<Key>()
const modifies = new Map<Key, Record<string, string>>()
const adds: Record<string, string>[] = []

for (const row of deltaRows) {
    const key = keyOf(row.eco, row.name, row.pgn)
    if (row.action === 'remove') removes.add(key)
    else if (row.action === 'modify') modifies.set(key, row)
    else if (row.action === 'add') adds.push(row)
}

// ── Reconstruct the expected curated key set from raw CSV + delta ─────────────

// A modify row may leave new_pgn blank: a comment-only annotation that
// doesn't change the position (see generate-gambits-json.py).
const modifiedPgn = (row: Record<string, string>, rawPgn: string): string => row.new_pgn.trim() || rawPgn

const expectedKeys = new Set<Key>()
for (const row of rawRows) {
    const rawKey = keyOf(row.eco, row.name, row.pgn)
    if (removes.has(rawKey)) continue
    const modify = modifies.get(rawKey)
    expectedKeys.add(modify ? keyOf(row.eco, row.name, modifiedPgn(modify, row.pgn)) : rawKey)
}
for (const row of adds) {
    expectedKeys.add(keyOf(row.eco, row.name, row.pgn))
}

describe('gambits.csv + gambits-delta.csv -> gambits.json', () => {
    test('delta references only existing raw CSV entries for remove/modify', () => {
        const rawKeySet = new Set(rawRows.map((r) => keyOf(r.eco, r.name, r.pgn)))
        const dangling = [...removes, ...modifies.keys()].filter((k) => !rawKeySet.has(k))
        expect(dangling, `remove/modify keys not found in gambits.csv:\n${dangling.join('\n')}`).toHaveLength(0)
    })

    test('no duplicate (eco, name, pgn) in JSON', () => {
        expect(jsonByKey.size).toBe(jsonEntries.length)
    })

    test('JSON key set matches raw CSV + delta exactly', () => {
        const jsonKeys = new Set(jsonByKey.keys())
        const missing = [...expectedKeys].filter((k) => !jsonKeys.has(k))
        const extra = [...jsonKeys].filter((k) => !expectedKeys.has(k))
        expect(missing, `expected entries missing from JSON:\n${missing.join('\n')}`).toHaveLength(0)
        expect(extra, `JSON entries not explained by CSV + delta:\n${extra.join('\n')}`).toHaveLength(0)
    })

    test('unmodified entries carry the raw CSV stats and metadata', () => {
        for (const row of rawRows) {
            const rawKey = keyOf(row.eco, row.name, row.pgn)
            if (removes.has(rawKey) || modifies.has(rawKey)) continue
            const json = jsonByKey.get(rawKey)
            if (!json) continue // already caught by the key-set test above

            expect(json.color, `color: ${rawKey}`).toBe(row.color)
            expect(json.move, `move: ${rawKey}`).toBe(Number(row.move))
            expect(json.fen, `fen: ${rawKey}`).toBe(row.fen)
            expect(json.master ?? '', `master: ${rawKey}`).toBe(row.master)
            expect(json.lichess ?? '', `lichess: ${rawKey}`).toBe(row.lichess)
            expect(json.white, `white: ${rawKey}`).toBe(Number(row.white))
            expect(json.draws, `draws: ${rawKey}`).toBe(Number(row.draws))
            expect(json.black, `black: ${rawKey}`).toBe(Number(row.black))
            expect(json.original_pgn, `unmodified entry should not carry original_pgn: ${rawKey}`).toBeUndefined()
        }
    })

    test('PGN-changing modify entries carry the delta stats, new PGN, and the raw PGN as original_pgn', () => {
        for (const [rawKey, delta] of modifies) {
            if (!delta.new_pgn.trim()) continue // comment-only modify, covered by the next test
            const newKey = keyOf(delta.eco, delta.name, delta.new_pgn)
            const raw = rawRows.find((r) => keyOf(r.eco, r.name, r.pgn) === rawKey)
            const json = jsonByKey.get(newKey)
            if (!json || !raw) continue // already caught by the key-set test above

            expect(json.original_pgn, `original_pgn: ${newKey}`).toBe(raw.pgn)
            expect(json.white, `white: ${newKey}`).toBe(Number(delta.white))
            expect(json.draws, `draws: ${newKey}`).toBe(Number(delta.draws))
            expect(json.black, `black: ${newKey}`).toBe(Number(delta.black))
            if (delta.comment) {
                expect(json.comment, `comment: ${newKey}`).toBe(delta.comment)
            }
        }
    })

    test('comment-only modify entries keep the raw PGN and stats, with no original_pgn', () => {
        for (const [rawKey, delta] of modifies) {
            if (delta.new_pgn.trim()) continue // PGN-changing modify, covered by the previous test
            const raw = rawRows.find((r) => keyOf(r.eco, r.name, r.pgn) === rawKey)
            const json = jsonByKey.get(rawKey)
            if (!json || !raw) continue // already caught by the key-set test above

            expect(json.original_pgn, `comment-only modify should not carry original_pgn: ${rawKey}`).toBeUndefined()
            expect(json.white, `white: ${rawKey}`).toBe(Number(raw.white))
            expect(json.draws, `draws: ${rawKey}`).toBe(Number(raw.draws))
            expect(json.black, `black: ${rawKey}`).toBe(Number(raw.black))
            if (delta.comment) {
                expect(json.comment, `comment: ${rawKey}`).toBe(delta.comment)
            }
        }
    })

    test('added entries carry the delta stats and never an original_pgn', () => {
        for (const row of adds) {
            const key = keyOf(row.eco, row.name, row.pgn)
            const json = jsonByKey.get(key)
            if (!json) continue // already caught by the key-set test above

            expect(json.original_pgn, `add entry should not carry original_pgn: ${key}`).toBeUndefined()
            expect(json.white, `white: ${key}`).toBe(Number(row.white))
            expect(json.draws, `draws: ${key}`).toBe(Number(row.draws))
            expect(json.black, `black: ${key}`).toBe(Number(row.black))
            if (row.comment) {
                expect(json.comment, `comment: ${key}`).toBe(row.comment)
            }
        }
    })

    test('every add/PGN-changing-modify delta row has its stats cached (run generate-gambits-json.py --fetch-stats otherwise)', () => {
        const pgnChangingModifies = [...modifies.values()].filter((row) => row.new_pgn.trim())
        const uncached = [...adds, ...pgnChangingModifies].filter((row) => !row.white && !row.draws && !row.black && !row.master)
        const names = uncached.map((row) => row.name)
        expect(names, `delta rows missing cached stats:\n${names.join('\n')}`).toHaveLength(0)
    })
})
