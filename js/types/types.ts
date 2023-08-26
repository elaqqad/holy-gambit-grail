type TrophyForColor = {
    color: 'w' | 'b'
    onMoveNumber?: number
}

export type TrophyCheckResult = TrophyForColor[]

export type TrophyCacheFile = {
    cache_updated_at: number
    games_analyzed: number
    moves_analyzed: number
    trophies: PlayerTrophiesByType
}

export type TrophyForGame = {
    [key: string]: {
        date: string
        opponent: {
            username: string
            title: string
        }
        link: string
    }
}

export type PlayerTrophiesByType = {
    [key: string]: TrophyForGame
}
export type GambitOpening = {
    eco: string
    name: string
    pgn: string
    move: number
    color: string
    fen: string
    master?: string
    lichess?: string
    white: number
    draws: number
    black: number
}
