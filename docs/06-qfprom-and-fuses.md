# 06 - QFPROM and fuses

[中文版](06-qfprom-and-fuses.zh-CN.md)

QFPROM is the fuse block on the SoC. Its bits are one-time-programmable. The boot chain, the kernel and the secure world all read values from it. This document lists what is known about the block, where each reader is, and what remains unknown. It describes how the system uses fuses. It does not describe any weakness.

## The block

The vendor device tree defines the block at `0x221C8000` with a 4 KB window:

```
qfprom@221c8000
    compatible = "qcom,qfprom"
    reg = <0x221c8000 0x1000>
    read-only
```

`read-only` means the kernel does not write fuses through this node. Writes happen in the secure world. Verified.

The device tree names one fuse cell:

| Cell | Offset | Bits | Users |
|---|---|---|---|
| `gpu_speed_bin` | `0x119`, 2 bytes | bit 5, 8 bits wide | GPU (`kgsl-3d0`, name `speed_bin`), and `qfprom@0` (`qcom,qfprom-sys`) |

The field gives the GPU speed bin, which the GPU driver uses to choose an operating point. It spans bits 5 to 12 of the two bytes at `0x119`. Verified from the device tree. What each value means is not known until the driver is read.

## The block's neighbours

Three other blocks sit next to the QFPROM window. The TrustZone table and SBL1's memory map both list them:

| Base | Where it appears | Count or size in that table |
|---|---|---|
| `0x221C0000` | TrustZone MMIO table, index 0 | count 8 |
| `0x221C4000` | TrustZone MMIO table, index 1 | count 4 |
| `0x221C2000` | TrustZone MMIO table, index 2; SBL1 descriptor array | count 8 |
| `0x221C8000` | TrustZone MMIO table, index 3; hypervisor map; SBL1; device tree | count 8 (TZ); 3 pages (hyp); 1 page (DTB) |

Only `0x221C8000` has a device-tree node. The names of the other three blocks are not known. The addresses are verified; the names are not.

## The TrustZone MMIO table

TrustZone has a table of five 16-byte entries at `0x1C141C40`: a 32-bit base and a 32-bit count per entry. Index 4 is `0x010C0000`.

Two functions use it. `0x1C067548` passes flag `0x9041` and `0x1C067598` passes flag `0x9061`. Each takes an index, rejects values above 4, and loads `base` and `count` from `table + index × 8`. Both have 15 call sites, and every index from 0 to 4 is used with both flags.

For the QFPROM block (index 3), `0x9041` is set from `0x1C084A30`, `0x1C084AEC` and `0x1C084B94`. `0x9061` is set from `0x1C065304`, `0x1C084B08` and `0x1C084BB8`.

The callee at `0x1C03ACAC` takes the base, the count and the flag. It locks, calls `0x146816F4` (TrustZone's own code), and unlocks. `0x146816F4` is an ordinary routine with no `SMC` instruction, so the call does not go through the secure monitor. The exception level it runs at is not established. The routine body is not yet read. The count's unit is not known, and neither is the meaning of the two flags. The flags may separate read-only from read-write treatment, which is unverified.

## Mapping sizes disagree

- The device tree gives `0x1000` (one page).
- The hypervisor's memory map gives `0x3000` (three pages) for `0x221C8000`, with attribute 4 and permission `0xF`. The record is `(va=0x221C8000, pa=0x221C8000, attr=0x4, perm=0xF, size=0x3000)` (`data/secure/hyp_mmio_map.tsv`).
- TrustZone's table gives count 8, unit unknown.

These can all be true: the hypervisor maps the whole neighbourhood, while the device tree describes only the part the kernel uses. Not confirmed. The values are verified; the interpretation is open.

## Readers in the kernel

| Reader | Evidence | Status |
|---|---|---|
| `nvmem_qfprom.ko` | `CONFIG_QCOM_QFPROM=m`, description "Qualcomm QFPROM driver", author Srinivas Kandagatla (Linaro) | the main path |
| `msm_kgsl.ko` | GPU driver; the device tree gives `nvmem-cell-names = "speed_bin"` | uses `gpu_speed_bin` |
| `qfprom@0` consumer | `compatible = "qcom,qfprom-sys"` | `CONFIG_QCOM_QFPROM_SYS` is not set, so this is not a built driver interface |
| `qcom-reboot-reason.ko` | reboot reason from the PMIC SDAM and IMEM (section 04) | not the fuse block; listed for the restart path |

The NVMEM framework exposes each cell by name. A consumer asks for a cell and never addresses the fuse block directly. Not every `nvmem-cells` consumer reads QFPROM: the reboot-reason node reads the PMIC SDAM, while the GPU and the `qfprom-sys` node read the fuse block.

## Readers in the boot chain and the secure world

### SBL1

SBL1 (the AArch64 program inside `xbl.img`) has one direct reference to `0x221C8000`: a `mov w13, #0x8000` and `movk w13, #0x221c, LSL #16` pair at `0x1482CED4`. That code is in the function that starts at `0x1482CD30`, which has one caller at `0x14825B3C`. The surrounding code stores a series of 64-bit values into a stack array: `0x221C2000`, `0x221C8000`, `0x22000000`, `0x20C20000`, and SBL1 addresses `0x148A3000`, `0x148B2000`, `0x148B5000` and `0x148C7000`. SBL1 contains `BootMemMapLib.c`, so this is most likely the boot memory map being built. Interpretation.

The method and the disassembly are in `data/xbl/sbl1_qfprom_xref.txt`.

### TrustZone

TrustZone (`tz.img`) holds the table above and two literal-pool slots with `0x221C8000`. The functions that use the table are listed above. TrustZone also has these names, which are strings and so observed:

- `qsee_fuse_read`, `qsee_fuse_write`: the read and write API.
- `qsee_blow_sw_fuse`: blows a software fuse.
- `qsee_is_sw_fuse_blown`: checks whether a software fuse is already blown.
- `OEM_rot_pk_hash1_fuse_values`: the root-of-trust public key hash.
- `OEM_rot_enc_key1_fuse_values`: the root-of-trust encryption key entry.
- `oem_defer_fuse_prov_operation`: a deferred provisioning operation.
- `invoke-oem-spare-fuses failed: 0x%x, 0x%x, 0x%x`: the spare-fuse path.
- `qfprom_data`: a buffer for fuse data.

DevCfg (`devcfg.img`) and TrustZone both have `PM_QFPROM_FLAG`, a flag that power management reads from the fuse block. Observed.

Featenabler (`featenabler.img`) uses software fuses to enable features per hardware revision (strings `soc_hw_version`, `ConfigureSwFuse failed for feature_id`, `DisplayCore_EnableSwFuse`). Observed.

### Hypervisor

The hypervisor has 8 literal-pool slots with `0x221C8000`, and its memory map has the `0x3000` record above. It is the most complete picture of the block's mapping.

### TME

The TME firmware has no reference to the block: no `LUI` with the QFPROM immediates and no literal. Verified by search.

## Where the literal appears

Counts from a literal scan (`data/qfprom_literal_candidates.json`):

| Image | Occurrences | Note |
|---|---:|---|
| `hyp.img` | 8 | hypervisor memory map |
| `xbl.img` | 2 | both in SBL1, the AArch64 program |
| `xbl_ramdump.img` | 2 | same pattern as SBL1 |
| `tz.img` | 2 | TrustZone table |
| `recovery.img` | 5 | probably DTB data; not confirmed |
| `boot.img` | 2 | probably DTB data; not confirmed |

The counts in `boot` and `recovery` are most likely copies of the device tree, since those images contain device-tree blobs. The hits in `xbl`, `xbl_ramdump`, `tz` and `hyp` are the ones to follow.

The same scan found `0x00784000` in `qupfw` (once), `boot` (twice), `recovery` (seven times) and `vendor_boot` (twice). That is not the device-tree base, so it is not QFPROM. Earlier notes listed `0x00780000` as a candidate. Those hits are mostly device-tree data.

## The reboot-reason path

Reboot reasons are stored in two places. The device-tree node `/soc/reboot_reason` lists both:

1. `sdam@b100/restart@48` on the PM8150 PMIC, bits 1 to 7 of the SDAM byte at `0x48`. SDAM is a small register bank on the PMIC that keeps data across resets.
2. `msm-imem@146aa000/restart_reason@65c`, in shared IMEM at `0x146AA000`. The XBL config has the same base (`SharedIMEMBaseAddr = 0x146AA000`).

The second copy is in memory that survives a warm reset. Verified from both files. The reason-code values are not decoded yet.

## Link to verified boot

The rollback index in `vbmeta` is `1770249600` (section 03). Anti-rollback needs a counter that cannot be lowered, and the usual way to get one is a fuse-backed counter. I cannot read the device's counter table yet, so the link between the vbmeta index and a fuse is a reasonable expectation, not a fact.

The device tree and overlay check is done. The base device tree defines one fuse cell (`gpu_speed_bin`). The 18 overlays in `dtbo.img` reference only one nvmem cell, the restart reason, so they add no fuse cells. Verified.
