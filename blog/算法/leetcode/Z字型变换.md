# Z字型变换
> https://leetcode.cn/problems/zigzag-conversion/

将一个给定字符串`s`根据给定的行数`numRow`,以从上往下、从左到右进行`Z`字形排列
比如输入字符串为 `PAYPALISHIRING` 行数为`3`时，排列如下:
```
P   A   H   N
A P L S I I G
Y   I   R
```
之后,你的输出需要从左往右逐行读取,产生出一个新的字符串. 比如:`PAHNAPLSIIGYIR`

**示例1**
```
输入：s = "PAYPALISHIRING", numRows = 3
输出："PAHNAPLSIIGYIR"
```

**示例2**
```
输入：s = "PAYPALISHIRING", numRows = 4
输出："PINALSIGYAHRPI"
解释：
P     I    N
A   L S  I G
Y A   H R
P     I
```

**示例3**
```
输入：s = "A", numRows = 1
输出："A"
```

**提示**
- `1 <= s.length <= 1000`
- `s`由英文字母(小写和大写)、`,`和`.`组成
- `1 <= numRows <= 1000`

**解题过程**

1. 特殊情况,当`numRows`等于1时,直接返回原字符串即可
2. 周期计算: `peroid = 2 * numRows - 2; reminder = index % period (index为字符串中字符下标)`
   - 当`reminder < numRows`时,则字符是在垂直向下的列中
   - 当`reminder >= numRows`时,则在斜向上排列的列中,通过`period - reminder`即可计算出对应行


```python
class Solution:
    def convert(self, s: str, numRows: int) -> str:
        if numRows == 1:
            return s

        period = 2 * numRows - 2
        rows = [""] * numRows
        for index in range(len(s)):
            reminder = index % period
            if reminder < numRows:
                rows[reminder] += s[index]
            else:
                rows[period-reminder] += s[index]
        return "".join(rows)
```