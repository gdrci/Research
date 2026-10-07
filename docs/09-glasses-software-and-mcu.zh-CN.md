# 09 - 眼镜端软件、MCU 与腕带

[English](09-glasses-software-and-mcu.md)

本文介绍启动链之上、应用处理器旁边的那部分系统：一个二级微控制器（MCU）、它与 Android 之间的传输、基于它的传感器和输入 HAL、肌电（EMG）输入通路，以及应用层。文中的文件计数来自 `data/userspace/`。

## MCU

眼镜上有一个与 SoC 分开的微控制器。好几个 HAL 和内核接口只为与它通信而存在。证据如下：

- `lpi_mcu` 服务（`odm/etc/init/vendor.meta.hardware.lpi_mcu-service.greatwhite.rc`，可执行文件 `odm/bin/hw/vendor.meta.hardware.lpi_mcu-service.greatwhite`）注册了 17 个 AIDL 接口，列于下文。
- `vendor/bin` 中的 `mcu-properties.sh` 读取 `/sys/devices/platform/soc/soc:meta,rt600_ctrl/is_rt600`。内核驱动名为 `meta,rt600_ctrl`。它的确切作用是根据名称以及 init 文件写入它的触发器推断的。
- `vendor/firmware` 中有 `mcu.default.rt700.tub` 和 `mcu.core1.default.rt700.tub`。`.tub` 文件很可能是 MCU 自己的固件。文件名中的 `rt700` 与脚本检测的音频编解码器变体相符。这两点都是推断。
- `odm/lib64/libmcu-vendor.so` 是厂商侧的 MCU 库，位于 ODM 分区中。

已从文件中验证的内容：名称、路径，以及 init 与属性的逻辑。MCU 的处理器类型和固件格式未验证。

### 它的 AIDL 接口

| 接口 | 作用（根据名称） |
|---|---|
| `vendor.meta.hardware.button.capturebutton.ICaptureButton` | 拍摄按钮 |
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

名称描述的是接口控制的内容。它们运行在哪里，由承载它们的服务决定：17 个接口全部由 `lpi_mcu_service` 注册，因此都面向 MCU。

### 传输：STP

`system_ext/bin/stpService`（由 `system_ext/etc/init/stpService.rc` 启动，类别 `main`，用户 `system`）通过 `/dev/stp` 节点与 MCU 通信。`palmvisionservice` 的 init 文件也提到了 STP 服务。hyperoff 功能使用它：

- 在 RT700 配置下，`mcu-properties.sh` 会设置 `persist.vendor.meta.hyperoff.use_stp=true`。
- `vendor.meta.stp_service.boot` 与 `vendor.meta.mcu_hal.stp_need_recovery` 分别是 STP 服务的启动标志和恢复标志。

恢复路径值得注意。当 `vendor.meta.mcu_hal.stp_need_recovery` 被设为 1 时，init 脚本等待五秒（用于收集日志），然后向 `/sys/devices/platform/soc/soc:meta,rt600_ctrl/trigger_assert` 写入 `1`，使 MCU 断言；随后清除该标志。注释说明重启选项被有意注释掉。已从 init 文件验证。文件中还写明 "only effective on greatwhite"（仅在 greatwhite 上有效）。

### 两种硬件配置：RT600 与 RT700

`mcu-properties.sh` 检查 `is_rt600`：

- 值为 `0` 时，设备为 RT700 配置，设置 `persist.vendor.meta.enable_hyperoff=true` 与 `persist.vendor.meta.hyperoff.use_stp=true`。
- 否则为 RT600 配置，不设置任何属性。

因此眼镜有两种音频编解码器（Realtek RT600 与 RT700），软件在启动时选择对应的行为。`dtbo.img` 中的覆盖层也按组件有所不同（第 04 节）。启用 `rt685_detect` 的覆盖层与 `rt700` 固件的名称与此相符。已观察；我尚未阅读编解码器驱动。

## EMG 输入（腕带）

腕带是一个肌电（EMG）输入设备。文件中的证据如下：

- `system_ext/etc/vintf/manifest/emg2_manifest.xml` 声明了 AIDL HAL `com.meta.wearable.emg`，接口为 `IEmgService`，实例为 `default` 和 `fmq`（快速消息队列）。
- `system_ext/lib64` 中有 `libemginput.so`、`libemg_quaternion_consumer.so`（来自腕带的姿态/四元数）、`libemg_device_status_consumer.so`、`libemg_state_sync_consumer.so`、`libemgcache.so`、`libemg_equeue.so`、`libemgserviceutils2.so` 和 `emgsdk-proto-cc.so`。
- MCU 固件 `mcu.default.rt700.tub` 中有字符串 `/dev/Band`、`/dev/BandOff` 和 `/dev/PhoneDisconnected`。`Band` 指向腕带，`BandOff` 指向其关闭状态。在提取的文件树中，只有 MCU 固件含有 `/dev/Band`。此前的草稿称 `libbluetooth_qti.so` 和 `libencode_c2.so` 也含有它，这是错误的：搜索在这两个库中都找不到 `/dev/Band`，它们中的 `Band` 匹配是 AAC 编解码器函数名（`FDKaacEnc_*Band*`）。该名称目前唯一已知的位置是 MCU 固件，因此没有任何共用名称把腕带与手机端联系起来。
- `/dev/PhoneDisconnected` 也出现在手机一侧：`system_ext/bin/navigationservice`、`SmartglassOOBERelease` 和 `SmartglassSystemUIRelease`。应用层把某个设备节点名称当作状态使用，这很可能是经由 MCU 传递的配套设备状态信号。根据名称推断。
- init 脚本 `init.emgrelay_receiver.rc` 与 `init.emgrelaydatax.rc` 启动 `emgrelay_receiver` 和 `emgrelaydatax`，其开关由 `system_ext.meta.mobileconfig.service.emgrelay.receiver.enable` 属性以及截屏管理器属性控制。

EMG 数据路径分为三部分，依据二进制文件的字符串得出：

- `system_ext/bin/emgrelay_receiver` 接收 protobuf 格式的 `EmgInferenceEvent` 消息，并把它们注入虚拟 EMG 服务（`com.meta.wearable.emg.sim.IVirtualEmgService`，带有 `IVirtualEmgStreamControlCallback`）。它的日志 `Failed to open channel to phone's EmgRelayReceiver service` 表明它会打开一个通往手机端的通道。其注册消息为 `Companion scope available [uuid=...], registering DataX service`。
- `system_ext/bin/emgrelaydatax` 序列化 `EMGGestureEvent` 消息（`EmgEventClient::onGestureDetected`），并把它们发送给 EMG 服务。其日志 `Failed to connect EmgEventClient to EMG service` 表明它连接的是 EMG 服务。
- `emg2` 实现 `IEmgService`，并通过 `fmq` 实例接收设备数据。

因此，腕带信号通过 `fmq` 队列进入 `emg2`（真实设备数据），以及通过虚拟服务进入（注入的推理事件）。从 MCU 到腕带数据源的环节尚未在代码中找到。依据字符串观察得出。相关二进制：`system_ext/bin/emgrelay_receiver`、`system_ext/bin/emgrelaydatax`。

EMG 服务路径（在提取的文件树中观察到）：

- `system_ext/bin/emg2` 是 EMG 服务，由 `persist.vendor.meta.enable_emg=1` 启动（`emg2.rc`）。它实现 `com.meta.wearable.emg.IEmgService`（清单 `emg2_manifest.xml`），有 `default` 和 `fmq` 两个实例。
- `fmq` 实例通过 AIDL 消息队列传输数据。`libemgfmq_helper.so` 通过 `android.hardware.common.fmq` 读写 `emg_fmq_packet_t` 数据包（`SynchronizedReadWriteEEEE`、`EventFlag`）。其消息涵盖队列长度、队列已满，以及读写指针损坏。
- `libemginput.so` 通过格式化名称打开设备节点（`/dev/%s`），另有 `/dev/gpiochip%u` 和 `/dev/joycon0`。格式化名称的来源尚未确定。
- `emg2` 中的事件名：`emg_raw_gesture_event`、`input_emg_raw_gesture_event`、`wearables_band_tightness_detector_events`。

未找到：腕带与 `emg2` 之间的传输。除 MCU 固件外，提取的文件树中没有任何二进制文件提到 `/dev/Band`。厂商 init 文件中也没有腕带或 EMG 的设备条目。因此该连接仍未确定。

`libmarvin-emg.meta.so` 与 `libemg_marvin-client.meta.so` 中使用了 "Marvin" 这个名字。它很可能是型号或客户端的内部代号。未验证。

## 厂商分区中的固件容器

`vendor/firmware` 中的文件是容器，每个容器都包含带名称的子镜像。下表中的名称是从各文件中找到的（完整列表见 `data/userspace/tub_contents.txt`）：

结构，依据 `case.default.cabo.tub` 与 `mcu.core1.default.rt700.tub`（已观察）：

- 文件开头是子镜像名称，以 NUL 填充（如 `case.bin`、`core1.bin`）。
- 载荷在前，文件末尾跟着 JSON 清单，部分文件还在第一个 JSON 之后带有第二个 JSON 块。
- 清单包含 `deployment_methods`（`["RPC"]`）、`md5`、`platform`（core1 文件中为 `greatwhite-rt700`）、`target_assets`（每项含 `name`、`type`、`layout.load_addr`、`layout.offset`，core1 文件中还有 `signature`）以及 `version`。
- `layout.offset` 的值（例如 `142409728`，即 `0x87D0000`）大于文件长度，它们是目标端的加载位置，不是文件偏移。
- 清单中的 `md5` 与任何已测试的范围都不匹配。已测试的起点：0、0x10、0x20、0x40、0x80、0x100、0x200、0x400、0x1000；终点：每个 JSON 左花括号以及文件末尾。因此被哈希的字节要么不以原样存在于文件中，要么经过压缩或加密。未验证。

| 容器 | 大小 | 子镜像名称 |
|---|---:|---|
| `mcu.default.rt700.tub` | 8.5 MB | `app.bin`、`display_calibration.bin`、`display_wpc_coeff.bin`、`touch-app-b0.cyacd2`、`boot_data.bin`、`pmic_reset_info.bin` |
| `mcu.core1.default.rt700.tub` | 88 KB | `core1.bin`、`debug_frame.bin` |
| `spl2.default.rt700.tub` | 573 KB | `app.recovery.bin`、`app.signed.bin`、`spl2.bin`、`core1.bin`、`dumptruck.bin`、`dsp_app.bin` |
| `dsp.default.rt700.tub` | 4.4 MB | `dsp_dtcm.bin`、`dsp_itcm.bin`、`dsp_app.bin`、`assets_ro.bin` |
| `touch.default.tub` | 105 KB | `touch-app-b0.cyacd2` |
| `case.default.tub`（以及 `.cabo`、`.cocos`、`.lynx` 变体） | 56–90 KB | `case.bin` |

名称所暗示的内容（推断）：

- MCU 运行一个应用（`app.bin`），并带有恢复镜像（`app.recovery.bin`）和已签名镜像。`spl2` 是二级加载程序，内含它自己的核心与 DSP 镜像副本。
- 触摸控制器使用 `.cyacd2`，这是 Cypress（现为 Infineon）PSoC 的固件格式。
- RT700 音频编解码器有自己的 DSP，指令存储与数据存储分开（`dsp_itcm.bin` 与 `dsp_dtcm.bin`）。该 DSP 容器为 4.4 MB。
- 显示校准数据存放在 MCU 容器中，与 `pmic_reset_info.bin` 相邻。

`.tub` 容器格式本身尚未解码。这些名称位于固定偏移处（例如在 DSP 文件中位于 `0x0`、`0x600` 和 `0x8A00`），但头部结构尚不清楚。

## 传感器、电源与输入 HAL

以下接口通过 `lpi_mcu_service` 运行在 MCU 上，因此其硬件属于眼镜，而不是手机级 SoC：

- 运动：`vendor.meta.hardware.sensor.imu`、`sensor.als`，以及 `system_ext` 中的 `libmotionservicehw.so`。
- 显示：`/dev/display/mock_als` 与 `/dev/display/location_info` 是 `vendor/lib64/hw/vendor.meta.sensors@2.0-impl.so` 中的字符串，`location_info` 也出现在 `system_ext/lib64/liblocationservice.so` 中。名称指向环境光路径和位置路径。
- 摄像头：`/dev/camfsync` 出现在 `odm/lib64/libmcu-vendor.so`、`vendor/etc/ueventd.rc` 以及 SELinux 文件上下文中。覆盖层中还有 `oculus,cam_fsync`。最可能的用途是摄像头之间的帧同步信号。根据名称推断。
- 配件认证：`vendor/bin/hw/vendor.meta.hardware.mfi@1.0-service` 使用 `/dev/mfi-i2c`，`ueventd.rc` 设置其权限。`mfi343s00176` 芯片位于覆盖层中（第 04 节）。
- 电池：`init.metasoc.sh` 把电量百分比和电压告警写入 `max17332-battery` 电源节点。脚本中执行这一操作的分支只在设备名为 `hammerhead` 时运行，因此在 `greatwhite` 上会跳过。`hammerhead` 是另一款手机的代号，该脚本是共用的。根据脚本观察。
- 时间：`vendor.meta.hardware.time` 服务。

## 应用层

`system_ext` 和 `product` 中有 34 个名为 `Smartglass*Release` 的应用包。列表中有 66 项，因为大多数应用同时以 `.apk` 与 `.odex` 形式存在（`data/userspace/smartglass_apps.txt`）。

列表中的例子：`SmartglassAccounts`、`SmartglassAiHistory`、`SmartglassAudioDataCollection`、`SmartglassBrowser`、`SmartglassCapture`、`SmartglassCommshub`、`SmartglassFiles`、`SmartglassGallery`、`SmartglassHandwritingPrototype`、`SmartglassInstagram`、`SmartglassLiveStream`、`SmartglassNabuPrompter`、`SmartglassNavigation`、`SmartglassOOBE`、`SmartglassPhone`、`SmartglassSensorLogger`、`SmartglassSettings`、`SmartglassSystemUI`、`SmartglassTalkback`，以及 `SmartglassFallingWordsGame`、`SmartglassGame2048` 等游戏。

`system_ext` 中还有 `MetaConstellationStateSDK.odex`、`DisplayOffloadManager.odex`，以及一组 `com.meta.wearable.*` 服务。

`Smartglass` 前缀是眼镜的应用家族名，可从包名中直接看出。

## Init 脚本与属性

- `data/userspace/init_rc_files.txt` 列出了找到的 163 个 `.rc` 文件。
- 与 MCU 相关的属性有：`persist.vendor.meta.enable_hyperoff`、`persist.vendor.meta.hyperoff.use_stp`、`vendor.meta.mcu_hal.stp_need_recovery`、`vendor.meta.enable_hyperoff`、`vendor.meta.stp_service.boot`，以及 `system_ext.meta.mobileconfig.service.emgrelay.receiver.enable`。
- `mobileconfig` 属性用于开关服务，它们出现在许多 `on property:` 触发器中。移动端配置是功能的服务端开关。

## 构建相关信息

- `odm/bin/hw_sync_timing.sh` 的头部注释写着 "HW Sync Timing Analysis Script for Blueshark"（为 Blueshark 编写的硬件同步时序分析脚本）。它解析 `dmesg` 中的 `gpio_mirror` 日志。因此 "Blueshark" 是镜像中出现的产品或项目名称。已观察。
- 该脚本中的版权声明为 "Meta Platforms, Inc. and affiliates. Confidential and proprietary"。我只把它作为来源记录，没有进一步使用。
