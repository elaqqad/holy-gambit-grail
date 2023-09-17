import { TrophyCacheFile } from '../types/types'

export async function getCachedGames(url: string): Promise<TrophyCacheFile | undefined> {
    const caches = new Map<string, string>()
    caches.set('https://lichess.org/@/zolpi', '/cache/lichess/zolpi.json')
    caches.set('https://lichess.org/@/ericrosen', '/cache/lichess/ericrosen.json')
    caches.set('https://lichess.org/@/chess-network', '/cache/lichess/chess-network.json')
    caches.set('https://lichess.org/@/drnykterstein', '/cache/lichess/drnykterstein.json')
    caches.set('https://lichess.org/@/massterofmayhem', '/cache/lichess/massterofmayhem.json')
    caches.set('https://lichess.org/@/penguingim1', '/cache/lichess/penguingim1.json')
    caches.set('https://lichess.org/@/saltyclown', '/cache/lichess/saltyclown.json')
    caches.set('https://lichess.org/@/fins', '/cache/lichess/fins.json')
    caches.set('https://lichess.org/@/rebeccaharris', '/cache/lichess/rebeccaharris.json')
    caches.set('https://lichess.org/@/grandmastergauri', '/cache/lichess/grandmastergauri.json')

    caches.set('https://www.chess.com/member/vampirechicken', '/cache/chesscom/vampirechicken.json')
    caches.set('https://www.chess.com/member/alexandrabotez', '/cache/chesscom/alexandrabotez.json')
    caches.set('https://www.chess.com/member/chessbrah', '/cache/chesscom/chessbrah.json')
    caches.set('https://www.chess.com/member/danielnaroditsky', '/cache/chesscom/danielnaroditsky.json')
    caches.set('https://www.chess.com/member/gothamchess', '/cache/chesscom/gothamchess.json')
    caches.set('https://www.chess.com/member/hikaru', '/cache/chesscom/hikaru.json')
    caches.set('https://www.chess.com/member/imrosen', '/cache/chesscom/imrosen.json')
    caches.set('https://www.chess.com/member/knvb', '/cache/chesscom/knvb.json')
    caches.set('https://www.chess.com/member/magnuscarlsen', '/cache/chesscom/magnuscarlsen.json')
    caches.set('https://www.chess.com/member/saltyclown', '/cache/chesscom/saltyclown.json')
    caches.set('https://www.chess.com/member/fins0905', '/cache/chesscom/fins0905.json')
    caches.set('https://www.chess.com/member/gmbenjaminfinegold', '/cache/chesscom/gmbenjaminfinegold.json')

    if (!caches.has(url)) {
        return undefined
    }
    return await fetch(caches.get(url)!)
        .then((response) => response.json())
        .then((result: TrophyCacheFile) => result)
}
