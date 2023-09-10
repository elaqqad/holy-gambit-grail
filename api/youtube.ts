import axios from 'axios'

export default async (req: any, res: any) => {
    try {
        const playlistId = req.query.id ?? 'PLKNTVdis2-YZZsI_9ReGDAEu-EGHSKD-h'
        const apiKey = process.env.YOUTUBE_API_KEY
        const snippets = []
        const urls = []
        let nextPageToken = ''
        do {
            const url = `https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=${playlistId}&key=${apiKey}`
            const response = await axios.get(nextPageToken === '' ? url : `${url}&pageToken=${nextPageToken}`)
            snippets.push(
                ...response.data.items.map((item: any) => ({
                    id: item.snippet.resourceId.videoId,
                    description: item.snippet.description,
                    title: item.snippet.title,
                }))
            )

            nextPageToken = response.data.nextPageToken
        } while (nextPageToken)
        // Define a regular expression to match Lichess or Chess.com URLs
        const regex = /https?:\/\/(lichess\.org\/\w+|www\.chess\.com\/game\/live\/\d+)/g

        // Loop through the descriptions and find the URLs that match the regex
        for (const videoInfo of snippets) {
            // Use the exec method to get all matches in the description
            let match
            while ((match = regex.exec(videoInfo.description)) !== null) {
                // Push the matched URL to the array
                const result = {
                    video: `https://www.youtube.com/watch?v=${videoInfo.id}`,
                    game: match[0],
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
