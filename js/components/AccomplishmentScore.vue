<template>
    <div
        class="px-3 py-2 rounded text-center"
        :class="{
            'bg-green-600': hasTrophies,
            'bg-yellow-300 text-yellow-800  accomplishment-does-not-have-games': !hasTrophies,
        }"
    >
        <VTooltip>
            <span @click.prevent="isExpanded = !isExpanded" class="hover:underline cursor-pointer">
                <svg
                    v-if="!isWhiteTheGambitter"
                    class="inline h-6 w-6"
                    fill="#000000"
                    version="1.1"
                    id="Layer_1"
                    xmlns="http://www.w3.org/2000/svg"
                    xmlns:xlink="http://www.w3.org/1999/xlink"
                    viewBox="0 0 100 100"
                    enable-background="new 0 0 100 100"
                    xml:space="preserve"
                >
                    <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
                    <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g>
                    <g id="SVGRepo_iconCarrier">
                        <path
                            d="M37,38c0-1.1,0.9-2,2-2h22c1.1,0,2,0.9,2,2s-0.9,2-2,2H39C37.9,40,37,39.1,37,38z M34,84h32c1.1,0,2-0.9,2-2s-0.9-2-2-2H34 c-1.1,0-2,0.9-2,2S32.9,84,34,84z M69,85H31c-2.2,0-4,1.8-4,4s1.8,4,4,4h38c2.2,0,4-1.8,4-4S71.2,85,69,85z M50,35 c7.18,0,13-5.82,13-13S57.18,9,50,9s-13,5.82-13,13S42.82,35,50,35z M58,41H42c0,33.478-4.052,33.959-5.99,38H63.99 C62.052,74.959,58,74.478,58,41z"
                        ></path>
                    </g>
                </svg>
                <svg
                    v-if="isWhiteTheGambitter"
                    class="inline h-6 w-6"
                    version="1.1"
                    id="Layer_1"
                    xmlns="http://www.w3.org/2000/svg"
                    xmlns:xlink="http://www.w3.org/1999/xlink"
                    viewBox="0 0 100 100"
                    enable-background="new 0 0 100 100"
                    xml:space="preserve"
                    fill="#000000"
                >
                    <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
                    <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g>
                    <g id="SVGRepo_iconCarrier">
                        <g>
                            <g>
                                <path
                                    fill="none"
                                    stroke="#000000"
                                    stroke-width="4"
                                    stroke-miterlimit="10"
                                    d="M73,89c0,2.2-1.8,4-4,4H31c-2.2,0-4-1.8-4-4l0,0 c0-2.2,1.8-4,4-4h38C71.2,85,73,86.8,73,89L73,89z"
                                ></path>
                            </g>
                            <circle fill="none" stroke="#000000" stroke-width="4" stroke-miterlimit="10" cx="50" cy="22" r="13"></circle>
                            <g>
                                <path
                                    fill="none"
                                    stroke="#000000"
                                    stroke-width="4"
                                    stroke-miterlimit="10"
                                    d="M63,38c0,1.65-1.35,3-3,3H40c-1.65,0-3-1.35-3-3 l0,0c0-1.65,1.35-3,3-3h20C61.65,35,63,36.35,63,38L63,38z"
                                ></path>
                            </g>
                            <g>
                                <path
                                    fill="none"
                                    stroke="#000000"
                                    stroke-width="4"
                                    stroke-miterlimit="10"
                                    d="M68,82c0,1.65-1.35,3-3,3H35c-1.65,0-3-1.35-3-3 l0,0c0-1.65,1.35-3,3-3h30C66.65,79,68,80.35,68,82L68,82z"
                                ></path>
                            </g>
                            <path
                                fill="none"
                                stroke="#000000"
                                stroke-width="4"
                                stroke-miterlimit="10"
                                d="M63.99,79C62.052,74.959,58,74.478,58,41H42 c0,33.478-4.052,33.959-5.99,38H63.99z"
                            ></path>
                        </g>
                    </g>
                </svg>
                {{ title }}
            </span>

            <template #popper>
                <TheChessboard :board-config="boardConfig" />
            </template>
        </VTooltip>

        <div v-if="hasTrophies || hasYoutube" @click.prevent="isExpanded = !isExpanded" class="cursor-pointer">
            <trophy-collection :count="trophyCount" :videos="youtube.length"></trophy-collection>
        </div>

        <template v-if="isExpanded">
            <div
                v-if="hasExpandableContent"
                class="rounded p-2"
                :class="{
                    'bg-green-700': hasTrophies,
                    'bg-yellow-200': !hasTrophies,
                }"
            >
                <span class="text-sm">
                    {{ gambitResults }}
                </span>
                <a :href="gameLink()" target="_blank" class="block underline hover:font-bold">
                    <svg xmlns="http://www.w3.org/2000/svg" class="inline h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                        <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                    </svg>
                    See moves
                </a>
                <a v-if="hasYoutube" :href="firstVideo" target="_blank" class="block underline hover:font-bold">
                    <svg xmlns="http://www.w3.org/2000/svg" class="inline h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path
                            fill-rule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                            clip-rule="evenodd"
                        />
                    </svg>
                    Watch Video
                </a>
            </div>

            <template v-if="hasTrophies">
                <h4 class="font-bold">
                    {{ trophyCount }}
                    <template v-if="trophyCount === 1"> {{ units[0] }} </template>
                    <template v-else> {{ units[1] }} </template>
                </h4>

                <div class="grid grid-cols-1 text-left">
                    <div
                        v-for="trophy in trophiesByOpponent"
                        :key="trophy[0]"
                        class="overflow-hidden"
                        :title="`Won ${
                            trophyCountByUsername(trophy[1].opponent.username) > 1
                                ? trophyCountByUsername(trophy[1].opponent.username) + ' times'
                                : '1 time'
                        } against this user`"
                    >
                        <a :href="trophy[1].link" class="hover:underline whitespace-nowrap" target="_blank">
                            <username-formatter :title="trophy[1].opponent.title || ''" :username="trophy[1].opponent.username"></username-formatter>
                        </a>
                        <span v-if="trophyCountByUsername(trophy[1].opponent.username) > 1" class="pl-2 text-sm text-gray-100 cursor-help"
                            >x{{ trophyCountByUsername(trophy[1].opponent.username) }}</span
                        >
                    </div>
                </div>
            </template>
        </template>
    </div>
</template>

<script lang="ts">
//import VToolTip from 'floating-vue'
import { TheChessboard, BoardConfig } from 'vue3-chessboard'
import 'vue3-chessboard/style.css'
import UsernameFormatter from './UsernameFormatter.vue'
import TrophyCollection from './TrophyCollection.vue'
import { Trophy, TrophyForGame, YoutubeTrophy } from '../types/types'
import { pgnFormatter } from '../utils/pgn-formatter'

export default {
    props: {
        title: {
            type: String,
            required: true,
        },
        gambitResults: String,
        trophies: {
            type: Object,
            required: true,
        },
        masterGame: String,
        lichessGame: String,
        playerColor: String,
        moveNumber: Number,
        gambitPgn: {
            type: String,
            required: true,
        },
        gambitFen: {
            type: String,
            required: true,
        },
        youtubeLink: String,
        site: String,
        youtube: {
            type: Array,
            required: true,
        },
        units: {
            type: Array,
            default: ['Game', 'Games'],
        },
    },
    components: {
        UsernameFormatter,
        TrophyCollection,
        TheChessboard,
    },
    mounted() {
        this.$emit('register-new-trophy')
    },
    data() {
        return {
            isExpanded: false,
            isHovered: false,
            boardApi: null,
            boardConfig: <BoardConfig>{
                coordinates: true,
                orientation: this.playerColor || 'white',
                fen: this.gambitFen,
                width: '200px',
            },
        }
    },
    computed: {
        trophyCount(): number {
            return Object.keys(this.trophies).length
        },
        hasTrophies(): boolean {
            return this.trophyCount > 0
        },
        hasYoutube(): boolean {
            return this.youtube.length > 0
        },
        firstVideo(): string {
            return (this.youtube[0] as YoutubeTrophy).video
        },
        isWhiteTheGambitter(): boolean {
            return this.playerColor === 'white'
        },
        hasExpandableContent(): boolean {
            return Boolean(this.gambitResults || this.gameLink() || this.youtubeLink)
        },
        usernameCount(): Map<string, number> {
            let usernames = Object.values(this.trophies as TrophyForGame).map((trophy) => trophy.opponent.username)

            return usernames.reduce((map, username) => {
                map.set(username, (map.get(username) || 0) + 1)
                return map
            }, new Map<string, number>())
        },
        trophiesByOpponent(): Map<string, Trophy> {
            return Object.values(this.trophies as TrophyForGame).reduce((previousMap: Map<string, Trophy>, newItem: Trophy) => {
                if (!previousMap.has(newItem.opponent.username)) {
                    previousMap.set(newItem.opponent.username, newItem)
                }
                return previousMap
            }, new Map<string, Trophy>())
        },
    },
    methods: {
        trophyCountByUsername(username: string): number {
            return this.usernameCount.get(username) || 0
        },
        gameLink(): string | undefined {
            console.log(this.site)
            if (this.site?.toLocaleLowerCase() === 'lichess' && (this.lichessGame !== undefined || this.masterGame !== undefined)) {
                return `https://lichess.org/${this.masterGame || this.lichessGame || ''}/${this.playerColor}#${this.moveNumber}`
            }
            const ply = this.moveNumber
            const moves = pgnFormatter(this.gambitPgn).replace(' ', '+')
            return `https://www.chess.com/explorer?moveList=${moves}&ply=${ply}`
        },
    },
}
</script>

<!-- <style lang="scss" scoped>
  .compb-header {
    color: blue;
  }
</style> -->
