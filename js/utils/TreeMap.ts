export class TreeMap<K, V> {
    private root: TreeNode<K, V> = new TreeNode<K, V>()

    public set(key: K[], value: V): void {
        let node = this.root
        for (const next of key) {
            const exists = node.children.get(next)
            if (exists !== undefined) {
                node = exists
            } else {
                const newNode = new TreeNode<K, V>()
                node.children.set(next, newNode)
                node = newNode
            }
        }
        node.values.push(value)
    }
    public get(key: Iterable<K>): V[] {
        return this.getMap(key, (a: K) => a)
    }
    public getMap<U>(key: Iterable<U>, map: (x: U) => K): V[] {
        const result = new Array<V>()
        let node = this.root
        result.push(...node.values)
        for (const next of key) {
            const exists = node.children.get(map(next))
            if (exists !== undefined) {
                node = exists
                result.push(...node.values)
            } else {
                return result
            }
        }
        return result
    }
}
class TreeNode<K, V> {
    public values: V[] = []
    public children: Map<K, TreeNode<K, V>> = new Map<K, TreeNode<K, V>>()
}

export function* mapIterator<T, U>(iterable: Iterable<T>, f: (x: T) => U): Iterable<U> {
    for (const x of iterable) {
        yield f(x)
    }
}
