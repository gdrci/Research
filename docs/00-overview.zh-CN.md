# 00 - 总览

[English](00-overview.md)

设备的启动顺序是固定的。每个阶段先校验下一个阶段，再把控制权交过去。下表是本分析使用的顺序。顺序尚未确认的地方，文中会注明。

## 启动路径

```
Boot ROM（PBL）                 芯片内部，不在 OTA 中                         未验证
  -> XBL 容器                   xbl.img（978,944 字节），三个程序
       1. 主存根                ELF32 EM_M32，入口 0x2211C000                 ISA 未定
       2. TME 固件              RISC-V，偏移 0x1C2F4                          已验证（字符串）
       3. SBL1                  AArch64，偏移 0x4AFC4，构建于 2026-03-05       已验证（字符串）
       SBL1 使用 SRoT MBNv7 证书链，加载并认证以下镜像
       -> TrustZone（QSEE）     tz.img            EL3 入口已验证
       -> 虚拟化层              hyp.img           内存映射已验证
       -> DevCfg、CPR、SHRM      devcfg.img、shrm.elf（由 SBL1 提到）           已观察
       -> Keymaster、uefisecapp、featenabler                                  已观察
       -> 远程处理器            aop、cpucp、qupfw、dsp、modem、bluetooth        已观察
  -> UEFI                      uefi.img，读取 oem_config.xml（MINK）           已观察
  -> AVB                       vbmeta.img、vbmeta_system.img                  签名已验证
  -> Linux 5.10.240            boot.img + vendor_boot.img                     已验证
  -> init、vendor、system      vendor.img、odm.img、system*.img、product       已验证
  -> 眼镜端服务                MCU HAL、STP、EMG、Smartglass 应用              已观察
```

`uefi.img` 很可能是加载程序。SBL1 的子系统列表和镜像名表中有 `uefi` 与 `APPSBL`，`uefi.img` 是 UEFI DXE 卷，而 `abl.img` 中没有相应字符串。跳转到加载程序的代码尚未反编译。第 02 节说明了证据。

## XBL 容器

`xbl.img` 并不是一个加载程序，而是包含三个程序，每个都有自己的 ELF 头部。SBL1 程序完成主要工作。TME 程序是 RISC-V 固件，SBL1 与 PBL 调用它进行认证。第一个程序是一个小型存根，其机器字段是标准架构都不使用的值。第 02 节分别介绍了这三个程序，第 07 节说明如何导入。

## 熔丝在哪里出现

QFPROM 是位于 `0x221C8000` 的熔丝块，窗口大小为 4 KB。从内核的角度看它是只读的，设备树对它有描述。有三处代码读取它：

- 内核，通过 `nvmem_qfprom` 驱动（内核配置 `CONFIG_QCOM_QFPROM=m`）；
- GPU 驱动，读取偏移 `0x119` 处的 `gpu_speed_bin` 字段，以选择工作点；
- 安全世界，其中包含 `qsee_fuse_read`、`qsee_fuse_write` 以及软件熔丝相关函数。

SBL1 中有一处直接引用该地址，位于构建启动内存映射的代码中。虚拟化层将该块映射为三页。第 06 节有详细说明。

## 两个 Android 版本

启动镜像、`vendor` 和 `odm` 带有 Android 12 的指纹（`SQ3A.220605.009.A1`）。`system`、`system_ext` 和 `product` 是 Android 14（`UKQ1.250303.001`）。厂商侧基于较旧的 Treble 底座，上面运行较新的框架。第 04 节讨论了其影响。

## 围绕 SoC 的眼镜部件

系统中有几个部分运行在应用处理器之外。一个微控制器（MCU）负责传感器、按键、铰链和充电盒，它通过一种名为 STP 的传输与系统通信。来自腕带的肌电（EMG）输入经由 EMG 服务到达手机端软件。第 09 节介绍了这些内容。硬件还分为两种音频编解码器变体，RT600 与 RT700，软件在启动时进行检测。

## 文档索引

| 文档 | 内容 |
|---|---|
| [01](01-package-layout.zh-CN.md) | OTA 格式、分区、哈希 |
| [02](02-boot-chain.zh-CN.md) | 逐阶段分析，包括 XBL 容器 |
| [03](03-avb-verified-boot.zh-CN.md) | vbmeta 描述符、签名、哈希校验、回滚索引 |
| [04](04-android-kernel-and-vendor.zh-CN.md) | 内核、ramdisk、fstab、模块、覆盖层、bootconfig |
| [05](05-remote-processors.zh-CN.md) | AOP、CPUCP、SHRM、QUP、DSP、基带、蓝牙 |
| [06](06-qfprom-and-fuses.zh-CN.md) | 熔丝块、内存映射、读取者 |
| [09](09-glasses-software-and-mcu.zh-CN.md) | MCU、STP、RT600/RT700、EMG 腕带、应用层 |
| [07](07-wireless-and-connectivity.zh-CN.md) | Wi-Fi 与蓝牙协议栈、WPSS 子系统、驱动、HAL、固件 |
| [08](08-peripheral-firmware-and-build-ids.zh-CN.md) | 构建 ID、GPU、摄像头、视频与视觉固件 |
| [11](11-evidence-index.zh-CN.md) | 各章节使用的 `data/` 目录 |
