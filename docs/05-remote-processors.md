# 05 - Remote processors and their firmware

[中文版](05-remote-processors.zh-CN.md)

The SoC has processors besides the application CPU, and each runs its own firmware. The boot chain loads some of them. The kernel loads others at runtime from the vendor partitions. This document identifies each one from its headers, strings and file listings. None of them has been disassembled yet.

| Processor | Image | Format | Status |
|---|---|---|---|
| Always-On Processor (AOP) | `aop.img`, `aop_config.img` | ELF32, ARM | identified from strings |
| CPU Control Processor (CPUCP) | `cpucp.img` | ELF32, RISC-V | identified; boot strings read |
| Shared Resource Manager (SHRM) | `shrm.img` | ELF32, RISC-V | identified; DDR firmware version read |
| QUP firmware | `qupfw.img` | ELF32, Hexagon (`EM_QDSP6`) | identified as Hexagon; role unknown |
| Audio and compute DSPs | `dsp.img` | ext4, `adsp` and `cdsp` | listed (section below) |
| Modem | `modem.img` | FAT | listed (section below) |
| Bluetooth | `bluetooth.img` | FAT | listed (section below) |
| TME (inside XBL) | part of `xbl.img` | RISC-V | see section 02 |

## AOP (`aop.img`, `aop_config.img`)

`aop.img` is a 32-bit ARM ELF with seven `PT_LOAD` segments. Its entry point is `0x0B000009`. The low bit is set, which is the ARM Thumb convention, so the entry is Thumb code. The instruction pattern agrees: `bx lr` (`0x4770`) appears 6.2 times per 1,000 halfwords, against a random baseline near 0.015. So the code is Thumb-2. A Ghidra disassembly from the entry confirms it: the entry loads function pointers from a literal pool, calls them, and returns with `bx r0` (`data/ghidra/aop_entry_thumb2_disasm.txt`).

The version string is `QC_IMAGE_VERSION_STRING=AOP.HO.4.0-00605-AURORA_E-1`. `AOP.HO` names the AOP image family and `AURORA` names the SoC. Verified as text.

The image contains `wlan_hamilton`, which points at the Hamilton Wi-Fi/Bluetooth combo. The vendor properties name the same part as the Bluetooth SoC. Observed.

`OEM_IMAGE_VERSION_STRING` holds a build host name. It is not analysed further.

`aop_config.img` is a 16 KB ELF with two segments and no readable strings.

## CPUCP (`cpucp.img`)

A 32-bit RISC-V ELF (`EM_RISCV`), entry `0x90`, seven `PT_LOAD` segments. Verified from the header.

Boot strings: `CPUCP boot started` and `SCMI init Done`, verified as text. SCMI (System Control and Management Interface) is the Arm standard that lets an application CPU ask a management processor for power, clock and performance changes. The strings suggest CPUCP implements the SCMI server side on this platform. Observed; not yet traced in code.

Two other images refer to CPUCP. `xbl_ramdump` names a `CPUCPFW region` and `CPUCPFW.BIN`, so XBL reserves memory for it. `devcfg` has `tgt_cpucp_config`, a per-target configuration block. SBL1 has `boot_prepare_cpucp` and `boot_reset_cpucp`, so SBL1 starts and resets CPUCP. Observed.

## SHRM (`shrm.img`)

A 32-bit RISC-V ELF, entry `0x200000`, two `PT_LOAD` segments. Verified from the header.

It contains `DDR_FW version : 275.0.0`. The name indicates DDR-related firmware, probably memory training or DDR power management. The role is unverified. SBL1 has `boot_shrm_mini_dump_init`, and XBL refers to a file named `shrm.elf`, which suggests SBL1 loads this image. Observed.

## QUP firmware (`qupfw.img`)

A Hexagon ELF with `e_machine = EM_QDSP6` and `e_flags = 0x3`. It has eleven `PT_LOAD` segments and a Qualcomm hash segment. `e_entry` is zero, which is unusual for a standalone image. It is more likely a library or an overlay. Verified from the header.

The image has no functional strings. It does carry a certificate chain (`Qualcomm Technologies, Inc.`, `Qualcomm Cryptographic Operations`, `SRoT MBNv7 Image Signing Root CA 6`, and `CASS - SBL4` near `0xB5FF`). Its role is unknown. The name suggests the Qualcomm Universal Peripheral (QUP) serial blocks, but that is a guess.

The layout is a Qualcomm image format. The `0x1000` segment begins with `QSI ` and holds a table of (offset, size) pairs. The `0x6328` segment begins with `SEFW`. Ghidra's Hexagon decode starts producing plausible instructions from `0x1100` onward (for example `memw R20,(R20+#0x1c)`), but the sequence is dominated by repeated `memw` patterns, so the code boundary is not established.

Earlier drafts said QUP holds real Hexagon code. That was wrong, because the decode rate was not a test of code. Whether `qupfw.img` contains any code, and where its entry is, is not established.

## Audio and compute DSPs (`dsp.img`)

An ext4 image. Its top-level directories are `adsp`, `cdsp` and `lost+found`. The `sdsp` directory exists but is empty in this build. Verified by listing the image. The earlier note that `sdsp` held firmware was wrong. The image is mounted at `/vendor/dsp` (section 04).

### `adsp` (34 files)

Hexagon shared objects and skeleton libraries for the application DSP. They group by function:

- Audio codecs: `aac_dec_module.so.1`, `aac_enc_etsi_module.so.1`, `flac_dec_module.so.1`, `lc3_dec_module.so.1`, `lc3_enc_module.so.1`, `liblc3_enc.so`, `liblc3qDec.so`, `sbc_dec_module.so.1`, `sbc_enc_module.so.1`, `spf-lc3-decoder.so.1`. The LC3 and SBC codecs are the Bluetooth audio formats.
- Voice processing: `fluence_bs_module_fvxii.so.1`, `fluence_ef_module_fvxii.so.1`, `fluence_nn_module_fvxii.so.1`, `fluence_pro_vc_module_fvxii.so.1`, `ffecns_module_VUI_vii.so.1`, `smecns_v2_module_fvxii.so.1`. The `fluence` and `ecns` names are the echo-cancellation and noise-suppression stages.
- Audio framework: `AudioSphereModule.so.1`, `SAPlusCmnModule.so.1`, `CFCM.so.1`, `acd_module.so.1`, `sdd_module.so.1`.
- Sensors and system: `libsns_device_mode_skel.so`, `libsns_direct_channel_skel.so`, `libsns_dynamic_loader_skel.so`, `libsns_remote_proc_state_skel.so`, `libsysmon_skel.so`, `libsysmondomain_skel.so`, `libsysmonquery_skel.so`, `libstabilitydomain_skel.so`.
- Runtime: `fastrpc_shell_0`, `libc++.so.1`, `libc++abi.so.1`.

The two text files `map_SHARED_LIBS_aurora.adsp_la.prodQ.txt` and `map_SSC_SHARED_LIBS_...` list the library paths as `../../build/ms/dynamic_modules/aurora.adsp_la.prod/…`. That is the build path for this image. Verified.

### `cdsp` (18 files)

Compute DSP. Notable items:

- `libevadsp_3_0.so` and `libevadsp_3_0_intermediate.so`: an EVA library. `msm-eva.ko` in the kernel is the matching kernel driver. The name points to an edge-video-analytics or vision workload. Unverified.
- `libsynx.so`, `libsynx_os.so`, `libsynx_threadutils.so`: the synx synchronisation objects, matching `synx-driver` in the kernel.
- `ubwcdma_dynlib.so`: UBWC (compressed buffer) DMA support.
- `libbenchmark_skel.so`, `libcrm_test_skel.so`: test and benchmark skeletons.
- `fastrpc_shell_3`, `fastrpc_shell_unsigned_3`: FastRPC shells for the compute DSP.

The kernel modules that load these images are `cdsp-loader.ko`, `adsp_loader_dlkm.ko`, `q6_dlkm.ko`, `mdt_loader.ko` and `frpc-adsprpc.ko`.

## Modem (`modem.img`)

A FAT16 image of 36.5 MB in 165 files. Listing: `data/remote/modem_listing.txt`. Verified with a FAT reader that handles long names.

Layout:

- `/image/kiwi/`: the main modem set. `amss.bin` (7.46 MB) and `amss20.bin` (6.50 MB) are the modem firmware images. `Data.msc` and `Data20.msc` are data sections. `bdwlan.elf` and `bdwlan.elf.xz` are Wi-Fi board data. `regdb.bin` is the wireless regulatory database. `phy_ucode.elf` and `phy_ucode20.elf` are PHY microcode. `qdss_trace_config_v1.cfg` and `v2.cfg` configure trace output.
- `/image/adsp.b00` to `adsp.b41` (with the header file `adsp.mdt`): the application DSP firmware itself, split into 40 loadable segments and a signature segment. Observed as a Hexagon ELF with entry `0x87600000`. The segment structure, the SHA-384 hash table, the signing chain and the trusted applications in the same image are in section 16. An earlier draft of this section said these were not the application DSP firmware; that was wrong. `cdsp.b00` to `cdsp.b12` is the compute DSP firmware, and it is described there too.

`amss.bin` is a 32-bit ELF with `e_machine = 0x28` (ARM). `kiwi` is the directory name the build uses for this modem configuration. Verified from headers. The name is not explained.

## Bluetooth (`bluetooth.img`)

A FAT16 image of 0.78 MB in 51 files. Listing: `data/remote/bluetooth_listing.txt`.

- `hmtbtfw10.tlv` and `hmtbtfw20.tlv`: Bluetooth firmware, in the TLV format.
- `hmtbtfw20.ver`: `BTFW.HAMILTON.2.0.0-00797-PATCHZ-1.105163.2.109423.3`. The chip name is Hamilton. Verified.
- `hmtnv10.*` and `hmtnv20.*`: non-volatile configuration files, about 30 variants (`.b0202` to `.b32`, `.bin`, `.b0c`). The suffixes look like per-product or per-antenna configuration. Unverified.

The fstab mounts the image read-only at `/vendor/bt_firmware` (section 04).

## How these fit with the rest

Three paths connect the remote processors to the fuse and boot analysis.

1. The XBL container's SBL1 program names `shrm.elf`, `devcfg.bin` and `cpr.bin`. It has `boot_prepare_cpucp` and `boot_reset_cpucp`. These are probably the images SBL1 loads for the remote processors and the power controller. Observed.
2. The kernel reaches the power-management processor through SCMI. Power limits set in fuses may reach the kernel through that path. This is a hypothesis; the fuse read path in CPUCP has not been checked.
3. The device tree ties the GPU speed bin to a fuse cell (section 06). The GPU driver reads that cell from the kernel side, not from a remote processor.
