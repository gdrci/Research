# 01 - 分区布局

[English](01-package-layout.md)

## OTA 文件

OTA 是标准的 Android A/B 全量升级包。

| 项目 | 值 |
|---|---|
| 文件 | `greatwhite_65394930092600080.zip` |
| 大小 | 1,439,273,084 字节 |
| SHA-256 | `6411fd4f52782e576b6ff7662fa3d62e7af838ae64f4843736a8fa1ef67b1068` |
| 内容 | `payload.bin`（1,439,266,670 字节）、`payload_properties.txt`、`care_map.pb`、`apex_info.pb`、`META-INF/` |
| 签名 | SignApk（`META-INF/com/android/otacert`） |
| 升级类型 | `ota-type=AB` |

`payload_properties.txt` 给出了 payload 自身的哈希与大小，其中 `METADATA_SIZE=97215`。元数据记录了目标版本：

```
pre-device=greatwhite
post-build=Meta/greatwhite/greatwhite:14/UKQ1.250303.001/65394930092600080:user/release-keys
post-sdk-level=34
post-security-patch-level=2026-02-05
post-timestamp=1780360088
```

`post-timestamp` 为 1780360088，换算为 UTC 时间是 2026 年 6 月 2 日 00:28:08（即太平洋时间 6 月 1 日 17:28）。启动镜像 `build.prop` 中的构建时间为 `Mon Jun 1 17:31:45 PDT 2026`，即 UTC 6 月 2 日 00:31:45，相差约三分钟，两者一致。

`payload.bin` 是全量 payload，而不是增量包。在没有原始镜像的情况下，`payload-dumper` 即可完整解出，因此每个分区都是完整的。33 个分区全部解出，每个镜像都计算了哈希。清单见 `data/inventory.json`，表格见 `data/partition_table.md`。

## 分区分组

| 分组 | 分区 | 容器格式 |
|---|---|---|
| 高通启动链 | `xbl`、`xbl_config`、`xbl_ramdump`、`abl`、`uefi`、`uefisecapp`、`imagefv` | ELF |
| 安全世界 | `tz`、`hyp`、`devcfg`、`keymaster`、`featenabler`、`multiimgqti`、`multiimgoem` | ELF |
| 远程处理器 | `aop`、`aop_config`、`cpucp`、`shrm`、`qupfw`、`dsp`、`modem`、`bluetooth` | ELF（RISC-V、Hexagon、ARM）、ext4、FAT |
| Android 启动 | `vbmeta`、`vbmeta_system`、`boot`、`dtbo`、`vendor_boot`、`recovery` | AVB、boot v4、DTBO |
| Android 文件系统 | `system`、`system_ext`、`product`、`vendor`、`odm` | ext4、dm-verity |

## 影响分析的容器细节

**`xbl.img` 是一个容器。** 它首尾相接地包含三个 ELF 程序：偏移 0 处的存根，`0x1C2F4` 处的 RISC-V TME 固件，以及 `0x4AFC4` 处的 AArch64 SBL1（第 02 节）。外层头部只描述存根。

**XBL 外层头部的机器字段不寻常。** 偏移 0 处的存根是 32 位 ELF，其 `e_machine` 为 1（`EM_M32`）。`xbl_config.img` 是 64 位 ELF，同样的值。标准的 ARM、AArch64 和 Hexagon 都使用其他值。加载器可能并不读取这个字段，因此这很可能是高通的约定，但我还没有在另一份高通 XBL 上核对过。

**`uefi.img` 的 ELF 类别不统一。** 它是 64 位 ELF，`e_machine = EM_ARM`（40）。ARM64 镜像通常使用 `EM_AARCH64`（183）。加载器可能忽略这个字段，也可能该镜像实际以 ARM32 代码运行。此点未定。

**高通段标志。** 多个 ELF 镜像含有 `PT_NULL` 头，其 `p_flags` 的高位有值（`0x2000000`、`0x7000000`）。这些是高通镜像格式中的哈希段和签名段，不是代码。`data/ghidra/import_map.json` 中的加载段表已排除它们。

**远程处理器镜像不全是 ELF。** `dsp.img` 是 ext4，`modem.img` 和 `bluetooth.img` 是 FAT。第一阶段 fstab 在运行时挂载它们。见第 05 节。

**镜像集合中没有 PBL。** 第一级引导程序位于 SoC 的掩膜 ROM 中，所以 OTA 不包含它。这是高通的标准做法，但我还没有在本设备上验证。

## 值得注意的数值

- 两个 vbmeta 镜像中的 `rollback_index=1770249600`。这是 2026 年 2 月 5 日 00:00 UTC 的 Unix 时间，与安全补丁级别是同一天。第 03 节有进一步说明。
- `vbmeta` 镜像为 8,192 字节，`vbmeta_system` 为 4,096 字节。
- `boot.img` 在磁盘上为 100,663,296 字节，但参与哈希计算的大小是 30,208,000 字节，其余为填充。
