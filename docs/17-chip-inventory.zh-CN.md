# 17 - 芯片清单

[English](17-chip-inventory.md)

本节列出 OTA 中显示眼镜所使用的集成电路，并给出每个识别结果的依据。这是逆向工程的清单。每一项给出文件中的器件型号、文件所示的功能，以及可信度：

- **已命名**：器件型号出现在与该功能相关的驱动、init 脚本、设备树或二进制字符串中。
- **推断**：功能清楚，但文件中没有器件型号，或只能按系列命名。
- **未命名**：存在该功能，但未找到器件型号。

## 应用处理器与电源

| 器件 | 功能 | 依据 | 可信度 |
|---|---|---|---|
| 高通 "Aurora" SoC（`SocAuroraLAA`） | 应用处理器，平台 `neo` | XBL `IMAGE_VARIANT_STRING=SocAuroraLAA`；设备树中的 `qcom,neo-*` 节点（pinctrl、pdc、pcie、nsp、mmss、videocc、rpmh-clk、system）；`ro.board.platform=neo`（第 04 节） | 已命名（代号）；文件中没有市场型号 公开搜索：未找到该代号的公开来源。高通公开的智能眼镜 SoC 为 AR1 Gen 1、AR1+ Gen 1 与 AR2 Gen 1。设备树中没有 AR1 或 AR2 名称，因此未作匹配。 |
| 高通 PM8150 | 通过 SPMI 连接的主 PMIC | 设备树中 50 个 `qcom,pm8150` 节点；SELinux 的 sysfs 标签中有 `pm8150@0`（第 11 节） | 已命名 公开搜索：Linux SPMI 绑定列出 `qcom,pm8150` 与 `qcom,pm8150b`；未找到公开的寄存器映射。 |
| 高通 PM8150（已对照设备树转储核实） | SPMI 从设备 0（`/soc/qcom,spmi@c42d000/qcom,pm8150@0`）上的外设基址：temp-alarm `0x2400`，power-on `0x800`，VADC `0x3100`（`qcom,spmi-adc5`），ADC-TM `0x3500`（`qcom,adc-tm5`），SDAM `0xB100`（重启原因位于 `0x48`），GPIO `0xC000`（`qcom,pm8150-gpio`，10 个 GPIO），时钟分频器 `0x5B00`。VADC 通道包括芯片温度（`0x06`）、XO 热敏电阻（`0x4C`）、机壳热敏电阻（`0x4D`）与 WLAN 热敏电阻（`0x4E`）。RTC 节点（`qcom,pm8941-rtc`）的 `reg` 单元为 `0x6000`（`rtc`）与 `0x6100`（`alarm`）；转储的字符串显示丢失了第二个单元的末尾 NUL，因此此处按原始字节解码（`00 00 60 00` 与 `00 00 61 00`）。已由原始字节核实。来源：`data/android/vendor_ramdisk/vendor_dtb_dump.txt`。寄存器级细节未公开。 | 已命名；基址与通道来自设备树 |
| 高通 PM8008（PM8008i） | 带稳压器的配套 PMIC，共两颗 | 22 个 `qcom,pm8008i-regulator` 节点；`qcom,pm8008-chip`（第 04 节） | 已命名 |
| Maxim MAX77655 | 显示电源 PMIC，开机时配置 | `vendor/bin/hw` 中的 `max77655_util --config_gw_display_pmic`，由 `fix-gw-display-pmic.rc` 运行（第 13 节）；MCU tub 与启动镜像中也有 `max77655` | 已命名 公开搜索：Maxim 的 MAX77655 编程指南示例代码使用从机地址 0x44。未与数据手册核对。 |
| Maxim MAX77813 | 充电器或 PMIC（覆盖层） | 覆盖层中的 `max77813@18`（第 04 节） | 已命名 |
| Maxim MAX77789 | 充电器或 PMIC（覆盖层） | 覆盖层中的 `max77789@69` | 已命名 |
| Maxim MAX17332 | 电量计 | `vendor.img` 中 138 处命中；SELinux 与 `init.metasoc.sh` 中的 `max17332-battery` 电源节点（第 04、09、11 节） | 已命名 |
| MPS MP28167 | 稳压器（覆盖层） | 覆盖层中的 `mp28167@60` | 已命名 |
| Richtek RT6160 | 稳压器（覆盖层） | 覆盖层中的 `rt6160@75` | 已命名 |
| Renesas RAA491901 | 稳压器（覆盖层） | 覆盖层中的 `raa491901@29` | 已命名 |
| Dialog DA9172 | PMIC（一个覆盖层） | 覆盖层中的 `pmicDA9172@6A` | 已命名 |
| "OP02220" 与 "OP03010" 一对 | 显示 / LCoS 电源与驱动 PMIC。厂商未明确 | `pmicOP02220@44`、`pmicOP03010@40`；设备节点 `lcos-i2c-OP02220`、`lcos-i2c-OP03010`（第 04、13、14 节） | 器件名已命名；厂商未确定 |
| Silergy SY8809 与 SY5502 | 机壳固件中的 DC-DC 转换器 | `vendor.img` 与机壳 `.tub` 文件中分别有 14 与 8 处命中（第 09 节） | 固件中已命名；功能未确定 |

## 显示与 LCoS

| 器件 | 功能 | 依据 | 可信度 |
|---|---|---|---|
| LCoS 微显示引擎 | 眼镜的显示引擎，由 MCU 控制台驱动 | `mcu.default.rt700.tub` 中的 `lcos` 控制台命令（MIPI 初始化、PGEN、LED 驱动、温度、错误计数）（第 14 节） | 已命名为 LCoS；文件中没有厂商型号 |
| LCoS LED 驱动 | 红、绿、蓝 LED 电流与 PFM/PWM 驱动 | `setledcurrents`、`set-led-mode pfm/pwm`、`VF_1MA_*` 校准字段（第 14 节） | 已命名为 LED 驱动；文件中没有型号 |
| Visionox R66451 AMOLED | 带命令与视频模式、带与不带 DSC 的面板（第 13 节） | `vendor/etc/display` 中的 QDCM 校准文件名与背光校准 XML | 已命名（面板）；是否为眼镜所用面板尚未确认 |
| Novatek NT36672E | LCD 面板（QDCM 名称） | `qdcm_calib_data_nt36672e_*` | 已命名（面板） |
| Sharp 2k、4k 与 QHD 面板 | 面板（QDCM 名称） | `qdcm_calib_data_Sharp_*` | 已命名（面板） |
| Kinetic KTB8399 | 背光驱动 | 覆盖层中的 `ktb8399@60`（`kinetic,ktb8399`）（第 04 节） | 已命名 |
| Awinic AW2026 | LED 驱动 | 覆盖层中的 `aw2026@64`（`awinic,aw2026_led`） | 已命名 |

## 音频

| 器件 | 功能 | 依据 | 可信度 |
|---|---|---|---|
| Maxim MAX98388（ADI，16 凸点 WLP） | 单声道 D 类扬声器功放，带 I/V 反馈，PCM（I2S/LJ/TDM）输入，I2C 控制。供电 2.3 V 至 10 V。数据手册 Rev. 2（ADI，2024）：4 欧姆下 3.7 V 时输出 1.32 W，1 kHz 下 THD+N 优于 -83 dB，动态范围最高 111 dB（A 计权），软件关断低于 5 µW，上电 1 ms。I2C 地址表（数据手册表 9）由 ADDR 脚决定 7 位地址：接 VDD 为 0x38，接 GND 为 0x39，接 SDA 为 0x3A，接 SCL 为 0x3B。因此 ODM 脚本中的 `0x3A`（左）与 `0x38`（右）分别对应接 SDA 与接 VDD，与数据手册一致。内核绑定示例使用 0x39（接 GND）。 | 已命名。地址已据数据手册解决（第 12、17 节） |
| 高通 WCD 风格编解码宏（RX、TX、VA、WSA） | 音频编解码与 LPASS 宏 | 混音路径中的 `RX_MACRO`、`TX_MACRO`、`VA_MACRO`、`WSA_MACRO`，以及设备树中的 `lpass-cdc` 节点（第 12 节） | 已命名（系列）；编解码器型号不在文件中 |
| WCD9320 | 一个库中的编解码器名称 | `libats.so` 与 `vendor.img` 中包含该字符串（第 12 节） | 仅在字符串中命名；设备树中未使用 |
| NXP RT700（MIMXRT798S） | 一颗芯片内的 MCU（Cortex-M33）与 HiFi4 音频 DSP | DSP 镜像中的 `system_MIMXRT798S_hifi4.c`；MCU 镜像中的 `arvr/firmware/lib/uhal/peripherals/rt700/` 驱动（第 14、15 节） | 已命名 |
| NXP RT600 | 同一系列的另一变体（`is_rt600` 开关，第 09 节） | DSP 镜像中的 `nxp_rt600_RI2021_6_newlib` 工具链路径；内核驱动名 `rt600_ctrl` | 已命名为变体；RT600 型号只出现在工具链路径中 |
| 高通 WSA（功放宏） | 参考混音配置中的高通智能扬声器功放宏 | `WSA2_RX0`、`SpkrLeft VISENSE`（第 12 节） | 在参考配置中已命名；未在设备上确认 |

## 传感器与输入

| 器件 | 功能 | 依据 | 可信度 |
|---|---|---|---|
| TDK InvenSense ICM-45688 | 用于导航传感器融合与摄像头 IMU 记录的 6 轴 IMU | `libnavigationsensorfusion.so` 中含 "InvenSense ICM45688"（第 13 节） | 已命名 |
| Cypress PSoC 4（CY8C4046） | 镜框上的触控控制器 | `cy8c4046_fw` 驱动源路径、`psoc in %s mode` 字符串、`touch-app-b0.cyacd2` 镜像（第 14 节） | 已命名 |
| TI TMP114 | 温度传感器（覆盖层） | 覆盖层中的 `tmp114@4C`、`@4D`、`@4E`（第 04 节） | 已命名 |
| Maxim MAX31875 | 温度传感器（覆盖层） | 覆盖层中的 `max31875@48`、`@49`、`@4A` | 已命名 |
| TI ADS1115 | 模拟传感器用 ADC（覆盖层） | 覆盖层中的 `ads1115@49` | 已命名 |
| 环境光传感器 | ALS 驱动，带闪烁模式 | `als_*` 控制台字符串与 `als_flicker_*`（第 14 节） | 未命名 |
| 铰链传感器 | 铰链开合输入 | `hinge_open`、`hinge_close`（第 14 节） | 未命名 |

## 连接

| 器件 | 功能 | 依据 | 可信度 |
|---|---|---|---|
| 高通 WCN7850（固件横幅）；设备树中该家族命名为 WCN6x5x（`bt_wcn6x5x`、`qcom,kiwi`） | Wi-Fi 与蓝牙组合芯片 | 蓝牙补丁横幅 `PF=WCN7850ROM=`（第 07 节）；设备树节点 `/soc/bt_wcn6x5x` 与 `qcom,kiwi`；WLAN 标签 `WLAN.HMT`。高通 FastConnect 7800 资料（87-PW329-1 Rev. B，2023）订购型号为 WCN785x-1 与 WCN785x-5，工艺 14 nm，支持 Wi-Fi 7/6E/6、2.4/5/6 GHz、320 MHz 信道、4K QAM、MLO、蓝牙 5.4、LE Audio 与 ANT+。该资料未提及 WCN7850，也未列出主机接口。 | 已命名（固件）；该器件属于 WCN785x 系列。蓝牙 5.4 来自该资料；WCN7850 的确切版本未确认 |
| 高通 WPSS 子系统 | SoC 内的 Wi-Fi 远程处理器 | XBL 中的 `[FULL_WPSS]` 与 `[CORE_WPSS]` 节；SMP2P 设备树节点（第 07 节） | 子系统已命名；镜像不在 OTA 中 |
| NXP PTN5150 | USB Type-C 控制器（`ptn5150@1d`，在 18 个覆盖层中为 disabled） | 覆盖层（第 04 节） | 已命名 |
| Apple MFi 认证芯片（343S00176） | 机壳或手环的配件认证 | 覆盖层中的 `mfi343s00176@10`（`meta,mfi-i2c`）；`vendor.meta.hardware.mfi@1.0-service` 与 `/dev/mfi-i2c`（第 09 节） | 已命名。该芯片属于 Apple MFi 计划；芯片上的厂商字符串不在文件中 |
| STP 链路芯片（`st60a3g1`） | MCU 传输（覆盖层中的 `meta,st60-i2c`） | 覆盖层（第 04 节）；MCU 控制台中的 STP 事件（第 14 节） | 覆盖层中已命名；所示 18 个覆盖层中为 disabled |

## 存储与其他

| 器件 | 功能 | 依据 | 可信度 |
|---|---|---|---|
| 存储控制器 | 启动与数据存储 | 设备树中有 UFS PHY 时钟门控（`gcc_ufs_phy_gdsc`）与 SDHCI 主机（`sdhci@7c4000`，SELinux 标签中的 `mmc0` 路径）（第 04 节）。UEFI 镜像的启动设备字符串中列有 UFS、eMMC、NAND 与 NVMe（第 02 节） | 控制器已命名；器件型号未命名，所装的存储类型未确定 |
| 安全元件（`hal_secure_element`） | 安全元件 HAL | SELinux 域与服务标签（第 11 节） | 未命名 |
| 振动驱动 | 振动（`hal_vibrator`） | 仅有 SELinux 标签 | 未命名 |

## 证据

- `data/android/vendor_ramdisk/vendor_dtb_dump.txt`：SoC、PMIC 与传感器的兼容字符串。
- `data/android/vendor_ramdisk/modules_modinfo.tsv`：无线与传感器内核模块。
- `data/android/audio/max98388_v2.sh`：扬声器功放初始化序列，复制自 `odm/bin/`（第 12 节）。
- `data/mcu/mcu_console_strings.txt`：LCoS、触控、IMU 与 ALS 控制台字符串（第 14 节）。
- `data/dsp/dsp_symbol_table.txt`：RT700 DSP 符号（第 15 节）。
