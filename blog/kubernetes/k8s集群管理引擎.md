# Kubernetes多集群管理

## 核心功能

- 多集群管理
    - 纳管云上托管的Kubernetes集群
    - 纳管IDC中自建的Kubernetes集群
    - 管控集群也可以注册为子集群运行业务
    - 纳管版本高于1.28.0的各类Kubernetes集群
    - 支持通过动态的RBAC规则访问子集群
- 应用分发
    - 跨集群分发
        - 复制调度
        - 静态基于权重的拆分调度
    - 全种类应用资源
        - Kubernetes原生对象，如Deployment、StatefulSet和DaemonSet等
        - CRD
        - Helm Chart
- 命令行
    - 提供kubectl插件
    - 创建/更新/跟踪/删除多集群的资源
    - 像访问本地集群一样与任一子集群进行交互
- Client-go
    - 通过一个wrapper，完成与client-go的集成

## 架构图

![架构图](/images/多集群架构.jpg)

`kme-apiserver` 是一个 **Aggregated apiserver** 服务
- 提供managedclusters APIs, 基于[remotedialer](https://github.com/rancher/remotedialer)实现websockets服务器，来维护子集群的websocket连接
- 提供kubernetes风格API，将请求重定向/代理到每个子集群

`kme-controller-manager` 是一个控制器集合
- 维护`RegisterCluster`和`ManagedCluster`资源信息
- 校验`HelmChart`信息

`kme-agent` 用于更新集群状态，部署服务到子集群
- 报告子集群的状态信息，包括但不限于Kubernetes版本、readyz和livez状态
- 建立一个websocket连接到父集群
- Watch父集群的`Application`和`HelmRelease`资源，在子集群中部署相应服务