# 02 - Boot chain, stage by stage

[中文版](02-boot-chain.zh-CN.md)

This document goes through the images in boot order. Each section gives what the file contains and what the evidence shows. The XBL image is a container of three programs, not one loader.

Code-level statements in this document come from headless Ghidra 12.1.3 (decompilation and disassembly). Their output is in `data/ghidra/`.

## Stage 0: Boot ROM (PBL)

The primary boot loader is in mask ROM on the SoC. It runs first after reset, loads XBL from storage, and checks XBL's signature. The OTA does not include it.

Evidence that the chain depends on PBL: the XBL strings include `PBL Patch Ver: %d`, `PBL freq: %d MHZ`, and the source path `tme_messages/src/ImageAuthPblUtils.cpp`. These are observed. The internals of PBL are unverified.

## Stage 1: XBL container

File: `xbl.img`, 978,944 bytes. It holds three ELF programs back to back. Each one has its own header and its own load segments.

| Offset | Format | Entry | Identified as | Evidence |
|---|---|---|---|---|
| `0x00000` | ELF32, `e_machine = 1` (`EM_M32`) | `0x2211C000` | primary stub | two `PT_LOAD` segments, 114 KB of content. Its content is data-like (see 1c). |
| `0x1C2F4` | ELF32, `EM_RISCV` | `0x20412800` | TME firmware | source paths `tmeFwMain`, `tme_com`, `tme_messages`, `IPCC_*`, `xport_qmp_config_tme.c`; `TME_FW_VERSION_STRING=ssg.tmefw.1.0.1-00467-release`, built `October 05 2025` |
| `0x4AFC4` | ELF64, `EM_AARCH64` | `0x14824FA8` | SBL1, the secondary bootloader core | `SBL1 BUILD @ 13:02:53 on Mar  5 2026`, `QC_IMAGE_VERSION_STRING=BOOT.MXF.2.2-00536-AURORA-1.149279.3`, `OEM_IMAGE_VERSION_STRING=ip-10-195-200-195` |

The offsets were found by searching for the ELF magic. `data/xbl/xbl_container.txt` has the same table, and `data/xbl/string_regions.txt` maps each string to its region.

The two build dates are separate builds: TME on 5 October 2025, SBL1 on 5 March 2026.

### 1a. TME firmware (RISC-V)

This is a RISC-V 32-bit program that runs on the TME core. It provides the image-authentication services that XBL and PBL call through `tme_messages`, and it talks to the other processors through IPCC interrupts and the GLink transport (`tme_com/GLinkPort.cpp`, `xport_qmp_config_tme.c`).

The certificate names are in this region:

- `SRoT MBNv7 Image Signing Root CA 6 SubCA 10`, and related `SRoT MBNv7 Image Signing Root CA 60` strings.
- `Greatwhite_FW_Root_01`, `Greatwhite_FW_Root_11`, `Greatwhite_FW_Root_21`, `Greatwhite_FW_Root_31`, and `Greatwhite_FW_Signing_31`.

The `Greatwhite_FW_*` names are the device-specific firmware roots. Observed.

The TME image does not refer to the QFPROM base. A search of its code for `LUI` with the QFPROM immediates, and for the literal `0x221C8000`, found nothing (`data/xbl/tme_lui_scan.txt`). TME may reach fuses through its own interfaces. Observed, not proved.

`XPUPolicyVersion = 4.5` is also in this region. An XPU is a Qualcomm bus-access protection block, so this value is the version of the access policy. Its contents are not analysed.

### 1b. SBL1 (AArch64)

This is the program that does the bring-up. Its entry is `0x14824FA8`. The strings `Secure Boot:`, `PBL Patch` and `Image Load, Start` come from this region.

Its source-file strings cover the whole job:

- Boot control: `boot_pre_ddr_dtb_load`, `boot_post_ddr_dtb_load`, `boot_clock_init_rpm`, `boot_cdt_init`, `boot_fedl_check`, `boot_dload_entry`.
- Memory and DDR: `boot_ddr.c`, `boot_ddr_info.c`, `boot_ddr_share_data_to_aop`, `boot_populate_ddr_details_shared_table`, `BootMemMapLib.c`.
- Other processors: `boot_prepare_cpucp`, `boot_reset_cpucp`, `boot_cpucp.c`, `boot_shrm_mini_dump_init`, `boot_vsense.c`.
- Image loading and checks: `boot_mbn_loader.c`, `boot_elf_loader.c`, `boot_elf_auth.c`, `boot_blacklist.c`, `boot_qsee.c`, `boot_whitelist_prot.c`.
- Crash handling: `error_handler_el3.c`, `sbl_error_handler: DDR not initialized`, `boot_dload_dump_security_regions`, `boot_ramdump.c`.
- Shared memory and debug: `boot_smem_init`, `boot_smem_debug_init`, `boot_smem_alloc_for_minidump`, `/dev/icbcfg/boot`, `boot_eud.c`.

SBL1 has a subsystem list that includes `tz`, `mss`, `uefi`, `adsp`, `aop` and `ssc`. That list is in the same string block, at offset `0xCD0F9`. It is the strongest hint that `uefi` is the next loader. Observed.

The next-stage names are also in SBL1's string table. A block of image names at `0x813D0`–`0x813F8` reads `CPUCP_DTB`, `QSEE Dev Config`, `QSEE` and `APPSBL`. A separate `uefi` string sits at `0x82171`. `abl` does not appear there, and it is not in the `uefi` image either. `uefi.img` contains `UEFI DXE` and DXE core strings (`Dxe Core  FV decompression failed`, `DXE Heap`, `AddDecompressdFvForDxe failed`). These are the strings of a UEFI DXE firmware volume, so `uefi.img` is a UEFI payload. Observed. That `uefi` is loaded as `APPSBL` is inferred: SBL1's loader code that uses these names is not yet decompiled.

SBL1 refers to `shrm.elf`, `devcfg.bin`, `cpr.bin` and `_dcb.bin` by file name. These are the images it loads. The code that loads them is not yet decompiled.

#### The memory-map function

The QFPROM reference (section 06) sits inside one function, `FUN_1482CD30` in Ghidra, which is the SBL1 boot memory-map builder. It has one caller, at `0x14825B3C`.

The decompiled function (`data/ghidra/sbl1_memmap_decompiled.txt`) builds a table of region records on the stack. Each record holds a start address, a second address, a size and a class value. The class values in the table are `0x8`, `0x22`, `0x23`, `0x25`, `0x26` and `0x27`. Among the regions named are SBL1's own image (`0x14800000`, `0x14824000`), shared IMEM (`0x146AA000`), the TrustZone image (`0x14680000`), and the MMIO blocks `0x221C2000` and `0x221C8000`. The `BootMemMapLib.c` source name is in the same program.

The function does not write the records to hardware itself. It obtains an interface object through a call with protocol ID `0x3E` (`FUN_148298A4`), and then calls the object's first entry with the table.

The provider is now known. SBL1 fills its protocol registry from a static table at `0x148B5060` (51 entries, stride `0x30`, read by `FUN_14829BB8`). Entry 40 has ID `0x3E`, and its object is at `0x148B72C0`. The object's first method, `0x14854240`, is the one the memory-map builder calls with `(table, 0, 0)`. Decompiled, it:

- sizes the page tables from the DDR size (`FUN_148549B4`),
- allocates them (`FUN_148809C4`) and writes the table base and size to the out parameters,
- walks the region records at `table + 0x18` until it reaches a zero address, and maps each into the tables,
- sets the MMU attributes before returning.

So protocol `0x3E` is the AArch64 stage-1 translation-table service, and the region table is its input. Observed. Evidence: `data/ghidra/sbl1_protocol_table.txt` and `data/ghidra/sbl1_proto3e_mmu_decompiled.txt`.

The exact per-record field meanings are not confirmed, so this document does not assign a size to each record.

### 1c. The primary stub (content is data-like)

The first program, at offset 0, is the one with the odd machine value `EM_M32`. It is the least understood part of the container. Its region holds the version block `SEQ_FW_RELEASE_BUILD_VERSION_STRING=r10` and `SEQ_FW_BUILD_TYPE_STRING=RELEASE` at offset `0x145E4`. The certificate and XPU strings are in the TME region, and `Secure Boot:` is in SBL1's.

The tests on its content (`data/analysis/isa_tests.txt`, `data/ghidra/xbl_primary_stub_thumb2_disasm.txt`) are:

- **Per-word decode rate.** Hexagon 0.774, ARM32 0.769. This does not separate the two. The Hexagon control I used earlier (`adsp.b02`) is 62% zero words, so it is data, not code, and it is not a valid calibration. The rate does not separate the two ISAs.
- **Function-boundary instructions.** None of these appear: Hexagon `allocframe` and `dealloc_return`; ARM32 `push {..., lr}`, `pop {..., pc}`, `bx lr`; AArch64 `ret` (`0xD65F03C0`); RISC-V `ret` (`0x00008067`). Known AArch64 code has 24.6 `ret` per 1,000 words, so the test works.
- **Ghidra disassembly from the start address.** Disassembled from offset 0 as Thumb-2, 669 instructions decode before the first error. Known AArch64 code decodes 2,000 instructions from its entry in the same method. The Thumb-2 output is a repeating pattern (`stmia r4!,{r0}` followed by `adds r0,#0x3`, with values stepping towards `cmp r0,#0xf6`). That reads as a table of values, not code. Ghidra's ARM32 decode gives 0 instructions, and its Hexagon decode gives 1.
- **Entropy.** Most of the region is between 6.5 and 7.1 bits per byte.
- **Hexagon decode runs (Ghidra, raw import of the stub segment).** Starting at offsets 0x8, 0x10, 0x20, 0x40, 0x80 and 0xF0, the Hexagon decoder produces runs of 2 to 10 instructions before an invalid packet. A real Hexagon code region produces long runs. Recorded as a rejection, not a proof of format.
- **Capstone run lengths are not a test.** Capstone decodes almost any 4-byte pattern as ARM or RISC-V, so its long runs say nothing about the ISA. One 64 KB chunk at offset `0x10000` is lower (3.6 bits per byte).
- **Byte-level checks on the first 112 KB of the segment** (`0x2211C000`, `0x1C000` bytes). ARM32 decodes 0 instructions from the start and Thumb decodes 164 instructions in the first 16 KB. 27% of its words are zero. No stride from 2 to 32 words repeats more than 29% of the time, so there is no fixed record size. zlib and LZMA do not decode from offsets 0 to 60. The companion segment at `0x22143000` (640 bytes) does not start with DER or X.509 data; it begins with a Qualcomm-style header of packed fields. None of these results identifies the format.

The conclusion is that the primary stub is a data table, not code of a tested ISA. Its exact format is not identified.

### Where the TrustZone region is registered

The image regions are registered in `sbl1_config.c`, in a routine at `0x1482DAE4`. It calls `FUN_1482E6C4` and then `FUN_148612EC` (`boot_ram_partition_drv.c`). That function registers three regions through `FUN_148615E0`: SBL1 (`0x14800000`, `0x200000`, type 4), TrustZone (`0x14680000`, `0x2B000`, type 5), and a third region at `0xA6E00000` (`0x40000`, type 4). These type values are the same classes used in the memory map. Observed. Evidence: `data/ghidra/sbl1_xblconfig_partition_evidence.txt`.

In the emergency-download path (`boot_dload_entry`, `0x1482E274`), SBL1 also calls a load-and-authenticate interface with `(0x14680000, 0x2B000, 0x4001)`. The normal path's authenticate call is not yet located. The jump into TrustZone and the per-thread context it receives in `x0` (the `tpidr_el0` value in the entry code) are also not yet located.

## Stage 2: XBL configuration and ramdump builds

- `xbl_config.img` (147,456 bytes): a text configuration packed into an ELF, read by XBL at boot. Its keys and values are below.
- `xbl_ramdump.img` (708,608 bytes): a separate XBL build with RAM-dump support. Its entry is `0x80640000`, AArch64. It shares the `devcfg.bin` and `sbl_pmic_dump.bin` strings and the `CPUCPFW region`.

| Key | Value | Notes |
|---|---|---|
| `Version` | 3 | config format version |
| `MaxMemoryRegions` | 74 | size of the memory-region table |
| `EnableShell` | 0x1 | enables the XBL shell option; what it exposes in a shipping build is unverified |
| `SharedIMEMBaseAddr` | 0x146AA000 | confirmed by the device tree (see below) |
| `DloadCookieAddr` | 0x01FD3000 | address of the download-mode cookie, going by the name |
| `DloadCookieValue` | 0x10 | value for that cookie, going by the name |
| `PilSubsysDbgCookieAddr` | 0x146AA6DC | address of a debug cookie for the peripheral loader, going by the name |
| overlay | `pre-ddr-sxr-aurora-1.0-overlay.dtbo` | platform overlay for this SoC |

The cookie meanings come from the key names. The code that reads them is in SBL1 and has not been decompiled.

Shared IMEM at `0x146AA000` is confirmed by a second source. The vendor device tree defines `qcom,msm-imem@146aa000` with a `restart_reason` at offset `0x65C`. The hypervisor's memory map also maps `0x146AA000` with a size of 16 MB (`data/secure/hyp_mmio_map.tsv`).

## Stage 3: Secure world

These images run at EL3 or in the Hexagon secure partition. They provide the fuse API and the key services.

| Image | Format | Entry / segments | Evidence |
|---|---|---|---|
| `tz.img` | ELF64 AArch64 | entry `0x14680000`, 32 `PT_LOAD` | the first instructions write `tpidr_el0` and `tpidr_el1`, then read `sctlr_el3`. EL3 setup. Verified. |
| `hyp.img` | ELF64 AArch64 | entry `0x80000000`, 5 `PT_LOAD` | `HypX Version Not Supported!`, `smem_init`, `PILSubsys_getArbFuseBank`. Observed. |
| `devcfg.img` | ELF64 AArch64 | 2 `PT_LOAD` | `PM_QFPROM_FLAG`, `tgt_cpucp_config`, `fp_sensor_version`. Observed. |
| `keymaster.img` | ELF64 AArch64 | 5 `PT_LOAD` | `KEYMASTER_SET_VERSION`, `KEYMASTER_GET_VERSION`, `osVersion`. Observed. |
| `uefisecapp.img` | ELF64 AArch64 | 5 `PT_LOAD` | `CertRSA2048SHA256Guid`, `pkcs7_secboot_hash`, `pbl_secx509_parse_version`. Observed. |
| `featenabler.img` | ELF64 AArch64 | 5 `PT_LOAD` | `soc_hw_version`, `ConfigureSwFuse`, `DisplayCore_EnableSwFuse`. Observed. |
| `multiimgqti.img`, `multiimgoem.img` | ELF64 | 1 `PT_LOAD` each | almost no readable strings. Not analysed. |

### TrustZone details

The fuse interface strings in `tz.img`:

- `qsee_fuse_read`, `qsee_fuse_write`, `qsee_blow_sw_fuse`, `qsee_is_sw_fuse_blown`
- `OEM_rot_pk_hash1_fuse_values`, `OEM_rot_enc_key1_fuse_values`
- `oem_defer_fuse_prov_operation`
- `invoke-oem-spare-fuses failed: 0x%x, 0x%x, 0x%x`

These names show that root-of-trust key hashes and an encryption-key hash are fuse values, and that a deferred provisioning step exists. Observed.

#### The MMIO table and its mapper

TrustZone holds a table of five 16-byte entries at `0x1C141C40`. Each entry is a 32-bit base address and a 32-bit count:

| Index | Base | Count | Note |
|---:|---|---:|---|
| 0 | `0x221C0000` | 8 | |
| 1 | `0x221C4000` | 4 | |
| 2 | `0x221C2000` | 8 | |
| 3 | `0x221C8000` | 8 | the QFPROM block |
| 4 | `0x010C0000` | 8 | |

Two functions read the table: `FUN_1C067548` and `FUN_1C067598`. Each takes an index, rejects values above 4, reads `base` and `count`, and calls `FUN_1C03ACAC` with the base twice, the count, and a flag. The first function passes flag `0x9041`, the second `0x9061`. Each has 16 call sites: 15 `BL` and one tail `B`. Every index from 0 to 4 is used with both flags (`data/secure/tz_mmio_table_users.txt`; the mapper decompile is in `data/ghidra/tz_mmio_mapper_decompiled.txt`).

`FUN_1C03ACAC` takes a lock, calls `FUN_146816F4`, and releases the lock. `FUN_146816F4` builds a 32-byte request from the base, the second base, the count and the flag. It then calls `FUN_14681A68`, which is a stage-1 translation-table mapper. For each range it writes level-2 and level-3 descriptors into the live translation tables, and it issues the `TLBI`, `DSB` and `ISB` maintenance instructions. `FUN_146816F4` contains no `SMC` instruction, so the work stays inside TrustZone.

Decoding the flag, with `FUN_14682D04` (`data/ghidra/tz_mmio_mapper_decompiled.txt`):

- `0x9041` and `0x9061` differ in one bit, bit 5. That bit sets descriptor bit 7, `AP[2]`, which is the read-only bit at EL1. So `0x9041` maps the range read-write and `0x9061` maps it read-only.
- Both set `UXN` and `PXN` (execute-never), inner-shareable, and the access flag. Both select MAIR attribute index 1. The attribute index is probably device memory, which is an inference.
- The mapper treats the two base arguments as virtual and physical. Both are the same value here, so the mapping is an identity mapping, in line with the hypervisor's `va == pa` records.

The count is in KB. The mapper checks `count & 3` (a multiple of 4 KB pages) and adds `count × 0x400` to compute the end address. So the QFPROM entry, `0x221C8000` with count 8, covers 8 KB in TrustZone. This is inferred from the mapper's arithmetic.

The table is read only by the two functions above. Their 30 call sites, with the index each one passes, are listed in `data/secure/tz_mmio_table_users.txt`.

### Featenabler

`featenabler` decides which features a chip revision supports. It reads `soc_hw_version`, and for each feature ID it calls `ConfigureSwFuse`. Errors are logged as `ConfigureSwFuse failed for feature_id` and `feature id %li not supported for soc_hw_version %x`. The mechanism is software fuses gated by hardware revision. Observed.

## Stage 4: UEFI and ABL

- `uefi.img`: ELF64 with `EM_ARM`, entry `0xA7000000`, one `PT_LOAD`. The strings cover boot-device detection (`UFS`, `eMMC`, `NAND`, `NVME`, `SPI`, `Flashless`), SMP bring-up (`AuxBootStrap_%d`, `Continue booting UEFI on Core %d`), and the platform configuration (`uefiplatLA.cfg`, `OsTypeString`). It also names `qsee/mink/oem/config/aurora/oem_config.xml`, a MINK configuration for this SoC, and `data.load.elf`. Observed.
- `abl.img`: ELF32 with `EM_ARM`, entry `0x9FA00000`. It has almost no readable strings. Its ISA and role are not established. The condition-code and Thumb tests I ran on it were inconclusive, and the same condition-code test fails on the known ARM32 modem binary, so I do not rely on it.
- `imagefv.img`: ELF32 ARM, 20 KB, likely a firmware volume. Unverified.

`uefi` is the likelier loader. SBL1's subsystem list and its image-name table both include `uefi` or `APPSBL`, and `uefi.img` is a UEFI DXE volume. `abl.img` contains no UEFI, Android boot or fastboot strings. Observed. The one code reference to the `uefi` string (`0x14839E54`, `0x14839E84`, in `FUN_14839AE4`) is in PMIC configuration parsing (`/sw/pmic/pm/sw-config`), not in an image loader. The `APPSBL` entry in the name table has no code reference. So the handoff code is not found, and which image SBL1 jumps to is still unconfirmed. Decompile: `data/ghidra/sbl1_fn14839ae4_uefi_ref_decompiled.txt`.

## Stage 5 and later

Android verified boot is in section 03. The kernel, the ramdisks and the vendor partition are in section 04. Remote processors are in section 05. The glasses-side services are in section 09.

## QFPROM references across the boot chain

The base address `0x221C8000` appears in these places.

| Where | What is there |
|---|---|
| SBL1 (AArch64 program in `xbl.img`) | one direct code reference at `0x1482CED4`, in the memory-map function (see above) |
| TME (RISC-V program) | no reference |
| TrustZone (`tz.img`) | two literal-pool slots; the MMIO table at `0x1C141C40` is read by the mapper functions above |
| Hypervisor (`hyp.img`) | a memory map that maps the block with size `0x3000` (section 06) |
| `xbl_ramdump.img` | two literal-pool slots (the same pattern as SBL1) |
