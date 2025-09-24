# Linux隧道
> Linux L3隧道底层原理都是基于tun设备

## ipip
> Ipv4 in Ipv3,在Ipv4报文的基础上封装一个Ipv4报文

要使用`ipip`隧道,首先需要内核模块`ipip.ko`的支持
```shell
# 加载ipip模块
modprobe ipip
# 查看ipip模块是否加载
lsmod | grep ipip
```

![ipip隧道网络拓扑](/images/ipip隧道网络拓扑.png)

**创建Network namespace**
```shell
ip netns add ns1
ip netns add ns2
```

**创建两对Veth Pair设备,另其一端挂载network namespace中**
```shell
# 创建Veth Pair
ip link add v1 type veth peer name v1_p
ip link add v2 type veth peer name v2_p

# 挂载一端到network namespace
ip link set v1 netns ns1
ip link set v2 netns ns2
```

**给Veth Pair端点配置IP并启用**
```shell
ip addr add 10.10.10.1/24 dev v1_p
ip link set v1_p up
ip addr add 10.10.20.1/24 dev v2_p
ip link set v2_p up

ip netns exec ns1 ip addr add 10.10.10.2/24 dev v1
ip netns exec ns1 ip link set v1 up
ip netns exec ns2 ip addr add 10.10.20.2/24 dev v2
ip netns exec ns2 ip link set v2 up
```

**创建网桥,并把v1_p和v2_p的IP让给网桥**
```shell
ip link add name br0 type bridge
ip link set br0 up

ip link set dev v1_p master br0
ip link set dev v2_p master br0

ip addr del 10.10.10.1/24 dev v1_p
ip addr del 10.10.20.1/24 dev v2_p
ip addr add 10.10.10.1/24 dev br0
ip addr add 10.10.20.1/24 dev br0
```

**修改内核参数**
> ubuntu发行版需要配置该参数
```shell
echo 1 > /proc/sys/net/ipv4/conf/v1_p/accept_local
echo 1 > /proc/sys/net/ipv4/conf/v2_p/accept_local
echo 0 > /proc/sys/net/ipv4/conf/all/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/v1_p/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/v2_p/rp_filter
```

```shell
root@lima-k8s-network:~# ip netns exec ns1 ping 10.10.20.2
PING 10.10.20.2 (10.10.20.2) 56(84) bytes of data.
From 10.10.10.1: icmp_seq=1 Redirect Host(New nexthop: 10.10.20.2)
64 bytes from 10.10.20.2: icmp_seq=1 ttl=63 time=0.176 ms
From 10.10.10.1: icmp_seq=2 Redirect Host(New nexthop: 10.10.20.2)
64 bytes from 10.10.20.2: icmp_seq=2 ttl=64 time=0.196 ms
^C
--- 10.10.20.2 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1042ms
rtt min/avg/max/mdev = 0.176/0.186/0.196/0.010 ms
```

**ns1 network namespace中创建tun设备,并设置隧道模式为ipip**
```shell
# 创建tun设备,设置隧道外层IP
ip netns exec ns1 ip tunnel add tun1 mode ipip remote 10.10.20.2 local 10.10.10.2
ip netns exec ns1 ip link set tun1 up
# 设置隧道内层IP
ip netns exec ns1 ip addr add 10.10.100.10 peer 10.10.200.10 dev tun1
```

![ip报文封装示意图](/images/ip报文封装示意图.png)

**在ns2创建tun2和ipip tunnel**
```shell
# 创建tun设备,设置隧道外层IP
ip netns exec ns2 ip tunnel add tun2 mode ipip remote 10.10.10.2 local 10.10.20.2
ip netns exec ns2 ip link set tun2 up
# 设置隧道内层IP
ip netns exec ns2 ip addr add 10.10.200.10 peer 10.10.100.10 dev tun2
```

**完成配置后,两个tun设备端点就可以互通了**
```shell
root@lima-k8s-network:~# ip netns exec ns1 ping 10.10.200.10 -c 1
PING 10.10.200.10 (10.10.200.10) 56(84) bytes of data.
64 bytes from 10.10.200.10: icmp_seq=1 ttl=64 time=0.337 ms

--- 10.10.200.10 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.337/0.337/0.337/0.000 ms
```
