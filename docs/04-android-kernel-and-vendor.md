# 04 - Kernel, ramdisks, vendor, device tree

[中文版](04-android-kernel-and-vendor.zh-CN.md)

## boot.img

The boot image is version 4. Its header has an empty command line, because the command line comes from `vendor_boot`.

| Field | Value |
|---|---|
| Kernel size | 28,148,224 bytes |
| Ramdisk size | 2,049,602 bytes (legacy LZ4) |
| Kernel banner | `Linux version 5.10.240-perf-gd253e0b2f72b` |
| Kernel format | ARM64 `Image` |

The `-perf` suffix is the name of this kernel build. The `g` prefix on the commit hash is the git convention, so the kernel was built from a git tree.

### Build properties in the init ramdisk

`system/etc/ramdisk/build.prop` in the init ramdisk reads:

```
ro.product.bootimage.device=greatwhite
ro.bootimage.build.date=Mon Jun  1 17:31:45 PDT 2026
ro.bootimage.build.version.release=12
ro.bootimage.build.version.sdk=32
ro.bootimage.build.type=user
ro.bootimage.build.tags=release-keys
```

SDK 32 is Android 12L. These values are verified. They match the vendor fingerprint.

### The init ramdisk

The ramdisk holds four regular files: `init` (2.7 MB), `adb_debug.prop`, `system/bin/e2fsck`, and `system/etc/ramdisk/build.prop`. The text files are in `data/android/boot_ramdisk/`. `init` is the first-stage init binary. Verified.

## vendor_boot.img

Version 4, page size 4096.

| Field | Value |
|---|---|
| Vendor ramdisk | 13,523,624 bytes, legacy LZ4 with 8 MiB blocks |
| DTB | 408,428 bytes, loaded at `0x01F00000` |
| Bootconfig | 175 bytes |
| Ramdisk table | 1 entry |

### Command line

```
androidboot.memcg=1 androidboot.usbcontroller=a600000.dwc3 printk.devkmsg=on
log_buf_len=512k cgroup_disable=pressure sdhci_msm_scaling.default_perf_governor=1
androidboot.hardware=greatwhite firmware_class.path=/vendor/firmware/
androidboot.selinux=enforcing bootconfig buildvariant=user
```

`androidboot.selinux=enforcing` means SELinux starts in enforcing mode. `firmware_class.path` sets where the kernel looks for firmware blobs.

### Bootconfig

The bootconfig block (`data/android/vendor_boot/bootconfig.txt`) adds:

```
androidboot.hardware=greatwhite
androidboot.memcg=1
androidboot.usbcontroller=a600000.dwc3
androidboot.load_modules_parallel=true
androidboot.hibernation_resume_device=259:61
```

`259:61` is the major and minor number of the block device used for hibernation resume. Verified. Which partition that is depends on the device's block numbering, and I have not mapped it.

### Vendor ramdisk contents

224 regular files:

- `lib/modules/`: 214 kernel modules.
- `first_stage_ramdisk/fstab.greatwhite`: the first-stage fstab.
- `avb/`: three AVB public keys, named `q-gsi.avbpubkey`, `r-gsi.avbpubkey` and `s-gsi.avbpubkey`. The `gsi` suffix is the Android Generic System Image convention.

### Device props

`ro.board.platform=neo`, `ro.hardware.egl=adreno`, `ro.hardware.camera=qcom`, `persist.vendor.qcom.bluetooth.soc=hamilton`.

`neo` is the board platform name the vendor code uses. `hamilton` is the Bluetooth/Wi-Fi combo chip the vendor properties name, and the AOP image also refers to it (section 05).

## First-stage fstab

File: `data/android/vendor_ramdisk/fstab.greatwhite`.

| Mount | Source | Type | Options and flags |
|---|---|---|---|
| `/system`, `/product`, `/system_ext` | logical partitions | ext4, `ro` | `avb=vbmeta_system`, `first_stage_mount` |
| `/vendor`, `/odm` | logical partitions | ext4, `ro` | `avb=vbmeta`, `first_stage_mount` |
| `/metadata` | `by-name/metadata` | ext4 | `data=journal`, `formattable`, first stage |
| `/vendor/firmware_mnt` | `by-name/modem` | vfat, `ro` | `context=u:object_r:firmware_file:s0` |
| `/vendor/dsp` | `by-name/dsp` | ext4, `ro` | `context=...adsprpcd_file...` |
| `/vendor/bt_firmware` | `by-name/bluetooth` | vfat, `ro` | `uid=1002`, `gid=3002` |
| `/data` | `by-name/userdata` | f2fs | `fileencryption=aes-256-xts:aes-256-cts:v2+emmc_optimized+wrappedkey_v0`, `inlinecrypt`, `checkpoint=fs` |
| `/mnt/vendor/persist` | `by-name/persist` | ext4 | `sync` |
| `/storage/usbotg` | USB host | vfat | `voldmanaged=usbotg:auto` |
| zram swap | `/dev/block/zram0` | swap | `zramsize=1610612736` (1.5 GB), backing device 256 MB |

Three details matter here:

- `/data` uses hardware-wrapped keys (`wrappedkey_v0`) with inline encryption. The key handling is in `hwkm` and `crypto-qti-hwkm` (below).
- Modem, DSP and Bluetooth firmware are separate partitions, mounted read-only at runtime. The kernel loads them from `/vendor/firmware/`.
- `/metadata` is formattable at first boot, which makes it the place where the device creates its encryption metadata.

## Kernel configuration

File: `data/android/kernel/config.txt`, 7,581 lines, 1,754 options set to `y` and 184 to `m`.

| Option | State | Effect |
|---|---|---|
| `CONFIG_MODULE_SIG` | not set | kernel modules are not signature-checked |
| `CONFIG_CFI_CLANG` | not set | no clang control-flow integrity |
| `CONFIG_ARM64_PTR_AUTH` | y | pointer authentication |
| `CONFIG_ARM64_BTI_KERNEL` | y | branch target identification |
| `CONFIG_SHADOW_CALL_STACK` | y | shadow call stack |
| `CONFIG_ARM64_MTE` | y | memory tagging extension |
| `CONFIG_RANDOMIZE_BASE` | y | KASLR |
| `CONFIG_STACKPROTECTOR_STRONG` | y | stack canaries |
| `CONFIG_HARDENED_USERCOPY` | y | usercopy bounds checks |
| `CONFIG_STRICT_KERNEL_RWX` | y | kernel text is read-only |
| `CONFIG_INIT_ON_ALLOC_DEFAULT_ON` | y | zero-initialised allocations |
| `CONFIG_SECURITY_SELINUX_DEVELOP` | y | SELinux development hooks are built in |
| `CONFIG_KGDB` | not set | no kernel debugger over serial |
| `CONFIG_DYNAMIC_DEBUG` | not set | |
| `CONFIG_MAGIC_SYSRQ` | y | SysRq keys enabled |
| `CONFIG_DEBUG_FS` | y | debugfs mounted |
| `CONFIG_KVM` | unset | no KVM; the hypervisor is Gunyah |
| `CONFIG_HIBERNATION` | y | hibernation support |
| `CONFIG_DM_VERITY_FEC` | y | dm-verity forward error correction |
| `CONFIG_FS_VERITY` | y | file-level verity |
| `CONFIG_PSTORE_RAM` | y | crash log in RAM |
| `CONFIG_QCOM_QFPROM` | m | the QFPROM driver, built as a module |
| `CONFIG_QCOM_QFPROM_SYS` | not set | the `qfprom-sys` interface is not built |
| `CONFIG_MSM_TMECOM_QMP` | m | TME communication over QMP |
| `CONFIG_META_OATMEAL`, `CONFIG_META_GRANOLA_OATMEAL` | not set | Meta-specific options, both off in this build |
| `CONFIG_SECURITY_YAMA`, `CONFIG_SECURITY_LOCKDOWN_LSM` | not set | |

Several things stand out. The kernel has strong exploit mitigations (PAC, BTI, MTE, shadow stacks, KASLR, stack canaries, usercopy hardening). Module signing is off, which means the vendor modules are trusted by location and by AVB, not by a signature the kernel checks. The `SELINUX_DEVELOP` option is built in, but the command line sets `enforcing`.

## Kernel modules

File: `data/android/vendor_ramdisk/modules_modinfo.tsv`, one row per module with its licence, description, author and dependencies. 214 modules: 199 are GPL v2, 11 GPL, and 4 dual BSD/GPL. 106 have dependencies. Every module's vermagic matches `5.10.240-perf-gd253e0b2f72b SMP preempt mod_unload modversions aarch64`.

Modules that connect to the rest of the analysis:

| Module | Description (from modinfo) | Depends on | Why it matters |
|---|---|---|---|
| `nvmem_qfprom.ko` | Qualcomm QFPROM driver | none | The kernel's fuse reader. Author Srinivas Kandagatla (Linaro). |
| `tmecom-intf.ko` | MSM TMECom QTI mailbox protocol client | none | The kernel's mailbox client for TME firmware. |
| `hwkm.ko` | QTI Hardware Key Manager library | `tmecom-intf` | Key handling goes through TME. |
| `crypto-qti-hwkm.ko` | Crypto HWKM library for storage encryption | `hwkm` | Storage keys (the `wrappedkey_v0` path). |
| `qcom-dload-mode.ko` | MSM Download Mode Driver | none | Download mode, matching the XBL cookie. |
| `qcom-reboot-reason.ko` | MSM Reboot Reason Driver | none | Reboot reasons (section 06 has the DTB side). |
| `mfi_i2c_driver.ko` | MFi I2C driver | none | Accessory-authentication I2C. The target part is in the DTBO. |
| `cdsp-loader.ko`, `adsp_loader_dlkm.ko`, `q6_dlkm.ko`, `mdt_loader.ko` | DSP loaders | varies | Load DSP firmware from `/vendor/dsp`. |
| `msm_kgsl.ko` | 3D Graphics driver | several | GPU. Uses the `speed_bin` cell. |
| `camera.ko` | Camera Request Manager | several | Camera pipeline. |
| `gh_rm_drv.ko`, `gh_msgq.ko`, `mem_buf.ko` | Gunyah resource and message drivers | `gh_msgq` | Hypervisor-side messaging and shared memory. |

`hwkm.ko` depending on `tmecom-intf.ko` is the clearest evidence in this set of how key material moves: the kernel asks TME, and TME does the work. The TME firmware is the XBL-side component named in section 02.

## Device tree

The vendor DTB is at `data/android/vendor_ramdisk/vendor_dtb_dump.txt`. Relevant nodes:

- `/soc/qfprom@221c8000`: the fuse block. `reg = <0x221c8000 0x1000>`, `read-only`.
- `/soc/qfprom@221c8000/gpu_speed_bin@119`: fuse cell, byte `0x119`, bits 5 to 12.
- `/soc/qfprom@0`: consumer, `compatible = "qcom,qfprom-sys"`, with `nvmem-cell-names = "gpu_speed_bin"`.
- `/soc/qcom,kgsl-3d0@3d00000`: the GPU. Its `nvmem-cell-names` entry is `speed_bin`, and it points at the same cell.
- `/soc/reboot_reason`: reads `restart_reason` from the PMIC SDAM (`sdam@b100/restart@48`, bits 1 to 7) and from shared IMEM (`msm-imem@146aa000/restart_reason@65c`).
- `/soc/qcom,spmi@c42d000/qcom,pm8150@0`: PM8150 PMIC.

Two notes. The `qfprom-sys` consumer refers to a kernel config (`QCOM_QFPROM_SYS`) that is not set, so whatever reads that node is not this interface. The reboot-reason path has two storage locations, so a reboot reason can be kept across a reset even if the PMIC is reset.

## DTBO overlays

File: `data/android/dtbo/overlay_components.tsv`. The `dtbo.img` partition holds 18 overlays. Each overlay is a complete board configuration. The header's `id` and `rev` fields are zero in all 18, so the header does not identify the board. The overlays differ in which components they enable.

Component groups in the overlays, with how many of the 18 enable them:

| Group | Nodes | Enabled in |
|---|---|---|
| Display | `qcom,dsi-display-primary`, `qcom,dsi-display-secondary`, `qcom,mdss_dsi_ctrl0/1`, `qcom,mdss_mdp`, `qcom,dp_display`, `qcom,wb-display`, `sde_rsc_rpmh` | 18 |
| LCoS panel drivers | `lcosOP02220BA@65`, `lcosOP03010@64` (`meta,lcos-i2c-OP02220`, `meta,lcos-i2c-OP03010`) | 18 each. `lcosOP02220BA` is `okay` in all 18. `lcosOP03010` is `okay` in 16 and `disabled` in 2 (overlays 4 and 11, the Protostar FF3 and ULED builds). |
| Display power | `pmicOP02220@44`, `pmicOP03010@40` | `pmicOP02220` in 18, `pmicOP03010` in 16 (disabled in 2) |
| Display backlight or bias (inferred from the name) | `ktb8399@60` (`kinetic,ktb8399`) | 18, `okay` in all |
| Display temperature | `max31875@48`, `@49`, `@4A` | `okay` in 6 overlays, `disabled` in 12 |
| Display virtual sensors | `display-virtual-sensor`, `skin-virtual-sensor`, `outdoor-virtual-sensor`, `power-state-sensor` | `display-virtual-sensor` is `okay` in 7 |
| Temperature | `tmp114@4C`, `@4D`, `@4E` | 4, 4, 1 overlays |
| Fuel gauge | `max17332@36` | 1 |
| Charger / PMIC | `max77813@18` (`disabled` in 13, `okay` in 3), `max77813_se8_i2c@18` (2 overlays), `max77789@69`, `mp28167@60`, `rt6160@75`, `raa491901@29`, `pmicDA9172@6A` (1 overlay) | varies |
| Camera | `qcom,cam-sensor0`, `qcom,eeprom0`, `oculus,cam_fsync`, `qcom,cam-res-mgr` | 18 |
| Inputs | `gpio_keys`, `camera_key`, `p1_power_slider` (13), `rt685_detect` (13) | varies |
| Audio | `rt685_detect` (`gpio-keys`, 13 overlays), `meta,rt600_ctrl` | varies |
| Accessory and USB | `mfi343s00176@10` (`meta,mfi-i2c`, `okay` in 18), `ptn5150@1d` (`disabled` in 18), `usb_conn_gpio` | varies |
| Light and LED | `aw2026@64` (`awinic,aw2026_led`) | 18 |
| Peripheral link | `stp-interface`, `spi-stp@0` (`meta,spi-stp`), `st60a3g1@6d` (`meta,st60-i2c`, `disabled` in 18) | varies |
| Power and battery | `metabattery`, `mcu_thermistor`, `ads1115@49`, `hw-comparator-sensor` | 18 |
| Other Meta | `amem`, `hyperoff@0` (11), `reboot_reason`, `ramoops@a6c00000` | varies |

The LCoS names and the `meta,lcos-i2c` compatible strings point to LCoS (liquid crystal on silicon) microdisplay drivers. Which driver runs on which panel, and which one the shipping device uses, is not settled. The `ptn5150` USB-C controller and the `st60a3g1` device are present but disabled in all 18 overlays. I have not identified what they are.

The `mfi343s00176` node with `meta,mfi-i2c` is the MFi authentication part. Its role in accessory identification is inferred from the name. Unverified.

The count of 18 overlays and the per-overlay differences are verified. Each overlay's root node also carries a model name and a `qcom,board-id`, so each overlay names one hardware build. The table is in the next section.

### Board revisions

Each overlay's root node has `model`, `compatible` (`meta,greatwhite` plus a revision string), `qcom,msm-id = <0x243 0x10000>` (the same in all 18), and `qcom,board-id = <0x22 N>`. The second value is the board ID. Verified. Files: `data/android/dtbo/board_ids.tsv` and `data/android/dtbo/board_component_matrix.tsv` (71 components by 18 boards).

| Index | Model name | Board ID |
|---:|---|---|
| 0 | Greatwhite Config Dev0 | 0xB0 |
| 1 | Greatwhite EVT1 Camera DOE | 0xBA |
| 2 | Greatwhite Dev0 2023 | 0xB3 |
| 3 | Greatwhite Dev1.0 | 0xBB |
| 4 | Protostar FF3 (RT700) | 0xD1 |
| 5 | Greatwhite DVT | 0xAE |
| 6 | Greatwhite Dev0.2 | 0xB7 |
| 7 | Greatwhite EVT2 | 0xBF |
| 8 | Greatwhite Config Dev0.1 | 0xB1 |
| 9 | Greatwhite Dev1.1 | 0xBD |
| 10 | Greatwhite PreP1 | 0xB2 |
| 11 | Greatwhite ULED | 0xB9 |
| 12 | Greatwhite PreP1+ | 0xB4 |
| 13 | Greatwhite PVT | 0xAF |
| 14 | Greatwhite P1 (RT700) | 0xB6 |
| 15 | Greatwhite P1 (RT600) | 0xB5 |
| 16 | Greatwhite EVT1 (RT700) | 0xB8 |
| 17 | Greatwhite EVT1 DOE2 (Onewire) | 0xBC |

The names give a build sequence: Dev0 and Dev1 first, then PreP1, EVT1, EVT2, DVT and PVT, then the P1 build. "Protostar FF3" is a prototype label. "ULED" and "Onewire" are names only; their hardware meaning is not established.

The RT600 and RT700 variants of P1 differ in exactly four components. `hyperoff` is present only on RT700. `tmp114@4C` and `tmp114@4D` are present only on RT600. `display-virtual-sensor` is disabled on RT700 and enabled on RT600. The `hyperoff` difference matches the software: `mcu-properties.sh` turns on hyperoff only in the RT700 configuration (section 09).
