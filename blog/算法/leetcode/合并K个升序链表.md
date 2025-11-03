# 合并K个升序链表
> https://leetcode.cn/problems/merge-k-sorted-lists/description/

给你一个链表数组，每个链表都已经按升序排列。
请你将所有链表合并到一个升序链表中，返回合并后的链表。

**示例1**
```
输入：lists = [[1,4,5],[1,3,4],[2,6]]
输出：[1,1,2,3,4,4,5,6]
解释：链表数组如下：
[
  1->4->5,
  1->3->4,
  2->6
]
将它们合并到一个有序链表中得到。
1->1->2->3->4->4->5->6
```

**示例2**
```
输入：lists = []
输出：[]
```

**示例3**
```
输入：lists = [[]]
输出：[]
```

**提示**
- `k == lists.length`
- `0 <= k <= 10^4`
- `0 <= lists[i].length <= 500`
- `-10^4 <= lists[i][j] <= 10^4`
- `lists[i]`按 **升序** 排列
- `lists[i].length`的总和不超过 10^4


*分治法. 算法简单,但是效率低*
```python3
# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def mergeKLists(self, lists: List[Optional[ListNode]]) -> Optional[ListNode]:
        if not lists:
            return None
        if len(lists) == 1:
            return lists[0]
        ret: Optional[ListNode] = None
        for item in lists:
            ret = self.mergeLists(ret, item)
        return ret

    def mergeLists(self, list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
        if not list1 and not list2:
            return None

        dummp_list = ListNode()
        cur = dummp_list

        while list1 and list2:
            if list1.val < list2.val:
                cur.next = ListNode(list1.val)
                list1 = list1.next
            else:
                cur.next = ListNode(list2.val)
                list2 = list2.next
            cur = cur.next
        if list1:
            cur.next = list1
        if list2:
            cur.next = list2
        return dummp_list.next
```


*最小堆*
```python3
# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def mergeKLists(self, lists: List[Optional[ListNode]]) -> Optional[ListNode]:
        dummp_list = ListNode()

        heap = MinHeap()
        heads = [heap.push(head) for head in lists if head]

        cur = dummp_list
        while True:
            node =  heap.pop()
            if not node:
                break
            cur.next = ListNode(node.val)
            cur = cur.next
            if node.next:
                heap.push(node.next)

        return dummp_list.next

# 最小堆
class MinHeap:
    def __init__(self):
        self.heap: List[ListNode] = []

    # 父节点索引
    def parent(self, index: int):
        return (index - 1) // 2

    # 左节点索引
    def left_child(self, index: int):
        return 2 * index + 1

    # 右节点索引
    def right_child(self, index: int):
        return 2 * (index + 1)

    # 交换两个索引的元素
    def swap(self, i: int, j: int):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    # 上浮操作. 将元素向上调整以维护堆特性
    def percolate_up(self, index: int):
        while index > 0 and self.heap[index].val < self.heap[self.parent(index)].val:
            self.swap(index, self.parent(index))
            index = self.parent(index)

    # 下沉操作. 将元素向下调整以维护堆特性
    def percolate_down(self, index: int):
        size: int = len(self.heap)
        smallest: int = index
        left: int = self.left_child(index)
        right: int = self.right_child(index)

        # 找出当前节点，左子树，右子树中的最小值
        if (left < size) and self.heap[left].val < self.heap[smallest].val:
            smallest = left
        if (right < size) and self.heap[right].val < self.heap[smallest].val:
            smallest = right

        # 若最小值不是当前节点，则交换并继续下沉
        if smallest != index:
            self.swap(index, smallest)
            self.percolate_down(smallest)

    def push(self, node: ListNode) -> None:
        self.heap.append(node)
        self.percolate_up(len(self.heap)-1)

    def pop(self) -> ListNode | None:
        if not self.heap:
            return None
        # 交换第一个和最后一个元素
        self.swap(0, len(self.heap) - 1)
        node: ListNode = self.heap.pop()
        # 下沉新堆顶
        self.percolate_down(0)

        return node
```