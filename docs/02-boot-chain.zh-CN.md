# 02 - 启动链，逐阶段

[English](02-boot-chain.md)

本文按启动顺序介绍各镜像。每一节说明文件内容和证据。XBL 镜像是包含三个程序的容器，而不是单一的加载程序。

本文中涉及代码的陈述来自无界面的 Ghidra 12.1.3（反编译与反汇编）。其输出位于 `data/ghidra/`。

## 阶段 0：Boot ROM（PBL）

第一级引导程序位于 SoC 的掩膜 ROM 中，复位后最先运行，从存储中加载 XBL，并校验 XBL 的签名。OTA 中不包含它。

启动链依赖 PBL 的证据：XBL 的字符串中有 `PBL Patch Ver: %d`、`PBL freq: %d MHZ`，以及源文件路径 `tme_messages/src/ImageAuthPblUtils.cpp`。这些是已观察的结果。PBL 的内部实现未验证。

## 阶段 1：XBL 容器

文件：`xbl.img`，978,944 字节。它首尾相接地包含三个 ELF 程序，每个都有自己的头部和加载段。

| 偏移 | 格式 | 入口 | 识别结果 | 证据 |
|---|---|---|---|---|
| `0x00000` | ELF32，`e_machine = 1`（`EM_M32`） | `0x2211C000` | 主存根 | 两个 `PT_LOAD` 段，约 114 KB 内容。内容呈数据特征（见 1c）。 |
| `0x1C2F4` | ELF32，`EM_RISCV` | `0x20412800` | TME 固件 | 源路径 `tmeFwMain`、`tme_com`、`tme_messages`、`IPCC_*`、`xport_qmp_config_tme.c`；`TME_FW_VERSION_STRING=ssg.tmefw.1.0.1-00467-release`，构建时间 `October 05 2025` |
| `0x4AFC4` | ELF64，`EM_AARCH64` | `0x14824FA8` | SBL1，二级引导程序核心 | `SBL1 BUILD @ 13:02:53 on Mar  5 2026`，`QC_IMAGE_VERSION_STRING=BOOT.MXF.2.2-00536-AURORA-1.149279.3`，`OEM_IMAGE_VERSION_STRING=ip-10-195-200-195` |

这些偏移是通过搜索 ELF 魔数找到的。`data/xbl/xbl_container.txt` 中有相同的表格，`data/xbl/string_regions.txt` 给出每个字符串所在的区域。

两个构建日期是两次独立的构建：TME 于 2025 年 10 月 5 日构建，SBL1 于 2026 年 3 月 5 日构建。

### 1a. TME 固件（RISC-V）

这是运行在 TME 核心上的 RISC-V 32 位程序。它提供镜像认证服务，XBL 与 PBL 通过 `tme_messages` 调用这些服务，并通过 IPCC 中断和 GLink 传输（`tme_com/GLinkPort.cpp`、`xport_qmp_config_tme.c`）与其他处理器通信。

证书名称位于此区域：

- `SRoT MBNv7 Image Signing Root CA 6 SubCA 10`，以及相关的 `SRoT MBNv7 Image Signing Root CA 60` 字符串。
- `Greatwhite_FW_Root_01`、`Greatwhite_FW_Root_11`、`Greatwhite_FW_Root_21`、`Greatwhite_FW_Root_31`，以及 `Greatwhite_FW_Signing_31`。

`Greatwhite_FW_*` 名称是本设备专用的固件根证书。已观察。

TME 镜像不引用 QFPROM 基址。在其代码中搜索 `LUI` 指令（使用 QFPROM 的立即数）以及字面量 `0x221C8000`，均无结果（`data/xbl/tme_lui_scan.txt`）。TME 可能通过自己的接口访问熔丝。已观察，未证实。

同一区域还有 `XPUPolicyVersion = 4.5`。XPU 是高通的总线访问保护模块，因此这个值是访问策略的版本。其内容未分析。

### 1b. SBL1（AArch64）

这是完成初始化工作的程序，入口为 `0x14824FA8`。字符串 `Secure Boot:`、`PBL Patch` 和 `Image Load, Start` 都出自这个区域。

它的源文件字符串覆盖了整个流程：

- 启动控制：`boot_pre_ddr_dtb_load`、`boot_post_ddr_dtb_load`、`boot_clock_init_rpm`、`boot_cdt_init`、`boot_fedl_check`、`boot_dload_entry`。
- 内存与 DDR：`boot_ddr.c`、`boot_ddr_info.c`、`boot_ddr_share_data_to_aop`、`boot_populate_ddr_details_shared_table`、`BootMemMapLib.c`。
- 其他处理器：`boot_prepare_cpucp`、`boot_reset_cpucp`、`boot_cpucp.c`、`boot_shrm_mini_dump_init`、`boot_vsense.c`。
- 镜像加载与检查：`boot_mbn_loader.c`、`boot_elf_loader.c`、`boot_elf_auth.c`、`boot_blacklist.c`、`boot_qsee.c`、`boot_whitelist_prot.c`。
- 崩溃处理：`error_handler_el3.c`、`sbl_error_handler: DDR not initialized`、`boot_dload_dump_security_regions`、`boot_ramdump.c`。
- 共享内存与调试：`boot_smem_init`、`boot_smem_debug_init`、`boot_smem_alloc_for_minidump`、`/dev/icbcfg/boot`、`boot_eud.c`。

SBL1 有一个子系统列表，其中包括 `tz`、`mss`、`uefi`、`adsp`、`aop` 和 `ssc`。该列表位于同一字符串块的偏移 `0xCD0F9` 处。它是 `uefi` 是下一个加载程序的最强提示。已观察。

SBL1 的字符串表中也有下一阶段的镜像名。偏移 `0x813D0` 至 `0x813F8` 的一组镜像名依次为 `CPUCP_DTB`、`QSEE Dev Config`、`QSEE` 和 `APPSBL`。另有一个 `uefi` 字符串位于 `0x82171`。`abl` 不出现在这里，`uefi` 镜像中也没有它。`uefi.img` 含有 `UEFI DXE` 以及 DXE 内核字符串（`Dxe Core  FV decompression failed`、`DXE Heap`、`AddDecompressdFvForDxe failed`）。这些是 UEFI DXE 固件卷的字符串，因此 `uefi.img` 是一个 UEFI 载荷。已观察。`uefi` 作为 `APPSBL` 被加载是推断：使用这些名称的 SBL1 加载代码尚未反编译。

SBL1 按文件名引用了 `shrm.elf`、`devcfg.bin`、`cpr.bin` 和 `_dcb.bin`。这些是它加载的镜像。加载它们的代码尚未反编译。

#### 内存映射函数

QFPROM 引用（见第 06 节）位于一个函数内，在 Ghidra 中命名为 `FUN_1482CD30`，它是 SBL1 的启动内存映射构建函数。它只有一个调用点，位于 `0x14825B3C`。

反编译的函数（`data/ghidra/sbl1_memmap_decompiled.txt`）在栈上构建一张区域记录表。每条记录包含一个起始地址、第二个地址、大小和一个类别值。表中出现的类别值有 `0x8`、`0x22`、`0x23`、`0x25`、`0x26` 和 `0x27`。其中列出的区域包括 SBL1 自身的镜像（`0x14800000`、`0x14824000`）、共享 IMEM（`0x146AA000`）、TrustZone 镜像（`0x14680000`），以及 MMIO 块 `0x221C2000` 和 `0x221C8000`。同一程序中还有源文件名 `BootMemMapLib.c`。

该函数本身不把记录写入硬件。它通过协议 ID `0x3E` 的调用（`FUN_148298A4`）获得一个接口对象，然后以该表调用对象的第一个条目。

提供者现已确定。SBL1 从偏移 `0x148B5060` 处的静态表中填充协议注册表（51 个条目，步长 `0x30`，由 `FUN_14829BB8` 读取）。第 40 个条目的 ID 为 `0x3E`，其对象位于 `0x148B72C0`。该对象的第一个方法 `0x14854240` 就是内存映射构建器以 `(table, 0, 0)` 调用的函数。反编译显示，它：

- 根据 DDR 大小确定页表大小（`FUN_148549B4`），
- 分配页表（`FUN_148809C4`），并把表基址和大小写入输出参数，
- 遍历 `table + 0x18` 处的区域记录，直到遇到零地址，并将每个区域映射进页表，
- 在返回前设置 MMU 属性。

因此协议 `0x3E` 是 AArch64 第一阶段转换表服务，区域表是它的输入。已观察。证据见 `data/ghidra/sbl1_protocol_table.txt` 与 `data/ghidra/sbl1_proto3e_mmu_decompiled.txt`。

每条记录各字段的确切含义尚未确认，因此本文不为每条记录指定大小。

### 1c. 主存根（内容呈数据特征）

偏移 0 处的第一个程序，就是机器字段为不寻常值 `EM_M32` 的那个。它是整个容器中最不清楚的部分。它的区域中有版本信息块 `SEQ_FW_RELEASE_BUILD_VERSION_STRING=r10` 与 `SEQ_FW_BUILD_TYPE_STRING=RELEASE`，位于偏移 `0x145E4`。证书和 XPU 字符串位于 TME 区域，`Secure Boot:` 位于 SBL1 区域。

对其内容进行的测试（`data/analysis/isa_tests.txt`、`data/ghidra/xbl_primary_stub_thumb2_disasm.txt`）：

- **逐字解码率。** Hexagon 为 0.774，ARM32 为 0.769，无法区分。我之前用作 Hexagon 对照的 `adsp.b02` 有 62% 的字为零，是数据而不是代码，因此它不是有效的对照。该解码率无法区分两种指令集。
- **函数边界指令。** 以下均未出现：Hexagon 的 `allocframe` 与 `dealloc_return`；ARM32 的 `push {..., lr}`、`pop {..., pc}`、`bx lr`；AArch64 的 `ret`（`0xD65F03C0`）；RISC-V 的 `ret`（`0x00008067`）。已知 AArch64 代码每千个字有 24.6 个 `ret`，说明测试有效。
- **从起始地址开始的 Ghidra 反汇编。** 从偏移 0 开始按 Thumb-2 反汇编，在第一个错误之前能解码 669 条指令。在同一方法下，已知 AArch64 代码从入口可解码 2,000 条指令。Thumb-2 的输出是一个重复模式（`stmia r4!,{r0}` 后接 `adds r0,#0x3`，数值逐步趋向 `cmp r0,#0xf6`）。这更像一张数值表，而不是代码。Ghidra 的 ARM32 解码为 0 条指令，Hexagon 解码为 1 条。
- **熵。** 该区域大部分在每字节 6.5 到 7.1 比特之间。偏移 `0x10000` 处的一个 64 KB 块较低（每字节 3.6 比特）。
- **前 112 KB 的字节级检查**（`0x2211C000`，`0x1C000` 字节）。从起点开始，ARM32 解码出 0 条指令，Thumb 在前 16 KB 内解码出 164 条指令。27% 的字为零。步长 2 至 32 字之间没有任何一个重复率超过 29%，因此不存在固定的记录长度。zlib 和 LZMA 在偏移 0 至 60 之间都无法解码。伴随段位于 `0x22143000`（640 字节），不以 DER 或 X.509 数据开头，而是以打包字段组成的高通风格头部开头。这些结果都未识别出格式。

结论是：主存根是数据表，不是任何已测试指令集的代码。它的确切格式尚未确定。

## 阶段 2：XBL 配置与转储版本

- `xbl_config.img`（147,456 字节）：打包在 ELF 中的文本配置，XBL 启动时读取。其键与值见下表。
- `xbl_ramdump.img`（708,608 字节）：支持内存转储的另一个 XBL 构建。入口为 `0x80640000`，AArch64。它与 SBL1 共享 `devcfg.bin`、`sbl_pmic_dump.bin` 字符串和 `CPUCPFW region`。

| 键 | 值 | 说明 |
|---|---|---|
| `Version` | 3 | 配置格式版本 |
| `MaxMemoryRegions` | 74 | 内存区域表的大小 |
| `EnableShell` | 0x1 | 启用 XBL shell 选项；出厂构建中它暴露什么功能未验证 |
| `SharedIMEMBaseAddr` | 0x146AA000 | 已由设备树证实（见下文） |
| `DloadCookieAddr` | 0x01FD3000 | 按名称推断为下载模式 cookie 的地址 |
| `DloadCookieValue` | 0x10 | 按名称推断为写入该 cookie 的值 |
| `PilSubsysDbgCookieAddr` | 0x146AA6DC | 按名称推断为外设加载器调试 cookie 的地址 |
| 覆盖层 | `pre-ddr-sxr-aurora-1.0-overlay.dtbo` | 本 SoC 的平台覆盖层 |

cookie 字段的含义来自键名。读取它们的代码在 SBL1 中，尚未反编译。

共享 IMEM 地址 `0x146AA000` 有第二个来源证实。厂商设备树定义了 `qcom,msm-imem@146aa000` 节点，其 `restart_reason` 位于偏移 `0x65C`。虚拟化层的内存映射也将 `0x146AA000` 映射为 16 MB（`data/secure/hyp_mmio_map.tsv`）。

## 阶段 3：安全世界

这些镜像运行在 EL3 或 Hexagon 安全分区中，提供熔丝接口和密钥服务。

| 镜像 | 格式 | 入口 / 段 | 证据 |
|---|---|---|---|
| `tz.img` | ELF64 AArch64 | 入口 `0x14680000`，32 个 `PT_LOAD` | 最前面的指令写入 `tpidr_el0` 和 `tpidr_el1`，随后读取 `sctlr_el3`，这是 EL3 初始化。已验证。 |
| `hyp.img` | ELF64 AArch64 | 入口 `0x80000000`，5 个 `PT_LOAD` | `HypX Version Not Supported!`、`smem_init`、`PILSubsys_getArbFuseBank`。已观察。 |
| `devcfg.img` | ELF64 AArch64 | 2 个 `PT_LOAD` | `PM_QFPROM_FLAG`、`tgt_cpucp_config`、`fp_sensor_version`。已观察。 |
| `keymaster.img` | ELF64 AArch64 | 5 个 `PT_LOAD` | `KEYMASTER_SET_VERSION`、`KEYMASTER_GET_VERSION`、`osVersion`。已观察。 |
| `uefisecapp.img` | ELF64 AArch64 | 5 个 `PT_LOAD` | `CertRSA2048SHA256Guid`、`pkcs7_secboot_hash`、`pbl_secx509_parse_version`。已观察。 |
| `featenabler.img` | ELF64 AArch64 | 5 个 `PT_LOAD` | `soc_hw_version`、`ConfigureSwFuse`、`DisplayCore_EnableSwFuse`。已观察。 |
| `multiimgqti.img`、`multiimgoem.img` | ELF64 | 各 1 个 `PT_LOAD` | 几乎没有可读字符串，未分析。 |

### TrustZone 细节

`tz.img` 中描述熔丝接口的字符串：

- `qsee_fuse_read`、`qsee_fuse_write`、`qsee_blow_sw_fuse`、`qsee_is_sw_fuse_blown`
- `OEM_rot_pk_hash1_fuse_values`、`OEM_rot_enc_key1_fuse_values`
- `oem_defer_fuse_prov_operation`
- `invoke-oem-spare-fuses failed: 0x%x, 0x%x, 0x%x`

这些名称表明，信任根的密钥哈希和一个加密密钥哈希是以熔丝值保存的，并且存在一个延迟的熔丝配置步骤。已观察。

#### MMIO 表及其映射器

TrustZone 在 `0x1C141C40` 处有一张表，由五个 16 字节条目组成。每个条目包含一个 32 位基址和一个 32 位计数：

| 索引 | 基址 | 计数 | 说明 |
|---:|---|---:|---|
| 0 | `0x221C0000` | 8 | |
| 1 | `0x221C4000` | 4 | |
| 2 | `0x221C2000` | 8 | |
| 3 | `0x221C8000` | 8 | QFPROM 块 |
| 4 | `0x010C0000` | 8 | |

有两个函数读取该表：`FUN_1C067548` 和 `FUN_1C067598`。每个函数接收一个索引，拒绝大于 4 的值，读取 `基址` 与 `计数`，并以两次基址、计数和一个标志调用 `FUN_1C03ACAC`。第一个函数传入标志 `0x9041`，第二个传入 `0x9061`。两者各有 16 处调用点：15 处 `BL` 与 1 处尾调用 `B`。索引 0 到 4 都以两种标志被使用（`data/secure/tz_mmio_table_users.txt`；映射器反编译见 `data/ghidra/tz_mmio_mapper_decompiled.txt`）。

`FUN_1C03ACAC` 加锁，调用 `FUN_146816F4`，然后解锁。`FUN_146816F4` 用基址、第二个基址、计数和标志构造一个 32 字节的请求，然后调用 `FUN_14681A68`。后者是一个一阶段转换表映射器：对每个范围，它把二级和三级描述符写入正在使用的转换表，并发出 `TLBI`、`DSB` 和 `ISB` 维护指令。`FUN_146816F4` 中没有 `SMC` 指令，因此这些操作都留在 TrustZone 内部完成。

用 `FUN_14682D04` 解码标志（`data/ghidra/tz_mmio_mapper_decompiled.txt`）：

- `0x9041` 与 `0x9061` 只相差一位，即第 5 位。该位设置描述符的第 7 位，即 `AP[2]`，也就是 EL1 的只读位。因此 `0x9041` 以读写方式映射该范围，`0x9061` 以只读方式映射。
- 两者都设置 `UXN` 和 `PXN`（禁止执行）、内部共享，以及访问标志。两者都选择 MAIR 属性索引 1。该属性索引很可能对应设备内存，这是推断。
- 映射器把两个基址参数当作虚拟地址和物理地址。这里两者相同，因此是恒等映射，与虚拟化层中 `va == pa` 的记录一致。

计数以 KB 为单位。映射器检查 `count & 3`（即 4 KB 页的整数倍），并把 `count × 0x400` 加到起始地址上得到结束地址。因此 QFPROM 条目 `0x221C8000` 计数为 8，在 TrustZone 中覆盖 8 KB。这是从映射器的运算推断出来的。

该表只被上述两个函数读取。它们的 30 个调用点，以及各调用点传入的索引，列在 `data/secure/tz_mmio_table_users.txt` 中。

### Featenabler

`featenabler` 决定某一芯片版本支持哪些功能。它读取 `soc_hw_version`，并为每个功能 ID 调用 `ConfigureSwFuse`。出错时记录 `ConfigureSwFuse failed for feature_id` 和 `feature id %li not supported for soc_hw_version %x`。这一机制是按硬件版本门控的软件熔丝。已观察。

## 阶段 4：UEFI 与 ABL

- `uefi.img`：ELF64，`EM_ARM`，入口 `0xA7000000`，1 个 `PT_LOAD`。字符串涵盖启动设备检测（`UFS`、`eMMC`、`NAND`、`NVME`、`SPI`、`Flashless`）、多核启动（`AuxBootStrap_%d`、`Continue booting UEFI on Core %d`），以及平台配置（`uefiplatLA.cfg`、`OsTypeString`）。它还提到 `qsee/mink/oem/config/aurora/oem_config.xml`（本 SoC 的 MINK 配置）和 `data.load.elf`。已观察。
- `abl.img`：ELF32，`EM_ARM`，入口 `0x9FA00000`。几乎没有可读字符串。其指令集与作用未确定。我对它进行的条件码与 Thumb 测试都没有定论；在已知的 ARM32 基带二进制上，同样的条件码测试也失败，因此我不依赖它。
- `imagefv.img`：ELF32 ARM，20 KB，很可能是固件卷。未验证。

`uefi` 是更可能的加载程序。SBL1 的子系统列表和镜像名表都包含 `uefi` 或 `APPSBL`，且 `uefi.img` 是 UEFI DXE 卷。`abl.img` 中不含 UEFI、Android 启动或 fastboot 字符串。已观察。唯一一处对 `uefi` 字符串的代码引用（`FUN_14839AE4` 中的 `0x14839E54`、`0x14839E84`）位于 PMIC 配置解析（`/sw/pmic/pm/sw-config`）中，而不在镜像加载器里。镜像名表中的 `APPSBL` 条目也没有代码引用。因此跳转代码未找到，SBL1 实际跳转到哪个镜像仍未确认。反编译见 `data/ghidra/sbl1_fn14839ae4_uefi_ref_decompiled.txt`。

## 阶段 5 及之后

Android 验证启动见第 03 节。内核、ramdisk 与厂商分区见第 04 节。远程处理器见第 05 节。眼镜端服务见第 09 节。

## 启动链中的 QFPROM 引用

基址 `0x221C8000` 出现在以下位置。

| 位置 | 内容 |
|---|---|
| SBL1（`xbl.img` 中的 AArch64 程序） | `0x1482CED4` 处的一处直接代码引用，位于上述内存映射函数中 |
| TME（RISC-V 程序） | 无引用 |
| TrustZone（`tz.img`） | 两个字面量池槽位；`0x1C141C40` 处的 MMIO 表由上述映射器函数读取 |
| 虚拟化层（`hyp.img`） | 内存映射中以 `0x3000` 大小映射该块（第 06 节） |
| `xbl_ramdump.img` | 两个字面量池槽位（与 SBL1 相同的模式） |
