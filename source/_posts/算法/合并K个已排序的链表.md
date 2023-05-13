---
title: 合并K个已排序的链表
date: 2023-05-13 14:33:00
tags: [算法, 链表]
---

**描述**

合并 k 个升序的链表并将结果作为一个升序的链表返回其头节点。
<!--more-->

*数据范围：* 节点总数 **`0≤n≤5000`** ，每个节点的val满足 **`|val|≤1000`**

要求：时间复杂度 *O*(*`nlogn`*)

**示例1**

```
输入:  [{1,2,3},{4,5,6,7}]
返回:  {1,2,3,4,5,6,7}
```

**示例2**

```
输入:  [{1,2},{1,4,5},{6}]
返回:  {1,1,2,4,5,6}
```

**题解**

> 递归、分治

> 对于这k个链表，就相当于上述合并阶段的k个子问题，需要划分为链表数量更少的子问题，直到每一组合并时是两两合并，然后继续往上合并，这个过程基于递归：
> - **终止条件：** 划分的时候直到左右区间相等或左边大于右边。
> - **返回值：** 每级返回已经合并好的子问题链表。
> - **本级任务：** 对半划分，将划分后的子问题合并成新的链表。

1. 从链表数组的首和尾开始，每次划分从中间开始划分，划分成两半，得到左边 **`n/2`**个链表和右边**`n/2`** 个链表
2. 继续不断递归划分，直到每部分链表数为1.
3. 将划分好的相邻两部分链表，按照[两个有序链表合并](https://www.nowcoder.com/practice/a479a3f0c4554867b35356e0d57cf03d?tpId=295&sfm=html&channel=nowcoder)的方式合并，合并好的两部分继续往上合并，直到最终合并成一个链表。

```go
package main

type ListNode struct{
    Val int
    Next *ListNode
}


/**
 *
 * @param lists ListNode类一维数组
 * @return ListNode类
 */
func mergeKLists(lists []*ListNode) *ListNode {
	// write code here
	length := len(lists)
	if length == 0 {
		return nil
	}
	if length == 1 {
		return lists[0]
	}
	if length == 2 {
        return merge(lists[0], lists[1])
	}

	return merge(mergeKLists(lists[:length/2]), mergeKLists(lists[length/2:]))
}

func merge(lists1 *ListNode, lists2 *ListNode) *ListNode {
	head := &ListNode{}
	cur := head
	for lists1 != nil && lists2 != nil {
		if lists1.Val < lists2.Val {
			cur.Next = lists1
			lists1 = lists1.Next
		} else {
			cur.Next = lists2
			lists2 = lists2.Next
		}
		cur = cur.Next
	}
	if lists1 != nil {
		cur.Next = lists1
	}
	if lists2 != nil {
		cur.Next = lists2
	}

	return head.Next
}
```

