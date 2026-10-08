# Credits and third-party notices

[中文版](NOTICE.zh-CN.md)

## Author

Original analysis and documentation: **gdrci**.

This covers the documentation under `docs/` except section 10 and the images under `docs/images/`, the README files, and the evidence notes written during the analysis. Those are licensed under [CC BY 4.0](LICENSE).

## Not covered by the CC BY 4.0 grant

The following are excluded from the license in [LICENSE](LICENSE). Their rights remain with their owners.

| Material | Where it is | Owner | Basis |
|---|---|---|---|
| Ray-Ban Display firmware: excerpts, strings, symbol tables, disassembly and decompiler output, hex extracts and metadata | `data/` | Meta Platforms, Inc. and the owners of the third-party components in the firmware | Included as evidence for the analysis |
| Three figures from Qualcomm's *Enable Secure Boot on QCC730 Application Note* (80-Y8730-8, rev AB) | `docs/images/qcc730/` | Qualcomm Technologies, Inc. | Saved HTML pages; reproduced for reference |
| Section 10, QCC730 secure-boot reference, EN and ZH | `docs/10-qcc730-secure-boot-reference*.md` | Qualcomm Technologies, Inc. and the OP-TEE project | Summarised from the Qualcomm application note and the OP-TEE *Hoya architecture* documentation (saved by me) |
| Analog Devices MAX98388/MAX98389 datasheet (Rev. 2, 6/24) | Cited in `docs/12-audio.md`, `docs/17-chip-inventory.md` | Analog Devices, Inc. | Cited for specification values |
| Qualcomm FastConnect 7800 product brief (87-PW329-1 Rev. B) | Cited in `docs/17-chip-inventory.md` | Qualcomm Technologies, Inc. | Cited for product features |

## Tools and projects used

- **Ghidra** 12.1.3 (headless analysis and decompilation), Apache License 2.0.
- **Capstone** 5.0.7 (disassembly), BSD license.
- **Python** standard library (parsing of ELF, FDT and AVB structures).
- **Linux kernel** (GPL-2.0). Module names and metadata in `data/android/` come from the kernel modules in the firmware.
- **OP-TEE** documentation (the *Hoya architecture* page) for the reference in section 10. Consult the OP-TEE repository for its documentation license.

## Trademarks

Meta, Ray-Ban, Oculus, Qualcomm, Snapdragon, FastConnect, Android, Linux, NXP, Analog Devices, Maxim, Texas Instruments, Apple (MFi), Visionox, Novatek, Sharp and other product or company names appear in this repository only to identify parts, firmware and components. Their use does not imply endorsement or any affiliation.

## Affiliation

This repository is an independent analysis. It is not affiliated with, sponsored by or endorsed by Meta Platforms, Inc., Qualcomm, or any other vendor named in it.
