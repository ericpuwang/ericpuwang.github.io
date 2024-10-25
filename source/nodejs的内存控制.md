---
title: Node.js的内存控制
date: 2024-11-01
tags:
- Node.js
- 内存控制
- 垃圾回收
categories: Node.js
---

# V8的垃圾回收机制和内存限制
> Node.js是一个构建在Chrome的JavaScript运行时上的平台

## V8的内存限制
> Node.js基于V8构建，故在Node.js中使用JavaScript对象基本上都是通过V8自己的方式来进行分配和管理

在Node中通过JavaScript使用内存时就会发现只能使用部分内存（64位系统下约为1.4 GB,32位系统下约为0.7 GB）

```c
// https://github.com/v8/v8/blob/main/src/heap/heap.cc#L5045
// 64bit机器: 1400MB
// 32bit机器: 700MB
size_t max_old_generation_size = 700ul * (kSystemPointerSize / 4) * MB;

// https://github.com/v8/v8/blob/main/src/heap/heap.cc#L4968
// max_new_space_size =  2 * max_semi_space_size
size_t max_semi_space_size =
      (v8_flags.minor_ms ? v8_flags.minor_ms_max_new_space_capacity_mb
                         : v8_flags.scavenger_max_new_space_capacity_mb) *
      kMaxSemiSpaceCapacityBaseUnit;

// https://github.com/v8/v8/blob/main/src/heap/heap.cc#L263
// 堆内存最大保留空间
size_t Heap::MaxReserved() const {
  const size_t kMaxNewLargeObjectSpaceSize = max_semi_space_size_;
  return static_cast<size_t>(
      (v8_flags.minor_ms ? 1 : 2) * max_semi_space_size_ +
      kMaxNewLargeObjectSpaceSize + max_old_generation_size());
}
```

- `JS单线程机制`: 作为浏览器的脚本语言，JS的主要用途是与用户交互以及操作DOM，那么这也决定了其作为单线程的本质，单线程意味着执行的代码必须按顺序执行，在同一时间只能处理一个任务
- `垃圾回收机制`: 垃圾回收本身也是一件非常耗时的操作，假设V8的堆内存为1.5G，那么V8做一次小的垃圾回收需要50ms以上，而做一次非增量式回收甚至需要1s以上，可见其耗时之久，而在这1s的时间内，浏览器一直处于等待的状态，同时会失去对用户的响应，如果有动画正在运行，也会造成动画卡顿掉帧的情况，严重影响应用程序的性能

## V8的对象分配

在V8中，所有的JavaScript对象都是在堆上分配的

### 内存使用量查询

获取Node.js进程的内存使用量（以字节为单位）

```shell
# https://nodejs.cn/api/process.html#process_process_memoryusage
~ node
Welcome to Node.js v18.20.4.
Type ".help" for more information.
> process.memoryUsage()
{
  rss: 48644096,         # 常驻集大小，是进程在主内存设备(即总分配内存的子集)中占用的空间量(包括JavaScript和C++)
  heapTotal: 7192576,    # V8 的内存使用量
  heapUsed: 4961456,     # V8 的内存使用量
  external: 1113471,     # 绑定到V8管理的JavaScript对象的C++对象的内存使用量(不受V8垃圾回收策略控制)
  arrayBuffers: 10455    # 为ArrayBuffer和SharedArrayBuffer分配的内存，包括所有的Node.js Buffer。也包含在external值中
}
>
```

**当使用`Worker`线程时，则`rss`将是对整个进程都有效的值，而其他字段仅涉及当前线程。**

### 调整V8运行时内存

> 下述参数仅在V8初始化时生效,一旦生效就不能动态改变

- `--max-old-space-size`: 调整老生代堆内存空间大小. 单位`Mbytes`
- `--max-semi-space-size`: 调整semi空间大小，新生代内存空间大小是该值的两倍. 单位`Mbytes`

## V8的垃圾回收机制

V8的垃圾回收策略主要是基于`分代式垃圾回收机制`，其根据对象的存活时间将内存的垃圾回收进行不同的分代，然后对不同的分代采用不同的垃圾回收算法

### V8的内存结构

- 新生代内存区 `Young Generation`或`New Space`: 大多数对象开始被分配在该区域，该区域相对较小但是gc频率高。该区域被分为两半，一半用来分配内存，另一半用于在垃圾回收时将需要保留的对象复制过来
- 老生代内存区 `Old Generation`或`Old Space`: 一个对象经过多次复制依然存活时，它将会被认为是生命周期较长的对象。这种较长生命周期的对象随后会被移动到老生代中，采用新的算法进行管理。老生代又分为`老生代指针区`和`老生代数据区`
- 大对象区 `Large Object Space`: 存放体积超越其他区域大小的对象，每个对象都会有自己的内存，垃圾回收不会移动大对象区
- 代码区 `Code Space`: 代码对象，会被分配在这里，唯一拥有执行权限的内存区域
- Map区 `Map Space`: 存放对象的Map信息。每个Map对象固定大小，为了快速定位，所以将该空间单独出来。

### 新生代
新生代的对象主要通过`Scavenge`算法进行垃圾回收。在`Scavenge`算法的基础上，主要采用了`Cheney`算法。`Cheney`算法是一种采用复制的方式实现的垃圾回收算法。它将堆内存一分为二，每一部分空间称为semispace。在这两个semispace空间中，只有一个处于使用中，另一个则处于闲置状态。处于使用状态的semispace空间称为**From**空间，处于闲置状态的空间称为**To**空间。当我们分配对象时，先是在From空间中进行分配。当开始进行垃圾回收时，会检查From空间中的存活对象，这些存活对象将被复制到To空间中，而非存活对象占用的空间将会被释放。完成复制后，From空间和To空间的角色发生对换。简而言之，**在垃圾回收的过程中，就是通过将存活对象在两个semispace空间之间进行复制**

### 老生代

新生代对象被移动到老生代中的限制条件

- 对象是否经历过`Scavenge`回收
- To空间内存占用比超过限制。默认限制为**25%**

老生代垃圾回收算法: `Mark-Sweep(标记清除) & Mark-Compact(标记整理)`

对于老生代中的对象，由于存活对象占较大比重，再采用Scavenge的方式会有两个问题:

- 存活对象较多，复制存活对象的效率将会很低
- 浪费一半的空间

`Mark-Sweep(标记清除)`分为`标记`和`清除`两个阶段，在标记阶段遍历堆中所有对象，并标记活着的对象，在随后的清除阶段，只清除没有标记的对象。`Mark-Sweep`算法主要是通过判断某个对象是否可以被访问到，从而知道该对象是否应该被回收，具体步骤如下:

- 垃圾回收器会在内部构件一个根列表，用于从根结点出发寻找那些可以被访问到的变量。根结点列表：

  - 全局对象
  - 本地函数的局部变量和参数
  - 当前嵌套调用链上的其他函数的变量和参数

- 从根结点出发，遍历所有子结点，并将其标记为活动的。根结点不可达的地方即位不活动的，被视为垃圾
- 垃圾回收器释放所有非活动的内存块，并将其归还给操作系统

`Mark-Sweep`算法最大的问题是在进行一次标记清除回收后，内存空间会出现不连续的状态。内存碎片会导致后续的内存分配问题，提前触发垃圾回收(*不必要*)。为了解决内存碎片问题，提出了`Mark-Compact`算法

`Mark-Compact(标记整理)`是在`Mark-Sweep`算法的基础上演变而来。它们的差别在于对象在标记为死亡后，在整理的过程中，将活着的对象往一端移动，移动完成后，直接清理掉边界外的内存

![](/images/Mark-Compact垃圾回收示意图.jpg)

<font style="color:red">**垃圾回收算法的简单对比**</font>

| 回收算法 | Mark-Sweep | Mark-Compact | Scavenge |
| :--- | :--- | :--- | :--- |
| 速度 | 中等 | 最慢 | 最快 |
| 空间开销 | 少(有碎片) | 少(无碎片) | 双倍空间(无碎片) |
| 是否移动对象 | 否 | 是 | 是 |

V8主要使用`Mark-Sweep`，在空间不足以对从新生代中晋升过来的对象进行分配时才使用`Mark-Compact`

由于JS的单线程机制，垃圾回收的过程会阻碍主线程同步任务的执行，待执行完垃圾回收后才会再次恢复执行主任务的逻辑，这种行为被称为`全停顿(stop-the-world)`。为了减少垃圾回收带来的停顿时间，V8引擎又引入了`Incremental Marking(增量标记)`的概念，即将原本需要一次性遍历堆内存的操作改为增量标记的方式，先标记堆内存的一部分对象，然后暂停，将执行权重新交回JS主线程，待主线程任务执行完毕后再从原来暂停标记的地方继续标记，直到标记完整个堆内存。

> V8在经过增量标记的改进后，垃圾回收的最大停顿时间可以减少到原本的1/6左右

![](/images/Node.js增量标记示意图.jpg)

得益于增量标记的好处，V8引擎后续引入了`延迟清理(lazy sweeping)`和`增量式清理(incremental compaction)`，让清理和整理的过程也变成增量式的。同时为了充分利用多核CPU的性能，也将引入`并行标记`和`并行清理`，进一步地减少垃圾回收对主线程的影响，为应用提升更多的性能

# 如何避免内存泄露

- 尽可能少的创建全局变量
- 手动清除定时器
- 少用闭包
- 清除DOM引用
- 弱引用

# 参考

- [https://v8.dev/blog/concurrent-marking](https://v8.dev/blog/concurrent-marking)
- [https://www.cnblogs.com/cangqinglang/p/12668374.html](https://www.cnblogs.com/cangqinglang/p/12668374.html)
- [https://github.com/li-jia-nan/my-blog/issues/20](https://github.com/li-jia-nan/my-blog/issues/20)