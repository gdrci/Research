# 07 - Wireless and connectivity (Wi-Fi, Bluetooth, WPSS)

[中文](07-wireless-and-connectivity.zh-CN.md)

This section covers the Wi-Fi and Bluetooth stack as it is laid out in the OTA: the remote subsystem that runs the radio (WPSS), the kernel drivers, the init scripts and HAL services, the configuration files, and the firmware images. Each claim is marked as observed (read from the files), inferred (a reasonable reading that the files do not state), or not found.

## Summary

- The Wi-Fi and Bluetooth firmware are in two FAT16 images. Wi-Fi board data and the WLAN microcode are inside `modem.img` (`/image/kiwi/`). Bluetooth patches and NV files are in `bluetooth.img`.
- The radio runs in a remote subsystem called WPSS. The XBL configuration names it, and the device tree names its SMP2P channels for WLAN.
- The kernel side is the Qualcomm CNSS2/ICNSS2 platform driver plus the `wlan.ko` host driver.
- The host stack talks to the chip through two HAL services: the Qualcomm Wi-Fi HAL and a Meta (`vendor.oculus`) Wi-Fi HAL.

- The chip is the Qualcomm WCN7850, a combined Wi-Fi and Bluetooth part. The Bluetooth patch banner names it (`PF=WCN7850ROM=`), and the WLAN build tag is `WLAN.HMT`. Observed.

## Chip identity: WCN7850 in the firmware, WCN6x5x in the device tree

Two names appear for the same radio, and they do not fully agree:

- The Bluetooth patch banner says `PF=WCN7850ROM=` (observed, above).
- The device tree names the Bluetooth node `/soc/bt_wcn6x5x` with `compatible = "qcom,kiwi"`, and the supplies are named `qcom,bt-vdd-aon`, `qcom,bt-vdd-dig`, `qcom,bt-vdd-rfaOp8`, `qcom,bt-vdd-rfa2` and `qcom,bt-vdd18-aon`, with reset GPIOs for Bluetooth and WLAN (observed, `data/android/vendor_ramdisk/vendor_dtb_dump.txt`).
- The Linux binding for the WCN7850 Bluetooth part (`qcom,wcn7850-bt`) uses different supply names (`vddaon`, `vdddig`, `vddrfa0p8`, `vddrfa1p2`, `vddrfa1p8`, `vddrfacmn`, `vddwlcx`, `vddwlmx`). So the device tree follows the older WCN6x5x naming, not the WCN7850 binding exactly.

Public corroboration (search results, not opened): the upstream Linux `ath12k` driver supports WCN7850 with hw2.0 firmware, and the public firmware tree carries a WLAN build string of the form `WLAN.HMT.1.1.c5-00284-QCAHMTSWPL_V1.0_V2.0_SILICONZ-3`. The device's own tag is `WLAN.HMT.1.1.c4-00443-…`, the same family string with an earlier build. The public tree names the board file `ath12k/WCN7850/hw2.0/board-2.bin`. The device ships `bdwlan.elf`, not `board-2.bin`, so the device's WLAN data is packaged differently from the upstream layout. Inferred from the strings, not checked against the firmware itself.

The WLAN side uses the same family name: the modem directory is `kiwi` and the Wi-Fi config directory is `kiwi_v2` (sections 07 and 16). Inferred: `kiwi` is the internal platform name of this radio family, and the device tree is written for it.

Reference architecture. The Qualcomm WCN6856 overview (document 80-WL542-10, a different chip from the same generation) shows the structure that this family is likely to share: a PMU, a crystal and clock interface, OTP, RFFE control signals, a Bluetooth subsystem, and two WLAN MAC/PHY pairs. Its host interfaces are UART or USB for Bluetooth HCI, PCIe for WLAN, and Slimbus, PCM or I2S for Bluetooth audio. Those host interfaces match what this device shows: `ttyHS0` with `hs_uart_operation` for Bluetooth (this section), `mhi0` on PCIe for WLAN (section 11), and the Slimbus and SLIM-DEV1 back ends for audio (section 12). The WCN6856 is a different part, so this is an architecture reference only. Inferred, not checked against the WCN7850 datasheet, which has not been read.

## WPSS, the Wi-Fi remote subsystem

The XBL configuration (`data/strings/xbl_config.txt`) has two sections for the subsystem, `[FULL_WPSS]` and `[CORE_WPSS]`. Both are `Type = elf_split` with `ImagePath = \image\wpss` and `SubsysID = 6`. They reserve memory at `ResvMemoryStart = 0x85600000`. The partition labels are `modem_a` (full) and `core_nhlos_a` (core). Both carry the same `ProxyGuid`, `61513695-E0C6-4F07-BF41-A51A7770640E`. Observed. The sections are in `data/xbl/wpss_config_sections.txt`.

The PIL proxy list also names `PIL_WPSS`. Observed.

The device tree (`data/android/vendor_ramdisk/vendor_dtb_dump.txt`) defines the WPSS nodes:

- `/soc/qcom,smp2p-wpss` with `master-kernel` and `slave-kernel` children. These are the kernel-side ends of an SMP2P link.
- Five WLAN channels under it: `qcom,smp2p-wlan-1-in`, `-1-out`, `-2-in`, `-2-out` and `-3-out`. Observed.
- A coresight path `/soc/wpss_etm` with a funnel and TPDM nodes (`funnel_wpss`, `tpdm_wpss`, `tpdm_wpss1`). Observed. The trace path is not analysed further.

The WPSS firmware file itself (`wpss.mdt` or `wpss.b*`) is not in the OTA. Checked: a search of every extracted image for `wpss` found only configuration and tables, and QDSS trace strings inside the ADSP and CDSP segments (`modem.img`). The modem FAT image has no `wpss` file, and `vendor`, `odm`, `system_ext` and `product` have none. The XBL entry names `modem_a` as the partition for the image, so the image is most likely in a partition that the OTA does not include. Inferred.

The init script writes to the ICNSS driver before the Wi-Fi service starts (below). Observed:

    on early-boot
        write /sys/kernel/icnss/wlan_en_delay 1000
        write /sys/kernel/icnss/wpss_boot 1

So the kernel boots WPSS through a sysfs write. The `wlan_en_delay` value is a delay in milliseconds before the WLAN enable line is asserted. Inferred from the name.

## Kernel drivers

From `data/android/vendor_ramdisk/modules_modinfo.tsv`. Observed.

| Module | Description | Depends on |
|---|---|---|
| `icnss2.ko` | iWCN core platform driver | `wlan_firmware_service`, `qmi_helpers`, `pdr_interface`, `rproc_qcom_common`, `qcom_ramdump` |
| `cnss2.ko` | CNSS2 platform driver | `pci-msm-drv`, `qmi_helpers`, `wlan_firmware_service`, `mhi`, `cmd-db`, `cnss_plat_ipc_qmi_svc` |
| `wlan.ko` | WLAN host device driver (Qualcomm Atheros) | `cnss2`, `cnss_prealloc`, `cnss_nl`, `cnss_utils` |
| `wlan_firmware_service.ko` | WLAN firmware QMI service | `qmi_helpers` |
| `bt_fm_slim.ko` | BTFM Slimbus slave driver | `slimbus`, `btpower` |

The chain is `wlan.ko` on top of `cnss2`, which talks to the firmware over QMI. `icnss2` is the ICNSS path, the older platform driver. The module names are observed. Which of the two platform drivers the WPSS boot uses is inferred from the init script writing to `/sys/kernel/icnss`.

The vendor firmware directory has `wlan` as a subdirectory (`fs/vendor/firmware/wlan/qca_cld`). It contains three symbolic links, all dangling in the OTA:

- `WCNSS_qcom_cfg.ini` to `/vendor/etc/wifi/kiwi_v2/WCNSS_qcom_cfg.ini` (this target exists in the image)
- `wlan.cfg` to `/mnt/vendor/persist/wlan.cfg`
- `wlan_mac.bin` to `/mnt/vendor/persist/wlan_mac.bin`

The two `/mnt/vendor/persist` targets are written on the device at run time (the MAC address and the per-device config). They are not in the OTA. Observed. The `qca_cld` name is the Qualcomm Atheros cfg80211 driver family.

## Init scripts and HAL services

From `fs/vendor/etc/init/` (`data/userspace/wifi_bt_init_and_modules.txt`). Observed.

- `init.vendor.wlan.rc`: the early-boot writes above, and `wifi_qos_daemon` (class `late_start`, user `wifi`, `NET_ADMIN`).
- `vendor.lowi` runs `/vendor/bin/lowirpcd`, a Qualcomm low-power Wi-Fi RPC daemon (name from the file). Inferred from the name.
- `vendor.wifi_hal_legacy` runs `/vendor/bin/hw/android.hardware.wifi@1.0-service-lazy`, the Qualcomm Wi-Fi HAL.
- `vendor.oculus.wifi-hal-1-0` runs `/vendor/bin/hw/vendor.oculus.hardware.wifi@1.0-service`. Its binary exports `vendor::oculus::hardware::wifi::V1_0::IWifi` and registers it as a HIDL service. Observed from the binary's symbols. This is the Meta-side Wi-Fi interface.
- `android.hardware.bluetooth@1.0-service-qti` runs as `vendor.bluetooth-1-0-qti` in class `hal`, with `BLOCK_SUSPEND` and `NET_ADMIN`. On `boot` its UART control node `/sys/class/tty/ttyHS0/device/hs_uart_operation` is set to mode 0660, owner `bluetooth`. Observed. The node is on `ttyHS0`, which is the high-speed UART the Bluetooth driver uses. Inferred from the node name.

The supplicant and HAL libraries in `vendor/lib64` include the standard `android.hardware.wifi.supplicant@1.0` to `@1.5` and `android.hardware.wifi.hostapd@1.0` to `@1.3`. Observed from the file names.

## Wi-Fi configuration

Files under `vendor/etc/wifi/` (`data/userspace/wifi_config_and_symlinks.txt`). Observed.

- `kiwi_v2/WCNSS_qcom_cfg.ini`: the driver's factory-default overrides. Examples: `gDot11Mode=0`, `gEnableDFSMasterCap=1`, `FastRoamEnabled=1`, `gEnableTXSTBC=1`, `gEnableTxSUBeamformer=1`, `gVhtMpduLen=2`. The `kiwi_v2` name is the same as the `kiwi` directory in the modem image; whether they are related is inferred.
- `wpa_supplicant.conf`, `wpa_supplicant_overlay.conf`, `p2p_supplicant_overlay.conf`: supplicant configuration.
- `icm.conf`: a Qualcomm licence header (2017, 2019, 2022). Its body was not decoded.
- `vendor_cmd.xml`: vendor command table for the HAL.

## Firmware

### Wi-Fi: inside `modem.img`

`modem.img` is a FAT16 image of 36.5 MB with 165 files (`data/remote/modem_listing.txt`). Its Wi-Fi content is in `/image/kiwi/` (described in section 05):

- `amss.bin`, `amss20.bin`: modem firmware images.
- `bdwlan.elf`, `bdwlan.elf.xz`: Wi-Fi board data.
- `regdb.bin`: the wireless regulatory database.
- `phy_ucode.elf`, `phy_ucode20.elf`: PHY microcode.

The build ID for the WLAN side is `WLAN.HMT.1.1.c4-00443-QCAHMTSWPL_V1.0_V2.0_SILICONZ-1` (`data/remote/modem_verinfo.txt`). Observed. The `HMT` tag matches the Hamilton chip name used by Bluetooth (below). That the WLAN firmware runs on WPSS is inferred from the WPSS configuration and the `kiwi` path. The file-level link between the two is not confirmed.

### Bluetooth: `bluetooth.img`

`bluetooth.img` is a FAT16 image of 0.78 MB with 51 files (`data/remote/bluetooth_listing.txt`). Observed.

- `hmtbtfw10.tlv` (91,308 bytes) with version file `hmtbtfw10.ver` = `BTFW.HAMILTON.1.0.0-00214-PATCH-1`.
- `hmtbtfw20.tlv` (253,484 bytes) with version file `hmtbtfw20.ver` = `BTFW.HAMILTON.2.0.0-00797-PATCHZ-1.105163.2.109423.3`.
- `hmtnv10.*` and `hmtnv20.*`: NV configuration files, about 30 variants (`.bin`, `.b0c`, `.b0202`...`.b1e`). The suffixes look like per-variant configuration. Unverified.

Both TLV files start with the byte `0x01`, which is the HCI command packet indicator. The following bytes are a vendor patch segment. The exact segment layout is inferred and not decoded. The raw headers are in `data/remote/bluetooth_version_files.txt`.

The build manifest in `modem.img/verinfo/ver_info.txt` lists `btfm` as `BTFW.HAMILTON.2.0.0-00819-PATCHZ-1`. The Bluetooth image's own version file says `00797`. The two differ. Resolved in part: the patch's own text, inside `hmtbtfw20.tlv`, reads `Patch Release PF=WCN7850ROM= 0200 BUILD=BTFW.HAMILTON.2.0.0-00797-PATCHZ-1.105163.2.109423.3`, so the image is build 00797. The `00819` entry is a different build that this image does not carry. Observed from the TLV strings. The manifest is a build-level record and the `.ver` file is what the image carries. The reason for the difference is not established.

## What is not found

- The WPSS firmware image (`wpss.mdt` or `wpss.b*`). Searched in every extracted image; not in the OTA.
- The code that reads the `/sys/kernel/icnss` nodes, and the ICNSS-to-WPSS boot sequence. Not in the images examined.
- The `/mnt/vendor/persist` contents (`wlan.cfg`, `wlan_mac.bin`). Written at run time.
- The Bluetooth TLV segment format, beyond the first bytes.

## Evidence

- `data/xbl/wpss_config_sections.txt`
- `data/android/vendor_ramdisk/wpss_dt_nodes.txt`
- `data/android/vendor_ramdisk/modules_modinfo.tsv`
- `data/userspace/wifi_bt_init_and_modules.txt`
- `data/userspace/wifi_config_and_symlinks.txt`
- `data/remote/modem_listing.txt`, `data/remote/modem_verinfo.txt`
- `data/remote/bluetooth_listing.txt`, `data/remote/bluetooth_version_files.txt`
