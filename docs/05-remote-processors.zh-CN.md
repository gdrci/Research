# 05 - 远程处理器及其固件

[English](05-remote-processors.md)

SoC 除了应用处理器之外还有若干处理器，每个都运行自己的固件。预期启动链会加载其中一部分，内核则预期从厂商分区加载另外一些；加载路径未经追踪。本文根据头部信息、字符串和文件列表进行识别。目前只有两个小规模的反汇编样本：AOP 入口的 12 条指令 Ghidra 反汇编（`data/ghidra/aop_entry_thumb2_disasm.txt`），以及 `qupfw.img` 的 Ghidra Hexagon 解码。其他镜像均未反汇编。

| 处理器 | 镜像 | 格式 | 状态 |
|---|---|---|---|
| 常开处理器（AOP） | `aop.img`、`aop_config.img` | ELF32，ARM | 根据字符串识别 |
| CPU 控制处理器（CPUCP） | `cpucp.img` | ELF32，RISC-V | 已识别，已读取启动字符串 |
| 共享资源管理器（SHRM） | `shrm.img` | ELF32，RISC-V | 已识别，已读取 DDR 固件版本 |
| QUP 固件 | `qupfw.img` | ELF32，Hexagon（`EM_QDSP6`） | 确认为 Hexagon，作用未知 |
| 音频与计算 DSP | `dsp.img` | ext4，含 `adsp` 与 `cdsp` | 已列出（见下文） |
| 基带 | `modem.img` | FAT | 已列出（见下文） |
| 蓝牙 | `bluetooth.img` | FAT | 已列出（见下文） |
| TME（位于 XBL 内） | `xbl.img` 的一部分 | RISC-V | 见第 02 节 |

## AOP（`aop.img`、`aop_config.img`）

`aop.img` 是 32 位 ARM ELF，包含七个 `PT_LOAD` 段。入口点为 `0x0B000009`。最低位被置位，这是 ARM Thumb 的约定，因此入口处是 Thumb 代码。指令模式也与之相符：`bx lr`（`0x4770`）在第一个代码段（文件偏移 0x154）中每千个半字出现 6.2 次，随机基线约为 0.015；全文件的比率为每千个 2.8。因此入口代码为 Thumb（Ghidra 语言 `ARM:LE:32:v8T`）；该密度并不能确立 Thumb-2 的 32 位编码。入口处的 Ghidra 反汇编（`data/ghidra/aop_entry_thumb2_disasm.txt`）从字面量池加载字，通过寄存器调用，并以 `bx r0` 或 `bx r1` 返回。池中的字不能解析为已映射的代码地址，因此并未证明它们是函数指针。

版本字符串为 `QC_IMAGE_VERSION_STRING=AOP.HO.4.0-00605-AURORA_E-1`。`AOP.HO` 表示 AOP 镜像系列，`AURORA` 表示 SoC。作为文本已验证。

镜像中包含 `wlan_hamilton`，指向 Hamilton Wi-Fi/蓝牙组合芯片。厂商属性也把同一芯片列为蓝牙 SoC。已观察。

`OEM_IMAGE_VERSION_STRING` 中是构建主机名，未进一步分析。

`aop_config.img` 是 16 KB 的 ELF，有两个 PT_LOAD 段。其可读字符串为 PMIC 电源轨与时钟名称（`vrm.aoss`、`vrm.wlan`、`ldoa10`、`gpioa6`）以及证书主体（`data/strings/aop_config.txt`）。

## CPUCP（`cpucp.img`）

32 位 RISC-V ELF（`EM_RISCV`），入口 `0x90`，七个 `PT_LOAD` 段。根据头部已验证。

启动字符串 `CPUCP boot started` 与 `SCMI init Done` 作为文本已验证。SCMI（System Control and Management Interface）是（基于一般背景知识，非来自文件）Arm 的标准接口，允许应用处理器向管理处理器请求功耗、时钟和性能的变更。字符串表明，在这个平台上 CPUCP 实现了 SCMI 服务端。已观察，尚未在代码中追踪。

另有两个镜像提到了 CPUCP。`xbl_ramdump` 中有 `CPUCPFW region` 和 `CPUCPFW.BIN`，说明 XBL 为它预留了内存。`devcfg` 中有 `tgt_cpucp_config`，是按目标划分的配置块。SBL1 中有 `boot_prepare_cpucp` 和 `boot_reset_cpucp`，说明 SBL1 负责启动和复位 CPUCP。已观察。

## SHRM（`shrm.img`）

32 位 RISC-V ELF，入口 `0x200000`，两个 `PT_LOAD` 段。根据头部已验证。

其中包含 `DDR_FW version : 275.0.0`。名称表明这是与 DDR 相关的固件，可能负责内存训练或 DDR 功耗管理。作用未验证。SBL1 中有 `boot_shrm_mini_dump_init`，XBL 也提到名为 `shrm.elf` 的文件，说明 SBL1 很可能加载该镜像。已观察。

## QUP 固件（`qupfw.img`）

Hexagon ELF，`e_machine = EM_QDSP6`，`e_flags = 0x3`。它有十一个 `PT_LOAD` 段和一个高通哈希段。`e_entry` 为零，对于独立镜像来说不寻常，更像是库或覆盖层。根据头部已验证。

镜像中没有功能性字符串，但含有一条证书链（`Qualcomm Technologies, Inc.`、`Qualcomm Cryptographic Operations`、`SRoT MBNv7 Image Signing Root CA 6`，以及 `0xB5FF` 附近的 `CASS - SBL4`）。作用未知。名称暗示是高通通用外设（QUP）串行模块，但这只是猜测。

其布局是高通镜像格式。`0x1000` 段以 `QSI ` 魔数开头。其内容未经解码；其后的字节包含类似 ASN.1 DER 的 `30 0d` 与 `30 00` 模式，因此尚未确定（偏移，大小）表。`0x6328` 段以 `SEFW` 开头。Ghidra 的 Hexagon 解码从 `0x1100` 起开始得到看似合理的指令（例如 `memw R20,(R20+#0x1c)`），但序列主要由重复的 `memw` 组成，因此代码边界尚未确定。

解码率不能说明某区域是否为代码，因此不据此把 QUP 镜像视为代码。`qupfw.img` 中是否含有代码、入口在哪里，尚未确定。

## 音频与计算 DSP（`dsp.img`）

这是一个 ext4 镜像。顶层目录为 `adsp`、`cdsp` 和 `lost+found`。`sdsp` 目录存在，但在本构建中是空的。通过列出镜像内容已验证。该镜像挂载于 `/vendor/dsp`（第 04 节）。

### `adsp`（34 个文件）

应用 DSP 的 Hexagon 共享对象和骨架库，按功能分组：

- 音频编解码：`aac_dec_module.so.1`、`aac_enc_etsi_module.so.1`、`flac_dec_module.so.1`、`lc3_dec_module.so.1`、`lc3_enc_module.so.1`、`liblc3_enc.so`、`liblc3qDec.so`、`sbc_dec_module.so.1`、`sbc_enc_module.so.1`、`spf-lc3-decoder.so.1`。LC3 和 SBC 是蓝牙音频格式。
- 语音处理：`fluence_bs_module_fvxii.so.1`、`fluence_ef_module_fvxii.so.1`、`fluence_nn_module_fvxii.so.1`、`fluence_pro_vc_module_fvxii.so.1`、`ffecns_module_VUI_vii.so.1`、`smecns_v2_module_fvxii.so.1`。`fluence` 与 `ecns` 对应回声消除和降噪阶段。
- 音频框架：`AudioSphereModule.so.1`、`SAPlusCmnModule.so.1`、`CFCM.so.1`、`acd_module.so.1`、`sdd_module.so.1`。
- 传感器与系统：`libsns_device_mode_skel.so`、`libsns_direct_channel_skel.so`、`libsns_dynamic_loader_skel.so`、`libsns_remote_proc_state_skel.so`、`libsysmon_skel.so`、`libsysmondomain_skel.so`、`libsysmonquery_skel.so`、`libstabilitydomain_skel.so`。
- 运行时：`fastrpc_shell_0`、`libc++.so.1`、`libc++abi.so.1`。

两个文本文件 `map_SHARED_LIBS_aurora.adsp_la.prodQ.txt` 与 `map_SSC_SHARED_LIBS_...` 把库路径列为 `../../build/ms/dynamic_modules/aurora.adsp_la.prod/…`。这是本镜像的构建路径。已验证。

### `cdsp`（18 个文件）

计算 DSP。值得注意的项目：

- `libevadsp_3_0.so` 与 `libevadsp_3_0_intermediate.so`：EVA 库。内核中的 `msm-eva.ko` 是对应的内核驱动。名称指向边缘视频分析或视觉工作负载。未验证。
- `libsynx.so`、`libsynx_os.so`、`libsynx_threadutils.so`：synx 同步对象，与内核中的 `synx-driver` 对应。
- `ubwcdma_dynlib.so`：UBWC（压缩缓冲区）DMA 支持。
- `libbenchmark_skel.so`、`libcrm_test_skel.so`：测试与基准骨架。
- `fastrpc_shell_3`、`fastrpc_shell_unsigned_3`：计算 DSP 的 FastRPC shell。

涉及的内核模块包括 `cdsp-loader.ko`、`adsp_loader_dlkm.ko`、`q6_dlkm.ko`、`mdt_loader.ko`（在 `modules_modinfo.tsv` 中被描述为 MDT 固件解析器）以及 `frpc-adsprpc.ko`。其加载作用未经验证。

## 基带（`modem.img`）

这是一个 FAT16 镜像文件，大小 38.5 MB（38,522,880 字节），其内容为 165 个文件，共 36.5 MB（36,487,937 字节）。列表见 `data/remote/modem_listing.txt`。已通过能处理长文件名的 FAT 读取器验证。

目录结构：

- `/image/kiwi/`：主基带集合。`amss.bin`（7.46 MB）和 `amss20.bin`（6.50 MB）是基带固件镜像。`Data.msc` 和 `Data20.msc` 是数据段。`bdwlan.elf` 与 `bdwlan.elf.xz` 是 Wi-Fi 板级数据。`regdb.bin` 是无线监管数据库。`phy_ucode.elf` 与 `phy_ucode20.elf` 是 PHY 微码。`qdss_trace_config_v1.cfg` 与 `v2.cfg` 用于配置跟踪输出。
- `/image/adsp.b00` 至 `adsp.b41`（另有头文件 `adsp.mdt`）：应用 DSP 固件本身，分为 40 个可加载段（1 至 40）、一个头段（0）与一个签名段（41）。第 24 与 40 段文件大小为零且没有 `.bNN` 文件，因此存在 40 个 `.bNN` 文件。已观察为 Hexagon ELF，入口 `0x87600000`。段结构、SHA-384 哈希表、签名链以及同一镜像中的可信应用见第 16 节。早期草稿曾称这些不是应用 DSP 固件，这一说法有误。`cdsp.b00` 至 `cdsp.b12` 为计算 DSP 固件，同样在第 16 节说明。

`amss.bin` 是 32 位 ELF，`e_machine = 0x28`（ARM）。`kiwi` 是构建中此基带配置的目录名，其含义未说明。根据头部已验证，名称含义未解释。

## 蓝牙（`bluetooth.img`）

这是一个 FAT16 镜像文件，大小 1.22 MB（1,224,704 字节），其内容为 51 个文件，共 0.78 MB（780,143 字节）。列表见 `data/remote/bluetooth_listing.txt`。

- `hmtbtfw10.tlv` 与 `hmtbtfw20.tlv`：蓝牙固件，TLV 格式。
- `hmtbtfw20.ver`：`BTFW.HAMILTON.2.0.0-00797-PATCHZ-1.105163.2.109423.3`。芯片名为 Hamilton。已验证。
- `hmtnv10.*` 与 `hmtnv20.*`：非易失性配置文件，共 47 个：`hmtnv20.*` 有 45 个（`.b0202` 至 `.b3f`，以及 `.bin`），`hmtnv10.*` 有 2 个（`.b0c` 与 `.bin`）。后缀看起来是按产品或按天线的配置，未验证。

fstab 以只读方式把该镜像挂载在 `/vendor/bt_firmware`（第 04 节）。

## 与其他部分的联系

有三条路径把远程处理器与熔丝和启动分析联系起来。

1. XBL 容器中的 SBL1 程序提到 `shrm.elf`、`devcfg.bin` 和 `cpr.bin`，还有 `boot_prepare_cpucp` 与 `boot_reset_cpucp`。它们很可能是 SBL1 为远程处理器和功耗控制器加载的镜像。已观察。
2. 内核通过 SCMI 与功耗管理处理器通信。熔丝中设定的功耗限制可能经由这条路径传到内核。这是假设，尚未检查 CPUCP 中的熔丝读取路径。
3. 设备树把 GPU 速度分级绑定到一个熔丝字段（第 06 节）。GPU 驱动从内核一侧读取该字段，而不是通过远程处理器。
