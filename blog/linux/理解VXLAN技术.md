# Linux隧道网络: VXLAN
> Virtual eXtensible LAN,虚拟可扩展的局域网,是一种虚拟化隧道通信技术,是一种overlay技术,通过三层的网络搭建虚拟的二层网络

VXLAN是在底层物理网络(underlay)之上使用隧道技术,依托UDP层构建的overlay的逻辑网络,使逻辑网络和物理网络解耦,实现灵活的组网需求. 它是一个一对多的网络.

VXLAN技术解决了如下几个问题:
- VLAN HEADER只有`12bit`(最多支持 $2^{12}$ 子网的划分)的长度限制问题
- VXLAN的HEADER有`24bit`,可以支持 $2^{24}$ 个子网,并通过VNI(Virutal Network Identifier)区分不同的子网,相当于VLAN中的LAN ID
- 多租户网络隔离
- 大二层,同时保证二层的广播域不会过分扩大

VXLAN创建在原来的IP网络(三层)上,只要是三层可达(能通过IP互相通信)的网络就能够部署VXLAN. 在VXLAN网络的每个端点都有一个`VTEP`设备,负责VXLAN协议报文的封包和解包,也就是在虚拟报文上VTEP通信的报文头部. 物理网络上可以创建多个VXLAN网络,可以将这些VXLAN网络看作一个隧道,不同节点上的虚拟机/容器可以通过隧道直连,通过`VNI`标识不同的VXLAN网络,使得不同的VXLAN可以相互隔离

- `VTEP`(Virtual Tunnel Endpoints): VXLAN网络的边缘设备,用来进行VXLAN报文的处理(封包和解包). 可以是网络设备也可以是一台机器
- `VNI`(Virtual Networ Identifier): VNI是每个VXLAN网络的标识,是个24位整数
- `tunnel`: 虚拟通道,VXLAN通信双方都认为自己在直连通信,并不知道底层网络的存在

![VXLAN的封包格式](/images/VXLAN的封包格式.png)
VXLAN的报文就是MAC in UDP,即在三层网络的基础上构建一个虚拟的二层网络

VXLAN报文的转发过程就是: 原始报文经过VTEP,被Linux内核添加上VXLAN包头及外层的UDP头部,再发送出去,对端VTEP接收到VXLAN报文后拆除外层UDP头部,并根据VXLAN头部的VNI把原始报文发送到目的服务器.

## 点对点的VXLAN
![点对点的VXLAN](/images/点对点的VXLAN.png)

**创建VXLAN接口**
```shell
ip link add vxlan0 type vxlan \
  id 11 \
  dstport 4789 \
  remote 192.168.1.3 \
  local 192.168.1.2 \
  dev eth0
```
- remote是对端节点的IP
- local是本节点IP
- id是VNI的值
- dstport 是VTEP设备的端口

**为VXLAN网卡配置IP地址并启用**
```shell
ip addr add 172.17.1.2/24 dev vxlan0
ip link set vxlan0 up
```

执行成功后,路由表项多了如下内容:
```shell
root@lima-k8s-network:~# ip route
172.17.1.0/24 dev vxlan0 proto kernel scope link src 172.17.1.2
```
同时,vxlan0的FDB表项中的内容如下:
```shell
root@lima-k8s-network:~# bridge fdb
# 默认的VTEP对端地址为192.168.1.3
# 换句话说,原始报文经过vxlan0后会被内核添加上VXLAN头部,
# 而外部UDP头的目的IP地址会被冠上192.168.1.3
00:00:00:00:00:00 dev vxlan0 dst 192.168.1.3 via eth0 self permanent
```

**在主机host2执行如下操作**

```shell
ip link add vxlan0 type vxlan \
  id 11 \
  dstport 4789 \
  remote 192.168.1.2 \
  local 192.168.1.3 \
  dev eth0
ip addr add 172.17.1.3/24 dev vxlan0
ip link set vxlan0 up
```

**测试结果**
> 在host1中ping host2的VTEP设备地址172.17.1.3

```shell
root@lima-k8s-network:~# ping 172.17.1.3 -c 3
PING 172.17.1.3 (172.17.1.3) 56(84) bytes of data.
64 bytes from 172.17.1.3: icmp_seq=1 ttl=64 time=0.841 ms
64 bytes from 172.17.1.3: icmp_seq=2 ttl=64 time=0.382 ms
64 bytes from 172.17.1.3: icmp_seq=3 ttl=64 time=0.377 ms
```

## 多播模式的VXLAN
> 要组成同一个VXLAN网络,VTEP必须能感知到彼此的存在. 多播组本来的功能就是把网络中的某些节点组成一个虚拟的组. 如果VXLAN要使用多播模式,那么底层的网络结构需要支持多播的功能

> 多播地址让源设备能够将分组发送给一组设备. 属于多播组的设备将被分配一个多播组IP地址，多播地址范围为224.0.0.0～239.255.255.255

![多播模式下的VXLAN网络拓扑](/images/多播模式下的VXLAN网络拓扑.png)

**播模式下VXLAN通信的全过程**
1. host1的vxlan0发送ping报文到host2的`172.17.1.3`,内核发现源地址和目的地址在同一个局域网内. 需要知道对方的MAC地址,由于本地没有缓存,因此发送ARP请求
2. ARP报文源MAC地址为host1上vxlan0的MAC地址,目的MAC地址为`255.255.255.255`(广播地址),并根据配置添加VLXAN头部`vni=11`
3. 不知道对端VTEP在哪台主机同时配置了多播组,根据配置,VTEP会往多播地址`224.1.1.1`发送多播报文
4. 多播组中的所有主机都收到这个报文,内核发现是VXLAN报文,根据VNI发送给对应VTEP
5. host2的VTEP去掉VXLAN头部,取出真正的ARP报文. 同时,VTEP会记录源MAC地址和IP地址信息到FDB表中. 如果发现ARP不是发送给自己的则直接丢弃;如果是发送给自己的则生成ARP应答报文
6. 应答报文目的MAC地址发送方VTEP的MAC地址. 对端VTEP已经通过源报文学习到VTEP所在主机的MAC地址,因此会直接单播发送给目的VTEP
7. 应答报文通过底层网络直接返回发送主机,发送主机根据VNI把报文转发给对应VTEP,VTEP解包获取ARP报文,添加到VTEP缓存中,并根据报文学习目的VTEP所在主机的MAC地址,添加到FDB表中
8. VTEP双方已经通过一次ARP报文知道了建立ICMP通信需要的所有信息,因此后续的ICMP报文都在这条逻辑隧道中单播进行

**创建VXLAN接口**
> 和点对点模型相比就多了group参数
```shell
ip link add vxlan0 type vxlan \
  id 11 \
  dstport 4789 \
  group 224.1.1.1 \
  local 192.168.1.2 \
  dev eth0
```
- group参数表示将VTEP加入一个多播组,多播地址是224.1.1.1

**为VXLAN网卡配置IP地址并启用**
```shell
ip addr add 172.17.1.2/24 dev vxlan0
ip link set vxlan0 up
```

执行成功后,路由表项多了如下内容:
```shell
root@lima-k8s-network:~# ip route
172.17.1.0/24 dev vxlan0 proto kernel scope link src 172.17.1.2
```
同时,vxlan0的FDB表项中的内容如下:
```shell
root@lima-k8s-network:~# bridge fdb
# 原始报文经过vxlan0后会被内核添加上VXLAN头部,
# 而外部UDP头的目的IP地址会被冠上多播地址224.1.1.1
00:00:00:00:00:00 dev vxlan0 dst 224.1.1.1 via eth0 self permanent
```

## VXLAN+桥接网络

![VXLAN+网桥的网络拓扑](/images/VXLAN+网桥的网络拓扑.png)

**创建VXLAN网卡,使用多播模式**
```shell
ip link add vxlan0 type vxlan \
  id 11 \
  dstport 4789 \
  group 224.1.1.1 \
  local 192.168.1.2 \
  dev eth0
```

**创建网桥bridge0,把VXLAN网卡vxlan0绑定到上面**
```shell
ip link add br0 type bridge
ip link set vxlan0 master br0
ip link set vxlan0 up
ip link set br0 up
```

**创建Veth Pair**
```shell
ip netns add ns1
ip link add veth0 type veth peer name veth1
ip link set dev veth0 master br0
ip link set veth0 up

ip link set dev veth1 netns ns1
ip netns exec ns1 ip link set lo up
ip netns exec ns1 ip link set veth1 name eth0
ip netns exec ns1 ip addr add 172.17.1.2/24 dev eth0
ip netns exec ns1 ip link set eth0 up
```

**同样方法配置另一台主机**,绑定`172.17.1.3`到另外一个network namespace中的eth0. 从`172.17.1.2` ping `172.17.1.3`发现整个通信过程和前面的实验类似,只不过容器发出的ARP报文会先经过网桥,再转发给`vxlan0`;然后在`vxlan0`处由Linux内核添加`VXLAN`头部;最后通过多播的方式查询通信对端的MAC地址
