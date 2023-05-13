---
title: 链表中倒数最后K个节点
date: 2023-05-13 14:40:00
tags: [算法,链表]
---

**描述**

输入一个长度为 n 的链表，设链表中的元素的值为 a<sub>i</sub> ，返回该链表中倒数第k个节点。
如果该链表长度小于k，请返回一个长度为 0 的链表。
<!--more-->

**示例1**

```
输入:  {1,2,3,4,5},2
返回:  {4,5}
说明:  返回倒数第2个节点4，系统会打印后面所有的节点来比较。 
```

**示例2**

```
输入:  {2},8
返回:  {}
```

**题解**

> 快慢指针

第一个指针先移动k步，然后第二个指针再从头开始，这个时候这两个指针同时移动，当第一个指针到链表的末尾的时候，返回第二个指针即可

```go
package main

type ListNode struct{
    Val int
    Next *ListNode
}


/**
 * 代码中的类名、方法名、参数名已经指定，请勿修改，直接返回方法规定的值即可
 *
 *
 * @param pHead ListNode类
 * @param k int整型
 * @return ListNode类
 */
func FindKthToTail(pHead *ListNode, k int) *ListNode {
	// write code here
	if pHead == nil {
		return nil
	}

	fast := pHead
	slow := pHead

	for index := 0; index < k; index++ {
		if fast == nil {
			return fast
		}
		fast = fast.Next
	}

	for fast != nil {
		fast = fast.Next
		slow = slow.Next
	}

	return slow
}

```

