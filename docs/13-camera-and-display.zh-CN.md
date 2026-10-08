# 13 - 摄像头与显示用户空间

[English](13-camera-and-display.md)

本节记录内核之上的摄像头与显示软件：init 服务、摄像头与显示的 HAL 及服务进程、图像处理与色彩库、面板与摄像头的调校和校准文件，以及摄像头和显示驱动所绑定的设备树节点。图像协处理器的摄像头固件见第 08 节。LCoS 与背光校准在与显示协议栈相关的部分在此记录。

状态标注：已观察表示直接从文件读取；推断表示文件未明说但合理的解读；未找到表示该内容不在 OTA 中。摘要与哈希位于 `data/android/camera_display/`。

## 摄像头

### 服务与 init

来自 `system_ext/etc/init/`（已观察，副本见 `data/android/camera_display/`）：

- `cameraserver` 以用户 `cameraserver`、组 `audio camera input drmrpc` 运行 `/system/bin/cameraserver`，使用实时 I/O 优先级与 `rtprio 10`。它默认 `disabled`，并导出 AIDL 接口 `android.frameworks.cameraservice.service.ICameraService/default`。
- `init.hw.camera.rc` 创建两个 CPU 组 `/dev/cpuctl/camera-restricted` 与 `/dev/cpuset/camera-restricted`。视频采集期间，该 cpuset 限制在 CPU 0 至 2。已观察。
- `continuousaicamera` 以用户 `system` 运行 `/system_ext/bin/continuousaicamera_nova`，并具有 `WAKE_ALARM` 能力。仅当 `sys.settings.continuous_ai_camera_enabled=1` 时启动，并创建 `/data/misc/continuousaicamera` 及其 `snapshot`、`hold_sidecars` 子目录。已观察。
- `procamera` 以 `interface aidl procamera.IProCameraService/default` 运行 `/system_ext/bin/procamera`。它是 oneshot，默认禁用。
- `stubcameraservice` 以 `late_start` 类运行 `/system_ext/bin/stubcameraservice`，仅当 `persist.vendor.media.enableStubCamera=1` 时启动。已观察。

同一目录中的其他服务：`mediacaptureservice` 与 `ondevicecapture`。`vendor/bin` 中有 `captureengineservice` 二进制。按文件名观察。

### 连续 AI 摄像头服务

`continuousaicamera_nova`（967,528 字节）导出 AIDL 接口 `aidl::continuousaicamera::IContinuousAiCameraService`。由符号观察得出。它使用 `GraphicBuffer` 与 `GraphicBufferMapper` 读取帧，并通过 `CameraInputSurface` 接收画面。它还有一个面向 `sgruntimeservice` AI 采集人脸检测回调（`ISgrAICaptureFaceDetection`）的客户端接口。已观察。其库中包括 `libmarvin-continuousaicamera.meta.so` 与 `libalwaysoncamera*.so`，表明存在常亮采集管线。根据库名推断。

### 厂商摄像头库

来自 `vendor/lib64`（按文件名观察；库内代码未分析）：

- 图像处理：`libmmcamera_mfnr.so` 与 `libmmcamera_mfnr_t4.so`（多帧降噪）、`libmmcamera_bestats.so`（统计）、`libmmcamera_cac3.so`（色差校正）、`libmmcamera_lscv35.so`（镜头阴影）、`libmmcamera_pdpc.so`（相位检测像素校正）、`libcamerapostproc.so`。
- 框架支持：`libcamera_common.so`、`libcameracontext.so`、`libcamerasurface.so`、`libcamerainputsurface_vendor.so`、`libcamerametrics.so`、`libcameratelemetry_vendor.so`、`libcameraprivacy_vendor.so`、`libcamerawebserver.so`、`libqshcamera.so`，以及 `libcamera_nn_stub.so`（神经网络路径的桩）。
- 虚拟摄像头：`libvirtualcameraprovider.so`。其存在已观察；使用情况未检查。

### 调校与模型

`vendor/etc/camera/`（19 个文件，已观察）：

- `AIDenoiseTuning`、`CorePiAECTuning`（曝光控制）、`CorePiAWBTuning`（白平衡）、`CorePiFDTuning`（人脸检测）、`KFSCoreTuning`、`CameraALSLuxMap`（环境光传感器到勒克斯的映射）以及 `CameraAlsFovFlattenedMat`（环境光视场矩阵）。名称已观察；用途根据名称推断。
- `dnn/` 含神经网络模型：`dnn-model_wake-gesture-both-hands.bin`、`dnn-model_wake-gesture-left-hand.bin`、`dnn-model_wake-gesture-right-hand.bin`（手势唤醒模型）、`dnn-i3c-global.bin`、`dnn-i3c-1fps.bin`、`dnn-i3c-025fps-patch.bin`、`dnn-patch.bin`、`dnn-prep.bin`，以及 `food_detection.eai`。按文件名观察。手势唤醒模型表明手势可唤醒设备。根据文件名推断。

`vendor/bin` 中有 `camflicker` 二进制。已观察。其功能此处未分析；名称表明它用于检测传感器曝光的闪烁。

### 设备树

`data/android/vendor_ramdisk/vendor_dtb_dump.txt` 中的摄像头节点（已观察）：

- CPAS 模块（摄像头外设授权系统），即 `/soc/qcom,cam-cpas@ac13000`，其摄像头总线树包含 0 至 3 级节点。这些节点命名了 IFE、IPE、BPS、ICP、JPEG 与 CDM 客户端：`ife0` 至 `ife9`（线性统计、PDAF、RDI 像素原始、UBWC 写入）、`ipe0`、`bps0`、`icp0`、`jpeg-dma0`、`jpeg-enc0`，以及若干 `rt-cdm*` 节点。
- 处理节点：`/soc/qcom,cam-icp`、`/soc/qcom,cam-jpeg`、`/soc/qcom,cam-cdm-intf`。
- 摄像头的 IOMMU：`/soc/qcom,cam_smmu`，含 `msm_cam_smmu_ife`、`msm_cam_smmu_icp` 与 `msm_cam_smmu_jpeg` 上下文组，各有 `iova-mem-map`。
- 时钟门控：摄像头时钟控制器 `camcc` 的 `cam_cc_*` GDSC 节点（titan 顶层、IPE 0、BPS、IFE 0 至 2）。
- 传感器引脚：`cam_sensor_mclk0_active` 至 `mclk7`，以及 `cam_sensor_active_rst0` 与 `rst1`，各有 suspend 状态。已观察。

第 04 节列出了同一转储中的传感器与 EEPROM 节点（`qcom,cam-sensor0`、`qcom,eeprom0`、`oculus,cam_fsync` 与 `qcom,cam-res-mgr`）。摄像头内核驱动 `camera.ko`（摄像头请求管理器）在第 04 节。图像协处理器固件 `CAMERA_ICP.mbn` 在第 08 节。

## 显示

### 服务与启动

来自 `vendor/etc/init/` 与 `vendor/bin/`（已观察）：

- `qti_display_boot` 以 oneshot 方式在 `post-fs-data` 阶段运行 `/vendor/bin/init.qti.display_boot.sh`。该脚本通过读取 SoC ID（`/sys/devices/soc0/soc_id`）与平台名，选择按 SoC 设置的显示与 gralloc 属性。它将 `vendor.display.supports_background_blur` 设为 1，并按平台名分支（`taro`，以及脚本中列出的 SoC ID 分支）。`neo` 平台不在脚本前半部分所示的分支之中；其对应分支此处未核实。
- `fix-gw-display-pmic.rc` 在 `late-fs` 阶段运行 `/vendor/bin/hw/max77655_util --config_gw_display_pmic`。实用程序名与 `--config_gw_display_pmic` 选项已观察。推断：它通过 Maxim `max77655` PMIC 配置显示电源。设备树转储中不含 `max77655`，因此芯片型号未经确认。
- 显示 HAL 服务：`vendor.qti.hardware.display.composer`（`/vendor/bin/hw/vendor.qti.hardware.display.composer-service`，类别 `hal animation`，组 `graphics drmrpc`）、`vendor.qti.hardware.display.allocator-service`、`vendor.qti.hardware.display.demura-service`（demura 是面板均匀性校正），以及 `display-color-hal-1-0`（`vendor.display.color@1.0-service`）。已在 `vendor/etc/init` 与 `vendor/bin/hw` 中观察。
- `vendor.display.color` HAL 由 `vendor/lib64` 中的库提供 1.0 至 1.6 版本。按文件名观察。

### 图形与色彩库

`vendor/lib64`（按文件名观察）：

- 显示驱动库（SDM）：`libsdmcore.so`、`libsdmutils.so`、`libsdmextension.so`、`libsdm-disp-vndapis.so`、`libdisplayconfig.qti.so`。
- 色彩：`libsdm-color.so`、`libsdm-colormgr-algo.so`、`libqdcm-algo.so`、`libqdcm-json-mode-parser.so`、`libqdcm-mode-parser.so`、`libsnapdragoncolor-qdcm.so`。
- 缓冲区：`libgralloc.qti.so`、`libgralloccore.so`、`libgrallocutils.so`、`libminigbm_gralloc.so`。
- 策略与 QoS：`libdisplayqos.so`、`libdisplayskuutils.so`、`libdisplaydebug.so`，以及 `libdisplaymapping-meta.so`。最后一个是 Meta 的显示映射库。属性 `persist.vendor.meta.displaymapping.*` 在 SELinux 属性上下文中有对应标签（第 11 节）。
- `vendor/lib64` 中有合成器 HAL 2.1 至 2.4 版本（`android.hardware.graphics.composer@2.x.so`）。按文件名观察。

### 面板与校准

`vendor/etc/display/`（24 个文件，已观察）：

- 显示处理器配置：`DPU660.xml`、`DPU670.xml`、`DPU720.xml`、`DPU7__.xml`、`DPU820.xml`、`DPU830.xml`、`DPU8__.xml`、`DPU9__.xml`。数字为显示处理器（DPU）版本。`DPU7__` 等文件名中 `__` 的含义未确定。
- `advanced_sf_offsets.xml` 与 `thermallevel_to_fps.xml`：surface flinger 偏移，以及从热等级到帧率的表。
- 十二个面板模式的色彩校准（QDCM）JSON 文件：
  - `r66451` AMOLED（Visionox 面板）：命令与视频模式，各有带 DSC（显示流压缩）与不带 DSC 两版。
  - `nt36672e` LCD（Novatek 面板）：视频模式，带与不带 DSC。
  - `Sharp` 面板：2k 与 4k，命令与视频模式，带 Qsync 或 DSC。
  - `sharp_1080p` 与 `Sharp_qhd` 命令模式面板。
- Visionox AMOLED 面板的背光校准：`backlight_calib_r66451_amoled_cmd_mode_dsi_visionox_panel_with_DSC.xml` 与 `..._video_mode_...`。使用者为 `vendor/lib64` 中的 `libbacklight-calib.so`。已观察。

面板列表表明显示栈面向多种面板构建。仅凭文件名无法确定眼镜使用哪一块面板。下面的显示设置文件表明两块显示的尺寸不同。

`vendor/etc/display_settings.xml`（已观察，副本见 `data/android/camera_display/`）有两个 `display` 条目，名称分别为 `local:4630946274128011393` 与 `local:4630946521766656385`：

- 第一个强制为 600 × 600，`fixedToUserRotation="2"`，`forcedScalingMode="1"`；
- 第二个强制为 375 × 454，`forcedDensity` 为 100。

推断：两个本地显示对应眼镜的两块镜片，强制尺寸是框架应使用的面板尺寸。文件本身并未这样说明。

### LCoS 与背光 HAL

SELinux 策略中有 `hal_oculus_lcos`（`vendor.oculus.hardware.lcos::ILcos`）、`hal_oculus_backlight`（`vendor.oculus.hardware.backlight::IBacklight`）以及 `hal_oculus_display`（`vendor.oculus.hardware.display::IDisplayRefresh` 与 `vendor.oculus.hardware.graphics.composer::IComposer`）的域与接口（第 11 节）。LCoS 的控制本身运行在 MCU 固件中。控制台命令驱动显示引擎、LED 驱动与校准，见第 14 节。在已检视的 `vendor`、`odm`、`system_ext` 与 `product` 分区中，未找到 Android 端的 LCoS 控制二进制。背光 HAL 二进制未找到。`lcos` 内核驱动（兼容字符串 `meta,lcos-i2c`）在第 04 节。

## 与其他章节的关系

- 覆盖层表中的显示 PMIC 与背光 IC 在第 04 节。
- 摄像头与显示 GPU 驱动从第 06 节获取速度分级熔丝单元。
- 触发摄像头采集的 MCU 支持按键与传感器 HAL 在第 09 节。
- 图像协处理器固件 `CAMERA_ICP.mbn` 与视频 `vpu20_4v.mbn` 在第 08 节。

## 未找到的内容

- Android 端的 LCoS 控制二进制：控制在 MCU 固件中（第 14 节）。LCoS 控制路径的未决项已关闭。
- 背光 HAL 二进制。不在 OTA 的 `vendor` 或 `odm` 二进制中。
- 设备树节点之外的摄像头传感器驱动名称。所检视的文件中没有传感器模块名。
- 本设备的面板选择逻辑。不在 OTA 中。
- Android 摄像头提供者的图像管线配置（摄像头 XML）。所检视的文件中不存在。

## 证据

- `data/android/camera_display/summary.txt`：计数、哈希与调校文件列表。
- `data/android/camera_display/init.hw.camera.rc`、`cameraserver.greatwhite.rc`、`continuousaicamera_nova.rc`、`procamera.rc`、`stubcameraservice.rc`：摄像头 init 服务。
- `data/android/camera_display/display_settings.xml`、`fix-gw-display-pmic.rc`、`init.qti.display_boot.sh`、`vendor.qti.hardware.display.composer-service.rc`：显示启动与服务文件。
- `data/android/vendor_ramdisk/vendor_dtb_dump.txt`：摄像头与显示设备树节点。
- `data/userspace/init_rc_files.txt`：init 文件列表。
