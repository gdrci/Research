# 00 - Overview

[中文版](00-overview.zh-CN.md)

The device starts in a fixed sequence. Each stage checks the next one and then hands over control. The table below is the order used in this analysis. Where the order is not confirmed, the document says so.

## Boot path

```
Boot ROM (PBL)                 silicon, not in the OTA                       unverified
  -> XBL container             xbl.img (978,944 bytes), three programs
       1. primary stub         ELF32 EM_M32, entry 0x2211C000                 ISA open
       2. TME firmware         RISC-V, offset 0x1C2F4                         verified (strings)
       3. SBL1                 AArch64, offset 0x4AFC4, built 2026-03-05      verified (strings)
       SBL1 loads and authenticates the images below, using the SRoT MBNv7 chain
       -> TrustZone (QSEE)     tz.img            EL3 entry verified
       -> Hypervisor           hyp.img           memory map verified
       -> DevCfg, CPR, SHRM    devcfg.img, shrm.elf (named by SBL1)          observed
       -> Keymaster, uefisecapp, featenabler                                 observed
       -> remote processors    aop, cpucp, qupfw, dsp, modem, bluetooth      observed
  -> UEFI                      uefi.img, reads oem_config.xml (MINK)         observed
  -> AVB                       vbmeta.img, vbmeta_system.img                 signatures verified
  -> Linux 5.10.240            boot.img + vendor_boot.img                    verified
  -> init, vendor, system      vendor.img, odm.img, system*.img, product     verified
  -> glasses services          MCU HALs, STP, EMG, Smartglass apps           observed
```

`uefi.img` is the likely bootloader. SBL1's subsystem list and image-name table name `uefi` and `APPSBL`, and `uefi.img` is a UEFI DXE volume, while `abl.img` has no matching strings. The code that jumps to the loader is not yet decompiled. Section 02 explains the evidence.

## The XBL container

`xbl.img` is not one loader. It holds three programs, each with its own ELF header. The SBL1 program is the one that does the work. The TME program is a RISC-V firmware that SBL1 and PBL call for authentication. The first program is a small stub with a machine field that no standard architecture uses. Section 02 describes each, and section 07 explains how to import them.

## Where fuses come in

QFPROM is the fuse block at `0x221C8000`. It is a 4 KB window, read-only from the kernel's point of view, and the device tree describes it. Three places read it:

- the kernel, through `nvmem_qfprom` (module `CONFIG_QCOM_QFPROM=m`);
- the GPU driver, which reads the `gpu_speed_bin` cell at byte `0x119` to pick an operating point;
- the secure world, which carries `qsee_fuse_read`, `qsee_fuse_write` and software-fuse helpers.

SBL1 has one direct reference to the address, in code that builds a boot memory map. The hypervisor maps the block as three pages. Section 06 has the details.

## Two Android versions

The boot image, `vendor` and `odm` carry an Android 12 fingerprint (`SQ3A.220605.009.A1`). `system`, `system_ext` and `product` carry Android 14 (`UKQ1.250303.001`). The vendor side is an older Treble base under a newer framework. Section 04 covers the consequences.

## The glasses around the SoC

Several parts of the system run outside the application processor. A microcontroller (the MCU) handles the sensors, the buttons, the hinge and the charging case, and it is reached over a transport called STP. The electromyography input from the wrist band reaches the phone-side software through an EMG service. Section 09 covers these. The hardware is also split into two audio-codec variants, RT600 and RT700, which the software detects at boot.

## Document map

| Document | Subject |
|---|---|
| [01](01-package-layout.md) | OTA format, partitions, hashes |
| [02](02-boot-chain.md) | Stage-by-stage analysis, including the XBL container |
| [03](03-avb-verified-boot.md) | vbmeta descriptors, signatures, hash checks, rollback index |
| [04](04-android-kernel-and-vendor.md) | Kernel, ramdisks, fstab, modules, overlays, bootconfig |
| [05](05-remote-processors.md) | AOP, CPUCP, SHRM, QUP, DSPs, modem, Bluetooth |
| [06](06-qfprom-and-fuses.md) | Fuse block, memory maps, readers |
| [07](07-wireless-and-connectivity.md) | Wi-Fi and Bluetooth stack, WPSS subsystem, drivers, HALs, firmware |
| [08](08-peripheral-firmware-and-build-ids.md) | Build IDs, GPU, camera, video and vision firmware |
| [09](09-glasses-software-and-mcu.md) | MCU, STP, RT600/RT700, EMG band, app layer |
| [10](10-qcc730-secure-boot-reference.md) | External QCC730 secure-boot reference (different chip) |
| [11](11-evidence-index.md) | Which `data/` directory each section uses |
