import { describe, expect, test } from 'vitest'
import { TreeMap } from '../js/utils/TreeMap'

describe('test tree map', () => {
    test.each([
        [
            [
                { k: 'abcd', v: 1 },
                { k: 'abcde', v: 2 },
            ],
            [
                { k: 'abcd', v: [1] },
                { k: 'abcde', v: [1, 2] },
            ],
        ],
        [
            [
                { k: 'abcd', v: 3 },
                { k: 'abcde', v: 4 },
            ],
            [
                { k: 'word', v: [] },
                { k: 'abc', v: [] },
                { k: '', v: [] },
            ],
        ],
        [
            [
                { k: '', v: 5 },
                { k: 'a', v: 6 },
                { k: 'ab', v: 7 },
            ],
            [
                { k: '', v: [5] },
                { k: 'a', v: [5, 6] },
                { k: 'abc', v: [5, 6, 7] },
            ],
        ],
        [
            [
                { k: '', v: 8 },
                { k: 'a', v: 9 },
                { k: 'ab', v: 10 },
            ],
            [
                { k: '', v: [8] },
                { k: 'd', v: [8] },
            ],
        ],
    ])('test operations %p followed by searching keys %p', (setup, getExpected) => {
        const treeMap = new TreeMap()
        for (const a of setup) {
            treeMap.set(a.k.split(''), a.v)
        }
        getExpected.forEach((element) => {
            expect(treeMap.get(element.k.split(''))).toMatchObject(element.v)
        })
    })
})
