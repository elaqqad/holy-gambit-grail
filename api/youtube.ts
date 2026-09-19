import axios from 'axios'

// YouTube playlist IDs are alphanumeric plus '-' and '_' (typically ~34 chars, but this is
// deliberately permissive rather than exact). Rejecting anything else stops query-string
// injection into the outbound googleapis.com request.
const PLAYLIST_ID_PATTERN = /^[A-Za-z0-9_-]{1,64}$/
const DEFAULT_PLAYLIST_ID = 'PLKNTVdis2-YZZsI_9ReGDAEu-EGHSKD-h'
// Bounds the number of upstream requests (and YOUTUBE_API_KEY quota) a single call can consume.
const MAX_PAGES = 20

export default async (req: any, res: any) => {
    try {
        const requestedId = req.query.id
        const playlistId = typeof requestedId === 'string' && PLAYLIST_ID_PATTERN.test(requestedId) ? requestedId : DEFAULT_PLAYLIST_ID
        const apiKey = process.env.YOUTUBE_API_KEY
        const snippets = []
        const urls = []
        let nextPageToken = ''
        let pages = 0
        do {
            const url = `https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=${encodeURIComponent(playlistId)}&key=${apiKey}`
            const response = await axios.get(nextPageToken === '' ? url : `${url}&pageToken=${encodeURIComponent(nextPageToken)}`)
            snippets.push(
                ...response.data.items.map((item: any) => ({
                    id: item.snippet.resourceId.videoId,
                    description: item.snippet.description,
                    title: item.snippet.title,
                }))
            )

            nextPageToken = response.data.nextPageToken
            pages++
        } while (nextPageToken && pages < MAX_PAGES)
        // Define a regular expression to match Lichess or Chess.com URLs
        const regex = /https?:\/\/(lichess\.org\/\w+|www\.chess\.com\/game\/live\/\d+)/g

        // Loop through the descriptions and find the URLs that match the regex
        for (const videoInfo of snippets) {
            // Use the exec method to get all matches in the description
            let match
            let found = false
            while ((match = regex.exec(videoInfo.description)) !== null) {
                // Push the matched URL to the array
                const result = {
                    video: `https://www.youtube.com/watch?v=${videoInfo.id}`,
                    game: match[0],
                    title: videoInfo.title,
                }
                urls.push(result)
                found = true
            }
            if (!found) {
                const result = {
                    video: `https://www.youtube.com/watch?v=${videoInfo.id}`,
                    game: 'game was not referenced in comment',
                    title: videoInfo.title,
                }
                urls.push(result)
            }
        }
        res.status(200).json(urls)
    } catch (error) {
        console.log(error)
        return res.status(201).json([])
    }
}
