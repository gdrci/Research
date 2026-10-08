# 13 - 证据索引

[English](13-evidence-index.md)

本索引将 `data/` 下的每个目录对应到使用它的章节。章节在文件对结论至关重要时会按文件名引用证据；其他文件是某一主题的原始输出，按主题引用。两类都列在这里，便于读者找到任一结论的出处。

计数以撰写时的仓库为准。

| 目录 | 文件数 | 使用章节 | 内容 |
|---|---:|---|---|
| `data/inventory.json` | 1 | 01 | 每个镜像的 SHA-256、大小以及 ELF 或 FAT 头信息 |
| `data/partition_table.md`、`.zh-CN.md` | 2 | 01 | 来自 OTA 元数据的分区表 |
| `data/qfprom_literal_candidates.json` | 1 | 06 | 跨镜像扫描 QFPROM 地址字面量的结果 |
| `data/analysis/` | 4 | 02、05 | ISA 与解码器测试：Thumb、ARM、QUP 解码与 DSP 校准。这些是否定结果，作为记录保留。 |
| `data/android/` | 13 | 04 | 内核配置、安全选项、板型 ID、启动配置、fstab、`build.prop`、设备树转储、模块列表。`wpss_dt_nodes.txt` 被第 11 章使用。 |
| `data/avb/` | 3 | 03 | `vbmeta` 摘要、校验结果、哈希树重建 |
| `data/ghidra/` | 18 | 02、03、06 | SBL1、UEFI 与 TrustZone 的反编译函数，导入映射，以及 XBL 与 AOP 入口反汇编。第 02 与 06 章按函数地址引用。 |
| `data/remote/` | 8 | 05、11、12 | 调制解调器、蓝牙与 DSP 的 FAT 列表，调制解调器构建清单，以及蓝牙版本文件 |
| `data/secure/` | 25 | 06 | 熔丝与安全启动证据：TrustZone 对象与分发表、MMIO 表、PK 哈希路径、PIL 防回滚熔丝表、线程块设置函数、UEFI 熔丝区域表、featenabler 摘要、keymaster 字符串 |
| `data/strings/` | 20 | 00、02、06 | 每个镜像的 `strings` 输出。大多数基于名称的结论来源于此。 |
| `data/userspace/` | 9 | 04、09、11、12 | init 脚本、厂商固件列表、`.tub` 内容与 md5 测试、MCU HAL 名称、SmartGlass 应用、Wi-Fi 与蓝牙配置、外设固件头部 |
| `data/xbl/` | 6 | 02、06、11 | XBL 容器布局、SBL1 内存映射与 QFPROM 引用、TME 扫描、WPSS 配置节 |

## 章节中未按名称引用的文件

这些文件同样是证据，但使用它们的章节按主题描述，而非逐一点名：

- `data/strings/*.txt`：各镜像的字符串。第 00、02 章引用的是镜像，而非每个文件。
- `data/ghidra/*_decompiled.txt`：第 02 与 06 章按函数地址引用。
- `data/secure/tz_mmio_table.tsv`、`hyp_mmio_map.tsv`：第 06 章计数背后的完整表格。
- `data/android/security_options.tsv`、`board_component_matrix.tsv`、`overlay_components.tsv`：第 04 章用于内核选项与覆盖层检查。

## 工具

生成这些文件的脚本不属于本仓库，仓库中保留的是输出结果。
