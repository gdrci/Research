# 01 - Package layout

[中文版](01-package-layout.zh-CN.md)

## The OTA file

The OTA is a standard Android A/B full update.

| Item | Value |
|---|---|
| File | `greatwhite_65394930092600080.zip` |
| Size | 1,439,273,084 bytes |
| SHA-256 | `6411fd4f52782e576b6ff7662fa3d62e7af838ae64f4843736a8fa1ef67b1068` |
| Contents | `payload.bin` (1,439,266,670 bytes), `payload_properties.txt`, `care_map.pb`, `apex_info.pb`, `META-INF/` |
| Signing | SignApk (`META-INF/com/android/otacert`) |
| Update type | `ota-type=AB` |

`payload_properties.txt` gives the payload's own hash and size, with `METADATA_SIZE=97215`. The metadata lists the target build:

```
pre-device=greatwhite
post-build=Meta/greatwhite/greatwhite:14/UKQ1.250303.001/65394930092600080:user/release-keys
post-sdk-level=34
post-security-patch-level=2026-02-05
post-timestamp=1780360088
```

`post-timestamp` is 1780360088, which is 2026-06-02 00:28:08 UTC (June 1, 17:28 PDT). The boot image's `build.prop` gives `Mon Jun 1 17:31:45 PDT 2026`, which is 00:31:45 UTC on June 2, about three minutes later. The two agree.

`payload.bin` is a full payload, not an incremental one. `payload-dumper` extracted it without an original image set, so every partition is complete. All 33 partitions were extracted and every image was hashed. The inventory is in `data/inventory.json`, and the table is in `data/partition_table.md`.

## Partition groups

| Group | Partitions | Container |
|---|---|---|
| Qualcomm boot chain | `xbl`, `xbl_config`, `xbl_ramdump`, `abl`, `uefi`, `uefisecapp`, `imagefv` | ELF |
| Secure world | `tz`, `hyp`, `devcfg`, `keymaster`, `featenabler`, `multiimgqti`, `multiimgoem` | ELF |
| Remote processors | `aop`, `aop_config`, `cpucp`, `shrm`, `qupfw`, `dsp`, `modem`, `bluetooth` | ELF (RISC-V, Hexagon, ARM), ext4, FAT |
| Android boot | `vbmeta`, `vbmeta_system`, `boot`, `dtbo`, `vendor_boot`, `recovery` | AVB, boot v4, DTBO |
| Android filesystems | `system`, `system_ext`, `product`, `vendor`, `odm` | ext4, dm-verity |

## Container details that matter

**`xbl.img` is a container.** It holds three ELF programs back to back: a stub at offset 0, a RISC-V TME firmware at `0x1C2F4`, and an AArch64 SBL1 at `0x4AFC4` (section 02). The outer header describes only the stub.

**XBL's outer header has an unusual machine field.** The stub at offset 0 is a 32-bit ELF whose `e_machine` is 1 (`EM_M32`). `xbl_config.img` is a 64-bit ELF with the same value. Standard ARM, AArch64 and Hexagon all use other values. The field is not what the loader reads, so this is probably a Qualcomm convention, but I have not confirmed it against another Qualcomm XBL.

**`uefi.img` mixes ELF classes.** It is a 64-bit ELF with `e_machine = EM_ARM` (40). ARM64 images normally use `EM_AARCH64` (183). The loader may ignore the field, or the image may run as ARM32 code. This is open.

**Qualcomm segment flags.** Several ELF images have `PT_NULL` headers whose `p_flags` contain high bits (`0x2000000`, `0x7000000`). These are the hash and signature segments of the Qualcomm image format. They are not code. The table of load segments in `ghidra/import_map.json` excludes them.

**Remote-processor images are not ELF-only.** `dsp.img` is ext4 and `modem.img` and `bluetooth.img` are FAT. The first-stage fstab mounts them at runtime. See section 05.

**No PBL in the image set.** The primary boot loader lives in the SoC's mask ROM, so the OTA does not contain it. This is the standard Qualcomm arrangement; I have not verified it on this device.

## Noteworthy values

- `rollback_index=1770249600` in both vbmeta images. That is the Unix time of 2026-02-05 00:00 UTC, the same day as the security patch level. Section 03 covers the rest.
- The `vbmeta` image is 8,192 bytes and `vbmeta_system` is 4,096 bytes.
- `boot.img` is 100,663,296 bytes on disk, but its hashed size is 30,208,000 bytes. The rest is padding.
