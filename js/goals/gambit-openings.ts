import { Chess } from 'chess.js'
import { Game } from 'chess-fetcher'
import type { PgnMove } from '@mliebelt/pgn-types'
import { GambitOpening, TrophyCheckResult } from '../types/types'

export function gambitTrophy(game: Game, gambit: GambitOpening): TrophyCheckResult {
    if (!game.result.winner) {
        return []
    }
    if (game.result.winner === gambit.color) {
        return [
            {
                color: gambit.color == 'white' ? 'w' : 'b',
                onMoveNumber: gambit.move,
            },
        ]
    }
    return []
}
export function winnerIsUser(game: Game, username: string) {
    if (game.result.winner == 'white') return game.players.white.username?.toLowerCase() === username
    if (game.result.winner == 'black') return game.players.black.username?.toLowerCase() === username
    return false
}
export function gameAgainstBot(game: Game, title: string | undefined) {
    return (
        title !== 'BOT' &&
        (typeof game.players.white.username === 'undefined' ||
            typeof game.players.black.username === 'undefined' ||
            game.players.white.title === 'BOT' ||
            game.players.black.title === 'BOT')
    )
}

export function pgnToMoves(pgn: string): string[] {
    return pgn
        .replace(/^1. /g, '')
        .replace(/\s+(\d+\.)\s+/g, ' ')
        .split(' ')
}

export function pgnPrefix(gambit: GambitOpening): string[] {
    return pgnToMoves(gambit.pgn)
}
export async function allGambits(): Promise<GambitOpening[]> {
    return await fetch('/data/gambits.json'!)
        .then((response) => response.json())
        .then((result: GambitOpening[]) => result)
}

export function buildGambitPositionIndex(gambits: GambitOpening[]): Map<string, GambitOpening[]> {
    const index = new Map<string, GambitOpening[]>()
    for (const gambit of gambits) {
        const key = gambit.fen.split(' ').slice(0, 4).join(' ')
        const bucket = index.get(key) ?? []
        bucket.push(gambit)
        index.set(key, bucket)
    }
    return index
}

export function findGambitsInMoves(moves: PgnMove[], gambitsByFen: Map<string, GambitOpening[]>): { gambit: GambitOpening; onMoveNumber: number }[] {
    const results: { gambit: GambitOpening; onMoveNumber: number }[] = []
    const chess = new Chess()
    for (let i = 0; i < moves.length; i++) {
        try {
            chess.move(moves[i].notation.notation)
        } catch {
            break
        }
        const key = chess.fen().split(' ').slice(0, 4).join(' ')
        const matched = gambitsByFen.get(key)
        if (matched) {
            for (const gambit of matched) {
                results.push({ gambit, onMoveNumber: i + 1 })
            }
        }
    }
    return results
}
