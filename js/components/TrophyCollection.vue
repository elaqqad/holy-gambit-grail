<template>
    <div class="box" style="flex-direction: column">
        <div
            class="flex flex-wrap justify-center"
            :class="{
                '-space-x-1.6': size === 'large',
                '-space-x-1.5': size !== 'large',
            }"
        >
            <span class="my-1 hight-4" style="text-align: center; font-size: 27px">
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
                class="my-1"
                :class="{
                    'heigth-3': size === 'large',
                    'heigth-2-5': size !== 'large',
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
        </div>
    </div>
</template>

<script lang="ts">
export default {
    props: {
        count: Number,
        size: String,
    },
    computed: {
        maximum: function () {
            if (this.count == undefined) return 0
            return this.count <= 100 ? this.count : 100
        },
    },
}
</script>
