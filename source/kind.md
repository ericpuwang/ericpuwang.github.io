# 使用KIND创建K8S集群

## 安装kind

```shell
go install sigs.k8s.io/kind@v0.24.0
```

## 编译容器网络插件

```shell
mkdir -p /opt/kind
git clone https://github.com/containernetworking/plugins.git /opt/kind/plugins
cd /opt/kind/plugins
# 编译linux容器CNI
bash build_linux.sh
```

## 创建集群

### 集群配置
> 禁用kind提高的默认cni `kindnet`

```yaml
# 文件路径: /opt/kind/config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry]
    config_path = "/etc/containerd/certs.d"
nodes:
- role: control-plane
  image: kindest/node:v1.28.13@sha256:45d319897776e11167e4698f6b14938eb4d52eb381d9e3d7a9086c16c69a8110
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  - |
    kind: ClusterConfiguration
    apiServer:
        extraArgs:
          enable-admission-plugins: NamespaceLifecycle,LimitRanger,ServiceAccount,NodeRestriction,MutatingAdmissionWebhook,ValidatingAdmissionWebhook,ResourceQuota
  extraPortMappings:
  - containerPort: 30080
    hostPort: 80
  - containerPort: 30443
    hostPort: 443
  extraMounts:
  - hostPath: /opt/kind/plugins/bin
    containerPath: /opt/cni/bin
- role: worker
  image: kindest/node:v1.28.13@sha256:45d319897776e11167e4698f6b14938eb4d52eb381d9e3d7a9086c16c69a8110
  extraMounts:
  - hostPath: /opt/kind/plugins/bin
    containerPath: /opt/cni/bin
- role: worker
  image: kindest/node:v1.28.13@sha256:45d319897776e11167e4698f6b14938eb4d52eb381d9e3d7a9086c16c69a8110
  extraMounts:
  - hostPath: /opt/kind/plugins/bin
    containerPath: /opt/cni/bin
- role: worker
  image: kindest/node:v1.28.13@sha256:45d319897776e11167e4698f6b14938eb4d52eb381d9e3d7a9086c16c69a8110
  extraMounts:
  - hostPath: /opt/kind/plugins/bin
    containerPath: /opt/cni/bin
```

### 创建集群
```shell
kind create cluster --config /opt/kind/config.yaml
```

## K8S CNI
> 本文使用kube-flannel cni

```shell
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

<font style="color: red">**PS:**</font> kind创建的集群中podCIDR为`10.244.0.0/16`。如果修改了kind集群的默认podCIDR，则需要下载上述清单并修改网络以匹配集群中的pod网络。

# Docker Registry
> 参考文档: https://kind.sigs.k8s.io/docs/user/local-registry/

```bash
#!/bin/sh
set -o errexit

# 1. Create registry container unless it already exists
reg_name='kind-registry'
reg_port='5001'
if [ "$(docker inspect -f '{{.State.Running}}' "${reg_name}" 2>/dev/null || true)" != 'true' ]; then
  docker run \
    -d --restart=always -p "127.0.0.1:${reg_port}:5000" --network bridge --name "${reg_name}" \
    registry:2
fi

# 2. Add the registry config to the nodes
#
# This is necessary because localhost resolves to loopback addresses that are
# network-namespace local.
# In other words: localhost in the container is not localhost on the host.
#
# We want a consistent name that works from both ends, so we tell containerd to
# alias localhost:${reg_port} to the registry container when pulling images
REGISTRY_DIR="/etc/containerd/certs.d/localhost:${reg_port}"
for node in $(kind get nodes); do
  docker exec "${node}" mkdir -p "${REGISTRY_DIR}"
  cat <<EOF | docker exec -i "${node}" cp /dev/stdin "${REGISTRY_DIR}/hosts.toml"
[host."http://${reg_name}:5000"]
EOF
done

# 3. Connect the registry to the cluster network if not already connected
# This allows kind to bootstrap the network but ensures they're on the same network
if [ "$(docker inspect -f='{{json .NetworkSettings.Networks.kind}}' "${reg_name}")" = 'null' ]; then
  docker network connect "kind" "${reg_name}"
fi

# 4. Document the local registry
# https://github.com/kubernetes/enhancements/tree/master/keps/sig-cluster-lifecycle/generic/1755-communicating-a-local-registry
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: local-registry-hosting
  namespace: kube-public
data:
  localRegistryHosting.v1: |
    host: "localhost:${reg_port}"
    help: "https://kind.sigs.k8s.io/docs/user/local-registry/"
EOF
```

## 镜像加速

```bash
#!/bin/sh
set -o errexit

# Add the registry config to the nodes
REGISTRY_DIR="/etc/containerd/certs.d/docker.io"
for node in $(kind get nodes); do
  docker exec "${node}" mkdir -p "${REGISTRY_DIR}"
  cat <<EOF | docker exec -i "${node}" cp /dev/stdin "${REGISTRY_DIR}/hosts.toml"
server = "https://registry-1.docker.io"

[host."https://docker.m.daocloud.io"]
[host."https://dockerproxy.com"]
EOF
done
```