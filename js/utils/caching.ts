import { TrophyCacheFile } from '../types/types'

export async function getCachedGames(url: string): Promise<TrophyCacheFile | undefined> {
    const caches = new Map<string, string>()
    // caches.set('https://lichess.org/@/german11', '/cache/lichess/german11.json')
    // caches.set('https://lichess.org/@/chess-network', '/cache/lichess/chess-network.json')
    // caches.set('https://lichess.org/@/drnykterstein', '/cache/lichess/drnykterstein.json')
    // caches.set('https://lichess.org/@/ericrosen', '/cache/lichess/ericrosen.json')
    // caches.set('https://lichess.org/@/massterofmayhem', '/cache/lichess/massterofmayhem.json')
    // caches.set('https://lichess.org/@/penguingim1', '/cache/lichess/penguingim1.json')
    // caches.set('https://lichess.org/@/saltyclown', '/cache/lichess/saltyclown.json')

    // caches.set('https://www.chess.com/member/alexandrabotez', '/cache/chesscom/alexandrabotez.json')
    // caches.set('https://www.chess.com/member/chessbrah', '/cache/chesscom/chessbrah.json')
    // caches.set('https://www.chess.com/member/danielnaroditsky', '/cache/chesscom/danielnaroditsky.json')
    // caches.set('https://www.chess.com/member/gothamchess', '/cache/chesscom/gothamchess.json')
    // caches.set('https://www.chess.com/member/hikaru', '/cache/chesscom/hikaru.json')
    // caches.set('https://www.chess.com/member/imrosen', '/cache/chesscom/imrosen.json')
    // caches.set('https://www.chess.com/member/knvb', '/cache/chesscom/knvb.json')
    // caches.set('https://www.chess.com/member/magnuscarlsen', '/cache/chesscom/magnuscarlsen.json')
    // caches.set('https://www.chess.com/member/saltyclown', '/cache/chesscom/saltyclown.json')
    if (!caches.has(url)) {
        return undefined
    }
    return await fetch(caches.get(url)!)
        .then((response) => response.json())
        .then((result: TrophyCacheFile) => result)
}
