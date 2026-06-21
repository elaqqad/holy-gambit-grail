/**
 * Validates that scripts/gambits.csv and public/data/gambits.json are in sync.
 *
 * The CSV is the source of truth. The JSON is generated from it via
 * `python scripts/generate-gambits-json.py`. These tests catch drift between
 * the two files — e.g. after editing the CSV without regenerating the JSON.
 *
 * The unique key for each entry is (eco, name, pgn) because some gambits
 * intentionally appear more than once under the same name with different PGNs
 * (gambit offer vs. gambit accepted variants).
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

// ── Load both files ───────────────────────────────────────────────────────────

const csvRows = parseCSV(readFileSync('scripts/gambits.csv', 'utf8'))
const jsonEntries = JSON.parse(readFileSync('public/data/gambits.json', 'utf8')) as Record<string, unknown>[]

const csvKeys = csvRows.map((r) => `${r.eco}|${r.name}|${r.pgn}`)
const jsonKeys = jsonEntries.map((g) => `${g.eco}|${g.name}|${g.pgn}`)
const csvKeySet = new Set(csvKeys)
const jsonKeySet = new Set(jsonKeys)

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('gambits CSV/JSON sync', () => {
    test('same number of entries', () => {
        expect(jsonEntries.length).toBe(csvRows.length)
    })

    test('no duplicate (eco, name, pgn) in CSV', () => {
        expect(csvKeySet.size).toBe(csvRows.length)
    })

    test('no duplicate (eco, name, pgn) in JSON', () => {
        expect(jsonKeySet.size).toBe(jsonEntries.length)
    })

    test('every CSV entry exists in JSON', () => {
        const missing = csvKeys.filter((k) => !jsonKeySet.has(k))
        expect(missing, `CSV entries missing from JSON:\n${missing.join('\n')}`).toHaveLength(0)
    })

    test('every JSON entry exists in CSV', () => {
        const extra = jsonKeys.filter((k) => !csvKeySet.has(k))
        expect(extra, `JSON entries not in CSV:\n${extra.join('\n')}`).toHaveLength(0)
    })

    test('stats and metadata match between CSV and JSON', () => {
        const jsonByKey = new Map(jsonEntries.map((g) => [`${g.eco}|${g.name}|${g.pgn}`, g]))
        for (const row of csvRows) {
            const key = `${row.eco}|${row.name}|${row.pgn}`
            const json = jsonByKey.get(key)
            if (!json) continue // already caught by 'every CSV entry exists in JSON'

            expect(json.color, `color: ${key}`).toBe(row.color)
            expect(json.move, `move: ${key}`).toBe(Number(row.move))
            expect(json.fen, `fen: ${key}`).toBe(row.fen)
            expect(json.master ?? '', `master: ${key}`).toBe(row.master)
            expect(json.lichess ?? '', `lichess: ${key}`).toBe(row.lichess)
            expect(json.white, `white: ${key}`).toBe(Number(row.white))
            expect(json.draws, `draws: ${key}`).toBe(Number(row.draws))
            expect(json.black, `black: ${key}`).toBe(Number(row.black))
        }
    })
})
