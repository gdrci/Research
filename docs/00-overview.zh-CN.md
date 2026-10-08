# 00 - 总览

[English](00-overview.md)

设备的启动顺序是固定的。每个阶段先校验下一个阶段，再把控制权交过去。下表是本分析使用的顺序。顺序尚未确认的地方，文中会注明。

## 启动路径

```
Boot ROM（PBL）                 芯片内部，不在 OTA 中                         未验证
  -> XBL 容器                   xbl.img（978,944 字节），三个程序
       1. 主存根                ELF32 EM_M32，入口 0x2211C000                 ISA 未定
       2. TME 固件              RISC-V，偏移 0x1C2F4                          头部已验证；身份为观察所得（字符串）
       3. SBL1                  AArch64，偏移 0x4AFC4，构建于 2026-03-05       头部已验证；构建日期为观察所得（字符串）
       SBL1 预计使用 SRoT MBNv7 证书链加载并认证以下镜像（推断；读取的代码中没有此顺序）
       -> TrustZone（QSEE）     tz.img            EL3 入口已验证
       -> 虚拟化层              hyp.img           内存映射已验证
       -> DevCfg、CPR、SHRM      devcfg.img、shrm.elf（由 SBL1 提到）           已观察
       -> Keymaster、uefisecapp、featenabler                                  已观察
       -> 远程处理器            aop、cpucp、qupfw、dsp、modem、bluetooth        已观察
  -> UEFI                      uefi.img，读取 oem_config.xml（MINK）           已观察
  -> AVB                       vbmeta.img、vbmeta_system.img                  签名已验证
  -> Linux 5.10.240            boot.img + vendor_boot.img                     头部已验证；启动横幅为观察所得
  -> init、vendor、system      vendor.img、odm.img、system*.img、product       文件系统已验证；init 为推断
  -> 眼镜端服务                MCU HAL、STP、EMG、Smartglass 应用              已观察
```

`uefi.img` 很可能是加载程序。SBL1 的子系统列表和镜像名表中有 `uefi` 与 `APPSBL`，`uefi.img` 是 UEFI DXE 卷，而 `abl.img` 中没有相应字符串。跳转到加载程序的代码尚未反编译。第 02 节说明了证据。

## XBL 容器

`xbl.img` 并不是一个加载程序，而是包含三个程序，每个都有自己的 ELF 头部。SBL1 程序完成主要工作。TME 程序是 RISC-V 固件，SBL1 与 PBL 调用它进行认证。第一个程序是一个小型存根，其机器字段值（EM_M32，1）不被该容器的三个程序中的任何一个使用。第 02 节分别介绍了这三个程序，。

## 熔丝在哪里出现

QFPROM 是位于 `0x221C8000` 的熔丝块，窗口大小为 4 KB。从内核的角度看它是只读的，设备树对它有描述。有三处代码读取它：

- 内核，通过 `nvmem_qfprom` 驱动（内核配置 `CONFIG_QCOM_QFPROM=m`）；
- `gpu_speed_bin` 字段位于字节 `0x119`，由节点 `/soc/qfprom@0`（`qcom,qfprom-sys`）使用；读取它的 GPU 驱动未确认；
- 安全世界，其中包含 `qsee_fuse_read`、`qsee_fuse_write` 以及软件熔丝相关函数。

SBL1 中有一处直接引用该地址，位于构建启动内存映射的代码中。虚拟化层将该块映射为三页。第 06 节有详细说明。

## 两个 Android 版本

启动镜像、`vendor` 和 `odm` 带有 Android 12 的指纹（`SQ3A.220605.009.A1`）。`system`、`system_ext` 和 `product` 是 Android 14（`UKQ1.250303.001`）。厂商侧基于较旧的 Treble 底座，上面运行较新的框架。第 04 节讨论了其影响。

## 围绕 SoC 的眼镜部件

系统中有几个部分运行在应用处理器之外。一个微控制器（MCU）负责传感器、按键、铰链和充电盒，它通过一种名为 STP 的传输与系统通信。来自腕带的肌电（EMG）输入经由 EMG 服务到达手机端软件。第 09 节介绍了这些内容。硬件还分为两种音频编解码器变体，RT600 与 RT700，按产品和板型列出。软件在启动时如何选择，尚未确定。

## 文档索引

| 文档 | 内容 |
|---|---|
| [01](01-package-layout.zh-CN.md) | OTA 格式、分区、哈希 |
| [02](02-boot-chain.zh-CN.md) | 逐阶段分析，包括 XBL 容器 |
| [03](03-avb-verified-boot.zh-CN.md) | vbmeta 描述符、签名、哈希校验、回滚索引 |
| [04](04-android-kernel-and-vendor.zh-CN.md) | 内核、ramdisk、fstab、模块、覆盖层、bootconfig |
| [05](05-remote-processors.zh-CN.md) | AOP、CPUCP、SHRM、QUP、DSP、基带、蓝牙 |
| [06](06-qfprom-and-fuses.zh-CN.md) | 熔丝块、内存映射、读取者 |
| [07](07-wireless-and-connectivity.zh-CN.md) | Wi-Fi 与蓝牙协议栈、WPSS 子系统、驱动、HAL、固件 |
| [08](08-peripheral-firmware-and-build-ids.zh-CN.md) | 构建 ID、GPU、摄像头、视频与视觉固件 |
| [09](09-glasses-software-and-mcu.zh-CN.md) | MCU、STP、RT600/RT700、EMG 腕带、应用层 |
| [10](10-qcc730-secure-boot-reference.zh-CN.md) | 外部 QCC730 安全启动参考（另一款芯片） |
| [11](11-selinux-and-vendor-policy.zh-CN.md) | 厂商 SELinux 策略、上下文、seapp 与签名者 |
| [12](12-audio.zh-CN.md) | 音频协议栈、LPASS、后端、混音器路径、策略、音效、ACDB |
| [13](13-camera-and-display.zh-CN.md) | 摄像头与显示的服务、库、调校、面板 |
| [14](14-mcu-console-and-lcos.zh-CN.md) | MCU 控制台、LCoS 控制器、触控、IMU、ALS 与子镜像布局 |
| [15](15-audio-dsp-firmware.zh-CN.md) | RT700 HiFi4 DSP：唤醒词、听力、扬声器模型、麦克风 |
| [16](16-modem-partition-firmware.zh-CN.md) | ADSP、CDSP、可信应用及其签名链 |
| [17](17-chip-inventory.zh-CN.md) | 集成电路：SoC、PMIC、功放、传感器、连接，附依据与可信度 |
| [19](19-emulation-reference.zh-CN.md) | 处理器、入口点、地址、总线器件与模拟开放项 |
| [18](18-evidence-index.zh-CN.md) | 每个证据文件及引用它的章节 |
