# 13 - Camera and display userspace

[中文](13-camera-and-display.zh-CN.md)

This section covers the camera and display software above the kernel: the init services, the camera and display HAL and service processes, the image-processing and colour libraries, the tuning and calibration files for panels and cameras, and the device-tree nodes that the camera and display drivers bind to. The camera firmware for the image co-processor is in section 08. The LCoS and backlight calibration are covered here where they touch the display stack.

Status labels: observed means read directly from a file; inferred means a reasonable reading that the files do not state; not found means the item is not in the OTA. Summary and hashes are in `data/android/camera_display/`.

## Camera

### Services and init

From `system_ext/etc/init/` (observed, copies in `data/android/camera_display/`):

- `cameraserver` runs `/system/bin/cameraserver` as user `cameraserver`, group `audio camera input drmrpc`, with real-time I/O priority and `rtprio 10`. It is `disabled` until started and exposes the AIDL interface `android.frameworks.cameraservice.service.ICameraService/default`.
- `init.hw.camera.rc` creates two CPU groups, `/dev/cpuctl/camera-restricted` and `/dev/cpuset/camera-restricted`. The cpuset is limited to CPUs 0 to 2 during video capture. Observed.
- `continuousaicamera` runs `/system_ext/bin/continuousaicamera_nova` as user `system`, with `WAKE_ALARM`. It is started only when `sys.settings.continuous_ai_camera_enabled=1`, and it creates `/data/misc/continuousaicamera` with `snapshot` and `hold_sidecars` subdirectories. Observed.
- `procamera` runs `/system_ext/bin/procamera` as `interface aidl procamera.IProCameraService/default`. It is a oneshot, disabled by default.
- `stubcameraservice` runs `/system_ext/bin/stubcameraservice` in class `late_start`, started only when `persist.vendor.media.enableStubCamera=1`. Observed.

Other services in the same directory: `mediacaptureservice` and `ondevicecapture`. `vendor/bin` has a `captureengineservice` binary. Observed as file names.

### The continuous AI camera service

`continuousaicamera_nova` (967,528 bytes) exports the AIDL interface `aidl::continuousaicamera::IContinuousAiCameraService`. Observed from its symbols. It uses `GraphicBuffer` and `GraphicBufferMapper` to read frames, and a `CameraInputSurface` to receive them. It also has a client interface for an `sgruntimeservice` AI capture face-detection callback (`ISgrAICaptureFaceDetection`). Observed. Its libraries include `libmarvin-continuousaicamera.meta.so` and `libalwaysoncamera*.so`, which indicates an always-on capture pipeline. Inferred from the names.

### Vendor camera libraries

From `vendor/lib64` (observed as file names; the code behind them is not analysed):

- Image processing: `libmmcamera_mfnr.so` and `libmmcamera_mfnr_t4.so` (multi-frame noise reduction), `libmmcamera_bestats.so` (statistics), `libmmcamera_cac3.so` (chromatic aberration correction), `libmmcamera_lscv35.so` (lens shading), `libmmcamera_pdpc.so` (phase-detect pixel correction), `libcamerapostproc.so`.
- Framework support: `libcamera_common.so`, `libcameracontext.so`, `libcamerasurface.so`, `libcamerainputsurface_vendor.so`, `libcamerametrics.so`, `libcameratelemetry_vendor.so`, `libcameraprivacy_vendor.so`, `libcamerawebserver.so`, `libqshcamera.so`, and `libcamera_nn_stub.so` (a stub for the neural-network path).
- A virtual camera: `libvirtualcameraprovider.so`. Its presence is observed. Its use is not checked.

### Tuning and models

`vendor/etc/camera/` (19 files, observed):

- `AIDenoiseTuning`, `CorePiAECTuning` (exposure control), `CorePiAWBTuning` (white balance), `CorePiFDTuning` (face detection), `KFSCoreTuning`, `CameraALSLuxMap` (ambient light sensor to lux map) and `CameraAlsFovFlattenedMat` (ambient light field-of-view matrix). The names are observed; their use is inferred from the names.
- `dnn/` holds the neural-network models: `dnn-model_wake-gesture-both-hands.bin`, `dnn-model_wake-gesture-left-hand.bin`, `dnn-model_wake-gesture-right-hand.bin` (gesture wake-up models), `dnn-i3c-global.bin`, `dnn-i3c-1fps.bin`, `dnn-i3c-025fps-patch.bin`, `dnn-patch.bin`, `dnn-prep.bin`, and `food_detection.eai`. Observed as file names. The wake-gesture models suggest hand gestures wake the device. Inferred from the names.

The `camflicker` binary is in `vendor/bin`. Observed. Its function is not analysed here; the name suggests flicker detection for the sensor exposure.

### Device tree

The camera nodes in `data/android/vendor_ramdisk/vendor_dtb_dump.txt` (observed):

- The CPAS block (Camera Peripheral Authorization System), `/soc/qcom,cam-cpas@ac13000`, with a camera bus tree of level 0 to level 3 nodes. The nodes name the IFE, IPE, BPS, ICP, JPEG and CDM clients: `ife0` to `ife9` (linear stats, PDAF, RDI pixel raw, UBWC write), `ipe0`, `bps0`, `icp0`, `jpeg-dma0`, `jpeg-enc0`, and several `rt-cdm*` nodes.
- Processing nodes: `/soc/qcom,cam-icp`, `/soc/qcom,cam-jpeg`, `/soc/qcom,cam-cdm-intf`.
- The IOMMU for the camera: `/soc/qcom,cam_smmu` with the `msm_cam_smmu_ife`, `msm_cam_smmu_icp` and `msm_cam_smmu_jpeg` context banks, each with an `iova-mem-map`.
- Clock gating: `cam_cc_*` GDSC nodes for the camera clock controller `camcc` (titan top, IPE 0, BPS, IFE 0 to 2).
- Sensor pins: `cam_sensor_mclk0_active` to `mclk7` and `cam_sensor_active_rst0` and `rst1`, with suspend states. Observed.

Section 04 lists the sensor and EEPROM nodes (`qcom,cam-sensor0`, `qcom,eeprom0`, `oculus,cam_fsync` and `qcom,cam-res-mgr`) from the same dump.

The camera kernel driver `camera.ko` (Camera Request Manager) is in section 04. The image co-processor firmware `CAMERA_ICP.mbn` is in section 08.

## Display

### Services and boot

From `vendor/etc/init/` and `vendor/bin/` (observed):

- `qti_display_boot` runs `/vendor/bin/init.qti.display_boot.sh` as a oneshot at `post-fs-data`. The script selects per-SoC display and gralloc properties by reading the SoC ID (`/sys/devices/soc0/soc_id`) and the platform name. It sets `vendor.display.supports_background_blur` to 1 and branches on the platform name (`taro`, and a case for the SoC IDs listed in the script). The `neo` platform is not one of the branches shown in the first part of the script; the branch for it is not checked here.
- `fix-gw-display-pmic.rc` runs `/vendor/bin/hw/max77655_util --config_gw_display_pmic` in `late-fs`. The utility name and the `--config_gw_display_pmic` option are observed. Inferred: it configures the display power through a Maxim `max77655` PMIC. The device-tree dump does not contain `max77655`, so the chip is not confirmed.
- Display HAL services: `vendor.qti.hardware.display.composer` (`/vendor/bin/hw/vendor.qti.hardware.display.composer-service`, class `hal animation`, group `graphics drmrpc`), `vendor.qti.hardware.display.allocator-service`, `vendor.qti.hardware.display.demura-service` (demura is the panel uniformity correction), and `display-color-hal-1-0` (`vendor.display.color@1.0-service`). Observed in `vendor/etc/init` and `vendor/bin/hw`.
- The `vendor.display.color` HAL is provided in versions 1.0 to 1.6 by the libraries in `vendor/lib64`. Observed as file names.

### Graphics and colour libraries

`vendor/lib64` (observed as file names):

- Display driver library (SDM): `libsdmcore.so`, `libsdmutils.so`, `libsdmextension.so`, `libsdm-disp-vndapis.so`, `libdisplayconfig.qti.so`.
- Colour: `libsdm-color.so`, `libsdm-colormgr-algo.so`, `libqdcm-algo.so`, `libqdcm-json-mode-parser.so`, `libqdcm-mode-parser.so`, `libsnapdragoncolor-qdcm.so`.
- Buffers: `libgralloc.qti.so`, `libgralloccore.so`, `libgrallocutils.so`, `libminigbm_gralloc.so`.
- Policy and QoS: `libdisplayqos.so`, `libdisplayskuutils.so`, `libdisplaydebug.so`, and `libdisplaymapping-meta.so`. The last one is the Meta display-mapping library. The property `persist.vendor.meta.displaymapping.*` has a label in the SELinux property contexts (section 11).
- Composer HAL versions 2.1 to 2.4 are present in `vendor/lib64` (`android.hardware.graphics.composer@2.x.so`). Observed as file names.

### Panels and calibration

`vendor/etc/display/` (24 files, observed):

- Display-processor configuration: `DPU660.xml`, `DPU670.xml`, `DPU720.xml`, `DPU7__.xml`, `DPU820.xml`, `DPU830.xml`, `DPU8__.xml`, `DPU9__.xml`. The number is the display processor (DPU) version. The meaning of the `__` in `DPU7__`, `DPU8__` and `DPU9__` is not established.
- `advanced_sf_offsets.xml` and `thermallevel_to_fps.xml`: surface-flinger offsets, and a table from thermal level to frame rate.
- Twelve colour-calibration (QDCM) JSON files for the panel modes:
  - `r66451` AMOLED, from the Visionox panel: command and video mode, each with and without DSC (display stream compression).
  - `nt36672e` LCD, from the Novatek panel: video mode, with and without DSC.
  - `Sharp` panels: 2k and 4k, command and video mode, with Qsync or DSC.
  - `sharp_1080p` and `Sharp_qhd` command-mode panels.
- Backlight calibration for the Visionox AMOLED panel: `backlight_calib_r66451_amoled_cmd_mode_dsi_visionox_panel_with_DSC.xml` and `..._video_mode_...`. The consumer is `libbacklight-calib.so` (in `vendor/lib64`). Observed.

The panel list shows the display stack was built for several panels. Which panel the glasses use is not stated in the file names alone. The display-settings file below suggests the two displays are not the same size.

`vendor/etc/display_settings.xml` (observed, copied to `data/android/camera_display/`) has two `display` entries with the names `local:4630946274128011393` and `local:4630946521766656385`:

- the first is forced to 600 by 600 with `fixedToUserRotation="2"` and `forcedScalingMode="1"`;
- the second is forced to 375 by 454 with a `forcedDensity` of 100.

Inferred: the two local displays are the two lenses of the glasses, and the forced sizes are the panel sizes the framework should use. The file does not say this.

### LCoS and backlight HALs

The SELinux policy has domains and interfaces for `hal_oculus_lcos` (`vendor.oculus.hardware.lcos::ILcos`), `hal_oculus_backlight` (`vendor.oculus.hardware.backlight::IBacklight`) and `hal_oculus_display` (`vendor.oculus.hardware.display::IDisplayRefresh` and the `vendor.oculus.hardware.graphics.composer::IComposer`) (section 11). The LCoS control itself runs in the MCU firmware. The console commands drive the display engine, the LED drivers and the calibration, and they are described in section 14. No Android-side LCoS control binary was found in the `vendor`, `odm`, `system_ext` or `product` partitions. The backlight HAL binary is not found. The `lcos` kernel driver (`meta,lcos-i2c` compatible string) is in section 04.

## Relation to other sections

- The display PMIC and the backlight IC in the overlay tables are in section 04.
- The camera and display GPU drivers take their speed-bin fuse cell from section 06.
- The MCU-backed button and sensor HALs that trigger camera capture are in section 09.
- The image co-processor firmware `CAMERA_ICP.mbn` and the video `vpu20_4v.mbn` are in section 08.

## What is not found

- The Android-side LCoS control binary: the control is in the MCU firmware (section 14). Closed as an open item for the LCoS control path.
- The backlight HAL binary. Not in the OTA's `vendor` or `odm` binaries.
- The camera sensor drivers' names beyond the device-tree nodes. The sensor module names are not in the files examined.
- The panel selection logic for this device. Not in the OTA.
- The image pipeline configuration (`camera` XML for the Android camera provider). Not present in the files examined.

## Evidence

- `data/android/camera_display/summary.txt`: counts, hashes and the tuning list.
- `data/android/camera_display/init.hw.camera.rc`, `cameraserver.greatwhite.rc`, `continuousaicamera_nova.rc`, `procamera.rc`, `stubcameraservice.rc`: camera init services.
- `data/android/camera_display/display_settings.xml`, `fix-gw-display-pmic.rc`, `init.qti.display_boot.sh`, `vendor.qti.hardware.display.composer-service.rc`: display boot and service files.
- `data/android/vendor_ramdisk/vendor_dtb_dump.txt`: camera and display device-tree nodes.
- `data/userspace/init_rc_files.txt`: the init file list.
