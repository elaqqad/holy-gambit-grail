import { describe, expect, test } from 'vitest'
import { TreeMap, mapIterator } from '../js/utils/TreeMap'

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

describe('Test error case of TreeMap', () =>
    test.each([
        { k: 'abc', v: 1 },
        { k: '', v: 2 },
    ])('Error should be thrown after inserting the same key', (keyValuePair) => {
        const treeMap = new TreeMap()
        treeMap.set(keyValuePair.k.split(''), keyValuePair.v)
        expect(() => treeMap.set(keyValuePair.k.split(''), keyValuePair.v)).toThrowError()
    }))

describe('Test mapIterator', () =>
    test.each([
        { input: [1, 2, 3, 4, 5], operation: (x: number) => x * x, output: [1, 4, 9, 16, 25] },
        { input: [1, 2, 3, 4, 5], operation: (x: number) => x + 1, output: [2, 3, 4, 5, 6] },
    ])('Should apply the function piecewise', (inputsAndOutputs) => {
        expect(Array.from(mapIterator(inputsAndOutputs.input, inputsAndOutputs.operation))).toMatchObject(inputsAndOutputs.output)
    }))
