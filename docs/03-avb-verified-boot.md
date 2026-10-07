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

## What was checked against the images

The script `tools/avb_verify.py` checks signatures and hashes directly from the extracted images. Output: `data/avb/verify_results.txt`.

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
| `odm` dm-verity root, SHA-1 (52,924,416 bytes) | does not match |
| `product` dm-verity root, SHA-1 (650,182,656 bytes) | does not match |
| `system_ext` dm-verity root, SHA-1 (410,660,864 bytes) | does not match |

So the signed metadata covers the `boot`, `dtbo`, `vendor_boot`, `vendor` and `system` contents exactly as shipped. Verified.

### The SHA-1 trees

The three SHA-1 trees do not match under the layout the script implements, which is the standard v1 layout with the salt prepended to each block and each hash block padded to 4096 bytes. The SHA-256 trees match under the same code, so the code is right for SHA-256. For `odm`, I also tried the salt appended instead, and that did not match either.

Possible explanations, none tested:

- the SHA-1 trees use a different layout or a different hash-block packing;
- the descriptor's data range differs from the range I hashed;
- the trees are correct and I have the layout wrong.

These three partitions have FEC enabled (`fec_num_roots=2` on `odm`). FEC does not change the root hash, so it is not the cause. The mismatch is open. It should not be read as a failed check.

Still not checked: the chain-partition public keys' use, and the FEC data.
