# 17 - Chip inventory

[中文](17-chip-inventory.zh-CN.md)

This section lists the integrated circuits that the OTA shows the glasses use, with the evidence for each identification. It is a reverse-engineering inventory. Each entry gives the part as named in the files, the function the files give for it, and a confidence level:

- **Named**: the part number appears in a driver, init script, device tree, or binary string tied to that function.
- **Inferred**: the function is clear but the part number is not in the files, or the part is named by a family.
- **Not named**: the function is present but no part number was found.

## Application processor and power

| Part | Function | Evidence | Confidence |
|---|---|---|---|
| Qualcomm "Aurora" SoC (`SocAuroraLAA`) | Application processor, platform `neo` | XBL `IMAGE_VARIANT_STRING=SocAuroraLAA`; device tree `qcom,neo-*` nodes (pinctrl, pdc, pcie, nsp, mmss, videocc, rpmh-clk, system); `ro.board.platform=neo` (section 04) | Named (codename); marketing number not in the files Public search: no public source for the codename. Qualcomm's public smart-glasses SoCs are AR1 Gen 1, AR1+ Gen 1 and AR2 Gen 1. The device tree has no AR1 or AR2 names, so no match is made. |
| Qualcomm PM8150 | Main PMIC over SPMI | 50 `qcom,pm8150` nodes in the device tree; `pm8150@0` in the SELinux sysfs labels (section 11) | Named Public search: the Linux SPMI binding lists `qcom,pm8150` and `qcom,pm8150b`; no public register map found. |
| Qualcomm PM8008 (PM8008i) | Companion PMIC with regulators, in two chips | 22 `qcom,pm8008i-regulator` nodes; `qcom,pm8008-chip` (section 04) | Named |
| Maxim MAX77655 | Display power PMIC, configured at boot | `max77655_util --config_gw_display_pmic` in `vendor/bin/hw`, run by `fix-gw-display-pmic.rc` (section 13); `max77655` in the MCU tub and the boot images | Named Public search: Maxim's MAX77655 programmer's guide uses slave address 0x44 in its example code. Not checked against the datasheet. |
| Maxim MAX77813 | Charger or PMIC (overlays) | `max77813@18` in overlays (section 04) | Named |
| Maxim MAX77789 | Charger or PMIC (overlays) | `max77789@69` in overlays | Named |
| Maxim MAX17332 | Fuel gauge | 138 hits in `vendor.img`, `max17332-battery` power-supply nodes in SELinux and in `init.metasoc.sh` (sections 04, 09, 11) | Named |
| MPS MP28167 | Regulator (overlays) | `mp28167@60` in overlays | Named |
| Richtek RT6160 | Regulator (overlays) | `rt6160@75` in overlays | Named |
| Renesas RAA491901 | Regulator (overlays) | `raa491901@29` in overlays | Named |
| Dialog DA9172 | PMIC (one overlay) | `pmicDA9172@6A` in overlays | Named |
| "OP02220" and "OP03010" pair | Display / LCoS power and driver PMICs. The vendor is not named | `pmicOP02220@44`, `pmicOP03010@40`; `lcos-i2c-OP02220`, `lcos-i2c-OP03010` device nodes (sections 04, 13, 14) | Named (part names); vendor not established |
| Silergy SY8809 and SY5502 | DC-DC converters in the case firmware | 14 and 8 hits in `vendor.img` and the case `.tub` files (section 09) | Named in firmware; function not established |

## Display and LCoS

| Part | Function | Evidence | Confidence |
|---|---|---|---|
| LCoS micro-display engine | The display engine of the glasses, driven by the MCU console | `lcos` console commands (MIPI init, PGEN, LED drivers, temperature, error counters) in `mcu.default.rt700.tub` (section 14) | Named as LCoS; vendor part number not in the files |
| LCoS LED drivers | Red, green and blue LED current and PFM/PWM drivers | `setledcurrents`, `set-led-mode pfm/pwm`, `VF_1MA_*` calibration fields (section 14) | Named as LED drivers; part not in the files |
| Visionox R66451 AMOLED | Panel with command and video modes, with and without DSC (section 13) | QDCM calibration file names and backlight calibration XML in `vendor/etc/display` | Named (panel); whether it is the glasses' panel is not confirmed |
| Novatek NT36672E | LCD panel (QDCM names) | `qdcm_calib_data_nt36672e_*` | Named (panel) |
| Sharp 2k, 4k and QHD panels | Panels (QDCM names) | `qdcm_calib_data_Sharp_*` | Named (panel) |
| Kinetic KTB8399 | Backlight driver | `ktb8399@60` (`kinetic,ktb8399`) in overlays (section 04) | Named |
| Awinic AW2026 | LED driver | `aw2026@64` (`awinic,aw2026_led`) in overlays | Named |

## Audio

| Part | Function | Evidence | Confidence |
|---|---|---|---|
| Maxim MAX98388 (ADI, 16-bump WLP) | Mono Class-D speaker amplifier with I/V feedback, PCM (I2S/LJ/TDM) input and I2C control. Supply 2.3 V to 10 V. Datasheet Rev. 2 (ADI, 2024): 1.32 W into 4 ohm at 3.7 V, THD+N better than -83 dB at 1 kHz, dynamic range up to 111 dB A-weighted, software shutdown below 5 uW, 1 ms turn-on. Its I2C address table (datasheet Table 9) sets the 7-bit address from the ADDR pin: VDD gives 0x38, GND gives 0x39, SDA gives 0x3A, SCL gives 0x3B. The ODM script's `0x3A` (left) and `0x38` (right) are therefore the SDA and VDD straps, so the left/right address values are consistent with the datasheet. The kernel binding example uses 0x39 (GND strap). | Named. Address resolved from the datasheet (sections 12, 17) |
| Qualcomm WCD-style codec macros (RX, TX, VA, WSA) | Audio codec and LPASS macros | `RX_MACRO`, `TX_MACRO`, `VA_MACRO`, `WSA_MACRO` in the mixer paths, and the `lpass-cdc` nodes in the device tree (section 12) | Named (family); the codec part number is not in the files |
| WCD9320 | Codec name in one library | `libats.so` and `vendor.img` contain the string (section 12) | Named in a string only; not used in the device tree |
| NXP RT700 (MIMXRT798S) | MCU (Cortex-M33) and HiFi4 audio DSP in one part | `system_MIMXRT798S_hifi4.c` in the DSP image; `arvr/firmware/lib/uhal/peripherals/rt700/` drivers in the MCU image (sections 14, 15) | Named |
| NXP RT600 | The other variant of the same family (`is_rt600` switch, section 09) | `nxp_rt600_RI2021_6_newlib` toolchain path in the DSP image; `rt600_ctrl` kernel driver name | Named as a variant; the RT600 part number is in the toolchain path only |
| Qualcomm WSA (speaker amp macros) | Qualcomm smart-speaker amplifier macros in the reference mixer config | `WSA2_RX0`, `SpkrLeft VISENSE` (section 12) | Named in the reference config; not confirmed on the device |

## Sensors and input

| Part | Function | Evidence | Confidence |
|---|---|---|---|
| TDK InvenSense ICM-45688 | 6-axis IMU for navigation sensor fusion and the camera IMU logger | `libnavigationsensorfusion.so` contains "InvenSense ICM45688" (section 13) | Named |
| Cypress PSoC 4 (CY8C4046) | Touch controller on the frame | `cy8c4046_fw` driver source path, `psoc in %s mode` strings, `touch-app-b0.cyacd2` image (section 14) | Named |
| TI TMP114 | Temperature sensors (overlays) | `tmp114@4C`, `@4D`, `@4E` in overlays (section 04) | Named |
| Maxim MAX31875 | Temperature sensors (overlays) | `max31875@48`, `@49`, `@4A` in overlays | Named |
| TI ADS1115 | ADC for analogue sensors (overlays) | `ads1115@49` in overlays | Named |
| Ambient light sensor | ALS driver, with a flicker mode | `als_*` console strings and `als_flicker_*` (section 14) | Not named |
| Hinge sensor | Hinge open and close input | `hinge_open`, `hinge_close` (section 14) | Not named |

## Connectivity

| Part | Function | Evidence | Confidence |
|---|---|---|---|
| Qualcomm WCN7850 (firmware banner); the device tree names the family WCN6x5x (`bt_wcn6x5x`, `qcom,kiwi`) | Wi-Fi and Bluetooth combo | Bluetooth patch banner `PF=WCN7850ROM=` (section 07); device tree node `/soc/bt_wcn6x5x` with `qcom,kiwi`; WLAN tag `WLAN.HMT`. Qualcomm's FastConnect 7800 brief (87-PW329-1 Rev. B, 2023) orders parts WCN785x-1 and WCN785x-5, names 14 nm process, Wi-Fi 7/6E/6, 2.4/5/6 GHz, 320 MHz channels, 4K QAM, MLO, Bluetooth 5.4, LE Audio and ANT+. The brief does not name WCN7850 or list the host interfaces. | Named (firmware); the part falls in the WCN785x family. Bluetooth 5.4 is from the brief; WCN7850's exact version is not confirmed |
| Qualcomm WPSS subsystem | Wi-Fi remote processor inside the SoC | XBL `[FULL_WPSS]` and `[CORE_WPSS]` sections; SMP2P device-tree nodes (section 07) | Named subsystem; the image is not in the OTA |
| NXP PTN5150 | USB Type-C controller (`ptn5150@1d`, disabled in 18 overlays) | Overlays (section 04) | Named |
| Apple MFi authentication chip (343S00176) | Accessory authentication for the case or the band | `mfi343s00176@10` (`meta,mfi-i2c`) in overlays; `vendor.meta.hardware.mfi@1.0-service` and `/dev/mfi-i2c` (section 09) | Named. The MFi part is an Apple-program chip; the vendor string on the part is not in the files |
| STP link chip (`st60a3g1`) | The MCU transport (`meta,st60-i2c` in overlays) | Overlays (section 04); STP events in the MCU console (section 14) | Named in overlays; disabled in the 18 overlays shown |

## Memory, storage and other

| Part | Function | Evidence | Confidence |
|---|---|---|---|
| Storage controllers | Boot and data storage | A UFS PHY clock gate (`gcc_ufs_phy_gdsc`) and an SDHCI host (`sdhci@7c4000`, the `mmc0` path in the SELinux labels) are in the device tree (section 04). The UEFI image lists UFS, eMMC, NAND and NVMe among its boot-device strings (section 02) | Named controllers; the device part is not named, and which storage type is fitted is not established |
| Secure element (`hal_secure_element`) | Secure element HAL | SELinux domain and service labels (section 11) | Not named |
| Haptic driver | Vibration (`hal_vibrator`) | SELinux label only | Not named |

## Evidence

- `data/android/vendor_ramdisk/vendor_dtb_dump.txt`: SoC, PMIC and sensor compatible strings.
- `data/android/vendor_ramdisk/modules_modinfo.tsv`: the wireless and sensor kernel modules.
- `data/android/audio/max98388_v2.sh`: the speaker amplifier init sequences, copied from `odm/bin/` (section 12).
- `data/mcu/mcu_console_strings.txt`: LCoS, touch, IMU and ALS console strings (section 14).
- `data/dsp/dsp_symbol_table.txt`: the RT700 DSP symbols (section 15).
