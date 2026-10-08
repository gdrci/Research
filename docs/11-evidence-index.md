# 11 - Evidence index

[中文](11-evidence-index.zh-CN.md)

This index maps each directory under `data/` to the section that uses it. The sections cite the evidence by file name where the file is central to a claim. Other files are the raw output behind a topic and are cited by topic. Both kinds are listed here so a reader can find the source of any claim.

Counts are from the repository at the time of writing.

| Directory | Files | Used in | What it holds |
|---|---:|---|---|
| `data/inventory.json` | 1 | 01 | SHA-256, size and ELF or FAT headers for each image |
| `data/partition_table.md`, `.zh-CN.md` | 2 | 01 | Partition table from the OTA metadata |
| `data/qfprom_literal_candidates.json` | 1 | 06 | Literal scan of QFPROM addresses across images |
| `data/analysis/` | 4 | 02, 05 | ISA and decoder tests: Thumb, ARM, the QUP decode, and DSP calibration. These are negative results, kept as record. |
| `data/android/` | 13 | 04 | Kernel config, security options, board IDs, boot config, fstab, `build.prop`, device-tree dump, module list. `wpss_dt_nodes.txt` is used by 07. |
| `data/avb/` | 3 | 03 | `vbmeta` summary, verify results, hash-tree rebuild |
| `data/ghidra/` | 18 | 02, 03, 06 | Decompiled functions for SBL1, UEFI and TrustZone, the import map, and the XBL and AOP entry disassembly. Cited by function address in 02 and 06. |
| `data/remote/` | 8 | 05, 07, 08 | Modem, Bluetooth and DSP FAT listings, the modem build manifest, and the Bluetooth version files |
| `data/secure/` | 25 | 06 | Fuse and secure-boot evidence: TrustZone object and dispatch tables, MMIO tables, PK-hash path, PIL arb-fuse table, thread-block setter, UEFI fuse region table, featenabler summaries, keymaster strings |
| `data/strings/` | 20 | 00, 02, 06 | `strings` output for each image. These are the source of most name-based claims. |
| `data/userspace/` | 9 | 04, 07, 08, 09 | Init scripts, vendor firmware listing, `.tub` contents and md5 tests, MCU HAL names, SmartGlass apps, Wi-Fi and Bluetooth config, peripheral firmware headers |
| `data/xbl/` | 6 | 02, 06, 07 | XBL container layout, SBL1 memory map and QFPROM references, TME scan, WPSS configuration sections |

## Files not named in a section

These files are real evidence, but the section that uses them describes them by topic rather than by name:

- `data/strings/*.txt`: the per-image strings. Section 00 and 02 cite the images, not each file.
- `data/ghidra/*_decompiled.txt`: cited by function address in sections 02 and 06.
- `data/secure/tz_mmio_table.tsv`, `hyp_mmio_map.tsv`: the full tables behind section 06's counts.
- `data/android/security_options.tsv`, `board_component_matrix.tsv`, `overlay_components.tsv`: section 04 uses them for the kernel options and overlay checks.

## Tools

The scripts that produced these files are not part of the repository. The outputs are.
