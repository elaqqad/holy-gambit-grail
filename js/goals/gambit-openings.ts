import { Game } from 'chess-fetcher'
import { GambitOpening, TrophyCheckResult } from '../types/types'
import data from '../data/gambits.json'

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
    if (game.result.winner == 'white') return game.players.white.username.toLowerCase() === username
    if (game.result.winner == 'black') return game.players.black.username.toLowerCase() === username
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

export function pgnPrefix(gambit: GambitOpening): string[] {
    return gambit.pgn
        .replace(/^1. /g, '')
        .replace(/\s+(\d+\.)\s+/g, ' ')
        .split(' ')
}
export function allGambits(): GambitOpening[] {
    return data as GambitOpening[]
}
