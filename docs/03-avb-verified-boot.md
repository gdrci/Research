# 03 - Android Verified Boot

[中文版](03-avb-verified-boot.zh-CN.md)

Verified Boot here follows the libavb 1.x format. The parsed output is in `data/avb/vbmeta_summary.txt`. The parser reads structure and keys. It does not check signatures, because the reference `avbtool` is not available in the analysis environment.

## vbmeta.img

| Field | Value |
|---|---|
| libavb version | 1.0 |
| Algorithm | SHA256_RSA2048 |
| Rollback index | 1770249600, location 0 |
| Flags | 0x0 (verification is on) |
| Release string | `avbtool 1.2.0` |
| Public key | 520 bytes, SHA-256 `0d5c1533678bc678252d94dbe5c9689ebdfe72f34c32fdbbcc87e3952c814abe` |

Descriptors, in the order they appear:

| Type | Partition | Size | Hash | Notes |
|---|---|---:|---|---|
| hash | `boot` | 30,208,000 | sha256 | Whole-image hash. |
| hash | `dtbo` | 2,435,291 | sha256 | Whole-image hash. |
| hash | `vendor_boot` | 13,946,880 | sha256 | Whole-image hash. |
| hashtree | `vendor` | 453,591,040 | sha256 | dm-verity, format v1. |
| hashtree | `odm` | 52,924,416 | sha1 | dm-verity, format v1. |
| chain | `recovery` | | | rollback location 1 |
| chain | `vbmeta_system` | | | rollback location 2 |

Properties attached to the image: fingerprints and `os_version` for the Android 12 partitions, all reading `facebook/greatwhite/greatwhite:12/SQ3A.220605.009.A1/65394930092600080:user/release-keys`.

The `odm` hashtree uses SHA-1. The `vendor` one uses SHA-256. The mix is unusual, and the reason is unverified.

## vbmeta_system.img

| Type | Partition | Size | Hash |
|---|---|---:|---|
| hashtree | `system` | 1,433,899,008 | sha256 |
| hashtree | `product` | 650,182,656 | sha1 |
| hashtree | `system_ext` | 410,660,864 | sha1 |

Properties: fingerprints `Meta/greatwhite/greatwhite:14/UKQ1.250303.001/...`, `os_version=14`, and `security_patch=2026-02-05`.

`vbmeta_system` has the same public key as `vbmeta`. Both are signed by one key. Verified from the key hash.

## Rollback index

The value 1770249600 is the Unix time of 2026-02-05 00:00 UTC. It equals the patch date, so it appears to be set from the patch level when the image is built. Verified value; the link to the patch date is observed.

Anti-rollback only works if the device also keeps a fuse-backed copy of the counter. The copy is not located yet. Section 06 explains where to look.

## Fstab entries that depend on AVB

The first-stage fstab (section 04) uses `avb=vbmeta` for `vendor` and `odm`, and `avb=vbmeta_system` for `system`, `system_ext` and `product`. Those values are the chain that the verifier follows. Verified.

### Verified boot and device state in `uefi.img`

`uefi.img` is a firmware volume (`_FVH` at `0x1000`, length `0x289000`). Its DXE code sits in a GUID-defined section (`1d301fe9-be79-4353-91c2-d23bc959ae0c`) whose payload is gzip. Decompressed, it is 3,911,688 bytes. The string list is `data/strings/uefi_dxe_fv_strings.txt` (18,305 strings).

The verified-boot module `VerifiedBootDxe` does four things, from its strings:
- It reads and writes device state (`RWDeviceState`). The state goes through a QSEE app (`gQcomQseecomProtocolGuid`), through RPMB (`Succeed using rpmb`), or through devinfo.
- It sends boot state and milestones to the QSEE app (`Send_Milestone`, `Reset_State`, `SendBootState`).
- It computes a root-of-trust digest for a locked or unlocked device (`SendROT`, `vb_get_digest_locked_device`, `vb_get_digest_unlocked_device`). It verifies signatures against an OEM certificate or an embedded key, and it computes a certificate fingerprint.
- It skips verification when the device is unlocked (`Device is unlocked! Skipping verification!`).

The image names software-fuse ranges: `FUSE_CONTROLLER_SW_RANGE0`, `_SW_RANGE1`, `_SW_RANGE3`, `_SW_RANGE4`, `_SW_RANGE5`, `VIRT_FUSE_CONTROLLER_SW_RANGE3`, and a `TME_FUSECONTROLLER`. Anti-rollback state would be in these ranges, but the strings don't say which range holds the `vbmeta` index. The RPMB strings are the write-counter reads (`rpmb_read_counter_pkt`), not the `vbmeta` index. Observed from strings. Findings: `data/secure/uefi_verified_boot_findings.txt`.

## What was checked against the images

The signature and hash checks were run directly on the extracted images. Output: `data/avb/verify_results.txt`.

| Check | Result |
|---|---|
| `vbmeta` authentication hash over header and auxiliary block | matches |
| `vbmeta` RSA-2048 signature (PKCS#1 v1.5, SHA-256) | valid |
| `vbmeta_system` authentication hash | matches |
| `vbmeta_system` RSA signature | valid |
| `boot` whole-image SHA-256 (30,208,000 bytes) | matches |
| `dtbo` whole-image SHA-256 (2,435,291 bytes) | matches |
| `vendor_boot` whole-image SHA-256 (13,946,880 bytes) | matches |
| `vendor` dm-verity root, SHA-256 (453,591,040 bytes) | matches |
| `system` dm-verity root, SHA-256 (1,433,899,008 bytes) | matches |
| `odm` dm-verity root, SHA-1 (52,924,416 bytes) | matches (tree rebuilt, 32-byte digest slots) |
| `product` dm-verity root, SHA-1 (650,182,656 bytes) | matches (tree rebuilt, 32-byte digest slots) |
| `system_ext` dm-verity root, SHA-1 (410,660,864 bytes) | matches (tree rebuilt, 32-byte digest slots) |

So the signed metadata covers the `boot`, `dtbo`, `vendor_boot`, `vendor`, `system`, `odm`, `product` and `system_ext` contents exactly as shipped. Verified.

### The SHA-1 trees

The three SHA-1 trees (`odm`, `product`, `system_ext`) first failed under the standard layout, which uses one digest per 20-byte slot. The fix is in the layout, not the data. Each level stores its digests in 32-byte slots, zero-padded after the 20-byte SHA-1 digest. That gives 128 digests per 4096-byte block, not 204.

Evidence: for `odm`, the stored tree has 102 blocks, which matches 128 digests per block (101 level-0 blocks plus one root block). With 20-byte slots the count would be 65. Rebuilding every tree with 32-byte slots gives the descriptor's root digest for `odm`, `product` and `system_ext`. The same rebuild also matches the `vendor` and `system` SHA-256 roots. The stored tree equals the rebuilt tree, byte for byte, in top-down order. Output: `data/avb/hashtree_rebuild.txt`.

The FEC data was not checked. FEC does not change the root hash.

Still not checked: the chain-partition public keys' use, and the FEC data.
