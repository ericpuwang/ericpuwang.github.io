---
title: k8s service底层之iptables与ipvs
data: 2023-05-08 15:29
tags: [kubernetes, linux, iptables]
---

***service底层实现主要有两个网络模式: iptables和ipvs. 他们都是由kube-proxy维护***

## Iptables

`kube-proxy`通过Service的Informer感知到ApiServer的`Service`和`EndPoint`的变化情况。作为该事件的响应，它会在宿主机上创建相应的`iptables`规则。这些规则会捕获到`Service`的ClusterIp和Port的流量，并将流量按照比例重定向到`Service`的后端`Pod`中

<!--more-->

`kube-proxy`在iptables的NAT表PREROUTING链中实现它的NAT和负载均衡功能

`Iptables`为防火墙而设计且基于内核规则列表，kube-proxy 使用的是一种 O(n) 算法，其中的 n 随集群规模同步增长，所以这里的集群规模越大，更明确的说就是服务和后端`Pod`的数量越大，查询的时间就会越长

<font color='red'>**Tips**</font>: 当后端`Pod`不可用时无法进行重试

![](images/k8s_service_iptables.png)


## Ipvs

基于IPVS实现Service转发，Kubernetes几乎能够具备无限的水平扩展能力

在IPVS模式下，`kube-proxy`通过Service的Informer感知到ApiServer的`Service`和`Endpoint`的变化情况。作为该事件的响应，它会调用netlink接口创建IPVS规则，并定期将IPVS规则与K8S的`Service`和`Endpoint`同步。访问服务时，IPVS 将流量定向到后端Pod之一。

当我们创建了前面的`Service`之后，kube-proxy首先会在宿主机上创建一个虚拟网卡（叫作：kube-ipvs0），并为它分配Service VIP作为IP地址。接下来，kube-proxy就会通过Linux的IPVS模块，为这个IP地址设置三个 IPVS虚拟主机，并设置这三个虚拟主机之间使用轮询模式 (rr) 来作为负载均衡策略。拓扑图如下所示拓扑图：

![](images/k8s_service_ipvs.png)
