import { PlayerTrophiesByType, TrophyCacheFile } from '../types/types'

export function exportAsJson(
    playerTrophiesByType: PlayerTrophiesByType,
    username: string,
    counts: { totalGames: number; downloaded: number; totalMoves: number }
): void {
    let contents: TrophyCacheFile = {
        cache_updated_at: Date.now(),
        games_analyzed: counts.downloaded,
        moves_analyzed: counts.totalMoves,
        trophies: playerTrophiesByType,
    }

    downloadFile(`${username}.json`, JSON.stringify(contents, null, 2), 'application/json')
}

export function exportAsCsv(playerTrophiesByType: PlayerTrophiesByType, username: string): void {
    let rows: {
        trophy: string
        date: string
        opponent: string
        link: string
    }[] = []

    for (const [trophyName, accomplishment] of Object.entries(playerTrophiesByType)) {
        for (const trophy of Object.values(accomplishment)) {
            rows.push({
                trophy: trophyName,
                date: trophy.date,
                opponent: (trophy.opponent.title + ' ' + trophy.opponent.username).trim(),
                link: trophy.link,
            })
        }
    }
    const header = Object.keys(rows[0]).join(',')
    const values = rows.map((o) => Object.values(o).join(',')).join('\n')
    const csv = header + '\n' + values
    downloadFile(`${username}.csv`, csv, 'text/csv')
}

function downloadFile(filename: string, contents: string, contentType: string): void {
    let element = document.createElement('a')
    element.setAttribute('href', 'data:' + contentType + ';charset=utf-8,' + encodeURIComponent(contents))
    element.setAttribute('download', filename)

    element.style.display = 'none'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
}
