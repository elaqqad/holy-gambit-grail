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
        this.add(key, node, value)
    }
    private add(key: K[], node: TreeNode<K, V>, value: V) {
        if (node.value !== undefined) {
            throw new Error(`Key ${key.join(',')} already has a value ${node.value}, cannot add ${value}`)
        } else {
            node.value = value
        }
    }
    public get(key: Iterable<K>): V[] {
        const result = new Array()
        let node = this.root
        if (node.value != undefined) {
            result.push(node.value)
        }
        for (const next of key) {
            const exists = node.children.get(next)
            if (exists !== undefined) {
                node = exists
                if (node.value != undefined) {
                    result.push(node.value)
                }
            } else {
                return result
            }
        }
        return result
    }
}
class TreeNode<K, V> {
    public value?: V
    public children: Map<K, TreeNode<K, V>> = new Map<K, TreeNode<K, V>>()
}

export function* mapIterator<T, U>(iterable: Iterable<T>, f: (x: T) => U): Iterable<U> {
    for (const x of iterable) {
        yield f(x)
    }
}
