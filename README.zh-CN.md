# Ray-Ban Display（greatwhite）

本仓库记录 Ray-Ban Display 固件的文档：系统如何构建、如何启动，以及各部分如何配合。贯穿启动链的线索是 QFPROM 熔丝块。

英文版：[README.md](README.md)

Discord：[discord.gg/oculus](https://discord.gg/oculus) · gdrci（Discord）

## 范围

本仓库描述系统如何构建与启动，不是漏洞研究。文中不包含任何漏洞利用代码，也不包含关于缺陷的结论。固件二进制文件不在本仓库中。

## 目标设备

| 项目 | 值 | 依据 |
|---|---|---|
| 设备 | Meta Ray-Ban Display，代号 `greatwhite` | OTA 元数据中的 `pre-device` |
| OTA | `greatwhite_65394930092600080.zip`，1,439,273,084 字节 | 文件大小 |
| OTA SHA-256 | `6411fd4f52782e576b6ff7662fa3d62e7af838ae64f4843736a8fa1ef67b1068` | 计算得出 |
| 构建版本 | `Meta/greatwhite/greatwhite:14/UKQ1.250303.001/65394930092600080:user/release-keys` | `vbmeta_system` 属性 |
| 安全补丁级别 | 2026-02-05 | `vbmeta_system` 属性 |
| SoC 代号 | `Aurora` | XBL 的 `TME_FW_CHIPSET_STRING`，SBL1 的 `IMAGE_VARIANT_STRING=SocAuroraLAA` |
| 内核 | Linux 5.10.240，ARM64 | 启动镜像中的内核版本横幅 |

## 文档

| 文档 | 英文 | 中文 |
|---|---|---|
| 总览 | [00](docs/00-overview.md) | [00](docs/00-overview.zh-CN.md) |
| 分区布局 | [01](docs/01-package-layout.md) | [01](docs/01-package-layout.zh-CN.md) |
| 启动链 | [02](docs/02-boot-chain.md) | [02](docs/02-boot-chain.zh-CN.md) |
| Android 验证启动 | [03](docs/03-avb-verified-boot.md) | [03](docs/03-avb-verified-boot.zh-CN.md) |
| 内核与厂商分区 | [04](docs/04-android-kernel-and-vendor.md) | [04](docs/04-android-kernel-and-vendor.zh-CN.md) |
| 远程处理器 | [05](docs/05-remote-processors.md) | [05](docs/05-remote-processors.zh-CN.md) |
| QFPROM 与熔丝 | [06](docs/06-qfprom-and-fuses.md) | [06](docs/06-qfprom-and-fuses.zh-CN.md) |
| 无线与连接 | [07](docs/07-wireless-and-connectivity.md) | [07](docs/07-wireless-and-connectivity.zh-CN.md) |
| 外设固件与构建 ID | [08](docs/08-peripheral-firmware-and-build-ids.md) | [08](docs/08-peripheral-firmware-and-build-ids.zh-CN.md) |
| 眼镜端软件与 MCU | [09](docs/09-glasses-software-and-mcu.md) | [09](docs/09-glasses-software-and-mcu.zh-CN.md) |
| QCC730 安全启动参考（外部资料，另一款芯片） | [10](docs/10-qcc730-secure-boot-reference.md) | [10](docs/10-qcc730-secure-boot-reference.zh-CN.md) |
| SELinux 与厂商策略 | [11](docs/11-selinux-and-vendor-policy.md) | [11](docs/11-selinux-and-vendor-policy.zh-CN.md) |
| 音频 | [12](docs/12-audio.md) | [12](docs/12-audio.zh-CN.md) |
| 摄像头与显示用户空间 | [13](docs/13-camera-and-display.md) | [13](docs/13-camera-and-display.zh-CN.md) |
| MCU 控制台、LCoS 与触控 | [14](docs/14-mcu-console-and-lcos.md) | [14](docs/14-mcu-console-and-lcos.zh-CN.md) |
| 音频 DSP 固件（RT700 HiFi4） | [15](docs/15-audio-dsp-firmware.md) | [15](docs/15-audio-dsp-firmware.zh-CN.md) |
| 调制解调器分区：ADSP、CDSP 与可信应用 | [16](docs/16-modem-partition-firmware.md) | [16](docs/16-modem-partition-firmware.zh-CN.md) |
| 证据索引 | [17](docs/17-evidence-index.md) | [17](docs/17-evidence-index.zh-CN.md) |


## 证据标注

- **已验证（Verified）**：直接从头部信息、哈希值、解析出的结构或文件中读取。
- **已观察（Observed）**：字符串、名称或配置值指向某个结论，但对应代码尚未阅读。
- **已推断（Inferred）**：根据名称或上下文得出的结论，并明确标注为推断。
- **未验证（Unverified）**：背景知识或猜测。
