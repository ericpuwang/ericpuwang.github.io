---
title: 使用kubernetes证书保护工作负载
date: 2025-01-16
tags:
- k8s
---

# 介绍
由于稳定版的CertificateSigningRequest API(`certificates.k8s.io/v1`)不允许将`.spec.signerName`设置为`kubernetes.io/legacy-unknown`, 为了使用kubernetes证书保护工作负载, 参考kube-controller-manager中的`certificate controller`实现一个[自定义证书签署者](https://github.com/ericpuwang/certificate-controller.git)。

`cms.io/app-serving`: 该服务证书被API服务器视为有效的服务端证书, 但没有其他保证。`certificate-controller`不会自动批准该证书

- 信任分发: 没有。这个签名者在 Kubernetes 集群中没有标准的信任或分发
- 许可的主体: 全部
- 允许的x509扩展: 允许subjectAltName和key usage扩展，并弃用其他扩展
- 允许的密钥用法: 必须包含`["server auth"]`，但不能包含`["digital signature", "key encipherment", "server auth"]`之外的键
- 过期时间/证书有效期: 1年（默认值和最大值）
- 允许/不允许CA位: 不允许

# 签发证书
> singerName `cms.io/app-serving`

1. 创建私有
```shell
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=apiserver-proxy"
```
2. 创建CertificateSigningRequest
```shell
cat <<EOF | kubectl apply -f -
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: apiserver-proxy
  labels:
    k8s-app: apiserver-proxy
spec:
  groups:
  - system:authenticated
  request: $(cat server.csr | base64 -w 0 | tr -d "\n")
  signerName: cms.io/app-serving
  expirationSeconds: 86400  # one day, default is one year
  usages:
  - server auth
  - digital signature
  - key encipherment
EOF
```
3. 批准CertificateSigningRequest
```shell
kubectl certificate approve apiserver-proxy
```
4. 取得证书
```shell
kubectl get csr apiserver-proxy -o jsonpath='{.status.certificate}'| base64 -d > server.crt
```