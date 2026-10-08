# 09 - 眼镜端软件、MCU 与腕带

[English](09-glasses-software-and-mcu.md)

本文介绍启动链之上、应用处理器旁边的那部分系统：一个二级微控制器（MCU）、它与 Android 之间的传输、基于它的传感器和输入 HAL、肌电（EMG）输入通路，以及应用层。文中的文件计数来自 `data/userspace/`。

## MCU

眼镜上有一个与 SoC 分开的微控制器。好几个 HAL 和内核接口只为与它通信而存在。证据如下：

- `lpi_mcu_service` 服务（`odm/etc/init/vendor.meta.hardware.lpi_mcu-service.greatwhite.rc`，可执行文件 `odm/bin/hw/vendor.meta.hardware.lpi_mcu-service.greatwhite`）链接了 20 个 AIDL 接口库，列于下文。其 init 文件与 VINTF 清单声明了其中 17 个（`actionbutton`、`powerbutton` 与 `battery_provisioning` 已链接但未声明）。
- `vendor/bin` 中的 `mcu-properties.sh` 读取 `/sys/devices/platform/soc/soc:meta,rt600_ctrl/is_rt600`。`meta,rt600_ctrl` 是 `dtbo.img` 中的设备树覆盖节点（fragment@15）；内核驱动不在仓库中。它的确切作用是根据名称以及 init 文件写入它的触发器推断的。
- `vendor/firmware` 中有 `mcu.default.rt700.tub` 和 `mcu.core1.default.rt700.tub`。`.tub` 文件是 MCU 自己的固件。MCU 固件面向 RT700 平台构建：其源码包括 `arvr/firmware/lib/uhal/peripherals/rt700/*.c` 与 `platforms/greatwhite/rt700/mcu/bsp`，并使用 ARM_CM33_NTZ 移植的 FreeRTOS v10.4.6，该信息见于 `.tub` 文件（不在 `mcu_console_strings.txt` 中）。该容器未标明 NXP 或 MIMX 型号，因此 RT700 的身份是从源码路径推断的。文件名中的 `rt700` 指处理器平台，而不只是音频编解码器。这更正了早期草稿中把它称为音频编解码器变体的说法。原句变体相符。这两点都是推断。
- `odm/lib64/libmcu-vendor.so` 是厂商侧的 MCU 库，位于 ODM 分区中。

已从文件中验证的内容：名称、路径、init 与属性的逻辑，以及 MCU 处理器（Cortex-M33，依据 FreeRTOS 移植路径）。`.tub` 载荷包含明文字符串与代码；`mcu.core1.default.rt700.tub` 前 0xC000 字节的熵很高（每字节 6.6–7.1 位）。

### 它的 AIDL 接口

| 接口 | 作用（根据名称） |
|---|---|
| `vendor.meta.hardware.button.actionbutton.IActionButton` | 动作按钮 |
| `vendor.meta.hardware.button.capturebutton.ICaptureButton` | 拍摄按钮 |
| `vendor.meta.hardware.button.powerbutton.IPowerButton` | 电源按钮 |
| `vendor.meta.hardware.button.powerslider.IPowerSlider` | 镜框上的电源滑块 |
| `vendor.meta.hardware.captouch.ICaptouch` | 电容式触摸 |
| `vendor.meta.hardware.casestate.ICaseState` | 充电盒的状态 |
| `vendor.meta.hardware.companionstate.ICompanionState` | 配套设备（手机或腕带）的状态 |
| `vendor.meta.hardware.diagnostics.mcu.IMcuConnection` | 与 MCU 的诊断连接 |
| `vendor.meta.hardware.earcon.IEarcon` | 提示音 |
| `vendor.meta.hardware.factoryreset.mcu.IFactoryReset` | 恢复出厂设置 |
| `vendor.meta.hardware.health.mcu.IHealth` | MCU 一侧的电池与健康信息 |
| `vendor.meta.hardware.hinge.IHinge` | 铰链状态（可折叠镜框） |
| `vendor.meta.hardware.light.notification.INotificationLight` | 通知灯 |
| `vendor.meta.hardware.mount.IMount` | 佩戴检测 |
| `vendor.meta.hardware.power.mcu.IPower` | 电源控制 |
| `vendor.meta.hardware.sensor.als.IAls` | 环境光传感器 |
| `vendor.meta.hardware.sensor.imu.IImu` | 惯性传感器（加速度计和陀螺仪） |
| `vendor.meta.hardware.wakeword.IWakeword` | 唤醒词 |
| `vendor.meta.hardware.audionotification.IAudioNotification` | 音频通知 |
| `vendor.meta.hardware.battery_provisioning.IBatteryProvisioning` | 电池供电配置 |

名称描述的是接口控制的内容。它们运行在哪里，由承载它们的服务决定：服务二进制链接了全部 20 个接口库，但其 init 文件与 VINTF 清单只声明了 17 个（不包括 `actionbutton`、`powerbutton` 与 `battery_provisioning`），因此只有这 17 个作为服务实例注册。它们都面向 MCU。

### 传输：STP

`system_ext/bin/stpService`（由 `system_ext/etc/init/stpService.rc` 启动，类别 `main`，用户 `system`）通过 `/dev/stp%d` 设备节点与 MCU 通信（`palmvisionservice` 的 init 注释中提到 `/dev/stp25` 与 `/dev/stp27`）。`palmvisionservice` 的 init 文件也提到了 STP 服务。hyperoff 功能使用它：

- 在 RT700 配置下，`mcu-properties.sh` 会设置 `persist.vendor.meta.hyperoff.use_stp=true`。
- `vendor.meta.stp_service.boot` 与 `vendor.meta.mcu_hal.stp_need_recovery` 分别是 STP 服务的启动标志和恢复标志。

恢复路径值得注意。当 `vendor.meta.mcu_hal.stp_need_recovery` 被设为 1 时，init 脚本等待五秒（用于收集日志），然后向 `/sys/devices/platform/soc/soc:meta,rt600_ctrl/trigger_assert` 写入 `1`，使 MCU 断言；随后清除该标志。该文件将重启行保持注释状态（“暂时”），并附有待复查的 TODO。已从 init 文件验证。文件中还写明 "only effective on greatwhite"（仅在 greatwhite 上有效）。

### 两种硬件配置：RT600 与 RT700

`mcu-properties.sh` 检查 `is_rt600`：

- 值为 `0` 时，设备为 RT700 配置，设置 `persist.vendor.meta.enable_hyperoff=true` 与 `persist.vendor.meta.hyperoff.use_stp=true`。
- 否则为 RT600 配置，不设置任何属性。

因此眼镜有两种 NXP RT600 与 RT700 系列的变体（DSP 构建中包含 `nxp_rt600` 工具路径与 `MIMXRT798S`，即 RT700 型号；已观察），软件在启动时选择对应的行为。`dtbo.img` 中的覆盖层也按组件有所不同（第 04 节）。覆盖层中包含 `gpio_rt685_detect` 与 `rt700_bkup_disp_ctrl_high/low` 节点。`dtbo.img` 中未出现固件文件名。已观察；我尚未阅读编解码器驱动。

## EMG 输入（腕带）

腕带是一个肌电（EMG）输入设备。文件中的证据如下：

- `system_ext/etc/vintf/manifest/emg2_manifest.xml` 声明了 AIDL HAL `com.meta.wearable.emg`，接口为 `IEmgService`，实例为 `default` 和 `fmq`（快速消息队列）。
- `system_ext/lib64` 中有 `libemginput.so`、`libemg_quaternion_consumer.so`（来自腕带的姿态/四元数）、`libemg_device_status_consumer.so`、`libemg_state_sync_consumer.so`、`libemgcache.so`、`libemg_equeue.so`、`libemgserviceutils2.so` 和 `emgsdk-proto-cc.so`。
- MCU 固件 `mcu.default.rt700.tub` 中有 `/dev/Band`、`/dev/BandOff` 和 `/dev/PhoneDisconnected`，但它们不是设备节点，而是 MCU 界面资源中的图标路径：`./Resources/system/images/ic/432/sm/fl/dev/Band.png`、`BandOff.png` 和 `PhoneDisconnected.png`。因此它们表示状态图标（腕带已连接、腕带关闭、手机断开）。已观察。此前把它们当作设备的理解是错误的。
- 确切字符串 `/dev/PhoneDisconnected` 只出现在 MCU 固件中。手机一侧含有 `PhoneDisconnected` 的标识符：`system_ext/bin/navigationservice` 中的 `onPhoneDisconnected`，以及 OOBE 与 SystemUI 包中的 `renderPhoneDisconnectedIcon`。没有共享的设备节点字符串支持配套状态的解读，因此此处不作该解读。
- init 脚本 `init.emgrelay_receiver.rc` 与 `init.emgrelaydatax.rc` 启动 `emgrelay_receiver` 和 `emgrelaydatax`，其开关由 `system_ext.meta.mobileconfig.service.emgrelay.receiver.enable` 属性以及截屏管理器属性控制。

EMG 数据路径分为三部分，依据二进制文件的字符串得出：

- `system_ext/bin/emgrelay_receiver` 接收 protobuf 格式的 `EmgInferenceEvent` 消息，并把它们注入虚拟 EMG 服务（`com.meta.wearable.emg.sim.IVirtualEmgService`，带有 `IVirtualEmgStreamControlCallback`）。它的日志 `Failed to open channel to phone's EmgRelayReceiver service` 表明它会打开一个通往手机端的通道。其注册消息为 `Companion scope available [uuid=...], registering DataX service`。
- `system_ext/bin/emgrelaydatax` 序列化 `EMGGestureEvent` 消息（`EmgEventClient::onGestureDetected`），并把它们发送给 EMG 服务。其日志 `Failed to connect EmgEventClient to EMG service` 表明它连接的是 EMG 服务。
- `emg2` 实现 `IEmgService`，并通过 `fmq` 实例接收设备数据。

因此，腕带信号通过 `fmq` 队列进入 `emg2`（真实设备数据），以及通过虚拟服务进入（注入的推理事件）。从 MCU 到腕带数据源的环节尚未在代码中找到。依据字符串观察得出。相关二进制：`system_ext/bin/emgrelay_receiver`、`system_ext/bin/emgrelaydatax`。

EMG 服务路径（在提取的文件树中观察到）：

- `system_ext/bin/emg2` 是 EMG 服务，由 `persist.vendor.meta.enable_emg=1` 启动（`emg2.rc`）。它实现 `com.meta.wearable.emg.IEmgService`（清单 `emg2_manifest.xml`），有 `default` 和 `fmq` 两个实例。
- `fmq` 实例通过 AIDL 消息队列传输数据。`libemgfmq_helper.so` 通过 `android.hardware.common.fmq` 读写 `emg_fmq_packet_t` 数据包（`SynchronizedReadWriteEEEE`、`EventFlag`）。其消息涵盖队列长度，以及读写指针损坏。
- `libemginput.so` 通过格式化名称打开设备节点（`/dev/%s`），另有 `/dev/gpiochip%u` 和 `/dev/joycon0`。格式化名称的来源尚未确定。
- `emg2` 中的事件名：`emg_raw_gesture_event`、`input_emg_raw_gesture_event`、`wearables_band_tightness_detector_events`。

腕带在代码中名为 **Uniband**（移动配置名称中的 `enable_uniband_partial_gestures`、`wearables_uniband_allowlist`；`libemginput.so` 中的 `Uniband Enable`、`Uniband Capabilities Query`）。从腕带到 `emg2` 的数据路径如下：

- `system_ext/lib64/libatc_service.so` 是传输控制器。其字符串涵盖 BLE 链路、L2CAP 监听与安全 PSM、对端 ID、伴随 BLE RSSI 和传输会话。Uniband 链路很可能由这里处理。这是根据命名和传输字符串推断的，代码中并未直接显示。
- `system_ext/lib64/libemginput.so` 包含 `WirelessInputDevice` 和 `WirelessInputDeviceControl`。它们打开通往无线输入服务的通道，发送能力与设备信息请求，配置连接类型（`DIRECT_CONNECTION` 或 `Companion`），并排队 `UnibandEvent` 消息（`queueUnibandEvent`）。RPC 消息位于 `com.oculus.wearableinputservice` protobuf 包中。
- `emg2` 及其消费者库（`libemg_device_status_consumer.so`、`libemg_gesture_consumer.so`、`libemg_quaternion_consumer.so`）接收解码后的设备状态、电量、检测器与腕带贴合度事件。

代码中未显示：承载腕带与 `libatc_service` 之间字节的无线电层传输。链路的其余部分为已观察。

`libmarvin-emg.meta.so` 与 `libemg_marvin-client.meta.so` 中使用了 "Marvin" 这个名字。它很可能是型号或客户端的内部代号。未验证。

## 厂商分区中的固件容器

`vendor/firmware` 中的文件是容器，每个容器都包含带名称的子镜像。下表列出主要子镜像名称；完整列表见 `data/userspace/tub_contents.txt`：

结构，依据 `case.default.cabo.tub` 与 `mcu.core1.default.rt700.tub`（已观察）：

- 文件开头是子镜像名称，以 NUL 填充（如 `case.bin`、`core1.bin`）。
- 载荷在前，文件末尾跟着 JSON 清单，`mcu.default` 在其清单之前含有许多内嵌 JSON 对象（日志与遥测字典，自 0x715606 起）；`mcu.core1` 只有一个清单。
- 清单包含 `deployment_methods`（`case.default.tub` 为 `["RPC"]`，MCU、DSP 和 core1 文件为 `["TBSP"]`，`spl2` 为 `["ISP"]`；完整表格见 `data/userspace/tub_md5_tests.txt`）、`md5`、`platform`（core1 文件中为 `greatwhite-rt700`）、`target_assets`（每项含 `name`、`type`、`layout.offset`，core1 文件中还有 `signature`；`layout.load_addr` 见于 `app.bin`、`dumptruck.bin` 与 `core1.bin`，而 `offload_assets_ro.bin` 与 `romfs.bin` 中没有）以及 `version`。
- `layout.offset` 的值（例如 `134807552`，即 `0x8090000`（`mcu.default.rt700.tub` 中的 `app.bin` 条目））大于文件长度，它们是目标端的加载位置，不是文件偏移。
- 清单中的 `md5` 与任何已测试的范围都不匹配。`mcu.default.rt700.tub` 也是如此（清单 md5 `8589b5e414f8352e39106fc3796ad050`）：其 `app.bin` 条目的 `offset` 为 134807552，超出 8.5 MB 的文件长度，且文件到其两个清单起始位置为止的前缀均不匹配。已测试的起点：0、0x10、0x20、0x40、0x80、0x100、0x200、0x400、0x1000；终点：每个 JSON 左花括号以及文件末尾。因此被哈希的字节要么不以原样存在于文件中，要么经过压缩或加密。未验证。
- `mcu.core1.default.rt700.tub`（清单 md5 `3d498ec201781cb20dcead30ca031032`，88 KB）的同一范围测试同样无匹配，清单 JSON（带或不带 `md5` 键）也无匹配。其载荷不含压缩文件头，前 0xC000 字节的熵为 6.6–7.1 比特，与加密相符，但也与原始 Arm 机器码相符；加密的解读未经确立。较小的文件（`case.default.tub`、`.cabo`、`.cocos`、`touch.default.tub`、`spl2.default.rt700.tub`）的范围测试也无匹配。`case.default.tub` 与 `case.default.lynx.tub` 逐字节相同（md5 `cd101cf1ed50caf9ca47bdfacc44084d`）。证据见 `data/userspace/tub_md5_tests.txt`。

| 容器 | 大小 | 子镜像名称 |
|---|---:|---|
| `mcu.default.rt700.tub` | 8.5 MB | `app.bin`、`display_calibration.bin`、`display_wpc_coeff.bin`、`touch-app-b0.cyacd2`、`boot_data.bin`、`pmic_reset_info.bin`，另有 28 个（见 `data/userspace/tub_contents.txt`）|
| `mcu.core1.default.rt700.tub` | 88 KB | `core1.bin`、`debug_frame.bin` |
| `spl2.default.rt700.tub` | 573 KB | `app.recovery.bin`、`app.signed.bin`、`spl2.bin`、`core1.bin`、`dumptruck.bin`、`dsp_app.bin`、`dsp_dtcm.bin`、`dsp_itcm.bin`、`spl2_secure_table.bin` |
| `dsp.default.rt700.tub` | 4.4 MB | `dsp_dtcm.bin`、`dsp_itcm.bin`、`dsp_app.bin`、`assets_ro.bin` |
| `touch.default.tub` | 105 KB | `touch-app-b0.cyacd2` |
| `case.default.tub`（以及 `.cabo`、`.cocos`、`.lynx` 变体） | 56–90 KB | `case.bin` |

名称所暗示的内容（推断）：

- MCU 运行一个应用（`app.bin`），并带有恢复镜像（`app.recovery.bin`）和已签名镜像。`spl2` 是二级加载程序，内含它自己的核心与 DSP 镜像副本。
- 触摸控制器使用 `.cyacd2` 文件。Cypress（现为 Infineon）PSoC 的归属来自外部知识，并非来自文件。
- RT700 芯片有一个 HiFi4 DSP（镜像中有源文件 `system_MIMXRT798S_hifi4.c`），指令存储与数据存储分开（`dsp_itcm.bin` 与 `dsp_dtcm.bin`）。该 DSP 容器为 4.4 MB。第 15 节描述该 DSP 固件。
- 显示校准数据存放在 MCU 容器中，与 `pmic_reset_info.bin` 相邻。

`.tub` 容器格式本身尚未解码。这些名称位于固定偏移处（例如在 DSP 文件中位于 `0x0`、`0x600` 和 `0x8A00`），但头部结构尚不清楚。

## 传感器、电源与输入 HAL

以下接口通过 `lpi_mcu_service` 运行在 MCU 上，因此其硬件属于眼镜，而不是手机级 SoC：

- 运动：`vendor.meta.hardware.sensor.imu`、`sensor.als`，以及 `system_ext` 中的 `libmotionservicehw.so`。
- 显示：`/dev/display/mock_als` 与 `/dev/display/location_info` 是 `vendor/lib64/hw/vendor.meta.sensors@2.0-impl.so` 中的字符串，`location_info` 也出现在 `system_ext/lib64/liblocationservice.so` 中。名称指向环境光路径和位置路径。
- 摄像头：`/dev/camfsync` 出现在 `odm/lib64/libmcu-vendor.so`、`vendor/etc/ueventd.rc` 以及 SELinux 文件上下文中。覆盖层中还有 `oculus,cam_fsync`。最可能的用途是摄像头之间的帧同步信号。根据名称推断。
- 配件认证：`vendor/bin/hw/vendor.meta.hardware.mfi@1.0-service` 使用 `/dev/mfi-i2c`，`ueventd.rc` 设置其权限。`mfi343s00176` 芯片位于覆盖层中（第 04 节）。
- 电池：`init.metasoc.sh` 把电量百分比和电压告警写入 `max17332-battery` 电源节点。脚本中执行这一操作的分支只在设备名为 `hammerhead` 时运行，因此在 `greatwhite` 上会跳过。`hammerhead` 据外部知识是另一款手机的代号，该脚本是共用的。根据脚本观察。
- 时间：`vendor.meta.hardware.time-service` 可执行文件。

## 应用层

`system_ext` 和 `product` 中有 32 个名为 `Smartglass*Release` 的应用包。列表中有 66 项：32 个包各自同时以 `.apk` 与 `.odex` 形式存在（64 项），另加 `WindowManager-SplashScreen-Smartglasses-Res.apk` 与 `services.smartglass.odex`（`data/userspace/smartglass_apps.txt`）。

列表中的例子：`SmartglassAccounts`、`SmartglassAiHistory`、`SmartglassAudioDataCollection`、`SmartglassBrowser`、`SmartglassCapture`、`SmartglassCommshub`、`SmartglassFiles`、`SmartglassGallery`、`SmartglassHandwritingPrototype`、`SmartglassInstagram`、`SmartglassLiveStream`、`SmartglassNabuPrompter`、`SmartglassNavigation`、`SmartglassOOBE`、`SmartglassPhone`、`SmartglassSensorLogger`、`SmartglassSettings`、`SmartglassSystemUI`、`SmartglassTalkback`，以及 `SmartglassFallingWordsGame`、`SmartglassGame2048` 等游戏。

`system_ext` 中还有 `MetaConstellationStateSDK.odex`、`DisplayOffloadManager.odex`，以及一组 `com.meta.wearable.*` 服务。

`Smartglass` 前缀是眼镜的应用家族名，可从包名中直接看出。

## Init 脚本与属性

- `data/userspace/init_rc_files.txt` 列出了找到的 163 个 `.rc` 文件。
- 与 MCU 相关的属性有：`persist.vendor.meta.enable_hyperoff`、`persist.vendor.meta.hyperoff.use_stp`、`vendor.meta.mcu_hal.stp_need_recovery`、`vendor.meta.stp_service.boot`，以及 `system_ext.meta.mobileconfig.service.emgrelay.receiver.enable`。
- `mobileconfig` 属性用于开关服务，它们出现在许多 `on property:` 触发器中。移动端配置是功能的服务端开关。

## 构建相关信息

- `odm/bin/hw_sync_timing.sh` 的头部注释写着 "HW Sync Timing Analysis Script for Blueshark"（为 Blueshark 编写的硬件同步时序分析脚本）。它解析 `dmesg` 中的 `gpio_mirror` 日志。因此 "Blueshark" 是镜像中出现的产品或项目名称。已观察。
- 该脚本中的版权声明为 "Meta Platforms, Inc. and affiliates. Confidential and proprietary"。我只把它作为来源记录，没有进一步使用。
