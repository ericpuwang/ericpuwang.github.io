# Go Redis使用可重入锁支持选主

## 分析
对于资源共享需求较低的场景，可以使用有时效性的**互斥锁**，可以实现选主功能。可以参考[<span style="color: red">K8S选主机制</span>](高可用模式下的选主机制.md)

## 方案

### 定义选主对象
> 选主锁使用带有时效的Redis互斥锁, 只有得到该互斥锁，才能执行程序

```go
type LeaderElector struct {
	config   LeaderElectionConfig
	lock     *lock.RedisLock
	isLeader bool
}
```

### 执行选主逻辑，并启动服务

```go
func (le *LeaderElector) Run(ctx context.Context) {
	defer lock.HandleCrash()
	defer func() {
		if le.config.Callbacks.OnStoppedLeading != nil {
			le.config.Callbacks.OnStoppedLeading(ctx)
		}
	}()

	if !le.acquire(ctx) {
		// 取消上下文
		return
	}

	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	go le.config.Callbacks.OnStartedLeading(ctx)
	le.renew(ctx)
}
```

## 示例

```go
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"time"

	"github.com/CodeNinja917/leaderelection"
	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

func main() {
	var (
		redisAddr string
		lockName  string
		id        string
	)
	flag.StringVar(&redisAddr, "redis-addr", "localhost:6379", "redis addr")
	flag.StringVar(&lockName, "lock-name", "", "the lease lock resource name")
	flag.StringVar(&id, "id", uuid.New().String(), "the holder identify name")
	flag.Parse()

	cfg := leaderelection.LeaderElectionConfig{
		RedisConfig: redis.Options{Addr: redisAddr},
		Callbacks: leaderelection.LeaderCallbacks{
			OnStartedLeading: func(ctx context.Context) {
				for {
					select {
					case <-ctx.Done():
						return
					default:
						time.Sleep(10 * time.Second)
						fmt.Println("Controller loop...")
					}
				}
			},
			OnStoppedLeading: func(ctx context.Context) {
				fmt.Printf("leader lost: %s\n", id)
				os.Exit(0)
			},
			OnNewLeader: func(identity string) {
				if identity == id {
					return
				}
				fmt.Printf("new leader elected: %s\n", identity)
			},
		},
		ReleaseOnCancel: true,
		Identity:        id,
		Key:             lockName,
	}
	ctx := context.Background()
	le, err := leaderelection.NewLeaderElector(ctx, cfg)
	if err != nil {
		fmt.Printf("ERROR: %v\n", err)
		return
	}
	le.Run(ctx)
}
```