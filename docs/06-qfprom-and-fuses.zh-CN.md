# 06 - QFPROM 与熔丝

[English](06-qfprom-and-fuses.md)

QFPROM 是 SoC 上的熔丝块，其中的位只能写一次。启动链、内核和安全世界都从中读取数值。本文列出已知信息、各读取者所在的位置，以及尚未弄清的部分。本文描述系统如何使用熔丝，不描述任何缺陷。

## 熔丝块

厂商设备树在 `0x221C8000` 定义了该块，窗口大小 4 KB：

```
qfprom@221c8000
    compatible = "qcom,qfprom"
    reg = <0x221c8000 0x1000>
    read-only
```

`read-only` 表示内核不通过该节点写入熔丝，写入发生在安全世界中。已验证。

设备树只命名了一个熔丝字段：

| 字段 | 偏移 | 位 | 使用者 |
|---|---|---|---|
| `gpu_speed_bin` | `0x119`，2 字节 | 第 5 位起，宽 8 位 | GPU（`kgsl-3d0`，名称 `speed_bin`），以及 `qfprom@0`（`qcom,qfprom-sys`） |

该字段给出 GPU 的速度分级，GPU 驱动据此选择工作点。它占用 `0x119` 处两个字节中的第 5 到 12 位。根据设备树已验证。每个取值的含义要等读取驱动代码后才能确定。

## 相邻的块

QFPROM 窗口旁边还有三个块。TrustZone 的 MMIO 表和 SBL1 的内存映射都列出了它们：

| 基址 | 出现位置 | 该表中的计数或大小 |
|---|---|---|
| `0x221C0000` | TrustZone MMIO 表，索引 0 | 计数 8 |
| `0x221C4000` | TrustZone MMIO 表，索引 1 | 计数 4 |
| `0x221C2000` | TrustZone MMIO 表，索引 2；SBL1 描述符数组 | 计数 8 |
| `0x221C8000` | TrustZone MMIO 表，索引 3；虚拟化层映射；SBL1；设备树 | 计数 8（TZ）；3 页（hyp）；1 页（DTB） |

只有 `0x221C8000` 在设备树中有节点。其他三个块的名称未知。地址已验证，名称未验证。

## TrustZone MMIO 表

TrustZone 在 `0x1C141C40` 处有一张表，由五个 16 字节条目组成，每个条目包含一个 32 位基址和一个 32 位计数。索引 4 为 `0x010C0000`。

有两个函数使用该表。`0x1C067548` 传入标志 `0x9041`，`0x1C067598` 传入标志 `0x9061`。两者都接收一个索引，拒绝大于 4 的值，并从 `表 + 索引 × 8` 读取 `基址` 与 `计数`。两者各有 15 处调用点，且索引 0 到 4 都以两种标志被使用。

对于 QFPROM 块（索引 3），标志 `0x9041` 由 `0x1C084A30`、`0x1C084AEC` 和 `0x1C084B94` 设置；标志 `0x9061` 由 `0x1C065304`、`0x1C084B08` 和 `0x1C084BB8` 设置。

被调用的 `0x1C03ACAC` 接收基址、计数与标志。它加锁，调用 `0x146816F4`（TrustZone 自身的代码），然后解锁。`0x146816F4` 是一个普通例程，没有 `SMC` 指令，因此映射是在软件中完成的，不需要调用安全监控器。该例程的内容尚未阅读。计数的单位未知，两个标志的含义也未知。两种标志可能区分只读与读写处理，这一点未验证。

## 映射大小不一致

- 设备树给出 `0x1000`（一页）。
- 虚拟化层的内存映射给出 `0x3000`（三页），属性为 4，权限为 `0xF`。记录为 `(va=0x221C8000, pa=0x221C8000, attr=0x4, perm=0xF, size=0x3000)`（`data/secure/hyp_mmio_map.tsv`）。
- TrustZone 表给出计数 8，单位未知。

这些可以同时成立：虚拟化层映射整个邻近区域，而设备树只描述内核实际使用的那部分。尚未证实。数值已验证，解释仍然开放。

## 内核中的读取者

| 读取者 | 证据 | 状态 |
|---|---|---|
| `nvmem_qfprom.ko` | `CONFIG_QCOM_QFPROM=m`，描述为 "Qualcomm QFPROM driver"，作者 Srinivas Kandagatla（Linaro） | 主要路径 |
| `msm_kgsl.ko` | GPU 驱动；设备树中为 `nvmem-cell-names = "speed_bin"` | 使用 `gpu_speed_bin` |
| `qfprom@0` 消费者 | `compatible = "qcom,qfprom-sys"` | `CONFIG_QCOM_QFPROM_SYS` 未设置，因此这不是一个已编译的驱动接口 |
| `qcom-reboot-reason.ko` | 从 PMIC SDAM 和 IMEM 读取复位原因（第 04 节） | 不是熔丝块，列在此处说明复位路径 |

NVMEM 框架按名称导出每个字段。消费者请求某个字段，从不直接访问熔丝块。并非所有 `nvmem-cells` 的消费者都读取 QFPROM：复位原因节点读取的是 PMIC SDAM，GPU 和 `qfprom-sys` 节点读取的是熔丝块。

## 启动链与安全世界中的读取者

### SBL1

SBL1（`xbl.img` 中的 AArch64 程序）有一处直接引用 `0x221C8000`：`0x1482CED4` 处的 `mov w13, #0x8000` 与 `movk w13, #0x221c, LSL #16`。该代码位于始于 `0x1482CD30` 的函数中，该函数只有一个调用点 `0x14825B3C`。其周围的代码把一系列 64 位值存入栈上的数组：`0x221C2000`、`0x221C8000`、`0x22000000`、`0x20C20000`，以及 SBL1 的地址 `0x148A3000`、`0x148B2000`、`0x148B5000` 和 `0x148C7000`。SBL1 中含有 `BootMemMapLib.c`，因此它很可能是正在构建的启动内存映射。这是解释。

方法和反汇编见 `data/xbl/sbl1_qfprom_xref.txt`。

### TrustZone

TrustZone（`tz.img`）保存上述 MMIO 表，并有两个字面量池槽位保存 `0x221C8000`。使用该表的函数见上文。TrustZone 中有以下名称，它们是字符串，因此其用途为观察结果：

- `qsee_fuse_read`、`qsee_fuse_write`：读写接口。
- `qsee_blow_sw_fuse`：烧写软件熔丝。
- `qsee_is_sw_fuse_blown`：检查软件熔丝是否已被烧写。
- `OEM_rot_pk_hash1_fuse_values`：信任根公钥哈希。
- `OEM_rot_enc_key1_fuse_values`：信任根加密密钥条目。
- `oem_defer_fuse_prov_operation`：延迟的熔丝配置操作。
- `invoke-oem-spare-fuses failed: 0x%x, 0x%x, 0x%x`：备用熔丝路径。
- `qfprom_data`：熔丝数据缓冲区。

DevCfg（`devcfg.img`）和 TrustZone 都有 `PM_QFPROM_FLAG`，这是电源管理从熔丝块读取的标志。已观察。

Featenabler（`featenabler.img`）使用软件熔丝按硬件版本启用功能（字符串 `soc_hw_version`、`ConfigureSwFuse failed for feature_id`、`DisplayCore_EnableSwFuse`）。已观察。

### 虚拟化层

虚拟化层有 8 个字面量池槽位保存 `0x221C8000`，其内存映射中有上述 `0x3000` 记录。它是关于该块映射最完整的一份材料。

### TME

TME 固件中没有对该块的引用：没有带 QFPROM 立即数的 `LUI`，也没有字面量。已通过搜索验证。

## 字面量出现的位置

字面量扫描的计数（`data/qfprom_literal_candidates.json`）：

| 镜像 | 次数 | 说明 |
|---|---:|---|
| `hyp.img` | 8 | 虚拟化层内存映射 |
| `xbl.img` | 2 | 两处都在 SBL1（AArch64 程序）中 |
| `xbl_ramdump.img` | 2 | 与 SBL1 相同的模式 |
| `tz.img` | 2 | TrustZone 表 |
| `recovery.img` | 5 | 很可能是设备树数据，未确认 |
| `boot.img` | 2 | 很可能是设备树数据，未确认 |

`boot` 和 `recovery` 中的计数很可能是设备树的副本，因为这两个镜像含有设备树 blob。需要追踪的是 `xbl`、`xbl_ramdump`、`tz` 和 `hyp` 中的命中。

同一次扫描在 `qupfw`（一次）、`boot`（两次）、`recovery`（七次）和 `vendor_boot`（两次）中找到了 `0x00784000`。它不是设备树基址，因此不是 QFPROM。早期笔记曾把 `0x00780000` 列为候选，那些命中大多是设备树数据。

## 复位原因路径

复位原因保存在两个位置。设备树节点 `/soc/reboot_reason` 同时列出了这两处：

1. PM8150 PMIC 上的 `sdam@b100/restart@48`，即 SDAM 字节 `0x48` 的第 1 到 7 位。SDAM 是 PMIC 上的一小块寄存器区，用于在复位之间保存数据。
2. `msm-imem@146aa000/restart_reason@65c`，位于共享 IMEM `0x146AA000`。XBL 配置中有相同的基址（`SharedIMEMBaseAddr = 0x146AA000`）。

第二份副本位于温复位后仍然保留的内存中。两个文件中都有记录，已验证。复位原因码的具体取值尚未解码。

## 与验证启动的联系

`vbmeta` 中的回滚索引是 `1770249600`（第 03 节）。防回滚需要一个无法被降低的计数器，通常的做法是使用熔丝支撑的计数器。目前我还无法读取设备上的计数器表，因此 vbmeta 索引与某个熔丝之间的联系只是合理的预期，而不是事实。

设备树和覆盖层的检查已经完成。基础设备树只定义了一个熔丝字段（`gpu_speed_bin`）。`dtbo.img` 中的 18 个覆盖层只引用了一个 nvmem 字段，即复位原因，因此没有增加任何熔丝字段。已验证。
