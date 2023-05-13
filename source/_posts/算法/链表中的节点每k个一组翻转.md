---
title: 链表中的节点每k个一组翻转
date: 2023-05-13 14:44:00
tags: [算法,链表]
---

**描述**

将给出的链表中的节点每 k 个一组翻转，返回翻转后的链表。如果链表中的节点数不是 k 的倍数，将最后剩下的节点保持原样。你不能更改节点中的值，只能更改节点本身。
<!--more-->

*数据范围*： **`0≤n≤2000`** ， **`1≤k≤2000`** ，链表中每个元素都满足 **`0≤val≤1000`**

要求空间复杂度*O*(1)，时间复杂度*O*(n)

例如:

给定的链表 **`1→2→3→4→5`**

对于k=2，返回 **`2→1→4→3→5`**

对于k=3，返回 **`3→2→1→4→5`**

**示例1**

```
输入:  {1,2,3,4,5},2
返回:  {2,1,4,3,5}
```

**示例2**

```
输入:  {},1
返回:  {}
```

**题解**

> 递归、虚拟头节点
>
> **终止条件：** 当进行到最后一个分组，即不足k次遍历到链表尾（0次也算），就将剩余的部分直接返回
> **返回值：** 每一级要返回的就是翻转后的这一分组的头，以及连接好它后面所有翻转好的分组链表
> **本级任务：** 对于每个子问题，先遍历k次，找到该组结尾在哪里，然后从这一组开头遍历到结尾，依次翻转，结尾就可以作为下一个分组的开头，而先前指向开头的元素已经跑到了这一分组的最后，可以用它来连接它后面的子问题，即后面分组的头

1. 计算当前链表长度，若长度小于k，不用反转直接返回头节点
2. 反转前k个节点
3. 如果第k+1个节点存在，则从第k+1个节点开始采用递归方法

```go
package main

type ListNode struct{
    Val int
    Next *ListNode
}

/**
  * 
  * @param head ListNode类 
  * @param k int整型 
  * @return ListNode类
*/
func reverseKGroup( head *ListNode ,  k int ) *ListNode {
    length := size(head)
    if head == nil || head.Next == nil || length < k {
        return head
    }

    dummy := &ListNode{Next: head}
    for index := 1; index < k; index++ {
        temp := head.Next
        head.Next = temp.Next
        temp.Next = dummy.Next
        dummy.Next = temp
    }

    if head != nil {
        head.Next = reverseKGroup(head.Next, k)
    }

    return dummy.Next

}

func size(head *ListNode) int {
    size := 0
    for head != nil {
        size++
        head = head.Next
    }

    return size
}
```

