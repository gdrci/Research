# 08 - Peripheral firmware and build IDs

[中文](08-peripheral-firmware-and-build-ids.zh-CN.md)

This section covers two things that the other sections do not: the build identifiers the OTA records for each subsystem, and the firmware for the GPU, camera, video and vision blocks that sits in `vendor/firmware`. Each claim is marked as observed, inferred, or not found.

## Build identifiers

`modem.img` contains `/verinfo/ver_info.txt` (`data/remote/modem_verinfo.txt`). It is a JSON build manifest. Observed:

| Key | Value |
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

The metabuild is `Aurora.LA.2.0-00101-STD.PROD-1.149279.2`, with product flavour `asic` and a timestamp of `2026-06-01 12:36:15`.

What the manifest tells us:

- The `Aurora` name is the SoC codename used in section 00. The `LA` tag is the Qualcomm Linux Android base line.
- Several subsystem builds share the `1.149279` tag (`common`, `boot`), so they probably come from one release train. Inferred.
- The `btfm` entry (`00819`) does not match the Bluetooth image's own version file (`00797`). The patch banner inside the image says `00797`, so the image is that build and `00819` is a different build (section 07).
- The `apps_vendor` entry is `LA.VENDOR.12.2`, while the vendor partition is Android 12 (section 04). This matches the older Treble base described there.

The manifest is the only build-level record found in the OTA. The other images do not have the same kind of record. Not found.

## Peripheral firmware in `vendor/firmware`

The `vendor/firmware` directory has 42 entries (`data/userspace/vendor_firmware_files.txt`). Nine are `.tub` containers for the glasses MCU, sensors and audio, covered in section 09. The rest are listed below. Headers were read with pyelftools and the raw files were read directly (`data/userspace/peripheral_firmware_headers.txt`).

Two firmware formats appear:

- Qualcomm split ELF: a `.mdt` header file plus numbered segment files (`.b00`, `.b01`...), and a `.mbn` file that holds the whole image. Each segment is loaded by the remote-processor loader. Observed from the file names and the ELF headers.
- Raw microcode or GMU firmware with no ELF header.

### GPU (Adreno)

- `a620_zap.mdt`, `a620_zap.b00`–`b02`, `a620_zap.mbn`: a zap shader for the a620 class. The `.mbn` is 14,328 bytes.
- `a740v3_zap.mdt`, `a740v3_zap.b00`–`b02`, `a740v3_zap.elf`, `a740v3_zap.mbn`: a zap shader for the a740 class.
- `a650_sqe.fw` (31,988 bytes) and `a740v3_sqe.fw` (76,852 bytes): SQE (command-stream) microcode. Raw, no header.
- `a621_gmu.bin` (56,056 bytes) and `gmu_gen70200.bin` (67,608 bytes): GMU firmware. Both start with the words `0x0, 0x0, 0x1, 0x1dc, 0x4000`, which looks like a common header. Inferred.

The zap ELF headers say `e_machine = EM_QDSP6` (Hexagon), entry `0x1000`, and one loadable segment at `0x1000` with flags RWX (`0x8000007`). Observed. The Adreno driver loads the zap through the kernel's zap-shader path (`adreno_zap_shader_load` and `a6xx_zap_shader_init` in `msm.ko`, `kgsl_zap_shader_load` in `msm_kgsl`). Observed as symbol names. Inferred: the Qualcomm peripheral-authentication path loads these ELF files, and the Hexagon machine type is the value that path expects in the header. The zap then runs on the GPU side.

The `a740v3_zap.mbn` and `a620_zap.mbn` files carry the signing blocks. They include the strings `SECTOOLS SECP384R1 CURVE TEST ROOT01` and `General Use Test Key 0 (for testing only)`. Observed. Test-root strings in a shipped signed image show that the signing structure is present, but the chain to a production root is not checked here.

The GPU driver `msm_kgsl.ko` reads the speed-bin fuse cell (section 06). Inferred: the firmware files are loaded through the kernel GPU driver and the zap mechanism, but the loader code is not in the images examined.

### Camera image co-processor (`CAMERA_ICP`)

- `CAMERA_ICP.mdt` (7,724 bytes) and `CAMERA_ICP.mbn` (949,080 bytes): an Xtensa ELF with entry `0x0`, 21 program headers and 19 loadable segments.
- Segment files `CAMERA_ICP.b00` to `b20`. The largest is `b08` (866,156 bytes).
- Strings in the image: `QC_IMAGE_VERSION_STRING=CICP.FW.5.0-00020`, `CAMERA_640_V1 (Mimas)`, `CAMERA_740_V1 (Skye)`, and a source path `Z:/b/fw_core/Common/DbgUtils/src/icpdiag.c`. Observed.

`CICP` is the image's own name for the firmware. The `Mimas` and `Skye` names appear as two camera-configuration strings. Observed; the reading as hardware variants is inferred. The kernel side of the camera is in `init.hw.camera.rc` and `cameraserver.greatwhite.rc` (`data/userspace/init_rc_files.txt`).

### Video (`vpu20_4v.mbn`, Venus)

- `vpu20_4v.mbn` (2,079,528 bytes): an Xtensa ELF with entry `0xF500000`, 20 program headers and 18 loadable segments.
- Strings: `VenusSynx`, `VENUS is idle, no HW is running`, `venus_firmware.c`, `IPCC_OSVPU.c`. Observed.

The `Venus` name is the Qualcomm video codec block. The file name `vpu20_4v` is the image's name for the VPU 2.0 core with four video units. Inferred from the name.

### Vision (`evass.mbn`)

- `evass.mbn` (2,247,464 bytes): an Xtensa ELF with entry `0xF500000`, 20 program headers and 18 loadable segments. Its first segment table matches `vpu20_4v.mbn`, but the two files differ in about 1 million bytes. Observed.
- Strings include `facedetection`, `prevState_selectedAlignment`, `prevState_ageAlignment` and `prevState_ageSgm`. Observed.
- The vendor image has `etc/eva/facedetection/model3.dat`. Observed.

The image is an `EVA` firmware (the `EVA:` log prefix) built for Xtensa with XOS, and it drives the CVP hardware through `HFI_CMD_SESSION_CVP_*` session commands. Observed from the strings. Its log messages describe a stereo vision and late-stage reprojection pipeline: depth buffers and `EyeBufferReverseFences` for the left and right eyes, `LSR-DISPLAY-Forward` and `LSR-*-EYE-Forward` fences (late-stage reprojection to the display), `GainMap` fences, `SKIPPING SGM` (semi-global matching for depth), `ConcealMB` (macroblock concealment), `Global Align Matrix` and `EVA_FW_ValidateDmmAlignmentControl`. The tracking thresholds `imageConfHighThreshold`, `enablingSgmMinAgeThreshold`, `imageToGyroMinAgeThreshold` and `gyroToImageMinAgeThreshold` show that image tracks are aligned with the gyroscope. The face-detection model in `vendor/etc/eva/facedetection/model3.dat` belongs to the same pipeline. So `EVASS` is best read as the vision-processing firmware for depth, reprojection and tracking, with face detection as one client. Inferred from the strings; the expansion of `EVASS` itself is not in the files.

## Common format

The ELF images use the same segment layout as the Qualcomm remote processors in section 05: a `.mdt` header with `.bNN` segments, or a single `.mbn`. The header files list each segment's physical address and size, and the loader checks the segments against the signed hash. This is inferred from the naming and the `.mdt` headers; the loader code is not in the images examined.

## What is not found

- The loader for the GPU zap shader and the camera and video firmware in the kernel or the TrustZone image. The loader names are in section 05 and section 04; the link to these files is not confirmed.
- A build-level manifest for the GPU, camera and vision images. Not found.
- The expansion of `EVASS`. Not in the images. The function of the image is identified from the log strings (above), so this is a naming gap, not a functional one.

## Evidence

- `data/remote/modem_verinfo.txt`
- `data/userspace/peripheral_firmware_headers.txt`
- `data/userspace/vendor_firmware_files.txt`
- `data/userspace/init_rc_files.txt`
- `data/android/kernel/config.txt` (for the GPU and camera driver options)
