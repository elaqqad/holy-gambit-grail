<template>
    <div
        v-cloak
        class="container mx-auto my-8 w-11/12"
        :class="{
            'is-download-complete': isDownloadComplete,
        }"
    >
        <div class="text-center">
            <h1 class="text-6xl md:text-8xl mb-4">
                <a href="/"> Holy Gambit Grail ! </a>
            </h1>
            <p class="md:text-2xl">How many of these gambits have you won with ?</p>
        </div>

        <div
            class="flex flex-row my-8 bg-indigo-100 border-0 drop-shadow-2xl mx-auto p-4 rounded-lg shadow-indigo-500/50 shadow-lg text-yellow-600 md:w-3/5 mb-10"
            v-if="!isDownloading && !isDownloadComplete"
        >
            <div class="flex w-80 h-80 mb-1 -ml-4">
                <img src="/free_pawn.png" width="320" height="320" alt="take my pawn" />
            </div>
            <div class="flex mb-1 -ml-4">
                <form @submit.prevent="startDownload">
                    <div class="flex flex-row mb-2">
                        <div class="basis-1/4 text-2xl md:text-5xl text-center font-bold">
                            1
                            <ArrowIcon />
                        </div>
                        <div class="basis-3/4">
                            <div>
                                Select site:
                                <div class="text-yellow-900">
                                    <label class="cursor-pointer">
                                        <input type="radio" name="site" value="lichess" v-model="inputs.type" />
                                        Lichess
                                    </label>
                                    <label class="cursor-pointer ml-4">
                                        <input type="radio" name="site" value="chesscom" v-model="inputs.type" />
                                        Chess.com
                                    </label>
                                </div>
                            </div>
                            <div class="mt-2">
                                Enter username:

                                <input
                                    type="text"
                                    class="block w-full px-3 py-1.5 text-base font-normal text-gray-700 bg-white bg-clip-padding border border-solid border-gray-300 rounded transition ease-in-out m-0 focus:text-gray-700 focus:bg-white focus:border-blue-600 focus:outline-none"
                                    placeholder="Username here"
                                    spellcheck="false"
                                    data-lpignore="true"
                                    v-model="inputs.value"
                                />

                                <div class="text-sm">
                                    Examples on Lichess:
                                    <span class="dotted-underline text-yellow-900 cursor-pointer" @click.prevent="formFill('lichess', 'zolpi')"
                                        >Jonathan Schrantz </span
                                    >,
                                    <span class="dotted-underline text-yellow-900 cursor-pointer" @click.prevent="formFill('lichess', 'EricRosen')"
                                        >Eric Rosen</span
                                    >
                                    Or
                                    <span
                                        class="dotted-underline text-yellow-900 cursor-pointer"
                                        @click.prevent="formFill('lichess', 'DrNykterstein')"
                                    >
                                        DrNykterstein
                                    </span>
                                    <br />
                                    On chess.com:
                                    <span
                                        class="dotted-underline text-yellow-900 cursor-pointer"
                                        @click.prevent="formFill('chesscom', 'VampireChicken')"
                                        >Jonathan Schrantz</span
                                    >,
                                    <span class="dotted-underline text-yellow-900 cursor-pointer" @click.prevent="formFill('chesscom', 'IMRosen')"
                                        >Eric Rosen</span
                                    >,
                                    <span class="dotted-underline text-yellow-900 cursor-pointer" @click.prevent="formFill('chesscom', 'Hikaru')"
                                        >Hikaru Nakamura</span
                                    >,
                                    <span
                                        class="dotted-underline text-yellow-900 cursor-pointer"
                                        @click.prevent="formFill('chesscom', 'DanielNaroditsky')"
                                        >Daniel Naroditsky</span
                                    >,
                                    <span
                                        class="dotted-underline text-yellow-900 cursor-pointer"
                                        @click.prevent="formFill('chesscom', 'MagnusCarlsen')"
                                        >Magnus Carlsen</span
                                    >,
                                    <span class="dotted-underline text-yellow-900 cursor-pointer" @click.prevent="formFill('chesscom', 'GothamChess')"
                                        >GothamChess</span
                                    >
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="flex flex-row mb-4">
                        <div class="basis-1/4 text-2xl md:text-5xl text-center font-bold">
                            2
                            <ArrowIcon />
                        </div>
                        <div class="basis-3/4">
                            <lichess-login v-on:set-lichess-oauth-token="setLichessOauthToken"></lichess-login>
                            Youtube play list:

                            <input
                                type="text"
                                class="block w-full px-3 py-1.5 text-base font-normal text-gray-700 bg-white bg-clip-padding border border-solid border-gray-300 rounded transition ease-in-out m-0 focus:text-gray-700 focus:bg-white focus:border-blue-600 focus:outline-none"
                                placeholder="The id of HGG youtube playlist"
                                spellcheck="false"
                                data-lpignore="true"
                                v-model="inputs.playlist"
                            />
                        </div>
                    </div>

                    <div class="flex flex-row">
                        <div class="basis-1/4 text-2xl md:text-5xl text-center font-bold">
                            3
                            <ArrowIcon />
                        </div>
                        <div class="basis-3/4">
                            <div class="text-sm mt-1 mb-2">
                                Check games since
                                <select
                                    v-model.number="inputs.filters.sinceHoursAgo"
                                    class="bg-transparent border-b border-dotted border-sky-900 focus:outline-0 hover:border-dashed text-yellow-900 md:w-28"
                                >
                                    <option :value="6">6 hours ago</option>
                                    <option :value="24">24 hours ago</option>
                                    <option :value="24 * 7">last week</option>
                                    <option :value="24 * 31">last month</option>
                                    <option :value="24 * 31 * 3">last 3 months</option>
                                    <option :value="24 * 31 * 6">last 6 months</option>
                                    <option :value="24 * 365">last 12 months</option>
                                    <option :value="0">forever</option>
                                </select>
                            </div>

                            <button
                                type="submit"
                                class="px-6 py-2.5 bg-green-500 text-white font-medium text-xs leading-tight uppercase rounded shadow-md hover:bg-green-600 hover:shadow-lg focus:bg-green-600 focus:shadow-lg focus:outline-none focus:ring-0 active:bg-green-700 active:shadow-lg transition duration-150 ease-in-out"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" class="inline h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="2"
                                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                                    />
                                </svg>
                                Click here to analyze
                            </button>

                            <div v-if="errors.form" class="mt-2 font-bold text-red-500">
                                <svg xmlns="http://www.w3.org/2000/svg" class="inline h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="2"
                                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                                    />
                                </svg>
                                {{ errors.form }}
                            </div>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <download-progress
            v-if="isDownloading && !isDownloadComplete"
            :title="player.username"
            :analyzed="counts.analyzed"
            :downloaded="counts.downloaded"
            :total="counts.totalGames"
            :hideProgressBar="inputs.filters.sinceHoursAgo"
            @cancel-download="cancelDownload"
        ></download-progress>

        <div v-if="errors.api.message" class="text-center bg-orange-800 p-3">
            There was an error from the {{ inputs.type === 'lichess' ? 'Lichess' : 'Chess.com' }} API:
            <strong>{{ errors.api }}</strong>
            <p>Try only running 1 report at a time. You may have to wait before trying again.</p>
        </div>

        <div v-if="player.username" class="mt-8 bg-sky-800 p-4 text-center rounded-lg">
            <h2 class="text-2xl">
                <username-formatter :title="player.title" :username="player.username"></username-formatter>
                won with
                <strong class="font-bold">{{ totalAccomplishmentsCompleted }}</strong>
                <template v-if="trophyCount === 1"> Gambit </template>
                <template v-else> Gambits </template>
            </h2>

            <div class="mb-1">
                on
                <strong>{{ inputs.type === 'lichess' ? 'Lichess' : 'Chess.com' }}</strong>
                and has won
                <strong> {{ trophyCount.toLocaleString() }}</strong> total games
                <p v-if="sinceDateFormatted">since {{ sinceDateFormatted }}</p>
            </div>

            <trophy-collection :count="trophyCount" :videos="youtubeTrophiesCount" size="large"></trophy-collection>
            <div class="text-sm mt-2">
                <strong>{{ counts.analyzed.toLocaleString() }}</strong>
                rated games analyzed
            </div>
            <div class="mb-1">Only {{ trophyTypeCount - totalAccomplishmentsCompleted }} remaining to complete the Holy Gambit Grail !</div>
        </div>

        <div class="md:flex md:flex-row md:space-x-10">
            <div class="basis-full">
                <h2 class="heading">List of all {{ displayableGambits.length }} gambits sorted by popularity</h2>
                <div class="grid sm:grid-cols-4 md:grid-cols-6 xl:grid-cols-7 2xl:grid-cols-8 gap-1">
                    <accomplishment-score
                        v-for="(gambit, name) in displayableGambits"
                        :key="name"
                        :title="gambit.shortName"
                        :color="gambit.opening.color"
                        :gambit-results="gambit.results"
                        :trophies="gambit.Trophies || {}"
                        :masterGame="gambit.opening.master"
                        :lichessGame="gambit.opening.lichess"
                        :playerColor="gambit.opening.color"
                        :moveNumber="gambit.opening.move"
                        :youtube="gambit.Videos || []"
                    ></accomplishment-score>
                </div>
            </div>
        </div>

        <div class="mt-8 text-center text-sm">
            <div class="text-slate-200 mb-2" v-if="isDownloadComplete && trophyCount > 0">
                Download results as
                <a href="#" @click.prevent="exportAsCsv" class="dotted-underline">CSV</a>
                or
                <a href="#" @click.prevent="exportAsJson" class="dotted-underline">JSON</a>
            </div>
            <div class="text-slate-400">
                Not affiliated with Eric Rosen or Jonathan Schrantz.
                <br />
                Find a bug? Have a comment? Fill out
                <a
                    href="https://docs.google.com/forms/d/e/1FAIpQLSfU3EA_rByuYdSjh3IZYEteiQ2s5TcYCy-rvd3ylHlBEKghaw/viewform?usp=sf_link"
                    target="_blank"
                    class="dotted-underline"
                    >this form</a
                >
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { games, player, Game, Profile, addLichessOauthToken, cancelFetch } from 'chess-fetcher'
import axios from 'axios'
import AccomplishmentScore from './components/AccomplishmentScore.vue'
import ArrowIcon from './components/ArrowIcon.vue'
import ChangelogDate from './components/ChangelogDate.vue'
import DownloadProgress from './components/DownloadProgress.vue'
import LichessLogin from './components/LichessLogin.vue'
import UsernameFormatter from './components/UsernameFormatter.vue'
import RecentUpdates from './components/RecentUpdates.vue'
import TrophyCollection from './components/TrophyCollection.vue'
import { gambitTrophy, allGambits, gameAgainstBot, winnerIsUser, pgnPrefix } from './goals/gambit-openings'
import { DisplayableGambits, GambitOpening, PlayerTrophiesByType, YoutubeTrophy } from './types/types'
import { formatSinceDate } from './utils/format-since-date'
import { TreeMap } from './utils/TreeMap'
import { exportAsCsv, exportAsJson } from './utils/export-tools'
import { getCachedGames } from './utils/caching'

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export default {
    components: {
        AccomplishmentScore,
        ArrowIcon,
        ChangelogDate,
        DownloadProgress,
        LichessLogin,
        UsernameFormatter,
        RecentUpdates,
        TrophyCollection,
    },
    data() {
        return {
            inputs: {
                type: 'lichess',
                value: '',
                playlist: 'PLKNTVdis2-YZZsI_9ReGDAEu-EGHSKD-h',
                filters: {
                    sinceHoursAgo: 0,
                },
            },

            player: <Profile>{},

            errors: {
                form: '',
                api: <DOMException>{},
            },

            trophyTypeCount: 0,
            trophyWonCount: 0,
            youtubeVideosCount: 0,
            gambits: new Set<string>(),
            displayableGambits: <DisplayableGambits>{},
            gambitsTree: new TreeMap<string, GambitOpening>(),
            shortNames: new Map<string, string>(),
            isDownloading: false,
            isDownloadComplete: false,
            counts: {
                totalGames: 0,
                downloaded: 0,
                analyzed: 0,
            },

            usingCacheBeforeTimestamp: 0,
        }
    },

    computed: {
        username(): string {
            return this.inputs.value.trim().toLowerCase()
        },
        sinceDateFormatted(): string {
            if (this.inputs.filters.sinceHoursAgo) {
                let now = new Date().getTime()
                return formatSinceDate(now - this.inputs.filters.sinceHoursAgo * 60 * 60 * 1000)
            }

            return ''
        },
        totalAccomplishmentsCompleted(): number {
            return this.gambits.size
        },
        totalAccomplishmentsCompletedPercentage(): number {
            return Math.round((this.totalAccomplishmentsCompleted / this.trophyTypeCount) * 100)
        },
        trophyCount(): number {
            return this.trophyWonCount
        },
        youtubeTrophiesCount(): number {
            return this.youtubeVideosCount
        },

        GameCache(): Map<string, Game[]> {
            return new Map<string, Game[]>()
        },
    },

    watch: {
        inputs: {
            handler(value) {
                window.localStorage.setItem('savedForm', JSON.stringify(value))
            },
            deep: true,
        },
    },

    async mounted() {
        let savedForm = JSON.parse(window.localStorage.getItem('savedForm') || '{}')

        if (savedForm.type) {
            this.inputs.type = savedForm.type
        }

        if (savedForm.value) {
            this.inputs.value = savedForm.value
        }

        if (savedForm.filters) {
            this.inputs.filters = savedForm.filters
        }
        await this.LoadGambits()
    },

    methods: {
        async LoadGambits(): Promise<void> {
            const gambits = await allGambits()
            const names = new Set<string>()
            const result = new Array()
            for (let a of gambits) {
                if (!names.has(a.name)) {
                    names.add(a.name)
                    result.push(a)
                }
                const key = pgnPrefix(a)
                this.gambitsTree.set(key, a)
            }
            result.sort((a, b) => (a.white + a.black + a.draws < b.white + b.black + b.draws ? 1 : -1))
            this.shortNames = this.shortenOpenings(result.map((a) => a.name))
            for (let gambit of result) {
                const results = `
                            W: ${((100 * gambit.white) / (gambit.white + gambit.black + gambit.draws)).toLocaleString(undefined, {
                                maximumFractionDigits: 0,
                            })}%,
                            D: ${((100 * gambit.draws) / (gambit.white + gambit.black + gambit.draws)).toLocaleString(undefined, {
                                maximumFractionDigits: 0,
                            })}%,
                            B: ${((100 * gambit.black) / (gambit.white + gambit.black + gambit.draws)).toLocaleString(undefined, {
                                maximumFractionDigits: 0,
                            })}%
                        `
                this.displayableGambits[gambit.name] = {
                    shortName: this.shortNames.get(gambit.name) || gambit.name,
                    opening: gambit,
                    results: results,
                    Videos: [],
                    Trophies: {},
                }
                this.trophyTypeCount++
            }
        },
        shortenOpenings(openings: string[]): Map<string, string> {
            const shortNames = new Map<string, string>()
            const usedAlready = new Set()
            for (const opening of openings) {
                const words = opening.split(/[,:]+/)
                let shortName = words[words.length - 1].trim()
                if (usedAlready.has(shortName)) {
                    for (let i = words.length - 2; i >= 0; i--) {
                        shortName = words[i].trim() + ', ' + shortName
                        if (!usedAlready.has(shortName)) {
                            break
                        }
                    }
                }
                usedAlready.add(shortName.trim())
                shortNames.set(opening, shortName.trim())
            }
            return shortNames
        },
        formFill(type: string, value: string): void {
            this.inputs.type = type
            this.inputs.value = value
            this.inputs.filters.sinceHoursAgo = 0
        },

        setLichessOauthToken(token: string): void {
            addLichessOauthToken(token)
        },

        cancelDownload(): void {
            cancelFetch()

            this.isDownloading = false
            this.isDownloadComplete = true
        },
        async fetchYoutubeTrophies(): Promise<YoutubeTrophy[]> {
            const key = `youtube-playlist-games-${this.inputs.playlist}`
            const saved = window.localStorage.getItem(key)
            if (saved) {
                return JSON.parse(saved) as YoutubeTrophy[]
            }
            const response = await axios.get(`/api/youtube?id=${this.inputs.playlist}`)
            window.localStorage.setItem(key, JSON.stringify(response.data))
            return response.data as YoutubeTrophy[]
        },
        async startDownload(): Promise<void> {
            if (!this.username) {
                this.errors.form = 'Enter a username in Step #1'
                return
            }
            // Auto correct Eric's usernames in case someone is trying to toggle between his Lichess and Chess.com
            // but forgets to change the username
            if (this.username === 'ericrosen' && this.inputs.type === 'chesscom') {
                this.inputs.value = 'IMRosen'
            } else if (this.username === 'imrosen' && this.inputs.type === 'lichess') {
                this.inputs.value = 'EricRosen'
            }
            this.isDownloading = true
            let url = ''
            if (this.inputs.type === 'lichess') {
                url = `https://lichess.org/@/${this.username}`
            } else if (this.inputs.type === 'chesscom') {
                url = `https://www.chess.com/member/${this.username}`
            }
            this.fetchYoutubeTrophies().then(async (trophies: YoutubeTrophy[]) => {
                for (const youtubeTrophy of trophies) {
                    for (const gambit of Object.keys(this.displayableGambits)) {
                        if (youtubeTrophy.title.includes(this.shortNames.get(gambit) || gambit)) {
                            this.displayableGambits[gambit].Videos.push(youtubeTrophy)
                            this.youtubeVideosCount++
                        }
                    }
                }
            })
            player(url)
                .then(async (player: Profile) => {
                    this.player = player
                    window.document.title += ` - ${player.title} ${player.username}`
                    const playerGameCount: number = player.counts?.all || 0
                    if (player.site === 'chess.com') {
                        // Chess.com doesn't provide a reliable way to get the actual game count via the API.
                        // Actual game count is higher than reported, so I'll add 20%
                        this.counts.totalGames = Math.ceil(playerGameCount * 1.2)
                    } else {
                        this.counts.totalGames = playerGameCount
                    }
                    if (!this.inputs.filters.sinceHoursAgo) {
                        let result = await getCachedGames(url)
                        if (result !== undefined) {
                            this.usingCacheBeforeTimestamp = result.cache_updated_at
                            this.counts.downloaded = result.games_analyzed
                            this.counts.analyzed = result.games_analyzed
                            for (const fetched of Object.keys(result.trophies)) {
                                this.displayableGambits[fetched].Trophies = result.trophies[fetched]
                                const numberOfTrophies = Object.keys(result.trophies[fetched]).length
                                this.trophyWonCount += numberOfTrophies
                                if (numberOfTrophies > 0) {
                                    this.gambits.add(fetched)
                                }
                            }
                        }
                    }
                    let sinceTimestamp = this.inputs.filters.sinceHoursAgo
                        ? new Date().getTime() - this.inputs.filters.sinceHoursAgo * 60 * 60 * 1000
                        : 0
                    if (this.usingCacheBeforeTimestamp) {
                        sinceTimestamp = this.usingCacheBeforeTimestamp
                    }

                    games(url, (game: Game) => this.checkGameForTrophies(game), {
                        since: sinceTimestamp,
                        pgnInJson: true,
                        rated: true,
                    })
                        .then(() => {
                            this.isDownloadComplete = true
                        })
                        .catch((e: DOMException) => {
                            // If the user cancels the download, don't show an error message
                            if (e.message.includes('aborted')) {
                                return
                            }
                            this.errors.api = e
                        })
                })
                .catch((e: DOMException) => {
                    this.errors.api = e
                })
        },
        exportAsJson(): void {
            const playerTrophiesByType = <PlayerTrophiesByType>{}
            for (const key of Object.keys(this.displayableGambits)) {
                playerTrophiesByType[key] = this.displayableGambits[key].Trophies
            }
            exportAsJson(playerTrophiesByType, this.username, this.counts)
        },

        exportAsCsv(): void {
            const playerTrophiesByType = <PlayerTrophiesByType>{}
            for (const key of Object.keys(this.displayableGambits)) {
                playerTrophiesByType[key] = this.displayableGambits[key].Trophies
            }
            exportAsCsv(playerTrophiesByType, this.username)
        },
        addTrophyForPlayer(trophyName: string, game: Game, onMoveNumber?: number): void {
            if (this.displayableGambits[trophyName].Trophies[game.id]) {
                return
            }
            let opponent
            let link
            if (game.players.white.username.toLowerCase() === this.username) {
                opponent = game.players.black
                link = game.links.white
            } else {
                opponent = game.players.white
                link = game.links.black
            }

            if (game.site === 'lichess' && onMoveNumber) {
                link += `#${onMoveNumber}`
            } else if (onMoveNumber) {
                link += onMoveNumber - 1
            }

            this.displayableGambits[trophyName].Trophies[game.id] = {
                date: new Date(game.timestamp).toISOString().split('T')[0], // YYYY-MM-DD format
                opponent: {
                    username: opponent.username,
                    title: opponent.title || '',
                },
                link,
            }
            this.gambits.add(trophyName)
            this.trophyWonCount++
        },

        async checkGameForTrophies(game: Game): Promise<void> {
            // Add a 0ms setTimeout to stop the process from blocking the page
            // Without this, the page may become unresponsive as games are processed
            this.counts.downloaded++
            await wait(0)
            // only standard chess starting position games
            // only games won by the current user
            // ignore games against stockfish, anonymous users, and bots
            if (game.isStandard && winnerIsUser(game, this.player.username.toLowerCase()) && !gameAgainstBot(game, this.player.title)) {
                for (let gambit of this.gambitsTree.getMap(game.moves, (move) => move.notation.notation)) {
                    if (gambit != undefined) {
                        for (const result of gambitTrophy(game, gambit)) {
                            this.addTrophyForPlayer(`${gambit.name}`, game, result.onMoveNumber ?? 0)
                        }
                    }
                }
            }
            this.counts.analyzed++
        },
    },
}
</script>
