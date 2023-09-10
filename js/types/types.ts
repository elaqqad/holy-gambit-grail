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
export type Trophy = {
    date: string
    opponent: {
        username: string
        title: string
    }
    link: string
}
export type YoutubeTrophy = {
    game: string
    video: string
    title: string
}
export type TrophyForGame = {
    [key: string]: Trophy
}

export type PlayerTrophiesByType = {
    [key: string]: TrophyForGame
}
export type YoutubeVideoByType = {
    [key: string]: YoutubeTrophy[]
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
