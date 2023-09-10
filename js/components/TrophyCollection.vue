<template>
    <div class="box" style="flex-direction: column">
        <div class="flex flex-nowrap overflow-x-auto justify-center">
            <template v-if="hasTrophies">
                <span class="inline" style="text-align: center; font-size: 27px">
                    <strong>{{ count }}</strong>
                </span>
                <svg
                    version="1.1"
                    xmlns="http://www.w3.org/2000/svg"
                    xmlns:xlink="http://www.w3.org/1999/xlink"
                    x="0px"
                    y="0px"
                    style="enable-background: new 0 0 512 512"
                    xml:space="preserve"
                    viewBox="0 0 120 120"
                    class="inline"
                    :class="{
                        'h-10': size === 'large',
                        'h-9': size !== 'large',
                    }"
                >
                    <g>
                        <polygon style="fill: chartreuse" points="75.7,107.4 60,97.5 44.3,107.4 44.3,41.1 75.7,41.1  " />
                        <circle style="fill: chocolate" cx="60" cy="44.8" r="32.2" />
                        <circle style="fill: rgba(157, 255, 0, 0.708)" cx="60" cy="44.8" r="25.3" />
                        <path
                            style="fill: rgba(255, 25, 0, 0.708)"
                            d="M61.2,29.7l4.2,8.4c0.2,0.4,0.6,0.7,1,0.8l9.3,1.4c1.1,0.2,1.6,1.5,0.8,2.3l-6.7,6.6c-0.3,0.3-0.5,0.8-0.4,1.2   l1.6,9.3c0.2,1.1-1,2-2,1.4l-8.3-4.4c-0.4-0.2-0.9-0.2-1.3,0L51,61.1c-1,0.5-2.2-0.3-2-1.4l1.6-9.3c0.1-0.4-0.1-0.9-0.4-1.2   l-6.7-6.6c-0.8-0.8-0.4-2.2,0.8-2.3l9.3-1.4c0.4-0.1,0.8-0.3,1-0.8l4.2-8.4C59.3,28.7,60.7,28.7,61.2,29.7z"
                        />
                    </g>
                </svg>
            </template>
            <template v-if="hasVideos">
                <template v-if="hasMultipleVideos">
                    <span class="inline" style="text-align: center; font-size: 27px">
                        <strong>{{ videos }}</strong>
                    </span>
                </template>
                <svg
                    version="1.1"
                    viewBox="0 0 48 48"
                    xmlns="http://www.w3.org/2000/svg"
                    xmlns:xlink="http://www.w3.org/1999/xlink"
                    x="0px"
                    y="0px"
                    style="enable-background: new 0 0 512 512"
                    xml:space="preserve"
                    class="inline ml-2 mt-2"
                    :class="{
                        'h-10': size === 'large',
                        'h-8': size !== 'large',
                    }"
                    fill="#000000"
                >
                    <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g>
                    <g id="SVGRepo_iconCarrier">
                        <desc>Created with Sketch.</desc>
                        <defs></defs>
                        <g id="Icons" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
                            <g id="Color-" transform="translate(-200.000000, -368.000000)" fill="#CE1312">
                                <path
                                    d="M219.044,391.269916 L219.0425,377.687742 L232.0115,384.502244 L219.044,391.269916 Z M247.52,375.334163 C247.52,375.334163 247.0505,372.003199 245.612,370.536366 C243.7865,368.610299 241.7405,368.601235 240.803,368.489448 C234.086,368 224.0105,368 224.0105,368 L223.9895,368 C223.9895,368 213.914,368 207.197,368.489448 C206.258,368.601235 204.2135,368.610299 202.3865,370.536366 C200.948,372.003199 200.48,375.334163 200.48,375.334163 C200.48,375.334163 200,379.246723 200,383.157773 L200,386.82561 C200,390.73817 200.48,394.64922 200.48,394.64922 C200.48,394.64922 200.948,397.980184 202.3865,399.447016 C204.2135,401.373084 206.612,401.312658 207.68,401.513574 C211.52,401.885191 224,402 224,402 C224,402 234.086,401.984894 240.803,401.495446 C241.7405,401.382148 243.7865,401.373084 245.612,399.447016 C247.0505,397.980184 247.52,394.64922 247.52,394.64922 C247.52,394.64922 248,390.73817 248,386.82561 L248,383.157773 C248,379.246723 247.52,375.334163 247.52,375.334163 L247.52,375.334163 Z"
                                    id="Youtube"
                                ></path>
                            </g>
                        </g>
                    </g>
                </svg>
            </template>
        </div>
    </div>
</template>

<script lang="ts">
export default {
    props: {
        count: Number,
        size: String,
        videos: Number,
    },
    computed: {
        hasTrophies: function () {
            if (this.count == undefined) return false
            return this.count > 0
        },
        hasVideos: function () {
            if (this.videos == undefined) return false
            return this.videos > 0
        },
        hasMultipleVideos: function () {
            if (this.videos == undefined) return false
            return this.videos > 1
        },
    },
}
</script>
