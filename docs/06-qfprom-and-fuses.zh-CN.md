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

QFPROM 窗口旁边还有三个块。TrustZone 的 MMIO 表和 SBL1 的区域映射都列出了它们：

| 基址 | 出现位置 | 该表中的计数或大小 |
|---|---|---|
| `0x221C0000` | TrustZone MMIO 表，索引 0 | 计数 8 |
| `0x221C4000` | TrustZone MMIO 表，索引 1 | 计数 4 |
| `0x221C2000` | TrustZone MMIO 表，索引 2；SBL1 区域映射 | 计数 8 |
| `0x221C8000` | TrustZone MMIO 表，索引 3；虚拟化层映射；SBL1 区域映射；设备树 | 计数 8（TZ，8 KB）；3 页（hyp）；1 页（DTB） |

只有 `0x221C8000` 在设备树中有节点。其他三个块的名称未知。地址已验证，名称未验证。

## TrustZone MMIO 表

TrustZone 在 `0x1C141C40` 处有一张表，由五个 16 字节条目组成，每个条目包含一个 32 位基址和一个 32 位计数。索引 4 为 `0x010C0000`。

有两个函数读取该表。`FUN_1C067548` 传入标志 `0x9041`，`FUN_1C067598` 传入标志 `0x9061`。两者都拒绝大于 4 的索引，然后通过 `FUN_1C03ACAC` 映射该条目。两者各有 16 处调用点：15 处 `BL` 与 1 处尾调用 `B`。索引 0 到 4 都以两种标志被使用（`data/secure/tz_mmio_table_users.txt`）。

反编译的调用链是：`FUN_1C03ACAC` 加锁，调用 `FUN_146816F4`，然后解锁。`FUN_146816F4` 调用 `FUN_14681A68`，这是一个一阶段转换表映射器。该映射器把块描述符和页描述符写入正在使用的转换表，并发出 `TLBI`、`DSB` 和 `ISB` 维护指令。过程中没有 `SMC` 指令，因此映射留在 TrustZone 内部（`data/ghidra/tz_mmio_mapper_decompiled.txt`）。

标志的含义，来自 `FUN_14682D04`：

- `0x9041` 以 EL1 读写方式映射该范围。`0x9061` 只相差第 5 位，该位设置 `AP[2]`（只读位），因此 `0x9061` 以只读方式映射。
- 两者都设置禁止执行（`UXN` 和 `PXN`）、内部共享和访问标志，并且都选择 MAIR 属性索引 1。索引 1 很可能是设备内存类型，这是推断。

计数以 KB 为单位。映射器检查计数是否为 4 的倍数（即整数个 4 KB 页），并以 `基址 + 计数 × 0x400` 计算结束地址。因此 QFPROM 条目在 TrustZone 中映射 8 KB。这是从映射器的运算推断出来的。

映射器把两个基址参数当作虚拟地址和物理地址。这里两者相同，因此是恒等映射。

## 映射大小不一致

- 设备树给出 `0x1000`（一页）。
- TrustZone 的表给出 8 KB（由上面映射器的运算推断）。
- 虚拟化层的内存映射给出 `0x3000`（三页），属性为 4，权限为 `0xF`。记录为 `(va=0x221C8000, pa=0x221C8000, attr=0x4, perm=0xF, size=0x3000)`（`data/secure/hyp_mmio_map.tsv`）。

这三者可以同时成立：虚拟化层映射整个邻近区域，TrustZone 映射 8 KB，而设备树只描述内核实际使用的那部分。数值已验证；它们彼此一致的解读是一种解释。

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

SBL1（`xbl.img` 中的 AArch64 程序）有一处直接引用 `0x221C8000`：`0x1482CED4` 处的 `mov w13, #0x8000` 与 `movk w13, #0x221c, LSL #16`。该代码位于内存映射函数 `FUN_1482CD30` 中，该函数只有一个调用点 `0x14825B3C`。该函数构建一张区域记录表，其中包括 `0x221C2000` 和 `0x221C8000`，并通过协议 ID `0x3E` 找到的服务把该表交出去（`data/ghidra/sbl1_memmap_decompiled.txt`）。该服务尚未反编译。

### TrustZone

TrustZone（`tz.img`）保存上述表，并有两个字面量池槽位保存 `0x221C8000`。TrustZone 中还有以下名称，它们是字符串，因此其用途为观察结果：

- `qsee_fuse_read`、`qsee_fuse_write`：读写接口。
- `qsee_blow_sw_fuse`：烧写软件熔丝。
- `qsee_is_sw_fuse_blown`：检查软件熔丝是否已被烧写。
- `OEM_rot_pk_hash1_fuse_values`：信任根公钥哈希。
- `OEM_rot_enc_key1_fuse_values`：信任根加密密钥条目。
- `oem_defer_fuse_prov_operation`：延迟的熔丝配置操作。
- `invoke-oem-spare-fuses failed: 0x%x, 0x%x, 0x%x`：备用熔丝路径。
- `qfprom_data`：熔丝数据缓冲区。

TrustZone 中的 PK 哈希路径（`data/secure/tz_pkhash_path.txt`）观察如下。`PKHashExt` 处理程序注册名称 `GetPKHash`（函数 `0x1C395930`），并通过 `0x1C395C20`（`PKHashExtHandler_copyHash`，调用有界复制 `0x1C3AED14`）把 32 字节复制到其对象的 `+0x58` 偏移处。在初始化路径中，源是 `.rodata` 中 `0x1C3BE01E` 处的常量，旁边是许可证路径 `/persist/data/pfm/licen...` 的 DER 属性。因此该路径复制的是镜像中的值，而不是 QFPROM 中的值。函数 `0x1C396908`（`GetPKHash`/`GetDeviceID` 处理程序）通过方法 6 从运行时对象获取 16 字节设备 ID，并记录 `IDeviceID_getClientDeviceID failed`。方法 6 的提供者尚未确定。因此把 `OEM_rot_pk_hash1_fuse_values` 转换为哈希的读取者仍未找到。依据反汇编观察得出。复制的源地址是 DER 长度字节 `0x20`，复制可能早一个字节开始，此点未验证。

DevCfg（`devcfg.img`）和 TrustZone 都有 `PM_QFPROM_FLAG`，这是电源管理从熔丝块读取的标志。已观察。

Featenabler（`featenabler.img`）使用软件熔丝按硬件版本启用功能（字符串 `soc_hw_version`、`ConfigureSwFuse failed for feature_id`、`DisplayCore_EnableSwFuse`）。已观察。

### 虚拟化层

虚拟化层有 8 个字面量池槽位保存 `0x221C8000`，其内存映射中有上述 `0x3000` 记录。它是关于该块映射最完整的一份材料。扫描 `hyp.img` 发现，在 `0x221C8000`–`0x221CAFFF` 范围内没有其他常量：每个槽位都恰好是 `0x221C8000`，仅有一处 `movk` 使用 `0x221C`。因此镜像中没有代码通过绝对地址访问多出的两页。已观察。`0x3000` 的大小仍可能通过计算偏移覆盖这两页，此点未检查。

### TME

TME 固件中没有对该块的引用：没有带 QFPROM 立即数的 `LUI`，也没有字面量。已通过搜索验证。

### SBL1 熔丝读取函数（CPR）

SBL1 在 `0x14881880`–`0x14881A30` 范围内有一组熔丝字段读取函数。它们从 `0x221C27F8`、`0x221C27FC` 和 `0x221C2800` 三个字中读取 5 位字段。这些字位于 `0x221C2000` 块，而不在 `0x221C8000` 的 QFPROM 块中。一个分发函数通过 `0x148AC670` 处的跳转表从 15 个字段中选择。表格与位位置见 `data/secure/sbl1_cpr_fuse_getters.txt`。已观察。

一个调用方使用这些字段时，记录步长为 0xF8 字节，带有有符号 16 位上下限，并做了一次除法。SBL1 中还有字符串 `CPR rev %d data not found in voltage plan` 和 `/cpr.bin`。因此这些读取函数读取的是 CPR（核心功耗削减）的校准字段。该结论根据字符串与运算推断而来；镜像中没有记录名和字段名。

SBL1 还通过 `0x14853EF4`–`0x14853F30` 处的小型读取函数直接读取 QFPROM 块中的四个字：`0x221C8780`、`0x221C8784`、`0x221C8788` 和 `0x221C878C`。其使用者尚未确定。已观察。

### TrustZone 防回滚标志

`qsee_sfs_is_anti_rollback_enabled` 对应的函数位于 `0x1C32D6E0`（字符串引用位于 `0x1C32D710`，源码行 `0x356`）。它向 `FUN_1C32516C` 请求一个单字节标志。`FUN_1C32516C` 在 TLS 块（`tpidrro_el0`）中保存每线程缓存：`+0x18AB` 为有效标记，`+0x18AC` 为值。缓存未命中时，它通过 `FUN_1C32E024` 和 `FUN_1C32DFB0` 获取接口 ID `0x91` 对应的对象。后者以 4 字节缓冲区形式传入该 ID，经由 `FUN_1C302990` 调用对象。标志本身来自 ID `0x91` 的对象，其提供者尚未确定。缓存与查找方式已观察；标志的来源尚未找到。反汇编见 `data/secure/tz_antirollback_path.txt`。

对象 `0x91` 的请求路径现已映射（`data/secure/tz_object_0x91_requests.txt`）。只有两处代码请求它（`0x1C3251E0` 与 `0x1C325960`）。两者都调用 `FUN_1C32E024`，它先查找 `tpidrro_el0 + 0x28` 处的每线程缓存。未命中时，`FUN_1C32DFB0` 调用该线程的根对象：`tpidrro_el0 + 0x18` 处的函数指针与 `+0x20` 处的句柄，操作码为 `0x1001`，参数为 4 字节的 ID。因此 `0x91` 的提供者就是线程上下文在 `+0x18` 处安装的那个函数。这使上下文创建者与提供者成为同一个未决问题。已从反汇编观察得出。其他加载 `0x91` 的位置是日志行号。

对象调用入口（`FUN_1C302990`）是一个通过寄存器跳转的跳板，因此对象 `0x91` 的分发发生在 `tz.img` 代码之外，其提供者未找到。该对象模型与 SBL1 的协议注册表（`0x3E`，第 02 节）相同，后者的提供者现已确定。该标志与 `vbmeta` 相关：应用的回滚计数器保存在 RPMB 中（`tz.img` 中的 `tzbsp application rpmb version rollback label`）。该联系尚未在代码中确认。

### 防回滚管理器的位置

源文件名 `AntiRollbackMgr.cpp` 位于 `xbl.img` 内的 TME 固件中，与 GLink、SMEM 和 FreeRTOS 字符串相邻，而不在 TrustZone 中。因此防回滚管理器是 TME 上的服务。它与 TrustZone 标志（对象 `0x91`）之间的联系尚未确认：TME 是独立的处理器，TZ 到 TME 的 GLink 通道是可能的路径，但未经验证。在整个 TME 镜像中只找到 15 个 RISC-V `auipc` 配对，且都不在该地址，因此引用很可能位于表中。数据见 `data/secure/tme_antirollback_location.txt`。

TME 代码中没有直接构造 QFPROM 或 TrustZone MMIO 地址的常量（`lui`/`addi` 配对重建 `0x221C0000`–`0x221CFFFF` 或 `0x010C0000`–`0x010CFFFF` 的地址：无）。因此在该镜像中，TME 并不直接读取熔丝块。它的回滚计数器访问必须经过另一个组件，最可能是 TrustZone 的对象模型。这是推断，未被直接证明。TME 的 Ghidra 分析见 `data/secure/tme_ghidra_rollback_search.txt`。

### Featenabler 显示软件熔丝

`featenabler.img` 是一个 TrustZone 应用，根据许可证启用显示功能。它的软件熔丝不是 qsee 熔丝，而是显示硬件块中的 32 位字，通过 `HWIOUtils_Read` 和 `HWIOUtils_Write` 访问。依据 Ghidra 反编译（`data/secure/featenabler_display_swfuse_decompiled.txt`）得出。

许可证的 `FeatureID` 到熔丝索引的映射（`DisplayCore_ConfigureSwFuse`）：

| FeatureID | 索引 | 功能 | 字偏移 |
|---|---|---|---|
| 1000 (0x3E8) | 2 | `Display_QLTM` | 索引 * 4 + 8 = 0x10 |
| 1002 (0x3EA) | 12 | `Display_SPR` | 0x38 |
| 1003 (0x3EB) | 13 | `Display_Demura` | 0x3C |
| 1004 (0x3EC) | 14 | `Display_Allocate_Cache_Signal` | 0x40 |

启用时向该字写入 `1`。状态读取（`DisplayCore_ReadSwFuseStatus`）在字的 `(value & 0x11) == 1` 时返回真。

按 `soc_hw_version` 的门控（`DisplayCore_IsFeatureSupported`，取值与 `0xFFFFFF00` 做掩码）：
- `0xA0010100`、`0xA0010200`、`0xA0040100`、`0xA0080100`、`0x600F0100`、`0x600F0200`：功能 1000、1002、1003、1004 受支持（掩码 `0x1D`）。功能 1001 不受支持。
- `0x60080100`、`0x60080200`、`0x600D0100`、`0x600D0200`、`0x60170100`：只有功能 1000 受支持。
- 其他值：均不受支持。

未确定：显示块基址的来源（通过区域名称的 `IDeviceRegionFinder`）、许可证签名校验，以及每个 `soc_hw_version` 对应哪款 SoC。

`tz.img` 中的对象调用链（`data/secure/tz_object_invoke_chain.txt`）：`FUN_1C32E024` 以对象 ID `0x30`、`0x12`、`0x61`、`0x114`、`0x91`（两处）、`0xB` 和 `0x16` 被调用。查找函数 `FUN_1C32DFB0` 通过当前线程块 `tpidrro_el0 + 0x18` 处保存的函数指针跳转，句柄位于 `+0x20`。`0x1C304010` 处的例程在线程切入时，经过魔数检查后，从上下文块中加载这一对值。因此对象分发器是由上下文提供的一个函数。每个上下文对应哪个函数、上下文如何创建，尚未确定。

上下文的创建者仍未找到。切入函数 `0x1C108368` 在 `tz.img` 内没有调用者：没有分支、指针或地址形成指令能到达它。它从镜像外部进入，因此 TrustZone 入口接收到的上下文由 `tz.img` 之外的代码提供（`data/secure/tz_switch_in_entry_scan.txt`）。依据观察得出。对 `tz.img` 的静态扫描（包括搜索写入 `+0x18` 的函数地址，以及对象 ID `0x91`）没有找到把调用对（函数与句柄）写入线程块的存储指令（`data/secure/tz_object_0x91_provider_scan.txt`）。依据观察得出；扫描并不穷尽。切入例程（`0x1C304010`）检查 `+2` 处的半字为 `0x0002`。没有简单的常量存储写入该值，另有十处把 `0x20000` 装入无关字段。搜索记录见 `data/secure/tz_context_creation_search.txt`。

线程块指针只在少数几处写入（`data/secure/tz_thread_block_setter.txt`）。设置函数 `0x1C1399F8` 是 `msr tpidrro_el0, x0`；它唯一的直接调用者是切入函数 `0x1C108368`，该函数从上下文对象的 `+0x48` 处读取块指针。块本身不在那里分配。切入函数的函数指针槽位未找到，因此它很可能是通过对象表间接调用的。另有两个设置上下文对象的函数（约 `0x1C07F848` 和 `0x1C096B08`）调用包装函数 `0x1C108320`。它们是创建者的候选，但未找到写入新块的 `+0x18` 调用函数或 `+0x20` 句柄的代码。因此创建者仍未确定。

`tz.img` 中的静态分发表有 61 行，每行 16 字节：8 字节的键 `(type << 16) | method` 和一个处理函数指针。类型标签 2 与切入例程中的线程上下文检查相符。对象 ID `0x91` 不是该表中的键，因此该对象在运行时才被解析。已观察。证据见 `data/secure/tz_dispatch_table.txt`。

UEFI 熔丝库中有一张命名区域表（`data/secure/uefi_fuse_region_table.txt`）。每行包含名称、基址和大小。基址存储为物理地址减去 `0x20000000`，这就是原始值显示为 `0x21C2000` 的原因。还原后区域为：`QFPROM_CORR` 位于 `0x221C2000`（大小 `0x2000`）；`FUSE_CONTROLLER_SW_RANGE0` 位于 `0x221C4000`，`_RANGE1` 位于 `0x221C5000`，`_RANGE3` 位于 `0x221C7000`，`_RANGE4` 位于 `0x221C8000`，`_RANGE5` 位于 `0x221C9000`（每个 `0x1000`）；`VIRT_FUSE_CONTROLLER_SW_RANGE3` 位于 `0x221CA000`；TME RNG 位于 `0x221D0000`；TME 加密位于 `0x221E4000`；RSCC 位于 `0x22200000` 和 `0x22220000`；TME XPU 位于 `0x22240000`。`QFPROM_CORR` 与 `SW_RANGE4` 的地址与 TrustZone MMIO 表（`0x221C2000`、`0x221C8000`）一致。因此保存防回滚状态的软件熔丝范围是 `0x221C` 块内的 4 KB 窗口。已观察。哪个窗口保存 `vbmeta` 索引，尚未确定。

记录 `qsee_is_sw_fuse_blown` 结果的 TrustZone 代码见 `data/secure/tz_sw_fuse_check_area.txt`。位于 `0x1C3ECD78` 的一个函数把 9 字节记录解包为两个大端 32 位字，再写回，因此它是记录的序列化函数，而不是熔丝读取。记录熔丝烧断结果的例程用 `ldr w0,[x27,x8,lsl #2]` 遍历一个列表，该列表解码为 ASCII 文本，因此它不是熔丝 ID 表。检查使用哪些软件熔丝 ID，因此仍未确定。

`hyp.img` 是 Gunyah/QTEE 虚拟化资源管理器，而不是普通的虚拟化层。它的字符串列出了 RPC、VM 创建、memparcel 和 SMC 等待队列的源文件，以及本地和远程对象表（`localObjTable`、`remoteObjTable`、`LocalObj_retrieve`）。这使它成为 TrustZone 查找背后对象调用提供者的候选，但其中没有找到对象 `0x91` 的表项，因此尚未确认。它还包含 `PILSubsys_getArbFuseBank`，说明外设镜像（PIL）是按子系统的防回滚熔丝组进行检查的。如果该熔丝组是 `0x221C` 块中的某个软件熔丝范围，那么回滚状态就保存在那里；熔丝组与子系统的对应关系部分已解码（见下文）。依据字符串观察得出。证据见 `data/secure/hyp_rm_objects_and_arb_fuse.txt`。

熔丝组表的交叉引用（`data/secure/hyp_arb_fuse_xref_scan.txt`）。该表是 `hyp.img` 中位于 `0x2007E8` 的静态数组，共 19 条记录。`0x260C4` 处的读取函数返回它。它在代码中的使用者只有 `0x26000` 和 `0x26060` 处的查找例程，以及 `PILSubsys_getArbFuseBank`（`0x3EB4C`）。`hyp.img` 中没有代码通过静态地址写入熔丝组字段（`+0xD8`），文件镜像中每个熔丝组字段都是零。`PILSubsys_getArbFuseBank` 在镜像集中没有任何引用。在对代码块强制反汇编后，Ghidra 的引用管理器也找不到指向其入口的引用。既没有直接调用，也没有绝对或相对指针，没有 `ADR`，也没有 `ADRP`+`ADD` 指向它，且该名称未出现在其他镜像中。因此它的调用者位于本文分析的镜像之外。熔丝组的值因此是在运行时由镜像集之外的路径设置，或来自尚未定位的来源。依据观察得出。证据见 `data/secure/hyp_arb_fuse_reference_check.txt` 与 `data/ghidra/arb_fuse_refs_check.java`。

TrustZone 的安全启动状态字有命名的位，由一个例程报告（位于 `0x1C3DFF30`，它调用状态服务并逐位记录）：第 0 位为 secboot 启用检查，第 1 位为安全硬件密钥已编程，第 2 位为调试禁用检查，第 3 位为防回滚检查，第 4 位为熔丝配置检查，第 5 位为 RPMB 已配置检查，第 6 位为镜像证书中的调试检查，第 8 位为 TZ 安全调试熔丝，第 9 位为 MSS 安全调试熔丝，第 10 位为 CP 安全调试熔丝，第 11 位为非安全安全调试熔丝。状态服务通过 `0x1C401090` 处的间接槽调用，该槽在文件中为零，运行时才填充，因此计算第 3 位的函数尚未确定。依据字符串和报告例程的代码观察得出。

虚拟化层读取 UEFI 区域表中名为 `FUSE_CONTROLLER_SW_RANGE4` 的软件熔丝范围（`0x221C8000`，4 KB）中的若干字。其启动代码读取 `0x221C8610`、`0x221C8700`、`0x221C8744`（基址 `0x221C8000`）以及 `0x221C873C`。对 `0x221C873C` 这个字做测试：其低 4 位与位掩码 `0x4883`（第 0、1、7、11、14 位）比较，结果会设置虚拟化层状态字中的位。依据 `hyp.img`（AArch64，已自动分析）的反汇编观察得出。这些字各自保存什么字段，以及是否包含 PIL 防回滚熔丝组的值，尚未解码。位于 `0x9D4D4` 的标志在七处读取处控制分支；复制后的字尚未找到读取者（见 `data/secure/hyp_rm_objects_and_arb_fuse.txt`）。

PIL 防回滚熔丝查找已部分解码（`data/secure/hyp_pil_arb_fuse_table.txt`）。`PILSubsys_getArbFuseBank`（函数 `0x3EB4C`）接收子系统 ID 与输出指针。它扫描 `0x2007E8` 处的 19 条 `0x148` 字节记录（数量位于 `0x93AD8`）。ID 在记录偏移 `+0xD0` 处匹配；熔丝组值从 `+0xD8` 返回，记录标志 `+0x118` 决定结果：标志为 1 时返回错误 `0x300068`，正常匹配时返回 0 并给出值，未找到 ID 时返回 `0x300067`。依据反汇编观察得出。文件镜像中所有熔丝组值均为零，且未找到对 `+0xD8` 的写入，因此这些值由未定位的运行时代码设置。只有 ID 为 `0x2` 的记录设置了标志。镜像中没有各 ID 对应的子系统名称，因此熔丝组与子系统的对应关系尚不完整。

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

`vbmeta` 中的回滚索引是 `1770249600`（第 03 节）。防回滚需要一个无法被降低的计数器，通常的做法是使用熔丝支撑的计数器。设备上的计数器表尚未读取，因此 vbmeta 索引与某个熔丝之间的联系只是合理的预期，而不是事实。

## 未解决的问题

- `FUN_1C03ACAC` 所加的锁（经由 `FUN_1C062D44`），以及 `FUN_14681A68` 在 MMIO 路径之外的调用者。
- SBL1 区域表中每条记录的含义。接收它的服务（协议 `0x3E`，即页表构建器）已在第 02 节确定，但每条记录的字段布局尚未确认。
- 多出的两页是否通过计算偏移被使用。`hyp.img` 中没有指向那里的绝对地址。
- 字节 `0x221C8119` 及其相邻字节，用于确认 `gpu_speed_bin` 字段，以及同一字节中还有哪些位。
- `OEM_rot_pk_hash1_fuse_values` 的读取者，及其对应的 QFPROM 偏移。进一步搜索未在 `tz.img` 或 `devcfg.img` 中找到指向任何键名的指针、相对指针或 adrp 引用，因此键块是以非指针方式读取的（`data/secure/oem_key_pointer_search.txt`）。该名称是 `tz.img` 中 OEM 配置块（约 `0x13A295`–`0x13A7XX`，约 40 个键）中的一个键，`devcfg.img` 中也有它。通过 ADRP+ADD、ADR、绝对指针和重定位的搜索都未找到对它的代码引用（`data/secure/oem_rot_key_xref_search.txt`）。PK 哈希处理路径（`data/secure/tz_pkhash_path.txt`）本身不直接读取 QFPROM，其设备 ID 输入来自运行时对象的方法 6。读取者很可能是通过该对象对 OEM 块做的按名称查找。尚未找到。
- 对象 `0x91` 的提供者（即上文的防回滚标志对象），以及构建 TrustZone 线程上下文（`0x14680000` 入口块）的代码。两者在镜像中均未找到；搜索记录见 `data/secure/tz_object_0x91_and_oem_key_search.txt` 与 `data/secure/tz_context_creation_search.txt`。
- 将 vbmeta 回滚索引与已存储值比较的代码。
- `featenabler` 的显示块基址（`IDeviceRegionFinder` 的区域名称）、许可证签名校验，以及每个 `soc_hw_version` 对应的 SoC 名称。

设备树和覆盖层的检查已经完成。基础设备树只定义了一个熔丝字段（`gpu_speed_bin`）。`dtbo.img` 中的 18 个覆盖层只引用了一个 nvmem 字段，即复位原因，因此没有增加任何熔丝字段。已验证。
