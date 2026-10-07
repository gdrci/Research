# Partition table

[中文版](partition_table.zh-CN.md)

| # | Partition | Bytes | Kind | SHA-256 (first 16) | Role (expected; see docs) |
|---|---|---:|---|---|---|
| 1 | `abl` | 339,968 | elf | `52ee2dc8b6647ef3` | Android Bootloader (ABL), ARM32 ELF |
| 2 | `aop` | 241,664 | elf | `5dd8c9c8a091dbff` | Always-On Processor firmware (AOP.HO.4.0) |
| 3 | `aop_config` | 16,384 | elf | `a1b676d12b48a399` | AOP config |
| 4 | `bluetooth` | 1,224,704 | other | `9f22be3a573bc190` | Bluetooth firmware (FAT, /vendor/bt_firmware) |
| 5 | `boot` | 100,663,296 | android-boot | `1090962994e0f779` | Android GKI boot: kernel 5.10.240 + init ramdisk |
| 6 | `cpucp` | 106,496 | elf | `5e5b7cccd5b7c06d` | CPU Control Processor firmware (RISC-V, SCMI) |
| 7 | `devcfg` | 57,344 | elf | `e68dab205e07e54f` | DevCfg (PM/QFPROM flags, tgt config) |
| 8 | `dsp` | 67,108,864 | other | `f5fcc454f532dd24` | aDSP/cDSP firmware (ext4, /vendor/dsp) |
| 9 | `dtbo` | 24,117,248 | dtbo | `06f4125311547a8e` | DT overlays |
| 10 | `featenabler` | 90,112 | elf | `4fb8c054e494935b` | Feature enabler (SW-fuse feature gating) |
| 11 | `hyp` | 1,228,800 | elf | `2cccff6da124a373` | Hypervisor (Qualcomm hyp, smem and PIL handling) |
| 12 | `imagefv` | 20,480 | elf | `dfb6bb67b8cff059` | UEFI/image firmware volume (ARM32) |
| 13 | `keymaster` | 368,640 | elf | `5fd33a616ef98f48` | Keymaster TA (keys, OS version/patch) |
| 14 | `modem` | 38,522,880 | other | `04030355fff6a1d9` | Modem firmware (FAT, mounted /vendor/firmware_mnt) |
| 15 | `multiimgoem` | 16,384 | elf | `549fdf6e632cca8e` | Multi-image container (OEM) |
| 16 | `multiimgqti` | 12,288 | elf | `adbf4e1889010b1f` | Multi-image container (QTI) |
| 17 | `odm` | 53,850,112 | other | `ac0b4ced2453ee3e` | ODM partition |
| 18 | `product` | 660,692,992 | other | `fe4d2069f03080aa` | Android product |
| 19 | `qupfw` | 65,536 | elf | `9a219b19e6a0654b` | Hexagon firmware (EM_QDSP6; role not verified) |
| 20 | `recovery` | 104,857,600 | android-boot | `217ce83238d1d5ad` | Recovery (boot v4 image, ramdisk only) |
| 21 | `shrm` | 61,440 | elf | `66bb5cc9c5fbd4de` | Shared resource manager firmware (RISC-V; DDR fw version string) |
| 22 | `system` | 1,456,967,680 | other | `ab778a176c3b30fc` | Android system (Android 14) |
| 23 | `system_ext` | 417,329,152 | other | `8665f5e948600d03` | Android system_ext |
| 24 | `tz` | 3,469,312 | elf | `4e418f8343771347` | TrustZone (QSEE) secure world, EL3 entry |
| 25 | `uefi` | 2,670,592 | elf | `f63acf3695c97d99` | UEFI (ARM64 ELF, boot device detection, SMP bootstrap) |
| 26 | `uefisecapp` | 180,224 | elf | `d6d3997f7bacf744` | UEFI secure-boot TA (cert/PKCS7 handling) |
| 27 | `vbmeta` | 8,192 | avb-vbmeta | `340ffff6c7658bf2` | AVB root: hashes for boot, dtbo, vendor_boot; dm-verity for vendor/odm; chains recovery & vbmeta_system |
| 28 | `vbmeta_system` | 4,096 | avb-vbmeta | `cd898111d5762a2d` | AVB for system/system_ext/product |
| 29 | `vendor` | 460,947,456 | other | `40e7f65885ef2b2b` | Vendor (Android 12 fingerprint) |
| 30 | `vendor_boot` | 100,663,296 | android-vendor-boot | `586e4d32ed1b2cf0` | Vendor boot: vendor ramdisk (kernel modules, fstab) + DTB |
| 31 | `xbl` | 978,944 | elf | `939e0acc0455b166` | Qualcomm XBL (secondary bootloader core, image auth via SRoT MBNv7) |
| 32 | `xbl_config` | 147,456 | elf | `641bcf3201b87e81` | XBL platform/memory config (overlay pre-ddr-sxr-aurora) |
| 33 | `xbl_ramdump` | 708,608 | elf | `0510b3aa53383829` | XBL build with ramdump support |
