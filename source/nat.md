# Iptabes NAT

**<span color='red'>如果想要NAT功能能够正常使用，需要开启Linux主机的核心转发功能。</span>**

## SNAT

***配置SNAT，可以隐藏网内主机的IP地址，也可以共享公网IP，访问互联网，如果只是共享IP的话，只配置如下SNAT规则即可***

```shell
iptables -t nat -A POSTROUTING -s 10.1.0.0/16 -j SNAT --to-source 公网IP
```

**如果公网IP是动态获取的，不是固定的，则可以使用MASQUERADE进行动态的SNAT操作。**
```shell
# 将10.1网段的报文的源IP修改为eth0网卡中可用的地址。
iptables -t nat -A POSTROUTING -s 10.1.0.0/16 -o eth0 -j MASQUERADE
```


## DNAT

***配置DNAT，可以通过公网IP访问局域网内的服务。***

**<span color='red'>Tips:</span>** 理论上来说，只要配置DNAT规则，不需要对应的SNAT规则即可达到DNAT效果。但是测试过程中，对应SNAT规则也需要配置，才能正常DNAT，可以先尝试只配置DNAT规则，如果无法正常DNAT，再尝试添加对应的SNAT规则，SNAT规则配置一条即可，DNAT规则需要根据实际情况配置不同的DNAT规则。

```shell
iptables -t nat -I PREROUTING -d 公网IP -p tcp --dport 公网端口 -j DNAT --to-destination 私网IP:端口号

iptables -t nat -I PREROUTING -d 公网IP -p tcp --dport 8080 -j DNAT --to-destination 10.1.0.1:80

iptables -t nat -A POSTROUTING -s 10.1.0.0/16 -j SNAT --to-source 公网IP
```

**在本机进行目标端口映射时可以使用REDIRECT动作**
```shell
# 本机80端口映射到8080
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8080
```