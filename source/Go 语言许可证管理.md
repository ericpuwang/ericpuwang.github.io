---
title: Go语言许可证管理模块实践
date: 2025-07-26
tags:
- golang
---

# 基于Golang的许可证管理
> 在 Go 语言中实现一个安全、高效的许可证管理模块需要考虑多个方面，包括许可证生成、签名、验证、存储和吊销等核心功能

## 许可证数据结构设计
```go
// License 许可证结构
type License struct {
    ID              string            `json:"id"`               // 许可证ID
    CustomerID      string            `json:"customer_id"`      // 客户ID
    IssueDate       time.Time         `json:"issue_date"`       // 发行日期
    ExpireDate      time.Time         `json:"expire_date"`      // 过期日期
    Features        map[string]int    `json:"features"`         // 功能权限映射
    RateLimits      map[string]int    `json:"rate_limits"`      // API速率限制
    HardwareBinding string            `json:"hardware_binding"` // 硬件绑定信息
    Signature       string            `json:"signature"`        // 数字签名
}

// Feature 功能权限常量
const (
    FeatureBasic    = "basic"
    FeatureAdvanced = "advanced"
    FeaturePro      = "pro"
)
```

## 许可证生成和签名

> 许可证生成模块负责创建许可证并使用私钥进行签名

```go
// Generator 许可证生成器
type Generator struct {
    privateKey *rsa.PrivateKey
}

// NewGenerator 创建许可证生成器
func NewGenerator(privateKey *rsa.PrivateKey) *Generator {
    return &Generator{privateKey: privateKey}
}

// GenerateLicense 生成新许可证
func (g *Generator) GenerateLicense(
    id, customerID string,
    issueDate, expireDate time.Time,
    features map[string]int,
    rateLimits map[string]int,
    hardwareID string,
) (*License, error) {
    license := &License{
        ID:              id,
        CustomerID:      customerID,
        IssueDate:       issueDate,
        ExpireDate:      expireDate,
        Features:        features,
        RateLimits:      rateLimits,
        HardwareBinding: hardwareID,
    }

    // 生成签名
    err := g.sign(license)
    if err != nil {
        return nil, err
    }

    return license, nil
}

// sign 对许可证进行签名
func (g *Generator) sign(license *License) error {
    // 移除签名字段后序列化
    licenseBytes, err := json.Marshal(struct {
        ID              string            `json:"id"`
        CustomerID      string            `json:"customer_id"`
        IssueDate       time.Time         `json:"issue_date"`
        ExpireDate      time.Time         `json:"expire_date"`
        Features        map[string]int    `json:"features"`
        RateLimits      map[string]int    `json:"rate_limits"`
        HardwareBinding string            `json:"hardware_binding"`
    }{
        ID:              license.ID,
        CustomerID:      license.CustomerID,
        IssueDate:       license.IssueDate,
        ExpireDate:      license.ExpireDate,
        Features:        license.Features,
        RateLimits:      license.RateLimits,
        HardwareBinding: license.HardwareBinding,
    })

    if err != nil {
        return err
    }

    // 计算哈希
    hash := sha256.Sum256(licenseBytes)

    // 使用RSA PKCS#1 v1.5进行签名
    signature, err := rsa.SignPKCS1v15(
        nil,
        g.privateKey,
        crypto.SHA256,
        hash[:],
    )

    if err != nil {
        return err
    }

    // 转换为Base64编码
    license.Signature = base64.StdEncoding.EncodeToString(signature)
    return nil
}

// Generator 许可证生成器
type Generator struct {
    privateKey *rsa.PrivateKey
}

// NewGenerator 创建许可证生成器
func NewGenerator(privateKey *rsa.PrivateKey) *Generator {
    return &Generator{privateKey: privateKey}
}

// GenerateLicense 生成新许可证
func (g *Generator) GenerateLicense(
    id, customerID string,
    issueDate, expireDate time.Time,
    features map[string]int,
    rateLimits map[string]int,
    hardwareID string,
) (*License, error) {
    license := &License{
        ID:              id,
        CustomerID:      customerID,
        IssueDate:       issueDate,
        ExpireDate:      expireDate,
        Features:        features,
        RateLimits:      rateLimits,
        HardwareBinding: hardwareID,
    }

    // 生成签名
    err := g.sign(license)
    if err != nil {
        return nil, err
    }

    return license, nil
}

// sign 对许可证进行签名
func (g *Generator) sign(license *License) error {
    // 移除签名字段后序列化
    licenseBytes, err := json.Marshal(struct {
        ID              string            `json:"id"`
        CustomerID      string            `json:"customer_id"`
        IssueDate       time.Time         `json:"issue_date"`
        ExpireDate      time.Time         `json:"expire_date"`
        Features        map[string]int    `json:"features"`
        RateLimits      map[string]int    `json:"rate_limits"`
        HardwareBinding string            `json:"hardware_binding"`
    }{
        ID:              license.ID,
        CustomerID:      license.CustomerID,
        IssueDate:       license.IssueDate,
        ExpireDate:      license.ExpireDate,
        Features:        license.Features,
        RateLimits:      license.RateLimits,
        HardwareBinding: license.HardwareBinding,
    })

    if err != nil {
        return err
    }

    // 计算哈希
    hash := sha256.Sum256(licenseBytes)

    // 使用RSA PKCS#1 v1.5进行签名
    signature, err := rsa.SignPKCS1v15(
        nil,
        g.privateKey,
        crypto.SHA256,
        hash[:],
    )

    if err != nil {
        return err
    }

    // 转换为Base64编码
    license.Signature = base64.StdEncoding.EncodeToString(signature)
    return nil
}
```

## 许可证验证

> 验证模块负责检查许可证的有效性和权限

```go
// Validator 许可证验证器
type Validator struct {
    publicKey *rsa.PublicKey
}

// NewValidator 创建许可证验证器
func NewValidator(publicKey *rsa.PublicKey) *Validator {
    return &Validator{publicKey: publicKey}
}

// Validate 验证许可证
func (v *Validator) Validate(license *License, hardwareID string) error {
    // 1. 验证签名
    err := v.verifySignature(license)
    if err != nil {
        return fmt.Errorf("签名验证失败: %v", err)
    }

    // 2. 检查有效期
    now := time.Now()
    if now.Before(license.IssueDate) {
        return errors.New("许可证尚未生效")
    }

    if now.After(license.ExpireDate) {
        return errors.New("许可证已过期")
    }

    // 3. 验证硬件绑定（如果有）
    if license.HardwareBinding != "" && license.HardwareBinding != hardwareID {
        return errors.New("硬件绑定验证失败")
    }

    return nil
}

// verifySignature 验证许可证签名
func (v *Validator) verifySignature(license *License) error {
    // 移除签名字段后序列化
    licenseBytes, err := json.Marshal(struct {
        ID              string            `json:"id"`
        CustomerID      string            `json:"customer_id"`
        IssueDate       time.Time         `json:"issue_date"`
        ExpireDate      time.Time         `json:"expire_date"`
        Features        map[string]int    `json:"features"`
        RateLimits      map[string]int    `json:"rate_limits"`
        HardwareBinding string            `json:"hardware_binding"`
    }{
        ID:              license.ID,
        CustomerID:      license.CustomerID,
        IssueDate:       license.IssueDate,
        ExpireDate:      license.ExpireDate,
        Features:        license.Features,
        RateLimits:      license.RateLimits,
        HardwareBinding: license.HardwareBinding,
    })

    if err != nil {
        return err
    }

    // 计算哈希
    hash := sha256.Sum256(licenseBytes)

    // 解码签名
    signature, err := base64.StdEncoding.DecodeString(license.Signature)
    if err != nil {
        return err
    }

    // 验证签名
    return rsa.VerifyPKCS1v15(
        v.publicKey,
        crypto.SHA256,
        hash[:],
        signature,
    )
}

// HasFeature 检查是否有特定功能权限
func (v *Validator) HasFeature(license *License, feature string, minLevel int) bool {
    level, exists := license.Features[feature]
    return exists && level >= minLevel
}
```

## 硬件指纹采集

> 硬件指纹模块用于生成和验证设备唯一标识

```go
// Hardware 硬件信息采集器
type Hardware struct{}

// NewHardware 创建硬件信息采集器
func NewHardware() *Hardware {
    return &Hardware{}
}

// GetHardwareID 获取硬件唯一标识
func (h *Hardware) GetHardwareID() (string, error) {
    var parts []string

    // 1. 获取CPU信息
    cpuInfo, err := ioutil.ReadFile("/proc/cpuinfo")
    if err == nil {
        parts = append(parts, string(cpuInfo))
    }

    // 2. 获取主板信息
    boardInfo, err := ioutil.ReadFile("/sys/class/dmi/id/board_serial")
    if err == nil {
        parts = append(parts, string(boardInfo))
    }

    // 3. 获取网络接口信息
    ifaces, err := net.Interfaces()
    if err == nil {
        for _, iface := range ifaces {
            if iface.Flags&net.FlagUp != 0 && iface.HardwareAddr.String() != "" {
                parts = append(parts, iface.HardwareAddr.String())
                break
            }
        }
    }

    if len(parts) == 0 {
        return "", errors.New("无法获取硬件信息")
    }

    // 计算哈希
    hash := sha256.Sum256([]byte(strings.Join(parts, "|")))
    return hex.EncodeToString(hash[:]), nil
}
```

## 许可证存储和加载

> 安全地存储和加载许可证

```go
// Storage 许可证存储接口
type Storage interface {
    Save(license *License) error
    Load() (*License, error)
    Delete() error
}

// FileStorage 文件存储实现
type FileStorage struct {
    path   string
    cipher *aesCipher // 加密器
}

// NewFileStorage 创建文件存储
func NewFileStorage(path string, encryptionKey []byte) (*FileStorage, error) {
    cipher, err := newAesCipher(encryptionKey)
    if err != nil {
        return nil, err
    }

    return &FileStorage{
        path:   path,
        cipher: cipher,
    }, nil
}

// Save 保存许可证到文件
func (fs *FileStorage) Save(license *License) error {
    licenseBytes, err := json.Marshal(license)
    if err != nil {
        return err
    }

    // 加密许可证
    encrypted, err := fs.cipher.Encrypt(licenseBytes)
    if err != nil {
        return err
    }

    // 写入文件
    return ioutil.WriteFile(fs.path, encrypted, 0600)
}

// Load 从文件加载许可证
func (fs *FileStorage) Load() (*License, error) {
    // 读取文件
    encrypted, err := ioutil.ReadFile(fs.path)
    if err != nil {
        return nil, err
    }

    // 解密
    licenseBytes, err := fs.cipher.Decrypt(encrypted)
    if err != nil {
        return nil, err
    }

    // 解析许可证
    var license License
    err = json.Unmarshal(licenseBytes, &license)
    if err != nil {
        return nil, err
    }

    return &license, nil
}

// Delete 删除许可证文件
func (fs *FileStorage) Delete() error {
    return os.Remove(fs.path)
}
```

## 许可证安全管理建议

### 秘钥管理

- 秘钥应在HSM中生成和存储
- 公钥应该通过安全通道分发, 例如mtls
- 定时轮换秘钥对

### 许可证存储

- 使用强加密存储许可证文件
- 考虑分片存储等方案
- 限制许可证文件访问权限

### 代码安全

- 代码混淆 [burrowers/garble](https://github.com/burrowers/garble)
- 防篡改技术保护核心代码
- 日志脱敏