# 02 - Boot chain, stage by stage

[中文版](02-boot-chain.zh-CN.md)

This document goes through the images in boot order. Each section gives what the file contains, what the evidence shows, and what is still open. The XBL image is a container of three programs, not one loader.

## Stage 0: Boot ROM (PBL)

The primary boot loader is in mask ROM on the SoC. It runs first after reset, loads XBL from storage, and checks XBL's signature. The OTA does not include it.

Evidence that the chain depends on PBL: the XBL strings include `PBL Patch Ver: %d`, `PBL freq: %d MHZ`, and the source path `tme_messages/src/ImageAuthPblUtils.cpp`. These are observed. The internals of PBL are unverified.

## Stage 1: XBL container

File: `xbl.img`, 978,944 bytes. It holds three ELF programs back to back. Each one has its own header and its own load segments.

| Offset | Format | Entry | Identified as | Evidence |
|---|---|---|---|---|
| `0x00000` | ELF32, `e_machine = 1` (`EM_M32`) | `0x2211C000` | primary stub | two `PT_LOAD` segments, 114 KB of content. No code of any tested ISA matches (see 1c). |
| `0x1C2F4` | ELF32, `EM_RISCV` | `0x20412800` | TME firmware | source paths `tmeFwMain`, `tme_com`, `tme_messages`, `IPCC_*`, `xport_qmp_config_tme.c`; `TME_FW_VERSION_STRING=ssg.tmefw.1.0.1-00467-release`, built `October 05 2025` |
| `0x4AFC4` | ELF64, `EM_AARCH64` | `0x14824FA8` | SBL1, the secondary bootloader core | `SBL1 BUILD @ 13:02:53 on Mar  5 2026`, `QC_IMAGE_VERSION_STRING=BOOT.MXF.2.2-00536-AURORA-1.149279.3`, `OEM_IMAGE_VERSION_STRING=ip-10-195-200-195` |

The offsets were found by searching for the ELF magic. The table lists them in order. `data/xbl/xbl_container.txt` has the same table, and `data/xbl/string_regions.txt` maps each string to its region.

The two build dates are separate builds: TME on 5 October 2025, SBL1 on 5 March 2026.

### 1a. TME firmware (RISC-V)

This is a RISC-V 32-bit program that runs on the TME core. It provides the image-authentication services that XBL and PBL call through `tme_messages`, and it talks to the other processors through IPCC interrupts and the GLink transport (`tme_com/GLinkPort.cpp`, `xport_qmp_config_tme.c`).

The certificate names are in this region:

- `SRoT MBNv7 Image Signing Root CA 6 SubCA 10`, and related `SRoT MBNv7 Image Signing Root CA 60` strings.
- `Greatwhite_FW_Root_01`, `Greatwhite_FW_Root_11`, `Greatwhite_FW_Root_21`, `Greatwhite_FW_Root_31`, and `Greatwhite_FW_Signing_31`.

The `Greatwhite_FW_*` names are the device-specific firmware roots. Observed.

The TME image does not refer to the QFPROM base. A search of its code for `LUI` with the QFPROM immediates, and for the literal `0x221C8000`, found nothing (`data/xbl/tme_lui_scan.txt`). TME may reach fuses through its own interfaces. This is observed, not proved.

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

SBL1 has a subsystem list that includes `tz`, `mss`, `uefi`, `adsp`, `aop` and `ssc`. That list is in the same string block, at offset `0xCD0F9`. It is the strongest hint that `uefi` is the next loader.

SBL1 refers to `shrm.elf`, `devcfg.bin`, `cpr.bin` and `_dcb.bin` by file name. These are the images it loads. The code that loads them is not analysed yet.

#### The memory-map function

The QFPROM reference (section 06) is inside one function, which starts at `0x1482CD30`. The function is called from one place, `0x14825B3C`. The reference is 0x1A4 bytes into the function. Its body writes a set of region descriptors to the stack, and the `BootMemMapLib.c` source name is in the same program. The string references inside the function did not resolve with the simple `ADRP`+`ADD` pattern, so its log messages are not yet read.

### 1c. The primary stub (ISA not established)

The first program, at offset 0, is the one with the odd machine value `EM_M32`. It is the least understood part of the container. Its region holds the version block `SEQ_FW_RELEASE_BUILD_VERSION_STRING=r10` and `SEQ_FW_BUILD_TYPE_STRING=RELEASE` at offset `0x145E4`. The certificate and XPU strings are in the TME region, and `Secure Boot:` is in SBL1's.

The tests run on its code (`data/analysis/isa_tests.txt`) are:

- **Per-word decode rate.** Hexagon 0.774, ARM32 0.769. This does not separate the two. Known Hexagon code scores 0.969 under Hexagon and 0.894 under ARM32.
- **Function-boundary instructions.** None of these appear: Hexagon `allocframe` and `dealloc_return`; ARM32 `push {..., lr}`, `pop {..., pc}`, `bx lr`; AArch64 `ret` (`0xD65F03C0`); RISC-V `ret` (`0x00008067`).
- **Known-code controls.** SBL1 (known AArch64) has 24.6 `ret` per 1,000 words, so the test works. The stub has 0.
- **Entropy.** Most of the region is between 6.5 and 7.1 bits per byte. Code of any ISA usually sits lower. One 64 KB chunk at offset `0x10000` is lower (3.6 bits per byte), which is more like a table or padded data.

The stub has no returns in any ISA I tested, and its entropy is high. The working hypothesis is that it is a compressed or encrypted payload, or a data table, not code. This is unverified.

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

The cookie meanings come from the key names. The code that reads them is in SBL1 and has not been read.

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

#### The MMIO table and its users

TrustZone holds a table of five 16-byte entries at `0x1C141C40`. Each entry is a 32-bit base address and a 32-bit count:

| Index | Base | Count | Note |
|---:|---|---:|---|
| 0 | `0x221C0000` | 8 | |
| 1 | `0x221C4000` | 4 | |
| 2 | `0x221C2000` | 8 | |
| 3 | `0x221C8000` | 8 | the QFPROM block |
| 4 | `0x010C0000` | 8 | |

Two functions use the table. Both take an index in `w0`, reject values above 4, load `base` and `count` from `table + index × 8`, and call a routine with a flag:

- `0x1C067548`: flag `0x9041`. Used from 15 call sites.
- `0x1C067598`: flag `0x9061`. Used from 15 call sites.

Each call site passes one index from 0 to 4. So every block is handled with both flags. The called routine (`0x1C03ACAC`) wraps a call to `0x146816F4` between a lock and an unlock. That routine is in TrustZone's own image. It reads a state byte from its argument at offset `0x80`, and it has three return paths. It contains no `SMC` instruction, so the call does not leave to EL3. (`tz.img` as a whole has nine `SMC` instructions.) Its purpose is not established. The flags may separate read-only from read-write treatment, but that is unverified.

For the QFPROM block (index 3): flag `0x9041` is set from three sites (`0x1C084A30`, `0x1C084AEC`, `0x1C084B94`) and flag `0x9061` from three more (`0x1C065304`, `0x1C084B08`, `0x1C084BB8`). The count `8` and its unit are not known.

### Featenabler

`featenabler` decides which features a chip revision supports. It reads `soc_hw_version`, and for each feature ID it calls `ConfigureSwFuse`. Errors are logged as `ConfigureSwFuse failed for feature_id` and `feature id %li not supported for soc_hw_version %x`. The mechanism is software fuses gated by hardware revision. Observed.

## Stage 4: UEFI and ABL

- `uefi.img`: ELF64 with `EM_ARM`, entry `0xA7000000`, one `PT_LOAD`. The strings cover boot-device detection (`UFS`, `eMMC`, `NAND`, `NVME`, `SPI`, `Flashless`), SMP bring-up (`AuxBootStrap_%d`, `Continue booting UEFI on Core %d`), and the platform configuration (`uefiplatLA.cfg`, `OsTypeString`). It also names `qsee/mink/oem/config/aurora/oem_config.xml`, a MINK configuration for this SoC, and `data.load.elf`. Observed.
- `abl.img`: ELF32 with `EM_ARM`, entry `0x9FA00000`. It has almost no readable strings. Its ISA and role are not established. The condition-code and Thumb tests I ran on it were inconclusive, and on the known ARM32 modem binary the condition-code test also fails, so I do not rely on it.
- `imagefv.img`: ELF32 ARM, 20 KB, likely a firmware volume. Unverified.

`uefi` is the likelier loader. SBL1's subsystem list includes `uefi`, and `abl` does not appear in any image name or string I searched. This is observed, not proved.

## Stage 5 and later

Android verified boot is in section 03. The kernel, the ramdisks and the vendor partition are in section 04. Remote processors are in section 05. The glasses-side services are in section 09.

## QFPROM references across the boot chain

The base address `0x221C8000` appears in these places. The method is in `data/xbl/sbl1_qfprom_xref.txt`.

| Where | What is there |
|---|---|
| SBL1 (AArch64 program in `xbl.img`) | one direct code reference at `0x1482CED4`, in the memory-map function (see above) |
| TME (RISC-V program) | no reference |
| TrustZone (`tz.img`) | two literal-pool slots; the MMIO table at `0x1C141C40` is used by the functions above |
| Hypervisor (`hyp.img`) | a memory map that maps the block with size `0x3000` (section 06) |
| `xbl_ramdump.img` | two literal-pool slots (the same pattern as SBL1) |
