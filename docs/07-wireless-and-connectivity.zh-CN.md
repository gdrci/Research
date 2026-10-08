# 07 - 无线与连接（Wi-Fi、蓝牙、WPSS）

[English](07-wireless-and-connectivity.md)

本节记录 OTA 中 Wi-Fi 与蓝牙协议栈的组成：运行射频的远程子系统（WPSS）、内核驱动、init 脚本与 HAL 服务、配置文件以及固件镜像。每项结论都标明为已观察（直接读取文件）、推断（文件未明说但合理的解读）或未找到。

## 摘要

- Wi-Fi 与蓝牙固件分别位于两个 FAT16 镜像中。Wi-Fi 板级数据与 WLAN 微码在 `modem.img` 的 `/image/kiwi/` 中；蓝牙补丁与 NV 文件在 `bluetooth.img` 中。
- 射频运行在名为 WPSS 的远程子系统中。XBL 配置中有它的定义，设备树中有它的 WLAN SMP2P 通道。
- 内核侧是高通的 CNSS2/ICNSS2 平台驱动，外加 `wlan.ko` 主机驱动。
- 主机协议栈通过两个 HAL 服务与芯片通信：高通 Wi-Fi HAL 与 Meta（`vendor.oculus`）Wi-Fi HAL。

- 芯片为高通 WCN7850，Wi-Fi 与蓝牙合一。蓝牙补丁的横幅中写有该型号（`PF=WCN7850ROM=`），WLAN 构建标签为 `WLAN.HMT`。已观察。

## 芯片身份：固件中为 WCN7850，设备树中为 WCN6x5x

同一颗无线芯片在两处使用了两个名称，且二者并不完全一致：

- 蓝牙补丁横幅写的是 `PF=WCN7850ROM=`（已观察，见上文第 07 节）。
- 设备树把蓝牙节点命名为 `/soc/bt_wcn6x5x`，`compatible = "qcom,kiwi"`，其供电名为 `qcom,bt-vdd-aon-supply`、`qcom,bt-vdd-dig-supply`、`qcom,bt-vdd-io-supply`、`qcom,bt-vdd-rfaOp8_supply`（转储中按此拼写，带下划线）、`qcom,bt-vdd-rfa2-supply` 与 `qcom,bt-vdd18-aon-supply`，每项均有一个 `-config` 配套项，复位线为 `qcom,bt-reset-gpio`（已观察，`data/android/vendor_ramdisk/vendor_dtb_dump.txt`）。
- WCN7850 蓝牙部分的 Linux 绑定（`qcom,wcn7850-bt`）使用另一套供电名（`vddaon`、`vdddig`、`vddrfa0p8`、`vddrfa1p2`、`vddrfa1p8`、`vddrfacmn`、`vddwlcx`、`vddwlmx`）。因此设备树沿用的是较早的 WCN6x5x 命名，并非严格对应 WCN7850 绑定。

公开佐证（来自搜索结果，未打开原文）：上游 Linux `ath12k` 驱动支持 WCN7850 的 hw2.0 固件，公开固件树中的 WLAN 构建字符串形如 `WLAN.HMT.1.1.c5-00284-QCAHMTSWPL_V1.0_V2.0_SILICONZ-3`。设备自身的标签为 `WLAN.HMT.1.1.c4-00443-…`，是同一家族字符串的较早构建。公开树中的板级数据文件为 `ath12k/WCN7850/hw2.0/board-2.bin`，与 `amss.bin`、`m3.bin` 一同出现在首次加入 WCN7850 的 linux-firmware 合并请求中，搜索结果将其定在 2023 年 12 月。引用的合并请求为 [ath10k/ath11k/ath12k 固件 2023-12-21](https://lists.infradead.org/pipermail/ath11k/2023-December/005186.html)，该页面未打开，因此此合并请求中的 WCN7850 内容未经核对。搜索结果中的 WHENCE 未列出 `hmtbtfw20.tlv`，因此蓝牙补丁文件名无法由该来源确认。设备附带的是 `bdwlan.elf`，而非 `board-2.bin`，因此设备的 WLAN 数据打包方式与上游布局不同。根据字符串推断，未对固件本身核对。

WLAN 一侧使用同一家族名称：调制解调器目录为 `kiwi`，Wi-Fi 配置目录为 `kiwi_v2`（第 07、16 节）。推断：`kiwi` 是该无线芯片家族的内部平台名，设备树即为其编写。

参考架构（背景知识，并非来自本仓库中的文件）。高通 WCN6856 概述（文档 80-WL542-10，与本芯片同一代但为不同型号）展示了该家族可能共享的结构：PMU、晶振与时钟接口、OTP、RFFE 控制信号、蓝牙子系统，以及两组 WLAN MAC/PHY。其主机接口为蓝牙 HCI 使用 UART 或 USB，WLAN 使用 PCIe，蓝牙音频使用 Slimbus、PCM 或 I2S。这与本设备所见一致：蓝牙使用 `ttyHS0` 与 `hs_uart_operation`（本节），WLAN 使用 PCIe 上的 `mhi0`（第 11 节），音频使用 Slimbus 与 SLIM-DEV1 后端（第 12 节）。WCN6856 是不同型号，因此这只是架构参考。推断，未对照 WCN7850 数据手册核对（该手册尚未阅读）。

## WPSS：Wi-Fi 远程子系统

XBL 配置（`data/strings/xbl_config.txt`）中有两个该子系统的节，`[FULL_WPSS]` 与 `[CORE_WPSS]`。两者都是 `Type = elf_split`、`ImagePath = \image\wpss`、`SubsysID = 6`，并预留内存 `ResvMemoryStart = 0x85600000`。分区标签分别为 `modem_a`（完整版）与 `core_nhlos_a`（核心版）。两者的 `ProxyGuid` 相同，均为 `1CAAECA0-978B-4472-8B36-1ACD7F06B713`，并且都设置了 `ResvMemorySize = 0x01900000`。GUID `61513695-E0C6-4F07-BF41-A51A7770640E` 属于 `[MODEM]` 节（SubsysID 4），而不属于 WPSS。已观察。节内容见 `data/xbl/wpss_config_sections.txt`。

PIL 代理列表中也有 `PIL_WPSS`。已观察。

设备树（`data/android/vendor_ramdisk/vendor_dtb_dump.txt`）定义了 WPSS 节点：

- `/soc/qcom,smp2p-wpss`，下有 `master-kernel` 与 `slave-kernel` 两个子节点，是 SMP2P 链路的内核端。
- 其下五个 WLAN 通道：`qcom,smp2p-wlan-1-in`、`-1-out`、`-2-in`、`-2-out` 与 `-3-out`。已观察。
- `/soc/wpss_etm` 的 coresight 路径，包含 funnel 与 TPDM 节点（`funnel_wpss`、`tpdm_wpss`、`tpdm_wpss1`）。已观察。跟踪路径未作进一步分析。

WPSS 固件本身（`wpss.mdt` 或 `wpss.b*`）不在 OTA 中。已检查：对每个已提取镜像搜索 `wpss`，只找到配置与表格，以及 ADSP、CDSP 段（`modem.img`）中的 QDSS 跟踪字符串。modem FAT 镜像中没有 `wpss` 文件，`vendor`、`odm`、`system_ext`、`product` 中也没有。`[FULL_WPSS]` 条目指定 `modem_a`，`[CORE_WPSS]` 条目指定 `core_nhlos_a`。`modem.img` 在 OTA 中且没有 WPSS 文件，因此该 WPSS 镜像很可能位于 OTA 未携带的分区或文件中，或以搜索未能匹配的形式存在。推断。

init 脚本在 Wi-Fi 服务启动之前写入 ICNSS 驱动（见下）。已观察：

    on early-boot
        write /sys/kernel/icnss/wlan_en_delay 1000
        write /sys/kernel/icnss/wpss_boot 1

因此内核通过一次 sysfs 写入启动 WPSS。`wlan_en_delay` 的值是拉高 WLAN 使能线之前的延迟（毫秒）。根据名称推断。

## 内核驱动

来源：`data/android/vendor_ramdisk/modules_modinfo.tsv`。已观察。

| 模块 | 说明 | 依赖 |
|---|---|---|
| `icnss2.ko` | iWCN 核心平台驱动 | `wlan_firmware_service`、`qmi_helpers`、`pdr_interface`、`rproc_qcom_common`、`qcom_ramdump` |
| `cnss2.ko` | CNSS2 平台驱动 | `pci-msm-drv`、`qmi_helpers`、`wlan_firmware_service`、`mhi`、`cmd-db`、`cnss_plat_ipc_qmi_svc` |
| `wlan.ko` | WLAN 主机设备驱动（Qualcomm Atheros） | `cnss2`、`cnss_prealloc`、`cnss_nl`、`cnss_utils` |
| `wlan_firmware_service.ko` | WLAN 固件 QMI 服务 | `qmi_helpers` |
| `bt_fm_slim.ko` | BTFM Slimbus 从设备驱动 | `slimbus`、`btpower` |

调用链是 `wlan.ko` 位于 `cnss2` 之上，`cnss2` 通过 QMI 与固件通信。`icnss2` 是 ICNSS 路径，即较早的平台驱动。模块名为已观察。WPSS 启动使用两者中的哪一个，是根据 init 脚本写入 `/sys/kernel/icnss` 推断的。

厂商固件目录中有 `wlan` 子目录（`fs/vendor/firmware/wlan/qca_cld`），其中包含三个符号链接。其中两个在 OTA 中失效，因为它们的目标位于 `/mnt/vendor/persist`；第三个在镜像内可以解析：

- `WCNSS_qcom_cfg.ini` 指向 `/vendor/etc/wifi/kiwi_v2/WCNSS_qcom_cfg.ini`（该目标存在于镜像中）。
- `wlan.cfg` 指向 `/mnt/vendor/persist/wlan.cfg`。
- `wlan_mac.bin` 指向 `/mnt/vendor/persist/wlan_mac.bin`。

两个 `/mnt/vendor/persist` 目标在设备运行时写入（MAC 地址与每台设备的配置），不在 OTA 中。已观察。`qca_cld` 这一名称对应 Qualcomm Atheros cfg80211 驱动系列。

## init 脚本与 HAL 服务

来源：`fs/vendor/etc/init/`（`data/userspace/wifi_bt_init_and_modules.txt`）。已观察。

- `init.vendor.wlan.rc`：上述早期启动写入，以及 `wifi_qos_daemon`（类 `late_start`，用户 `wifi`，组 `net_admin`）。
- `vendor/etc/init/vendor.wlan.lowirpcd.rc` 存在于 init 文件列表中（`data/userspace/init_rc_files.txt`），因此预期存在 `lowirpcd` 服务。其服务正文不在已提取的列表中。根据文件名推断。
- `vendor.wifi_hal_legacy` 运行 `/vendor/bin/hw/android.hardware.wifi@1.0-service-lazy`，即高通 Wi-Fi HAL。
- `vendor.oculus.wifi-hal-1-0` 运行 `/vendor/bin/hw/vendor.oculus.hardware.wifi@1.0-service`。名称 `vendor.oculus.hardware.wifi` 出现在 `data/userspace/meta_hal_names.txt` 中，SELinux hwservice 上下文为其列出了 `IWifi`（`data/android/selinux/vendor_hwservice_contexts`）。本次未检查该二进制的导出符号。这是 Meta 一侧的 Wi-Fi 接口名称。
- `android.hardware.bluetooth@1.0-service-qti` 以 `vendor.bluetooth-1-0-qti` 的名义运行，类别为 `hal`，具有 `BLOCK_SUSPEND` 与 `NET_ADMIN` 能力。在 `boot` 阶段，其 UART 控制节点 `/sys/class/tty/ttyHS0/device/hs_uart_operation` 被设为模式 0660、属主 `bluetooth`。已观察。该节点位于 `ttyHS0`，这是蓝牙驱动使用的高速 UART。根据节点名推断。

`vendor.img` 的字符串中列有标准的 `android.hardware.wifi.supplicant@1.0` 至 `@1.5` 以及 `android.hardware.wifi.hostapd@1.0` 至 `@1.3` 接口（由 `vendor.img` 的字符串观察得出）。库文件本身不在仓库列表中。

## Wi-Fi 配置

`vendor/etc/wifi/` 下的文件（`data/userspace/wifi_config_and_symlinks.txt`）。已观察。

- `kiwi_v2/WCNSS_qcom_cfg.ini`：驱动的出厂默认覆盖项。示例：`gDot11Mode=0`、`gEnableDFSMasterCap=1`、`FastRoamEnabled=1`、`gEnableTXSTBC=1`、`gEnableTxSUBeamformer=1`、`gVhtMpduLen=2`。`kiwi_v2` 这一名称与调制解调器镜像中的 `kiwi` 目录相同；两者是否相关属于推断。
- `wpa_supplicant.conf`、`wpa_supplicant_overlay.conf`、`p2p_supplicant_overlay.conf`：supplicant 配置。
- `icm.conf`：配置文件，含 `num_devices=1`、`num_radios=1` 以及一个通信接口选项（`ioctl` 或 `cfg`），由 `vendor.img` 的字符串读取。其中没有许可证年份。
- `vendor_cmd.xml`：HAL 的厂商命令表。

## 固件

### Wi-Fi：位于 `modem.img` 中

`modem.img` 是一个 36.5 MB 的 FAT16 镜像，含 165 个文件（`data/remote/modem_listing.txt`）。其 Wi-Fi 内容位于 `/image/kiwi/`（第 05 节有描述）：

- `amss.bin`、`amss20.bin`：调制解调器固件镜像。
- `bdwlan.elf`、`bdwlan.elf.xz`：Wi-Fi 板级数据。
- `regdb.bin`：无线监管数据库。
- `phy_ucode.elf`、`phy_ucode20.elf`：PHY 微码。

WLAN 侧的构建 ID 为 `WLAN.HMT.1.1.c4-00443-QCAHMTSWPL_V1.0_V2.0_SILICONZ-1`（`data/remote/modem_verinfo.txt`）。已观察。`HMT` 标签与下述蓝牙使用的 Hamilton 芯片名一致。WLAN 固件运行在 WPSS 上是根据 WPSS 配置与 `kiwi` 路径推断的；两者在文件层面的关联尚未确认。

### 蓝牙：`bluetooth.img`

`bluetooth.img` 是一个 0.78 MB 的 FAT16 镜像，含 51 个文件（`data/remote/bluetooth_listing.txt`）。已观察。

- `hmtbtfw10.tlv`（91,308 字节），版本文件 `hmtbtfw10.ver` 为 `BTFW.HAMILTON.1.0.0-00214-PATCH-1`。
- `hmtbtfw20.tlv`（253,484 字节），版本文件 `hmtbtfw20.ver` 为 `BTFW.HAMILTON.2.0.0-00797-PATCHZ-1.105163.2.109423.3`。
- `hmtnv10.*` 与 `hmtnv20.*`：NV 配置文件，约 30 个变体（`.bin`、`.b0c`、`.b0202` 至 `.b1e` 等）。后缀看起来像按变体划分的配置。未验证。

蓝牙功能与主机接口（`bluetooth.img`，FAT 镜像；仅依据字符串）。镜像包含面向连接的等时流代码（`CIS-TX`、`CIS-RX`、`CIS-M`、`LE_ISO_prepareSduBufQ`、`SetupISODatapath`），即单播 LE Audio 传输。镜像中没有广播等时字符串（`BIG`、`BIS`），也没有周期性广告或 PAST 字符串，以及信道探测或到达角字符串。因此该镜像支持单播 LE Audio，字符串中也看不到蓝牙 5.4 或 6.0 的功能。蓝牙版本因此只能界定为单播 LE Audio 协议栈，不能确认为某个具体发布版本。主机传输为 UART（`ttyHS0`，见上文第 07 节）。依据字符串观察得出；未与蓝牙规范或数据手册核对。

两个 TLV 文件都以字节 `0x01` 开头，即 HCI 命令包指示符。其后是厂商补丁段。具体段格式为推断，未完整解码。原始头部见 `data/remote/bluetooth_version_files.txt`。

`modem.img/verinfo/ver_info.txt` 中的构建清单将 `btfm` 列为 `BTFW.HAMILTON.2.0.0-00819-PATCHZ-1`，而蓝牙镜像自身的版本文件写的是 `00797`。两者不同。已观察。清单是构建级别的记录，`.ver` 文件是镜像实际携带的内容；造成差异的原因尚未确定。已部分解决：补丁自身的文本（位于 `hmtbtfw20.tlv` 中）为 `Patch Release PF=WCN7850ROM= 0200 BUILD=BTFW.HAMILTON.2.0.0-00797-PATCHZ-1.105163.2.109423.3`，因此镜像是 00797 版本。清单中的 `00819` 是该镜像不包含的另一个构建。已从 TLV 字符串观察得出。

## 未找到的内容

- WPSS 固件镜像（`wpss.mdt` 或 `wpss.b*`）。已在所有已提取镜像中搜索，不在 OTA 中。
- 读取 `/sys/kernel/icnss` 节点的代码，以及 ICNSS 到 WPSS 的启动流程。在所检视的镜像中未找到。
- `/mnt/vendor/persist` 的内容（`wlan.cfg`、`wlan_mac.bin`）。运行时写入。
- 蓝牙 TLV 段格式（首字节之后的部分）。

## 证据

- `data/xbl/wpss_config_sections.txt`
- `data/android/vendor_ramdisk/wpss_dt_nodes.txt`
- `data/android/vendor_ramdisk/modules_modinfo.tsv`
- `data/userspace/wifi_bt_init_and_modules.txt`
- `data/userspace/wifi_config_and_symlinks.txt`
- `data/remote/modem_listing.txt`、`data/remote/modem_verinfo.txt`
- `data/remote/bluetooth_listing.txt`、`data/remote/bluetooth_version_files.txt`
