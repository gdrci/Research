# Ray-Ban Display (greatwhite)

Documentation of the Ray-Ban Display firmware: how the system is built, how it boots, and how its parts fit together. The QFPROM fuse block runs through the boot chain and is the common thread.

Chinese version: [README.zh-CN.md](README.zh-CN.md)

Discord: [discord.gg/oculus](https://discord.gg/oculus) · @gdrci (Discord)

## Scope

This repository describes how the system is built and how it starts. It is not vulnerability research. It contains no exploit material and no findings about weaknesses. Firmware binaries are not included.

## Target

| Field | Value | Basis |
|---|---|---|
| Device | Meta Ray-Ban Display, `greatwhite` | `pre-device` in OTA metadata |
| OTA | `greatwhite_65394930092600080.zip`, 1,439,273,084 bytes | file size |
| OTA SHA-256 | `6411fd4f52782e576b6ff7662fa3d62e7af838ae64f4843736a8fa1ef67b1068` | computed |
| Build | `Meta/greatwhite/greatwhite:14/UKQ1.250303.001/65394930092600080:user/release-keys` | `vbmeta_system` properties |
| Security patch | 2026-02-05 | `vbmeta_system` properties |
| SoC codename | `Aurora` | XBL `TME_FW_CHIPSET_STRING`, SBL1 `IMAGE_VARIANT_STRING=SocAuroraLAA` |
| Kernel | Linux 5.10.240, ARM64 | boot image kernel banner |

## Documents

| Document | English | 中文 |
|---|---|---|
| Overview | [00](docs/00-overview.md) | [00](docs/00-overview.zh-CN.md) |
| Package layout | [01](docs/01-package-layout.md) | [01](docs/01-package-layout.zh-CN.md) |
| Boot chain | [02](docs/02-boot-chain.md) | [02](docs/02-boot-chain.zh-CN.md) |
| Android Verified Boot | [03](docs/03-avb-verified-boot.md) | [03](docs/03-avb-verified-boot.zh-CN.md) |
| Kernel and vendor | [04](docs/04-android-kernel-and-vendor.md) | [04](docs/04-android-kernel-and-vendor.zh-CN.md) |
| Remote processors | [05](docs/05-remote-processors.md) | [05](docs/05-remote-processors.zh-CN.md) |
| QFPROM and fuses | [06](docs/06-qfprom-and-fuses.md) | [06](docs/06-qfprom-and-fuses.zh-CN.md) |
| Glasses software and MCU | [09](docs/09-glasses-software-and-mcu.md) | [09](docs/09-glasses-software-and-mcu.zh-CN.md) |

## Evidence labels

- **Verified**: read directly from a header, a hash, a parsed structure or a file.
- **Observed**: a string, a name or a configuration value that points one way. The code behind it has not been read.
- **Inferred**: a conclusion drawn from names or context, stated as such.
- **Unverified**: background knowledge or a guess.
