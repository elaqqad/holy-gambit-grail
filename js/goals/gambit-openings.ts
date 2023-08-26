import { Game } from 'chess-fetcher'
import { GambitOpening, TrophyCheckResult } from '../types/types'
import data from '../data/gambits.json'

export function gambitOpening(game: Game, gambit: GambitOpening): TrophyCheckResult {
    if (!game.result.winner) {
        return []
    }
    const winningColor = game.result.winner[0] as 'w' | 'b'
    const playerColor = gambit.color == 'white' ? 'w' : 'b'
    if (winningColor == playerColor) {
        return [
            {
                color: playerColor,
                onMoveNumber: gambit.move,
            },
        ]
    }

    return []
}
export function allGambits(): GambitOpening[] {
    return data as GambitOpening[]
}
