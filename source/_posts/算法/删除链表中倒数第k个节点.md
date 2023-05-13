---
title: 删除链表中倒数第k个节点
date: 2023-05-13 14:55:00
tags: [算法,链表]
---

**描述**

给定一个链表，删除链表的倒数第 n 个节点并返回链表的头指针
<!--more-->
例如，

给出链表 **`1→2→3→4→5，n=2`**

删除了链表中倒数第n个节点之后，链表变成 **`1→2→3→5`**

**示例1**

```
输入:  {1,2},2
返回:  {2} 
```

**题解**

> 虚拟头节点

可以通过快指针先走K步 慢指针先指向head，导致 快指针和慢指针相差n个结点，然后快指针移到末尾 这个时候慢指针就是倒数第n个结点的前一个节点，然后`slow.Next = slow.Next.Next`删除倒数第n个节点。

```go
package main

type ListNode struct{
    Val int
    Next *ListNode
}


/**
  * 
  * @param head ListNode类 
  * @param n int整型 
  * @return ListNode类
*/
func removeNthFromEnd( head *ListNode ,  n int ) *ListNode {
    // write code here
    dummy := &ListNode{Next: head}
    fast, slow := head, dummy
    for i := 0; i < n; i++ {
        fast = fast.Next
    }

    for fast != nil {
        fast = fast.Next
        slow = slow.Next
    }
    slow.Next = slow.Next.Next

    return dummy.Next
}
```

