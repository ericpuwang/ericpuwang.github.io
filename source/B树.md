# B树
> 适用于外查找的平衡多叉树

**定义:**
一棵m阶的B-树，或为空树，或为满足下列特性的m叉树:

- 树中每个结点至多有m棵子树
- 若根结点不是叶子结点，则至少有两棵子树
- 除根之外的所有非终端结点至少有$\lceil m/2 \rceil$棵子树
- 所有的叶子结点都出现在同一层次上，并且不带信息，通常称为失败结点(失败结点并不存在，指向这些结点的指针为空)
- 所有的非终端结点最多有`m-1`个关键字，结点结构入下图所示:

![](/images/B-树的结点结构.jpg)
其中， $K_i$ (i=1,...,n)为关键字，且 $K_i$ < $K_{i-1}$ (i=1,...,n-1);  $P_i$ (i=0,...,n)为指向子树根结点的指针，且指针 $P_{i-1}$ 所指子树中所有结点的关键字均小于 $K_i$ (i=1,...,n)， $P_n$ 所指子树中所有结点的关键字均大于 $K_n$ ，n( $\lceil m/2 \rceil - 1 \leq n \leq m-1$ )为关键字的个数（或n+1为子树个数）

**特点**

- 平衡
- 有序
- 多路

### 结构定义
```c
#define m 3 // B树的阶
typedef int KeyType;

// B树结构体
typedef struct BTNode
{
    int keynum; // 结点中关键字个数，即结点大小
    struct BTNode *parent; // 指向双亲结点
    // 存放关键字以及其孩子结点指针。正常结点最多存放m个孩子，但在插入判断时会多存放一个
    struct Node
    {
        KeyType key;
        struct BTNode *ptr;
    } node[m+1]; // key的0号单元未用

}BTNode, *BTree;

// 结构类型
typedef struct {
    BTNode *pt; // 指向找到的结点
    int i; // i..m，在结点中的关键字序号
    int tag; // 1: 查找成功; 0: 查找失败
}Result;
```

### B树的查找
将给定值key与根结点的各个关键字 $k_1$ , $k_2$ ,..., $k_j$ ( $1 \leq j \leq m-1$ )尽性比较，由于该关键字序列是有序的，所以查找时可采用顺序查找或者二分查找。查找时:

- 若key= $k_i$ ( $1 \leq i \leq j$ ),则查找成功
- 若 $key \le k_1$ ,则顺着指针 $p_0$ 所指向的子树继续向下查找
- 若 $k_i \le key \le k_{i+1}$ ,则顺着指针 $p_i$ 所指向的子树继续向下查找
- 若 $key \ge k_j$ ,则顺着指针 $p_j$ 所指向的子树继续向下查找

```c
#define FALSE 0
#define TRUE 1

// Search 顺着指针t继续向下查找
int Search(BTree t, KeyType key)
{
    int i = 0;
    for (int j = 1; j < t->keynum; j++)
    {
        if (t->node[j].key <= key)
        {
            i = j;
        }
    }
    return i;
}

Result SearchBTree(BTree t, KeyType key)
{
    // p指向待查结点
    BTree p = t;
    // q指向p的双亲
    BTree q;
    // 是否查询到结点
    int found = FALSE;
    // 关键字序号
    int index = 0;

    while (p && !found)
    {
        // p->node[index].key <= key < p->node[index+1].key
        int index = Search(p, key);
        if (index > 0 && p->node[index].key == key)
        {
            found = TRUE;
        } else
        {
            q = p;
            p = p->node[index].ptr;
        }
    }

    Result result = {q, index, 0};
    if (found == TRUE)
    {
        result.tag = 1;
        result.pt = p;
    }
    return result;
}
```

### B树的插入
B树是动态查找树，因此其生成过程是从空树起，在查找的过程中通过逐个插入关键字而得到。但由于B树中除根之外的所有非终端结点中的关键字个数必须大于等于 $\lceil m/2 \rceil - 1$ ，因此，每次插入一个关键字不是在树中添加一个叶子结点，而是首先在最低层的某个非终端结点中添加一个关键字，若该关键字的个数不超过m-1，则插入完成，否则表明结点已满，要结点产生"分裂"，将此结点在同一层分成两个结点。一般情况下，结点分裂方法是：以中间关键字为界把结点一分为二，成为两个结点，并把中间关键字向上插入到双亲结点上，若双亲结点已满，则采用同样的方法继续分解。最坏的情况下，一直分解到树根结点，这时B树高度增加1

**算法步骤**

1. 在B树中查找给定关键字的记录，若查找成功，则插入操作失败；否则将新记录作为空指针`ap`插入到查找失败的叶子结点的上一层结点(由`q`指向)中
2. 若插入新记录和空指针后，`q`指向的结点的关键字个数未超过m-1，则插入操作成功，否则转入步骤3
3. 以该结点的第 $\lceil m/2 \rceil$ 个关键字 $k_{\lceil m/2 \rceil}$ 为拆分点，将该结点分成3个部分： $k_{\lceil m/2 \rceil}$ 部分， $k_{\lceil m/2 \rceil}$ ， $k_{\lceil m/2 \rceil}$ 右边部分。 $k_{\lceil m/2 \rceil}$ 左边部分仍然保留在原结点中； $k_{\lceil m/2 \rceil}$ 右边部分存放在一个新创建的结点(由`ap`指向)中；关键字值为 $k_{\lceil m/2 \rceil}$ 的记录和指针`ap`插入到q的双亲结点中。因`q`的双亲结点增加一个新记录，所以必须对`q`的双亲结点重复步骤2和3的操作，依此类推，知道`q`指向的结点是根结点，转入步骤4
4. 由于根结点无双亲，则由其分裂产生的两个结点的指针指向`ap`和`q`，以及关键字为 $k_{\lceil m/2 \rceil}$ 的记录构成一个新的根结点。此时，树的高度加1

```c
#include<stdlib.h>

void Insert(BTree *q, KeyType key, BTree ap, int i)
{
    for (int j = (*q)->keynum; j > i; j--)
    {
        (*q)->node[j+1] = (*q)->node[j];
    }

    (*q)->node[i+1].key = key;
    (*q)->node[i+1].ptr = ap;
    (*q)->keynum++;
}

// 将结点q分裂成两个结点, mid之前的结点保留，mid之后的结点移入新结点ap
void Split(BTree *q, BTree *ap)
{
    int mid = (m+1)/2;
    *ap = (BTree)malloc(sizeof(BTNode));
    (*ap)->node[0].ptr = (*q)->node[mid].ptr;

    if ((*ap)->node[0].ptr)
    {
        (*ap)->node[0].ptr->parent = *ap;
    }

    for (int i = mid + 1; i <= m; i++)
    {
        (*ap)->node[i-mid] = (*q)->node[i];
        if ((*ap)->node[i-mid].ptr)
        {
            (*ap)->node[i-mid].ptr->parent = *ap;
        }
    }
    (*ap)->keynum = m - mid;
    (*ap)->parent = (*q)->parent;
    (*q)->keynum = mid - 1;
}

// 生成含信息(t, r, ap)的新的根结点&t, 原t和ap为子树指针
void NewRoot(BTree *t, KeyType key, BTree ap)
{
    BTree p;
    p = (BTree)malloc(sizeof(BTNode));
    p->node[0].ptr = *t;
    *t = p;

    if ((*t)->node[0].ptr)
    {
        (*t)->node[0].ptr->parent = t;
    }

    (*t)->parent = NULL;
    (*t)->keynum = 1;

    (*t)->node[1].ptr = ap;
    (*t)->node[1].key = key;
    if ((*t)->node[1].ptr)
    {
        (*t)->node[1].ptr->parent = *t;
    }
}

// 在m阶B树t上结点q的key[i]与key[i+1]之间插入关键字k的指针r
// 若引起结点过大，则沿双亲结点进行必要的结点“分裂”，是t仍然是m阶B树
void InsertBTree(BTree *t, KeyType key, BTree q, int i)
{
    BTree ap = NULL;
    int finished = 0;
    KeyType rx = key; // 需要插入的关键字的值
    int mid;
    while (q && !finished)
    {
        Insert(&q, rx, ap, i);
        if (q->keynum < m)
        {
            finished = 1;
        } else
        {
            int mid = (m+1)/2;
            rx = q->node[mid].key;
            Split(&q, &ap);
            q = q->parent;
            if (q)
            {
                i = Search(q, rx);
            }
        }
    }
    if (!finished)
    {
        NewRoot(t, rx, ap);
    }
}
```

### B树的删除
m阶B树的删除操作是在B树的某个结点中删除指定的关键字及其邻近的一个指针，删除后应该进行调整使该树仍然满足B树的定义，也就是保证每个结点的关键字数目范围为 $[\lceil m/2 \rceil - 1, m]$ 。删除记录后，结点的关键字个数如果小于 $\lceil m/2 \rceil -1$ ，则要进行"合并"结点的操作。除了删除记录，还要删除该记录邻近的指针。若该结点为最下层的非终端结点，由于其指针均为空，删除后不会影响其他结点，可直接删除；若该结点不是最下层的非终端结点，邻近的指针则指向一棵子树，不可直接删除。此时可做如下处理: **将要删除记录其右(左)边邻近指针指向的子树中关键字最小(大)的记录(该记录必定在最下层的非终端结点中)替换**。采取这种办法进行处理，无论要删除的记录所在的结点是否为最下层的非终端结点，都可归结为在最下层的非终端结点中删除记录的情况

**算法步骤**

先依据查找算法找到对应关键字在B树中的位置。然后判断该结点是否为叶子结点:

- 若是叶子结点，先直接删除该关键字，然后对该结点进行平衡判断，看关键字数目是否满足要去
- 若不是叶子结点，则判断该关键字的左子树或右子树是否满足B树定义(即关键字数目 $> \lceil m/2 \rceil$ )
  - 若左子树满足，则将左子树中提取最大关键字放到该结点中替换要删除的关键字
  - 若右子树满足，则将右子树中提取最小关键字放到该结点中替换要删除的关键字
  - 若左右子树都不满足，则合并左右子树。然后删除结点的关键字，再对该结点进行平衡判断

**<span style="color:red">平衡条件:</span>** 若该结点的关键字数目不满足最小要求，则找到该关键字的右兄弟结点或左兄弟结点是否满足B树定义。若右兄弟满足则进行左旋操作，若左兄弟满足则进行右旋操作。若都不满足，则将该结点和其左右兄弟的其中一个以及双亲结点中的分隔符合并

```c
#include<stdio.h>
#include<stdlib.h>
#define min_key_num = (m+1)/2 - 1;

void MergeBro(BTree *left, BTree *right)
{
    if (!(*left)->node[(*left)->keynum].ptr)
    {
        // 如果左子树为叶子结点
        (*left)->node[(*left)->keynum].ptr = (*right)->node[0].ptr;
        for (int j = 1; j <= (*right)->keynum; j++)
        {
            (*left)->keynum++;
            (*left)->node[(*left)->keynum] = (*right)->node[j];
        }
    } else
    {
        MergeBro(&(*left)->node[(*left)->keynum].ptr, &(*right)->node[0].ptr);
        for (int j = 1; j <= (*right)->keynum; j++)
        {
            (*left)->keynum++;
            (*left)->node[(*left)->keynum] = (*right)->node[j];
        }
    }

    if ((*left)->keynum >= m)
    {
        int mid = (m+1)/2;
        int rx = (*left)->node[mid].key;
        BTree ap = NULL;
        // 将q->key[mid+1,..m],q->ptr[mid..m]移入新结点ap
        Split(&(*left), &ap);
        BTree p = (*left)->parent;
        int i = Search(p, rx);
        Insert(&p, rx, ap, i);
    }
}

void Delete(BTree *q, int index)
{
    for (int i = index; i <= (*q)->keynum; i++)
    {
        (*q)->node[index] = (*q)->node[index+1];
    }
    (*q)->keynum--;
}

void LeftRotation(BTree *q, BTree *p, int i)
{
    // 将双亲结点转移至q结点末尾
    (*q)->keynum++;
    (*q)->node[(*q)->keynum].key = (*p)->node[i+1].key;

    // 将q结点的右兄弟的第一个关键字转移至双亲结点的分隔符位置
    BTree rightBroPtr = (*p)->node[i+1].ptr;
    (*p)->node[i+1].key = rightBroPtr->node[1].key;

    // 将右结点的关键字前移
    for (int j = 1; j < rightBroPtr->keynum; j++)
    {
        rightBroPtr->node[j] = rightBroPtr->node[j+1];
    }
    rightBroPtr->keynum--;
}

void RightRotation(BTree *q, BTree *p, int i)
{
    // 将q结点向后移动空出第一个关键字的位置
    for (int j = (*q)->keynum; j >= 1; j--)
    {
        (*q)->node[j+1] = (*q)->node[j];
    }

    // 将双亲结点移动至q结点的第一个关键字的位置
    (*q)->node[1].key = (*p)->node[i].key;
    (*q)->node[1].ptr = NULL;
    (*q)->keynum++;

    // 将左兄弟结点的最后一个关键字移动到双亲结点的分隔符位置
    BTree leftBroPtr = (*p)->node[i-1].ptr;
    (*p)->node[i].key = leftBroPtr->node[leftBroPtr->keynum].key;
    leftBroPtr->keynum--;
}

void MergeNode(BTree *q, BTree *p, int i);

void BalanceCheck(BTree *q, KeyType key)
{
    // 该结点不满足最小关键字数目要求
    if ((*q)->keynum < min_key_num)
    {
        BTree p = (*q)->parent;
        // 找到p结点在双亲结点的索引位置
        int i = Search(p, key);
        // 看q结点的右兄弟是否存在多余结点
        if (i+1 <= p->keynum && p->node[i+1].ptr->keynum > min_key_num)
        {
            LeftRotation(q, &p, i);
        }
        // 看q结点的左兄弟结点是否存在多余结点
        else if (i-1>=0 && p->node[i-1].ptr->keynum > min_key_num)
        {
            RightRotation(q, &p, i);
        }
        // 左右兄弟都不存在多余结点
        else
        {
            MergeNode(q, &p, i);
        }
    }
}

void MergeNode(BTree *q, BTree *p, int i)
{
    BTree rightBroPtr = NULL, leftBroPtr = NULL;
    if (i+1<=(*p)->keynum)
    {
        rightBroPtr = (*p)->node[i+1].ptr;
    }
    if (i-1>=0)
    {
        leftBroPtr = (*p)->node[i-1].ptr;
    }

    if (rightBroPtr)
    {
        // 将双亲结点的分隔符移动至q结点的最后
        (*q)->keynum++;
        (*q)->node[(*q)->keynum].key = (*p)->node[i+1].key;

        // 将右兄弟结点都移动到q结点上
        (*q)->node[(*q)->keynum].ptr = rightBroPtr->node[0].ptr;
        for (int j = 1; j <= rightBroPtr->keynum; j++)
        {
            (*q)->keynum++;
            (*q)->node[(*q)->keynum] = rightBroPtr->node[j];
        }

        // 将双亲结点的分隔符删除
        int key = (*p)->node[i+1].key;
        for (int j = i+1; j < (*p)->keynum; j++)
        {
            (*p)->node[j] = (*p)->node[j+1];
        }
        (*p)->keynum--;

        // 判断双亲结点是否为根结点,且关键字为空
        if (!(*p)->parent && !(*p)->keynum)
        {
            // 让q结点作为根结点
            (*q)->parent = NULL;
            (*p) = (*q);
        }
        BalanceCheck(p, key);
    }
    else if (leftBroPtr)
    {
        // 将双亲结点的分隔符移动至左兄弟结点的最后
        leftBroPtr->keynum++;
        leftBroPtr->node[leftBroPtr->keynum].key = (*p)->node[i].key;

        // 将q结点都移动左兄弟结点上
        leftBroPtr->node[leftBroPtr->keynum].ptr = (*q)->node[0].ptr;
        for (int j = 1; j <= (*q)->keynum; j++)
        {
            leftBroPtr->keynum++;
            leftBroPtr->node[leftBroPtr->keynum] = (*q)->node[j];
        }

        // 将双亲结点的分隔符删除
        KeyType key = (*p)->node[i].key;
        for (int j = i; j < (*p)->keynum; j++)
        {
            (*p)->node[j] = (*p)->node[j+1];
        }
        (*p)->keynum--;

        // 判断双亲结点是否为根结点,且关键字为空
        if (!(*p)->parent && !(*p)->keynum)
        {
            // 让q结点作为根结点
            (*q)->parent = NULL;
            (*p) = (*q);
        }
        BalanceCheck(p, key);
    }
}

void DeleteBTreeNode(BTree *t, KeyType key)
{
    // Result res = SearchBTree(*t, key);
    Result res;
    // 查找成功
    if (res.tag)
    {
        // 判断该结点是否叶子结点. 若是叶子结点，则删除该关键字，然后进行平衡判断
        if (!res.pt->node[res.i].ptr)
        {
            Delete(&res.pt, res.i);
            BalanceCheck(&res.pt, key);
        } else
        {
            BTree leftChildPtr = res.pt->node[res.i-1].ptr;
            BTree rightChildPtr = res.pt->node[res.i].ptr;
            // 左子树满足B树定义
            if (leftChildPtr->keynum > min_key_num)
            {
                res.pt->node[res.i].key = leftChildPtr->node[leftChildPtr->keynum].key;
                leftChildPtr->keynum--;
            } else if (rightChildPtr->keynum > min_key_num) // 右子树满足B树定义
            {
                res.pt->node[res.i].key = rightChildPtr->node[1].key;
                for (int j = 1; j < rightChildPtr->keynum; j++)
                {
                    rightChildPtr->node[j] = rightChildPtr->node[j+1];
                }
                rightChildPtr->keynum--;
            } else // 都不满足
            {
                MergeBro(&leftChildPtr, &rightChildPtr);
                res.i = Search(res.pt, key);
                for (int j = res.i; j < res.pt->keynum; j++)
                {
                    res.pt->node[j] = res.pt->node[j+1];
                }
                res.pt->keynum--;
                BalanceCheck(&res.pt, key);
            }
        }
    } else
    {
        printf("您查找的元素不存在\n");
    }
}
```