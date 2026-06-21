import { readdir, readFile, writeFile, mkdir } from 'node:fs/promises'
import path from 'node:path'
import process from 'node:process'
import { createInterface } from 'node:readline/promises'
import { games, player } from 'chess-fetcher'
import type { Game, Profile } from 'chess-fetcher'
import { buildGambitPositionIndex, findGambitsInMoves, gambitTrophy, gameAgainstBot, winnerIsUser } from '../js/goals/gambit-openings'
import type { GambitOpening, PlayerTrophiesByType, TrophyCacheFile } from '../js/types/types'

type Site = 'lichess' | 'chesscom'

type CacheTarget = {
    site: Site
    username: string
    filePath: string
}

type Counts = {
    downloaded: number
    analyzed: number
}

const root = process.cwd()
const cacheRoot = path.join(root, 'public', 'cache')
const gambitsPath = path.join(root, 'public', 'data', 'gambits.json')

const rl = createInterface({ input: process.stdin, output: process.stdout })

async function main(): Promise<void> {
    const targets = await discoverCacheTargets()

    console.log('Holy Gambit Grail cache updater')
    console.log(`Found ${targets.length} existing cache files.\n`)

    if (process.argv.includes('--list')) {
        targets.forEach((target) => console.log(`${target.site}/${target.username}`))
        return
    }

    const mode = await askChoice('What do you want to update?', ['All existing cache files', 'One existing cache file', 'A custom username'])

    const selectedTargets = mode === 0 ? targets : mode === 1 ? [await selectExistingTarget(targets)] : [await askCustomTarget()]

    const incremental = await askYesNo('Use existing cache and fetch only new games when possible?', true)
    const gambits = await loadGambits()
    const gambitsByFen = buildGambitPositionIndex(gambits)

    for (const target of selectedTargets) {
        try {
            await updateCache(target, gambits, gambitsByFen, incremental)
        } catch (error) {
            console.error(`\nFailed to update ${target.site}/${target.username}:`)
            console.error(error instanceof Error ? error.message : error)
        }
    }
}

async function discoverCacheTargets(): Promise<CacheTarget[]> {
    const targets: CacheTarget[] = []
    for (const site of ['lichess', 'chesscom'] satisfies Site[]) {
        const dir = path.join(cacheRoot, site)
        const files = await readdir(dir)
        for (const file of files.filter((name) => name.endsWith('.json')).sort()) {
            targets.push({
                site,
                username: path.basename(file, '.json'),
                filePath: path.join(dir, file),
            })
        }
    }
    return targets
}

async function selectExistingTarget(targets: CacheTarget[]): Promise<CacheTarget> {
    targets.forEach((target, index) => {
        console.log(`${index + 1}. ${target.site}/${target.username}`)
    })

    while (true) {
        const answer = await rl.question('\nChoose a cache file number: ')
        const index = Number(answer) - 1
        if (Number.isInteger(index) && targets[index]) {
            return targets[index]
        }
        console.log('Please enter one of the listed numbers.')
    }
}

async function askCustomTarget(): Promise<CacheTarget> {
    const siteIndex = await askChoice('Which site?', ['Lichess', 'Chess.com'])
    const site: Site = siteIndex === 0 ? 'lichess' : 'chesscom'
    const username = normalizeUsername(await rl.question('Username: '))
    if (!username) {
        throw new Error('Username is required.')
    }

    return {
        site,
        username,
        filePath: path.join(cacheRoot, site, `${username}.json`),
    }
}

async function askChoice(question: string, choices: string[]): Promise<number> {
    console.log(question)
    choices.forEach((choice, index) => {
        console.log(`${index + 1}. ${choice}`)
    })

    while (true) {
        const answer = await rl.question('Choose a number: ')
        const index = Number(answer) - 1
        if (Number.isInteger(index) && choices[index]) {
            return index
        }
        console.log('Please enter one of the listed numbers.')
    }
}

async function askYesNo(question: string, defaultValue: boolean): Promise<boolean> {
    const suffix = defaultValue ? 'Y/n' : 'y/N'
    const answer = (await rl.question(`${question} [${suffix}] `)).trim().toLowerCase()
    if (!answer) {
        return defaultValue
    }
    return answer === 'y' || answer === 'yes'
}

async function updateCache(
    target: CacheTarget,
    gambits: GambitOpening[],
    gambitsByFen: ReturnType<typeof buildGambitPositionIndex>,
    incremental: boolean
): Promise<void> {
    const existing = incremental ? await readCacheFile(target.filePath) : undefined
    const url = urlForTarget(target)
    const profile = await player(url)
    const username = profile.username.toLowerCase()
    const trophies = existing ? cloneTrophies(existing.trophies) : emptyTrophies(gambits)
    const counts: Counts = {
        downloaded: existing?.games_analyzed ?? 0,
        analyzed: existing?.moves_analyzed ?? 0,
    }
    const since = existing?.cache_updated_at ?? 0

    ensureTrophyKeys(trophies, gambits)
    console.log(`\nUpdating ${target.site}/${target.username}${since ? ` since ${new Date(since).toISOString()}` : ' from scratch'}...`)

    await games(
        url,
        (game: Game) => {
            checkGameForTrophies(game, profile, username, trophies, gambitsByFen, counts)
            if (counts.downloaded % 500 === 0) {
                console.log(`  ${counts.downloaded.toLocaleString()} games downloaded, ${counts.analyzed.toLocaleString()} analyzed`)
            }
        },
        {
            since,
            pgnInJson: true,
            rated: true,
        }
    )

    const cacheFile: TrophyCacheFile = {
        cache_updated_at: Date.now(),
        games_analyzed: counts.downloaded,
        moves_analyzed: counts.analyzed,
        trophies,
    }

    await mkdir(path.dirname(target.filePath), { recursive: true })
    await writeFile(target.filePath, `${JSON.stringify(cacheFile, null, 2)}\n`)
    console.log(`Saved ${path.relative(root, target.filePath)} with ${countTrophies(trophies).toLocaleString()} trophies.`)
}

function checkGameForTrophies(
    game: Game,
    profile: Profile,
    username: string,
    trophies: PlayerTrophiesByType,
    gambitsByFen: ReturnType<typeof buildGambitPositionIndex>,
    counts: Counts
): void {
    counts.downloaded++
    if (game.isStandard && winnerIsUser(game, username) && !gameAgainstBot(game, profile.title)) {
        for (const { gambit, onMoveNumber } of findGambitsInMoves(game.moves, gambitsByFen)) {
            for (const result of gambitTrophy(game, gambit)) {
                addTrophyForPlayer(trophies, gambit.name, game, username, onMoveNumber || result.onMoveNumber || 0)
            }
        }
    }
    counts.analyzed++
}

function addTrophyForPlayer(trophies: PlayerTrophiesByType, trophyName: string, game: Game, username: string, onMoveNumber?: number): void {
    trophies[trophyName] ??= {}
    if (trophies[trophyName][game.id]) {
        return
    }

    const userIsWhite = game.players.white.username?.toLowerCase() === username
    const opponent = userIsWhite ? game.players.black : game.players.white
    if (!opponent.username) {
        return
    }
    let link = userIsWhite ? game.links.white : game.links.black

    if (game.site === 'lichess' && onMoveNumber) {
        link += `#${onMoveNumber}`
    } else if (onMoveNumber) {
        link += onMoveNumber - 1
    }

    trophies[trophyName][game.id] = {
        date: new Date(game.timestamp).toISOString().split('T')[0],
        opponent: {
            username: opponent.username,
            title: opponent.title || '',
        },
        link,
    }
}

async function loadGambits(): Promise<GambitOpening[]> {
    const contents = await readFile(gambitsPath, 'utf8')
    return JSON.parse(contents) as GambitOpening[]
}

async function readCacheFile(filePath: string): Promise<TrophyCacheFile | undefined> {
    try {
        return JSON.parse(await readFile(filePath, 'utf8')) as TrophyCacheFile
    } catch (error) {
        if (error instanceof Error && 'code' in error && error.code === 'ENOENT') {
            return undefined
        }
        throw error
    }
}

function emptyTrophies(gambits: GambitOpening[]): PlayerTrophiesByType {
    const trophies: PlayerTrophiesByType = {}
    ensureTrophyKeys(trophies, gambits)
    return trophies
}

function cloneTrophies(trophies: PlayerTrophiesByType): PlayerTrophiesByType {
    return JSON.parse(JSON.stringify(trophies)) as PlayerTrophiesByType
}

function ensureTrophyKeys(trophies: PlayerTrophiesByType, gambits: GambitOpening[]): void {
    for (const gambit of gambits) {
        trophies[gambit.name] ??= {}
    }
}

function countTrophies(trophies: PlayerTrophiesByType): number {
    return Object.values(trophies).reduce((count, trophyByGame) => count + Object.keys(trophyByGame).length, 0)
}

function urlForTarget(target: CacheTarget): string {
    if (target.site === 'lichess') {
        return `https://lichess.org/@/${target.username}`
    }
    return `https://www.chess.com/member/${target.username}`
}

function normalizeUsername(username: string): string {
    return username.trim().toLowerCase()
}

main()
    .catch((error: unknown) => {
        console.error(error instanceof Error ? error.message : error)
        process.exitCode = 1
    })
    .finally(() => {
        rl.close()
    })
