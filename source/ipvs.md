# K8s IPVS工作原理

## IPVS

> IPVS 专门用于负载均衡，并使用更高效的数据结构（哈希表），允许几乎无限的规模扩张。

**Ipvs和Iptables区别**

| Netfilter Hook | 作用 | Iptables | Ipvs |
| :--- | :--- | :--- | :--- |
| `NF_IP_PRE_ROUTING`  | 接收的数据包进入协议栈后立即触发此回调函数。**发生在路由判断之前** | ✓        | **`✕`** |
| `NF_IP_LOCAL_IN`     | 接收的数据包经过路由判断后，如果目标地址在本机上，则将触发此回调函数 | ✓        | ✓                              |
| `NF_IP_FORWARD`      | 接收的数据包经过路由判断后，如果目标地址在其他机器上，则将触发此回调函数 | ✓        | ✓                              |
| `NF_IP_LOCAL_OUT`    | 本机产生的准备发送的数据包，在进入协议栈后立即触发此回调函数 | ✓        | ✓                              |
| `NF_IP_POST_ROUTING` | 本机产生的准备发送的数据包或者经由本机转发的数据包，在经过路由判断之后，将触发此回调函数。 | ✓        | **`✕`** |

**服务网络拓扑**

创建 ClusterIP 类型服务时，IPVS proxier 将执行以下三项操作：

- 确保节点存在虚拟接口，默认是`kube-ipvs0`
- 将ClusterIP绑定到虚拟接口
- 分别为每个ClusterIP地址创建IPVS虚拟服务器

**端口映射**

IPVS中有三种代理模式: `NAT`、`IPIP`和`DR`。目前只有`NAT`模式支持端口映射。`kube-proxy`利用NAT模式实现端口映射

```shell
# ipvsadm -ln
#  IPVS 服务端口443到Pod端口5443的映射
TCP  10.96.176.171:443 rr
  -> 10.244.110.164:5443          Masq    1      1          0
  -> 10.244.162.180:5443          Masq    1      3          0
```

**会话关系**

IPVS 支持客户端IP会话关联（持久连接）。 当服务指定会话关系时，IPVS 代理将在 IPVS 虚拟服务器中设置超时值（默认为180分钟= `10800秒`）

```shell
# kubectl describe svc nginx
Name:			nginx
...
IP:			    10.102.128.4
Port:			http	3080/TCP
Session Affinity:	ClientIP  # 会话保持

# ipvsadm -ln
IP Virtual Server version 1.2.1 (size=4096)
Prot LocalAddress:Port Scheduler Flags
  -> RemoteAddress:Port           Forward Weight ActiveConn InActConn
TCP  10.96.176.175:80 rr persistent 10800
```

**Iptables和Ipset**

`ipvs` 会使用 `iptables` 进行**`包过滤`**、**`SNAT`**、**`masquared(伪装)`**，并使用`ipset`来简化`iptables`的规则管理

kube-proxy `ipvs`模式在如下情况中依赖`iptables`实现:

- kube-proxy配置参数`--masquerade-all = true`
- kube-proxy启动时指定集群CIDR
- 支持`Loadbalancer`和`NodePort`类型的Service

| 名称 | 条目 | 使用场景 |
| :--- | :--- | :--- |
| KUBE-CLUSTER-IP                | All service IP + port                                        | Mark-Masq for cases that <font color="red">`masquerade-all=true`</font> or <font color="red">`clusterCIDR`</font> specified |
| KUBE-LOOP-BACK                 | All service IP + port + IP                                   | masquerade for solving hairpin purpose                       |
| KUBE-EXTERNAL-IP               | service external IP + port                                   | masquerade for packages to external IPs                      |
| KUBE-LOAD-BALANCER             | load balancer ingress IP + port                              | masquerade for packages to load balancer type service        |
| KUBE-LOAD-BALANCER-LOCAL       | LB ingress IP + port with <font color="red">`externalTrafficPolicy=local`</font> | accept packages to load balancer with <font color="red">`externalTrafficPolicy=local`</font> |
| KUBE-LOAD-BALANCER-FW          | load balancer ingress IP + port with <font color="red">`loadBalancerSourceRanges`</font> | package filter for load balancer with <font color="red">`loadBalancerSourceRanges`</font> specified |
| KUBE-LOAD-BALANCER-SOURCE-CIDR | load balancer ingress IP + port + source CIDR                | package filter for load balancer with <font color="red">`loadBalancerSourceRanges`</font> specified |
| KUBE-NODE-PORT-TCP             | nodeport type service TCP port                               | masquerade for packets to nodePort(TCP)                      |
| KUBE-NODE-PORT-LOCAL-TCP       | nodeport type service TCP port with <font color="red">`externalTrafficPolicy=local`</font> | accept packages to nodeport service with <font color="red">`externalTrafficPolicy=local`</font> |
| KUBE-NODE-PORT-UDP             | nodeport type service UDP port                               | masquerade for packets to nodePort(UDP)                      |
| KUBE-NODE-PORT-LOCAL-UDP       | nodeport type service UDP port with <font color="red">`externalTrafficPolicy=local`</font> | accept packages to nodeport service with <font color="red">`externalTrafficPolicy=local`</font> |

## 入网流量

1. **nat表**

   `PREROUTING` -> `KUBE-SERVICES` -> `KUBE-MARK-MASQ` -> `ACCEPT` 

   ```shell
   Chain PREROUTING (policy ACCEPT 0 packets, 0 bytes)
    pkts bytes target     prot opt in     out     source               destination
       7   491 KUBE-SERVICES  all  --  *      *       0.0.0.0/0            0.0.0.0/0            /* kubernetes service portals */
       2   191 DOCKER_OUTPUT  all  --  *      *       0.0.0.0/0            172.18.0.1
   ```

   ```shell
   Chain KUBE-SERVICES (2 references)
    pkts bytes target     prot opt in     out     source               destination
       0     0 KUBE-MARK-MASQ  all  --  *      *      !10.244.0.0/16        0.0.0.0/0            /* Kubernetes service cluster ip + port for masquerade purpose */ match-set KUBE-CLUSTER-IP dst,dst
      20  1200 KUBE-NODE-PORT  all  --  *      *       0.0.0.0/0            0.0.0.0/0            ADDRTYPE match dst-type LOCAL
       0     0 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            match-set KUBE-CLUSTER-IP dst,dst
   ```

   ```shell
   Chain KUBE-MARK-MASQ (2 references)
    pkts bytes target     prot opt in     out     source               destination
       0     0 MARK       all  --  *      *       0.0.0.0/0            0.0.0.0/0            MARK or 0x4000
   ```

2. **filter表**

   `INPUT` -> `KUBE-NODE-PORT` -> `KUBE-FIREWALL` -> `IPVS[kube-ipvs0]`

   ```shell
   Chain INPUT (policy ACCEPT 1021 packets, 145K bytes)
    pkts bytes target     prot opt in     out     source               destination
   2761K  402M KUBE-NODE-PORT  all  --  *      *       0.0.0.0/0            0.0.0.0/0            /* kubernetes health check rules */
   2768K  404M KUBE-FIREWALL  all  --  *      *       0.0.0.0/0            0.0.0.0/0
   ```

   ```shell
   Chain KUBE-NODE-PORT (1 references)
    pkts bytes target     prot opt in     out     source               destination
       0     0 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            /* Kubernetes health check node port */ match-set KUBE-HEALTH-CHECK-NODE-PORT dst
   ```

   ```shell
   Chain KUBE-FIREWALL (2 references)
    pkts bytes target     prot opt in     out     source               destination
       0     0 DROP       all  --  *      *       0.0.0.0/0            0.0.0.0/0            /* kubernetes firewall for dropping marked packets */ mark match 0x8000/0x8000
       0     0 DROP       all  --  *      *      !127.0.0.0/8          127.0.0.0/8          /* block incoming localnet connections */ ! ctstate RELATED,ESTABLISHED,DNAT
   ```

   ```shell
   root@ipvs-control-plane:/# ip addr show dev kube-ipvs0
   7: kube-ipvs0: <BROADCAST,NOARP> mtu 1500 qdisc noop state DOWN group default
       link/ether 82:b2:e2:12:d9:77 brd ff:ff:ff:ff:ff:ff
       inet 10.96.0.1/32 scope global kube-ipvs0
          valid_lft forever preferred_lft forever
       inet 10.96.0.10/32 scope global kube-ipvs0
          valid_lft forever preferred_lft forever
   ```

   ```shell
   root@ipvs-control-plane:/# ipset list
   
   ...
   
   Name: KUBE-LOOP-BACK
   Type: hash:ip,port,ip
   Revision: 5
   Header: family inet hashsize 1024 maxelem 65536
   Size in memory: 680
   References: 1
   Number of entries: 6
   Members:
   10.244.0.2,tcp:9153,10.244.0.2
   10.244.0.2,udp:53,10.244.0.2
   10.244.0.4,tcp:9153,10.244.0.4
   10.244.0.4,udp:53,10.244.0.4
   10.244.0.4,tcp:53,10.244.0.4
   10.244.0.2,tcp:53,10.244.0.2
   
   Name: KUBE-LOAD-BALANCER
   Type: hash:ip,port
   Revision: 5
   Header: family inet hashsize 1024 maxelem 65536
   Size in memory: 192
   References: 0
   Number of entries: 0
   Members:
   
   Name: KUBE-NODE-PORT-LOCAL-SCTP-HASH
   Type: hash:ip,port
   Revision: 5
   Header: family inet hashsize 1024 maxelem 65536
   Size in memory: 192
   References: 0
   Number of entries: 0
   Members:
   
   Name: KUBE-CLUSTER-IP
   Type: hash:ip,port
   Revision: 5
   Header: family inet hashsize 1024 maxelem 65536
   Size in memory: 448
   References: 2
   Number of entries: 4
   Members:
   10.96.0.1,tcp:443
   10.96.0.10,tcp:53
   10.96.0.10,udp:53
   10.96.0.10,tcp:9153
   
   ...
   ```

   ```shell
   root@ipvs-control-plane:/# ipvsadm -ln
   IP Virtual Server version 1.2.1 (size=4096)
   Prot LocalAddress:Port Scheduler Flags
     -> RemoteAddress:Port           Forward Weight ActiveConn InActConn
   TCP  10.96.0.1:443 rr
     -> 172.18.0.5:6443              Masq    1      3          0
   TCP  10.96.0.10:53 rr
     -> 10.244.0.2:53                Masq    1      0          0
     -> 10.244.0.4:53                Masq    1      0          0
   TCP  10.96.0.10:9153 rr
     -> 10.244.0.2:9153              Masq    1      0          0
     -> 10.244.0.4:9153              Masq    1      0          0
   UDP  10.96.0.10:53 rr
     -> 10.244.0.2:53                Masq    1      0          0
     -> 10.244.0.4:53                Masq    1      0          0
   ```

如上所示，kube-proxy 通过 iptables 允许访问 **KUBE-CLUSTER-IP** 的流量，并通过在虚拟网卡 `kube-ipvs0` 上配置 ClusterIP 的方式，让内核以为 ClusterIP 为本机 IP，从而走 iptables 的 **INPUT** 链进入本机，继而通过 `IP Virtual Server` 找到 Real Server 提供服务。



**`IPVS模式工作原理示意图:`**


![ipvs工作原理图.png](/images/ipvs工作原理图.png)

## FAQ

`Q:` 为什么每个svc会在ipvs网卡增加vip地址

`A:` 由于**IPVS**没有实现 `NF_IP_PRE_ROUTING`，就不会在进入`NF_IP_LOCAL_IN`之前进行地址转换。那么数据包经过路由判断后，会进入`NF_IP_LOCAL_IN` **Hook**点，**IPVS**回调函数如果发现目标**IP**地址不属于该节点，就会丢弃数据包。因此，K8S创建dummy网络接口k8s-ipvs0，然后将service cluster ip绑定到该接口上，内核在处理数据包时，会发现该目标 **IP** 地址属于该节点，于是可以继续处理数据包。
