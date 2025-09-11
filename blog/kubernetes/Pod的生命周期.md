# Pod的生命周期

> 本文主要介绍kubelet如何通过`syncloop`和`podworker`管理Pod的生命周期，以及如何通过CRI接口与container runtime交互

##