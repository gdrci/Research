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

- `Aurora` 是第 05 节中使用的 SoC 代号。`LA` 标记是高通 Linux Android 基线。
- 多个子系统构建共享标签 `1.149279`（`common`、`boot`），因此它们可能来自同一发布线。推断。
- `btfm` 条目（`00819`）与蓝牙镜像自身的版本文件（`00797`）不一致。镜像内的补丁横幅写的是 `00797`，因此镜像就是该构建，`00819` 是另一个构建（第 07 节）。
- `apps_vendor` 条目为 `LA.VENDOR.12.2`，而 vendor 分区为 Android 12（第 04 节）。这与该节所述的较旧 Treble 基线一致。

该清单是 OTA 中找到的唯一构建级别记录。其他镜像没有同类记录。未找到。

## `vendor/firmware` 中的外设固件

`vendor/firmware` 目录共 42 项（`data/userspace/vendor_firmware_files.txt`）。其中 9 个是 `.tub` 容器：MCU、DSP、case、触控与 SPL2 固件（第 09 节）。其余列于下文。头部信息用 pyelftools 读取，原始文件直接读取（`data/userspace/peripheral_firmware_headers.txt`）。

出现两种固件格式：

- 高通分段 ELF：一个 `.mdt` 头文件加上编号的段文件（`.b00`、`.b01`……），以及一个包含完整镜像的 `.mbn` 文件。每个段由远程处理器加载器加载。根据文件名与 ELF 头观察得出。
- 无 ELF 头的原始微码或 GMU 固件。

### GPU（Adreno）

- `a620_zap.mdt`、`a620_zap.b00`–`b02`、`a620_zap.mbn`：a620 类的 zap 着色器。`.mbn` 为 14,328 字节。
- `a740v3_zap.mdt`、`a740v3_zap.b00`–`b02`、`a740v3_zap.elf`、`a740v3_zap.mbn`：a740 类的 zap 着色器。
- `a650_sqe.fw`（31,988 字节）与 `a740v3_sqe.fw`（76,852 字节）：SQE（命令流）微码。原始格式，无头部。
- `a621_gmu.bin`（56,056 字节）与 `gmu_gen70200.bin`（67,608 字节）：GMU 固件。两者都以字 `0x0, 0x0, 0x1, 0x1dc, 0x4000` 开头，看起来像一个通用头部。推断。

zap 的 ELF 头写明 `e_machine = EM_QDSP6`（Hexagon），入口 `0x1000`，并有一个位于 `0x1000` 的可加载段，标志为 RWX（`0x8000007`）。已观察。Adreno 驱动通过内核的 zap 着色器路径加载它（`msm.ko` 中的 `adreno_zap_shader_load` 与 `a6xx_zap_shader_init`，`msm_kgsl` 中的 `kgsl_zap_shader_load`）。按符号名观察。推断：高通的外设认证路径加载这些 ELF 文件，Hexagon 机器类型是该路径在头部中期望的值；zap 随后在 GPU 一侧运行。

`a740v3_zap.mbn` 的签名块含有 SECTOOLS 测试根（`SECTOOLS SECP384R1 CURVE TEST ROOT0`、`General Use Test Key 0 (for testing only)`）。`a620_zap.mbn` 不含 SECTOOLS 字符串，而是含有 Meta Greatwhite_FW 链（第 16 节）。已观察。出货的签名镜像中出现测试根字符串，说明签名结构存在，但这里未检查其到生产根的信任链。

`msm_kgsl.ko` 模块含有 `speed_bin` 与 `speed-bin` 字符串，设备树将 `speed_bin` nvmem 单元命名出来（第 06 节）。读取该单元的代码未经检视。推断：固件文件通过内核 GPU 驱动与 zap 机制加载，但所检视的镜像中没有加载器代码。

### 摄像头图像协处理器（`CAMERA_ICP`）

- `CAMERA_ICP.mdt`（7,724 字节）与 `CAMERA_ICP.mbn`（949,080 字节）：Xtensa ELF，入口 `0x0`，21 个程序头，19 个可加载段。
- 段文件存在于 `CAMERA_ICP.b00`–`b09`、`b17`、`b18` 与 `b20`（共 13 个文件）；`.mbn` 包含完整镜像。最大的是 `b08`（866,156 字节）。
- 镜像中的字符串：`QC_IMAGE_VERSION_STRING=CICP.FW.5.0-00020`、`CAMERA_640_V1 (Mimas)`、`CAMERA_740_V1 (Skye)`，以及源路径 `Z:/b/fw_core/Common/DbgUtils/src/icpdiag.c`。已观察。

`CICP` 是镜像对自身固件的命名。`Mimas` 与 `Skye` 作为两个摄像头配置字符串出现。已观察；将其理解为两种硬件变体属于推断。摄像头初始化脚本 `init.hw.camera.rc` 与 `cameraserver.greatwhite.rc` 是 `system_ext/etc/init/` 中的用户空间文件（`data/userspace/init_rc_files.txt`）。

### 视频（`vpu20_4v.mbn`，Venus）

- `vpu20_4v.mbn`（2,079,528 字节）：Xtensa ELF，入口 `0xF500000`，20 个程序头，18 个可加载段。
- 字符串：`VenusSynx`、`VENUS is idle, no HW is running`、`venus_firmware.c`、`IPCC_OSVPU.c`。已观察。

`Venus` 是高通视频编解码模块的名称。文件名 `vpu20_4v` 是镜像对 VPU 2.0 核心（含四个视频单元）的命名。根据名称推断。

### 视觉（`evass.mbn`）

- `evass.mbn`（2,247,464 字节）：Xtensa ELF，入口 `0xF500000`，20 个程序头，18 个可加载段。其第一个段表与 `vpu20_4v.mbn` 一致，但两个文件约有 100 万字节不同。已观察。
- 字符串包括 `prevState_selectedAlignment`、`prevState_ageAlignment` 与 `prevState_ageSgm`。已观察。
- vendor 镜像中有 `etc/eva/facedetection/model3.dat`。已观察。

该镜像是为 Xtensa 与 XOS 构建的 `EVA` 固件（日志前缀 `EVA:`），通过 `HFI_CMD_SESSION_CVP_*` 会话命令驱动 CVP 硬件。已从字符串观察。其日志描述的是立体视觉与延迟重投影管线：左右眼的深度缓冲与 `EyeBufferReverseFences`，面向显示的 `LSR-DISPLAY-Forward` 与 `LSR-*-EYE-Forward` 栅栏（延迟重投影），`GainMap` 栅栏，`SKIPPING  SGM`（两个空格；用于深度的半全局匹配），`ConcealMB`（宏块隐藏），`Global Align Matrix` 与 `EVA_FW_ValidateDmmAlignmentControl`。跟踪阈值 `imageConfHighThreshold`、`enablingSgmMinAgeThreshold`、`imageToGyroMinAgeThreshold` 与 `gyroToImageMinAgeThreshold` 表明图像轨迹与陀螺仪对齐。`vendor/etc/eva/facedetection/model3.dat` 中的人脸检测模型属于同一管线。因此 `EVASS` 最好理解为用于深度、重投影与跟踪的视觉处理固件，人脸检测是其中一个客户端。根据字符串推断；`EVASS` 这一缩写本身不在文件中。

## 通用格式

ELF 镜像与第 05 节中高通远程处理器使用相同的段布局：一个带有 `.bNN` 段的 `.mdt` 头文件，或单个 `.mbn`。头文件列出每个段的物理地址与大小，加载器会将段与签名哈希进行核对。这是根据命名与 `.mdt` 头推断的；所检视的镜像中没有加载器代码。

## 未找到的内容

- GPU zap 着色器、摄像头与视频固件在内核或 TrustZone 镜像中的加载器。加载器名称见第 05 节与第 04 节，与这些文件的关联未确认。
- GPU、摄像头与视觉镜像的构建级别清单。未找到。
- `EVASS` 的展开含义。镜像中没有。镜像的功能已由日志字符串确定（见上），因此这是命名上的空缺，而非功能上的。

## 证据

- `data/remote/modem_verinfo.txt`
- `data/userspace/peripheral_firmware_headers.txt`
- `data/userspace/vendor_firmware_files.txt`
- `data/userspace/init_rc_files.txt`
- `data/android/kernel/config.txt`（GPU 与摄像头驱动选项）
