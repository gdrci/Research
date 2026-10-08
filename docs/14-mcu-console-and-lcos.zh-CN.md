# 14 - MCU 控制台、LCoS 显示控制器与传感器驱动

[English](14-mcu-console-and-lcos.md)

本节记录 `vendor/firmware/mcu.default.rt700.tub` 中 MCU 固件通过命令控制台暴露的功能：LCoS（硅基液晶）显示控制器、为其点亮的 LED 驱动、触控控制器、惯性与环境光传感器、铰链，以及 STP 传输。本节更正第 09 节的两处说法，并关闭第 13 节中"未找到 LCoS HAL 二进制"的未决项。

状态标注：已观察表示直接从文件读取；推断表示文件未明说但合理的解读；未找到表示该内容不在 OTA 中。控制台字符串及其文件偏移见 `data/mcu/mcu_console_strings.txt`。

## MCU 是什么

- MCU 固件源码路径中命名了平台 `rt700`（`arvr/firmware/projects/smartglasses/platforms/greatwhite/rt700/`）。该容器未标明 NXP；NXP 的身份属于外部知识，文件中并未显示。其外设驱动位于 `arvr/firmware/lib/uhal/peripherals/rt700/`（`rt700_clock.c`、`rt700_gpio.c`、`rt700_edma.c`、`rt700_spi_peripheral.c`、`rt700_power_domain.c`、`rt700_wdt.c`）。已观察。
- RTOS 为 FreeRTOS v10.4.6，使用移植层 `GCC/ARM_CM33_NTZ/non_secure/port.c`，因此内核为非安全模式的 Arm Cortex-M33（该核心身份由移植层路径推断得出）。已观察。
- 固件源码树名为 `arvr/firmware/projects/smartglasses/platforms/greatwhite/rt700/`。DSP 镜像中也有同样的路径（第 15 节）。因此文件名中的 `rt700` 指的是处理器平台，而不只是音频编解码器。这更正了第 09 节早期草稿把它称为音频编解码器变体的说法。
- 控制台是一组带帮助文本的命名命令。固件中含有帮助文本 `xra: See https://fburl.com/wiki/xra_mcu_commands for usage`（TUB 0x15BF15），按头部偏移位于 `case.bin` 载荷内；与控制台命令表的联系未显示。已观察。该 wiki 不在 OTA 中。

## LCoS 控制台

LCoS 是微显示引擎。控制台中有一组 `lcos` 命令（已观察，见 `data/mcu/mcu_console_strings.txt`，文件偏移 `0x13E000` 至 `0x142000`）：

电源与模式
- `lcos poweron`：执行 GPIO 与 I2C 上电时序，但不发送初始化序列。
- `lcos send-init-sequence`：发送将 LCoS 置入 PGEN 模式的 I2C 序列，假定已上电。
- `lcos init`：以 MIPI 模式初始化 LCoS。
- `lcos set-already-initialized`：在显示已开启时设置配置。
- `lcos poweroff`，`lcos toggle <间隔秒数> <切换次数>`（默认间隔 5 秒；命令输出 `Test complete.`，此联系根据相邻字符串 `toggle` 与 `Test complete.` 推断，数据中没有调用点）。
- `lcos mipi_rx <1/0>`：启动或停止 MIPI 接收管线。
- `lcos clearscreen`、`lcos clearbus`（通过切换时钟通道清除显示 I2C 总线）。

测试图案
- `lcos pgen <图案名> <r> <g> <b>`。图案名为 `disabled`、`checkerboard`、`hcolorbar`、`vcolorbar`、`hramp`、`vramp` 与 `solid`。RGB 仅对 `solid` 有效。未知名称回退为 `checkerboard`。已观察。

电压（名称已观察；物理作用根据名称推断）
- `lcos set-pixel-voltage <pixel_voltage_mV`（按二进制中的原样打印）与 `lcos get-pixel-voltage`（输出 `Pixel Voltage: %u mV`）。
- `lcos set-ito-voltages <正红> <正绿> <正蓝> <负红> <负绿> <负蓝>`（单位 mV）与 `get-ito-voltages`。ITO 为氧化铟锡电极层，根据缩写推断。
- `lcos get-led-voltages`（输出 `RED:%d GREEN:%d BLUE:%d BLANK:%d`）。

LED 驱动
- `lcos setledgains <r> <g> <b>`（最大 1023）与 `getledgains`。
- `lcos setledcurrents <r> <g> <b>`，单位微安（整数），以及 `getledcurrents`。
- `lcos getledbitres` 输出 LED 位分辨率与 rsense GPIO 的值。
- `lcos set-led-bitres-setting <auto|low|high>`、`get-led-bitres-setting` 与 `get-led-bitres-threshold`。阈值按颜色以微安输出（`r:%u, g:%u, b:%u microAmps`），决定驱动在高低分辨率之间切换的点。
- `lcos set-led-mode <pfm|pwm>` 与 `get-led-mode`。PFM 与 PWM 是模式名称（帮助文本位于 0x13EDAA 与 0x13F8FD）。展开含义（脉冲频率调制与脉冲宽度调制）为推断。
- `lcos set-interp-coeffs <r/g/b> <低斜率> <低偏移> <高斜率> <高偏移>` 与 `get-interp-coeffs`。系数以微安为单位，分低、高两档分辨率。已观察。

温度与健康
- `lcos readtemp <rb/g/lcos/schedule>`：从红蓝 LED（`rb`）、绿色 LED（`g`）或 LCoS 本身读取显示芯片温度；也接受 `schedule`。已观察。
- `lcos get-error-counts`：输出 `SOT_ERROR_FLAG_COUNT`、`CRC_ERROR_FLAG_COUNT`、`ECC_SINGLE_ERR_FLAG_COUNT`、`ECC_FATAL_ERR_FLAG_COUNT`、`SOT0_ERROR_COUNT` 与 `CRC_FAILURE_COUNT`。SOT 指 MIPI 的传输起始错误。根据名称推断。
- `lcos dump-de-otp`：转储系统级 DE OTP 回读值。DE OTP 是显示驱动中的一次性可编程区域。根据名称推断。
- `lcos get-pmic-rev`：读取 PMIC 芯片 ID（`PMIC chip ID: %d`）。显示 PMIC 即第 04 节所列的 `pmicOP03010`、`pmicOP02220`。

总线访问
- `lcos init-i2c`、`lcos deinit-i2c`，以及原始寄存器访问 `lcos i2c r <设备地址> <寄存器> <字节数>` 与 `lcos i2c w <设备地址> <寄存器> <数据(x,y,z,...)>`。所有数值均为十六进制。已观察。

校准与标识
- LCoS 设置输出为 `LCOS settings: is_pwm = %d, r = %d, g = %d, b = %d`。
- 固件中有工厂校准字段名：`VF_1MA_R/G/B` 与 `VF_140MA_R/G/B`（1 mA 与 140 mA 时的 LED 正向电压），以及按颜色的 `OFFSET_LOW_RES_*`、`SLOPE_LOW_RES_*`、`OFFSET_HIGH_RES_*`、`SLOPE_HIGH_RES_*`。字段名已观察；其含义（1 mA 与 140 mA 时的正向电压）与作为每台设备插值输入的作用为推断。
- 序列号字段为 `Display SN`、`LCOS SN`、`LED SN` 与 `DDB SN`。已观察。其值在设备上，不在 OTA 中。

## 为什么 Android 分区中没有 LCoS HAL

Android 端有 LCoS HAL 的 SELinux 标签（`hal_oculus_lcos` 与 `vendor.oculus.hardware.lcos::ILcos`，第 11 节），`ueventd.rc` 将 `/dev/lcos-i2c-OP03010` 与 `/dev/lcos-i2c-OP02220` 设为模式 0660、属主与属组 `system`，并有 sysfs 节点 `offload_enabled`（`ueventd.rc` 第 368 行；`vendor_file_contexts` 第 713 行有标签）。第 13 节未涵盖该节点。`lcos_init` 与 `lcos_uio` 标签也存在。但上述显示控制命令位于 MCU 固件中，而 Android 分区中没有运行这些命令的二进制。对 `vendor`、`odm`、`system_ext` 与 `product` 的 `debugfs` 目录遍历没有找到 LCoS 二进制。`system.img` 未用于此项检查，因此不能排除。推断：OTA 中的 LCoS 控制路径是 MCU 运行控制器及其控制台，而 Android 端只有设备节点与标签，用于一个 I2C 桥。这是根据控制台位置与设备节点名称推断的；文件中未显示节点与 MCU 之间的连接。

## 触控控制器（PSoC）

控制台打印 `psoc in %s mode`。Cypress/Infineon 的归属属于外部知识；第 09 节已说明，文件中并未命名该厂商。MCU 运行触控驱动。控制台包括：

- `touch probe`、`touch mode [tuner]`、`touch r <寄存器地址> <数量>`、`touch w <寄存器地址> <值...>`、`touch g <设备地址> <数量>`、`touch t <设备地址> <值...>`（原始寄存器与设备访问）。
- `touch reboot-dfu`、`touch dfu`（`touch.default.tub` 中 `touch-app-b0.cyacd2` 镜像的引导程序途径，第 09 节）。
- `touch read-touch-points`、`touch get[-presense|-dondoff]-ppc [<slot_id>]` 与 `touch set[-presense|-dondoff]-ppc [<slot_id>] <n_sub> <decn> <cdac_comp>`（按槽位的电容设置）。
- `touch set-use-case <cpu_freq_mhz> <refresh_rate_hz> <wake_on_touch> <deep_sleep> <sleep_in_active> <centroid_mode>`、`touch set-configuration` 与 `set-lp-configuration`（包含 `cdac`、`row_cdac`、`n_sub`、`sns_clk`、`cicrate` 等字段）。
- `touch self-test`、`touch read-palm-gesture`、`touch update-gesture-config`、`touch raw-data`、`touch get-fw-version`、`touch stats`、`touch touchpad-capacitance [slot]`。
- 复位：`touch hard-reset`、`soft-reset`、`watchdog-reset`、`hardfault-reset`、`reset-reason`（输出原因、堆栈，以及 CC 与 EC 字）。

已观察。`touch read-palm-gesture` 表明触控面板还会报告手掌手势。手掌手势与第 16 节中掌纹认证 TA 属于同一类输入。推断。

## IMU 与工厂校准

- `start`、`set-odr <数据速率-us> <批处理延迟-us>`、`chip-id`（输出 `Chip ID: 0x%X`），以及 `factory-cal`（输出校正矩阵与 `x`、`y`、`z` 偏移）。已观察。
- 第 09 节中的 IMU HAL 为 `vendor.meta.hardware.sensor.imu.IImu`。控制台未命名它；该联系为推断。控制台命令表未命名 IMU 芯片；MCU 固件在别处命名了 IMU 芯片（`LSM6DSV32X`、`lsm6dsr`、`icm45688`、`lsm6dsv`）。

## ALS、铰链与事件

- ALS 字符串：`als_sampling`、`als_stopped`、`als_data`、`als_read_failed`、`als_flicker_sampling`、`als_flicker_stopped`。这六个名称是日志、Zephyr 与遥测 JSON 字典中的条目，而非控制台命令。名称暗示与 `camflicker` 二进制（第 13 节）有联系；该联系为推断。
- 铰链：`system input hinge_open` 与 `hinge_close` 位于 `boot_data.bin` 段（0x15076C–0x15118C），不在控制台表中；`hinge_status` 在日志字典中。已观察。第 09 节中的 IHinge HAL 为可能的使用者；该联系为推断。
- 事件：`stp_channel_available_change`、`stp_read_header`、`stp_read_payload`、`stp_header_ready`、`stp_data_available`、`stp_read_failed`，以及 `unknown audio stp channel: %u`。这些是 STP 通道事件的字典条目（第 09 节涵盖 STP 传输）。日志中点名了音频 STP 通道。

## 其他控制台分组

控制台有电池热图命令（`Dump battery heatmap`、`Save battery heatmap`）；载荷 `batt.bin`、`battery_heatmap.bin` 与 `battery_heatmap2.bin` 仅按名称与之关联（推断），`hot_car_notif.bin`（热车通知，根据名称推断）、`factory_reset_telemetry.bin`，以及遥测字典（`logger_dict_generated.json`、`zephyr_log_dict_generated.json`、`tel_dict_generated.json`）。已按子镜像名称观察。

## MCU tub 的子镜像布局

`mcu.default.rt700.tub`（8,483,328 字节）包含 39 个命名子镜像（已观察，偏移见 `data/mcu/mcu_console_strings.txt`）。第一个是偏移 0 处的 `app.bin`，延伸至约 `0x1435E8`（1,324,520 字节）。其后依次为：显示校准（`display_wpc_coeff.bin`、`display_calibration.bin`）、触控固件（`touch-app-b0.cyacd2`）、开关机记录（`boot_data.bin`、`pmic_reset_info.bin`、`shutdown_state.bin`、`boot_shutdown_history.bin`）、`cf_*` 系数集（`cf_fixed_bf_weights_*`，名称表明是波束成形权重）、机壳固件（`case.bin`，因 `cocos`、`lynx`、`cabo` 三种机壳变体而嵌入三次）、`dumptruck.bin`、`offload_assets_ro.bin`、`romfs.bin`、`debug_frame.bin`，以及 JSON 字典与清单（`configs.json`、`metadata.json`）。已观察。

这说明 `.tub` 容器是一连串命名载荷，每个载荷开头有一个 ASCII 名称，清单位于尾部。载荷混合：代码与二进制表（`app.bin`、`dumptruck.bin`、`debug_frame.bin`）的熵约为每字节 5 至 7.3 位；`offload_assets_ro.bin` 大多为零字节；JSON 字典为明文。文件未显示任何载荷是否加密，`app.bin` 的熵（每字节 7.27 位）既符合编译代码，也符合加密数据。第 09 节称清单 md5（`8589b5e414f8352e39106fc3796ad050`）与任何已测试范围都不匹配，且被哈希的字节"不以原样存在于文件中，或经过压缩或加密。未验证。"对子镜像边界与清单偏移的测试（1,927 对起止点）也未匹配。未解决。

## 未找到的内容

- Android 中的 LCoS HAL 服务二进制。在已检视的 OTA 分区中未找到。
- `xra` 命令背后的 wiki。不在 OTA 中；仅存在 URL 字符串。
- ALS 的传感器芯片型号。未找到 ALS 芯片名。IMU 芯片在 MCU 固件的别处有命名（`LSM6DSV32X`、`lsm6dsr`、`icm45688`、`lsm6dsv`）。
- 面板专用的 LCoS 表格数值。这些是每台设备的数据，校准数据不在 OTA 中。

## 证据

- `data/mcu/mcu_console_strings.txt`：控制台字符串及偏移，以及子镜像名称头。
- `data/android/vendor_ramdisk/vendor_dtb_dump.txt`：显示节点（`glinkpkt-disp-bus`、`disp0-gdsc`、`disp1-gdsc`、`display-fps`）与摄像头 pinctrl 节点。其中没有 IMU、ALS 或铰链节点。
- LCoS 字符串的 `debugfs` 路径映射（`icheck` 与 `ncheck`）：这些字符串位于 `vendor.img` 中 inode 657 对应的 `/firmware/mcu.default.rt700.tub`。
