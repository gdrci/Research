# 08 - 外设固件与构建 ID

[English](08-peripheral-firmware-and-build-ids.md)

本节记录两类内容，其他章节未涵盖：OTA 为各子系统记录的构建标识符，以及 `vendor/firmware` 中 GPU、摄像头、视频和视觉模块的固件。每项结论都标明为已观察、推断或未找到。

## 构建标识符

`modem.img` 中含有 `/verinfo/ver_info.txt`（`data/remote/modem_verinfo.txt`）。这是一份 JSON 构建清单。已观察：

| 键 | 值 |
|---|---|
| `aop` | `AOP.HO.4.0-00605-AURORA_E-1` |
| `apps_vendor` | `LA.VENDOR.12.2.r1-16200-NEOLA.QSSI14.0-1.149645.1` |
| `boot` | `BOOT.MXF.2.2-00536-AURORA-1.149279.3` |
| `btfm` | `BTFW.HAMILTON.2.0.0-00819-PATCHZ-1` |
| `common` | `Aurora.LA.2.0-00101-STD.PROD-1.149279.2` |
| `cpucp` | `CPUCP.FW.1.0-00027-AURORA_EXT-1` |
| `dsp` | `DSP.XT.1.0-00988-AURORA-1` |
| `tz` | `TZ.XF.5.21-00251-AURORAAAAAANAZT-1.149633.2` |
| `tz_apps` | `TZ.APPS.1.21-00374-AURORAAAAAANAZT-2` |
| `wlan_hmt` | `WLAN.HMT.1.1.c4-00443-QCAHMTSWPL_V1.0_V2.0_SILICONZ-1` |

元构建为 `Aurora.LA.2.0-00101-STD.PROD-1.149279.2`，产品版本为 `asic`，时间戳为 `2026-06-01 12:36:15`。

清单能说明的内容：

- `Aurora` 是第 00 节中使用的 SoC 代号。`LA` 标记是高通 Linux Android 基线。
- 多个子系统构建共享标签 `1.149279`（`common`、`boot`），因此它们可能来自同一发布线。推断。
- `btfm` 条目（`00819`）与蓝牙镜像自身的版本文件（`00797`，第 07 节）不一致。第 07 节已如实记录，此处不作解决。
- `apps_vendor` 条目为 `LA.VENDOR.12.2`，而 vendor 分区为 Android 12（第 04 节）。这与该节所述的较旧 Treble 基线一致。

该清单是 OTA 中找到的唯一构建级别记录。其他镜像没有同类记录。未找到。

## `vendor/firmware` 中的外设固件

`vendor/firmware` 目录共 42 项（`data/userspace/vendor_firmware_files.txt`）。其中 9 个是眼镜 MCU、传感器和音频的 `.tub` 容器，第 09 节已涵盖。其余列于下文。头部信息用 pyelftools 读取，原始文件直接读取（`data/userspace/peripheral_firmware_headers.txt`）。

出现两种固件格式：

- 高通分段 ELF：一个 `.mdt` 头文件加上编号的段文件（`.b00`、`.b01`……），以及一个包含完整镜像的 `.mbn` 文件。每个段由远程处理器加载器加载。根据文件名与 ELF 头观察得出。
- 无 ELF 头的原始微码或 GMU 固件。

### GPU（Adreno）

- `a620_zap.mdt`、`a620_zap.b00`–`b02`、`a620_zap.mbn`：a620 类的 zap 着色器。`.mbn` 为 14,328 字节。
- `a740v3_zap.mdt`、`a740v3_zap.b00`–`b02`、`a740v3_zap.elf`、`a740v3_zap.mbn`：a740 类的 zap 着色器。
- `a650_sqe.fw`（31,988 字节）与 `a740v3_sqe.fw`（76,852 字节）：SQE（命令流）微码。原始格式，无头部。
- `a621_gmu.bin`（56,056 字节）与 `gmu_gen70200.bin`（67,608 字节）：GMU 固件。两者都以字 `0x0, 0x0, 0x1, 0x1dc, 0x4000` 开头，看起来像一个通用头部。推断。

zap 的 ELF 头写明 `e_machine = EM_QDSP6`（Hexagon），入口 `0x1000`，并有一个位于 `0x1000` 的可加载段，标志为 RWX（`0x8000007`）。已观察。GPU 侧的镜像不一定携带 Hexagon 机器类型，此点出乎意料；本文只记录读取到的内容，原因尚未确定。

`a740v3_zap.mbn` 与 `a620_zap.mbn` 含有签名块，其中包括字符串 `SECTOOLS SECP384R1 CURVE TEST ROOT01` 与 `General Use Test Key 0 (for testing only)`。已观察。出货的签名镜像中出现测试根字符串，说明签名结构存在，但这里未检查其到生产根的信任链。

GPU 驱动 `msm_kgsl.ko` 读取速度分级熔丝单元（第 06 节）。推断：固件文件通过内核 GPU 驱动与 zap 机制加载，但所检视的镜像中没有加载器代码。

### 摄像头图像协处理器（`CAMERA_ICP`）

- `CAMERA_ICP.mdt`（7,724 字节）与 `CAMERA_ICP.mbn`（949,080 字节）：Xtensa ELF，入口 `0x0`，21 个程序头，19 个可加载段。
- 段文件 `CAMERA_ICP.b00` 至 `b20`。最大的是 `b08`（866,156 字节）。
- 镜像中的字符串：`QC_IMAGE_VERSION_STRING=CICP.FW.5.0-00020`、`CAMERA_640_V1 (Mimas)`、`CAMERA_740_V1 (Skye)`，以及源路径 `Z:/b/fw_core/Common/DbgUtils/src/icpdiag.c`。已观察。

`CICP` 是镜像对自身固件的命名。`Mimas` 与 `Skye` 作为两个摄像头配置字符串出现。已观察；将其理解为两种硬件变体属于推断。内核侧的摄像头配置在 `init.hw.camera.rc` 与 `cameraserver.greatwhite.rc` 中（`data/userspace/init_rc_files.txt`）。

### 视频（`vpu20_4v.mbn`，Venus）

- `vpu20_4v.mbn`（2,079,528 字节）：Xtensa ELF，入口 `0xF500000`，20 个程序头，18 个可加载段。
- 字符串：`VenusSynx`、`VENUS is idle, no HW is running`、`venus_firmware.c`、`IPCC_OSVPU.c`。已观察。

`Venus` 是高通视频编解码模块的名称。文件名 `vpu20_4v` 是镜像对 VPU 2.0 核心（含四个视频单元）的命名。根据名称推断。

### 视觉（`evass.mbn`）

- `evass.mbn`（2,247,464 字节）：Xtensa ELF，入口 `0xF500000`，20 个程序头，18 个可加载段。其第一个段表与 `vpu20_4v.mbn` 一致，但两个文件约有 100 万字节不同。已观察。
- 字符串包括 `facedetection`、`prevState_selectedAlignment`、`prevState_ageAlignment` 与 `prevState_ageSgm`。已观察。
- vendor 镜像中有 `etc/eva/facedetection/model3.dat`。已观察。

该镜像是运行人脸检测与人脸对齐模型的视觉协处理器。文件中没有展开 `EVASS` 这一名称。根据字符串与模型文件推断。

## 通用格式

ELF 镜像与第 05 节中高通远程处理器使用相同的段布局：一个带有 `.bNN` 段的 `.mdt` 头文件，或单个 `.mbn`。头文件列出每个段的物理地址与大小，加载器会将段与签名哈希进行核对。这是根据命名与 `.mdt` 头推断的；所检视的镜像中没有加载器代码。

## 未找到的内容

- GPU zap 着色器、摄像头与视频固件在内核或 TrustZone 镜像中的加载器。加载器名称见第 05 节与第 04 节，与这些文件的关联未确认。
- GPU、摄像头与视觉镜像的构建级别清单。未找到。
- `EVASS` 的展开含义。镜像中未找到。

## 证据

- `data/remote/modem_verinfo.txt`
- `data/userspace/peripheral_firmware_headers.txt`
- `data/userspace/vendor_firmware_files.txt`
- `data/userspace/init_rc_files.txt`
- `data/android/kernel/config.txt`（GPU 与摄像头驱动选项）
