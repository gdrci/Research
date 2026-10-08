# 19 - Emulation reference

[中文版](19-emulation-reference.zh-CN.md)

This page collects the facts that someone building or maintaining an emulator, a device model or a test harness for this device would need. Each entry points to the section with its evidence. The page describes what the firmware is and how it is laid out. It does not describe how to change the behaviour of verification, fuses or secure boot.

## Processors

| Component | Image | Instruction set and format | Entry | Notes | Section |
|---|---|---|---|---|---|
| Primary XBL stub | `xbl.img`, program 1 | ELF32, `e_machine` 1 | `0x2211C000` | The machine value is not used by a standard ISA; the content is data-like | 02 |
| TME | `xbl.img`, program 2 | ELF32, RISC-V | `0x20412800` (from the program headers) | Six `PT_LOAD` segments. A linear sweep of its code decodes 52,066 instructions with the compressed extension | 02, 06 |
| SBL1 | `xbl.img`, program 3 | ELF, AArch64 | `0x14824FA8` | Runs the bring-up and loads the next images | 02 |
| TrustZone (QSEE) | `tz.img` | ELF64, AArch64 | `0x14680000` | Entered at EL3; the entry takes the thread context in `x0` | 02 |
| Hypervisor | `hyp.img` | ELF64, AArch64 | `0x80000000` | Five `PT_LOAD` segments | 02, 06 |
| Crash-dump XBL | `xbl_ramdump.img` | AArch64 | `0x80640000` | A separate XBL build with RAM-dump support | 02 |
| UEFI | `uefi.img` | ELF64, `e_machine` `EM_ARM` (40) | `0xA7000000` | The machine value is not the usual ARM64 one; the instruction set is not resolved | 02, 03 |
| Second loader | `abl.img` | ELF32, `EM_ARM` | `0x9FA00000` | Instruction set and role not established | 02 |
| Linux kernel | `boot.img` | ARM64 `Image`, Linux 5.10.240 | from the boot header | Kernel configuration in section 04 | 04 |
| AOP | `aop.img` | ELF32, ARM, Thumb entry | `0x0B000009` | Seven `PT_LOAD` segments | 05 |
| CPUCP | `cpucp.img` | ELF32, RISC-V | `0x90` | Seven `PT_LOAD` segments | 05 |
| SHRM | `shrm.img` | ELF32, RISC-V | `0x200000` | Two `PT_LOAD` segments | 05 |
| QUP | `qupfw.img` | ELF, Hexagon | none (`e_entry` is 0) | Whether it holds code is not established | 05 |
| Audio DSP (RT700 HiFi4) | `dsp.default.rt700.tub` | Xtensa (`EM_XTENSA`) | in the tub manifest | 4,429,312-byte container, unencrypted | 15 |
| Glasses MCU (RT700) | `mcu.default.rt700.tub` | see section 14 | see section 14 | Reached over STP | 09, 14 |

## Memory and address facts

- **QFPROM.** The fuse block is a 4 KB window at `0x221C8000` in the device tree. TrustZone maps 8 KB starting there (count 8 in its table). The hypervisor maps the block as three pages. SBL1 has one direct code reference to the base, in its memory-map function. Section 02 and section 06.
- **TrustZone MMIO table.** Five 8-byte entries at `tz.img` virtual address `0x1C141C40`. Each entry is a 32-bit base and a 32-bit count in KB. Section 02.
- **XBL stub segments.** Two segments of the primary stub: `0x2211C000` (`0x1C000` bytes) and `0x22143000` (`0x280` bytes). Section 02.
- **DTB placement.** The device tree in the vendor boot image is placed at `0x01F00000` (408,428 bytes). Section 04.
- **APPSBL region.** SBL1's image descriptor for `APPSBL` covers `0xA6E40000` to the top of the 32-bit space. `uefi.img` loads inside it at `0xA7000000`. Section 02.
- **Reboot reason.** Stored in the PM8150 SDAM register at byte `0x48`, bits 1 to 7, and in a shared IMEM cell at `0x146AA000` plus `0x65C`. Section 06.

## Boot handoffs

- The order of the boot stages is in section 00. Where the order is not confirmed, the document says so.
- SBL1 loads TrustZone through an MBN loader object and calls the loader's service object. Section 02.
- In the emergency-download path SBL1 calls its load-and-authenticate interface with `(0x14680000, 0x2B000, 0x4001)`. Section 02.
- Verified boot: the vbmeta descriptors, the hash and hashtree descriptors, and the chain descriptors for `recovery` and `vbmeta_system` are in section 03. Verified boot is described as observed, not reproduced.

## Peripherals on buses (device-tree overlays)

These are the bus addresses declared in the device-tree overlays. Some nodes are disabled on some boards; the board matrix in section 04 shows which. Section 17 has the chip-level detail.

| Device | Bus address | Section |
|---|---|---|
| MAX98388 speaker amplifiers | I2C `0x3A` (left) and `0x38` (right) from the ODM script | 12, 17 |
| PM8150 real-time clock | SPMI, base `0x6000` (rtc) and `0x6100` (alarm) | 17 |
| TMP114 temperature sensors | I2C `0x4C`, `0x4D`, `0x4E` | 17 |
| MAX31875 temperature sensors | I2C `0x48`, `0x49`, `0x4A` | 17 |
| ADS1115 ADC | I2C `0x49` | 17 |
| PTN5150 USB Type-C controller | I2C `0x1D` | 17 |
| MFi authentication chip | I2C `0x10` | 17 |
| STP transport chip | I2C `0x6D` | 17 |
| MAX77813, MAX77789, MP28167, RT6160, RAA491901 power ICs | I2C `0x18`, `0x69`, `0x60`, `0x75`, `0x29` | 17 |
| LCoS controllers | I2C `0x64` (OP03010) and `0x65` (OP02220 BA) | 17, 14 |
| Display power PMICs | I2C `0x40` (OP03010) and `0x44` (OP02220) | 17 |
| AW2026 LED driver | I2C `0x64` | 17 |

Some addresses are claimed by more than one device: `0x64` (AW2026 and the OP03010 controller) and `0x49` (MAX31875 and ADS1115). Section 17 lists each node in the overlays, but the files read here do not establish which device is present on a given board. A model needs that board-level answer before it can place devices on a bus.

## Things an emulator cannot take from this OTA

- **Silicon boot ROM (PBL).** It is not in the OTA.
- **Fuse values.** The OTA carries no fuse contents. The arb-fuse bank values are zero in the image file, and their runtime source is not located. Section 06.
- **DDR and memory map.** The DDR layout is not in the files read.
- **Interrupt routing and IPC.** Not documented in this repository.
- **MCU firmware internals.** Partly described in sections 09 and 14.

## Open items that block a faithful model

These are the stalled items from section 06, restated as emulation gaps:

- **Object `0x91` provider.** TrustZone asks for an object with this ID before it reads the anti-rollback flag. Its provider is not found in `tz.img`, `hyp.img` or the TME program.
- **OEM key reader.** The name `OEM_rot_pk_hash1_fuse_values` is in the key block of `tz.img`. Its reader is not found.
- **SBL1 header-driven jump.** The point where SBL1 jumps to the next image from the image header is not located.
- **Abl and uefi roles.** The instruction set of `abl.img` and the entry validity of `uefi.img` are unresolved (section 02).

Blocked items, which need a device or other material that this OTA does not contain, are listed in section 18.
