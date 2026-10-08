# 09 - Glasses software, the MCU, and the wrist band

[中文版](09-glasses-software-and-mcu.zh-CN.md)

This document covers the parts of the system that sit above the boot chain and beside the application processor. The main pieces are a secondary microcontroller (the MCU), the transport that links it to Android, the sensor and input HALs built on it, the electromyography (EMG) input path, and the app layer. The file counts here come from `data/userspace/`.

## The MCU

The glasses have a microcontroller that is separate from the SoC. Several HALs and kernel interfaces exist only to talk to it. The evidence:

- The `lpi_mcu_service` service (`odm/etc/init/vendor.meta.hardware.lpi_mcu-service.greatwhite.rc`, binary `odm/bin/hw/vendor.meta.hardware.lpi_mcu-service.greatwhite`) links 20 AIDL interface libraries; its init file and VINTF manifest declare 17 of them (`actionbutton`, `powerbutton` and `battery_provisioning` are linked but not declared). They are listed below. The count is from the service binary: 20 `vendor.meta.hardware.*` interface descriptors (the earlier draft said 17 and missed three).
- The `mcu-properties.sh` script in `vendor/bin` reads `/sys/devices/platform/soc/soc:meta,rt600_ctrl/is_rt600`. `meta,rt600_ctrl` is a device-tree overlay node in `dtbo.img` (fragment@15); the kernel driver is not in the tree. Its exact role is inferred from the name and from the trigger the init file writes to it.
- `vendor/firmware` holds `mcu.default.rt700.tub` and `mcu.core1.default.rt700.tub`. The `.tub` files are the MCU's own firmware. The MCU firmware is built for an RT700 platform: its sources include `arvr/firmware/lib/uhal/peripherals/rt700/*.c` and `platforms/greatwhite/rt700/mcu/bsp`, and it uses the ARM_CM33_NTZ port of FreeRTOS v10.4.6, found in the `.tub` files (not in `mcu_console_strings.txt`). The container does not name NXP or a MIMX part, so the RT700 identity is inferred from source paths. The `rt700` in the names is the processor platform, not only the audio codec. This corrects an earlier draft that called it an audio-codec variant.
- `odm/lib64/libmcu-vendor.so` is the vendor-side MCU library. It is on the ODM partition.

Verified from the files: the names, the paths, the init and property logic, and the MCU processor (Cortex-M33, from the FreeRTOS port path). The `.tub` payloads contain plain-text strings and code; the first 0xC000 bytes of `mcu.core1.default.rt700.tub` are high-entropy (6.6–7.1 bits per byte).

### Its AIDL interfaces

| Interface | Role (from the name) |
|---|---|
| `vendor.meta.hardware.button.actionbutton.IActionButton` | action button |
| `vendor.meta.hardware.button.capturebutton.ICaptureButton` | capture button |
| `vendor.meta.hardware.button.powerbutton.IPowerButton` | power button |
| `vendor.meta.hardware.button.powerslider.IPowerSlider` | power slider on the frame |
| `vendor.meta.hardware.captouch.ICaptouch` | capacitive touch |
| `vendor.meta.hardware.casestate.ICaseState` | state of the charging case |
| `vendor.meta.hardware.companionstate.ICompanionState` | state of the companion device (the phone or the band) |
| `vendor.meta.hardware.diagnostics.mcu.IMcuConnection` | diagnostics connection to the MCU |
| `vendor.meta.hardware.earcon.IEarcon` | audible cues |
| `vendor.meta.hardware.factoryreset.mcu.IFactoryReset` | factory reset |
| `vendor.meta.hardware.health.mcu.IHealth` | battery and health reporting from the MCU side |
| `vendor.meta.hardware.hinge.IHinge` | hinge state (folding frame) |
| `vendor.meta.hardware.light.notification.INotificationLight` | notification light |
| `vendor.meta.hardware.mount.IMount` | mount detection |
| `vendor.meta.hardware.power.mcu.IPower` | power control |
| `vendor.meta.hardware.sensor.als.IAls` | ambient light sensor |
| `vendor.meta.hardware.sensor.imu.IImu` | inertial sensor (accelerometer and gyroscope) |
| `vendor.meta.hardware.wakeword.IWakeword` | wake word |
| `vendor.meta.hardware.audionotification.IAudioNotification` | audio notifications |
| `vendor.meta.hardware.battery_provisioning.IBatteryProvisioning` | battery provisioning |

The names describe what the interface controls. Whether each one runs on the MCU or on the application processor is shown by the service that hosts it: the service binary links all 20 interface libraries, but its init file and VINTF manifest declare only 17 (not `actionbutton`, `powerbutton` or `battery_provisioning`), so only those 17 are registered as service instances. They are MCU-facing.

### The transport: STP

`system_ext/bin/stpService` (started by `system_ext/etc/init/stpService.rc`, class `main`, user `system`) talks to the MCU through `/dev/stp%d` device nodes (the palmvisionservice init comments name `/dev/stp25` and `/dev/stp27`). The `palmvisionservice` init file also refers to the STP service. The hyperoff feature uses it:

- `persist.vendor.meta.hyperoff.use_stp=true` is set by `mcu-properties.sh` on the RT700 configuration.
- `vendor.meta.stp_service.boot` and `vendor.meta.mcu_hal.stp_need_recovery` are the STP service's boot and recovery flags.

The init script has a recovery branch. When `vendor.meta.mcu_hal.stp_need_recovery` is set to 1, it waits five seconds to collect logs, writes `1` to `/sys/devices/platform/soc/soc:meta,rt600_ctrl/trigger_assert`, which asserts the MCU, and then clears the flag. The reboot line in the file is commented out, with a comment that it is only effective on greatwhite. Verified from the init file.

### Two hardware configurations: RT600 and RT700

`mcu-properties.sh` checks `is_rt600`:

- If the value is `0`, the device is the RT700 configuration. It sets `persist.vendor.meta.enable_hyperoff=true` and `persist.vendor.meta.hyperoff.use_stp=true`.
- Otherwise it is RT600. It sets nothing.

So the glasses come in two variants of the NXP RT600 and RT700 family (the DSP build contains `nxp_rt600` tool paths and `MIMXRT798S`, the RT700 part number; observed), and the software selects behaviour at boot. The overlays in `dtbo.img` also differ by component (section 04). The overlays contain `gpio_rt685_detect` and `rt700_bkup_disp_ctrl_high/low` nodes. No firmware file names appear in `dtbo.img`. Observed; the codec driver has not been read.

## EMG input (the wrist band)

The wrist band is an electromyography input device. Evidence from the files:

- `system_ext/etc/vintf/manifest/emg2_manifest.xml` declares the AIDL HAL `com.meta.wearable.emg` with interface `IEmgService`, instances `default` and `fmq` (fast message queue).
- `system_ext/lib64` contains `libemginput.so`, `libemg_quaternion_consumer.so` (orientation from the band), `libemg_device_status_consumer.so`, `libemg_state_sync_consumer.so`, `libemgcache.so`, `libemg_equeue.so`, `libemgserviceutils2.so` and `emgsdk-proto-cc.so`.
- The MCU firmware `mcu.default.rt700.tub` contains `/dev/Band`, `/dev/BandOff` and `/dev/PhoneDisconnected`, but these are not device nodes. They are icon paths in the MCU's UI resources: `./Resources/system/images/ic/432/sm/fl/dev/Band.png`, `BandOff.png` and `PhoneDisconnected.png`. So they name status icons (band connected, band off, phone disconnected). Observed. The earlier reading of them as a device was wrong.
- The exact string `/dev/PhoneDisconnected` appears only in the MCU firmware. The phone side has identifiers containing `PhoneDisconnected`: `onPhoneDisconnected` in `system_ext/bin/navigationservice`, and `renderPhoneDisconnectedIcon` in the OOBE and SystemUI packages. No shared device-node string supports a companion-state reading, so that reading is not made here.
- Init scripts `init.emgrelay_receiver.rc` and `init.emgrelaydatax.rc` start `emgrelay_receiver` and `emgrelaydatax`, gated by `system_ext.meta.mobileconfig.service.emgrelay.receiver.enable` and by the screencast-manager property.

The EMG data path has three parts, from the binaries' strings:

- `system_ext/bin/emgrelay_receiver` takes protobuf `EmgInferenceEvent` messages and injects them into the virtual EMG service (`com.meta.wearable.emg.sim.IVirtualEmgService`, with an `IVirtualEmgStreamControlCallback`). It logs `Failed to open channel to phone's EmgRelayReceiver service`, so it opens a channel to the phone side. Its registration message is `Companion scope available [uuid=...], registering DataX service`.
- `system_ext/bin/emgrelaydatax` serialises `EMGGestureEvent` messages (`EmgEventClient::onGestureDetected`) and sends them to the EMG service. It logs `Failed to connect EmgEventClient to EMG service`.
- `emg2` implements `IEmgService` and receives device data through its `fmq` instance.

So the band's signal reaches `emg2` through the `fmq` queue for real device data, and through the virtual service for injected inference events. The step from the MCU to the band data source is still not found in code. Observed from strings. Binaries: `system_ext/bin/emgrelay_receiver`, `system_ext/bin/emgrelaydatax`.

The EMG service path, observed in the extracted tree:

- `system_ext/bin/emg2` is the EMG service. It is started by `persist.vendor.meta.enable_emg=1` (`emg2.rc`). It implements `com.meta.wearable.emg.IEmgService` (manifest `emg2_manifest.xml`) with two instances, `default` and `fmq`.
- The `fmq` instance moves data through an AIDL message queue. `libemgfmq_helper.so` writes and reads `emg_fmq_packet_t` packets through `android.hardware.common.fmq` (`SynchronizedReadWriteEEEE`, `EventFlag`). Its messages cover the queue length and a corrupted read or write pointer.
- `libemginput.so` opens device nodes by a formatted name (`/dev/%s`) and also has `/dev/gpiochip%u` and `/dev/joycon0`. The format name is not resolved.
- Event names in `emg2`: `emg_raw_gesture_event`, `input_emg_raw_gesture_event`, `wearables_band_tightness_detector_events`.

The band is named **Uniband** in the code (`enable_uniband_partial_gestures`, `wearables_uniband_allowlist` in the mobile-config names; `Uniband Enable`, `Uniband Capabilities Query` in `libemginput.so`). The data path from the band to `emg2` is then:

- `system_ext/lib64/libatc_service.so` is a transport controller. Its strings cover BLE links, L2CAP listening and secure PSMs, peer IDs, companion BLE RSSI and transport sessions. The Uniband link is most likely a BLE/L2CAP transport handled here. This is inferred from the naming and the transport strings, not shown in code.
- `system_ext/lib64/libemginput.so` contains `WirelessInputDevice` and `WirelessInputDeviceControl`. They open a channel to the wireless input service, send capability and device-info requests, configure the connection type (`DIRECT_CONNECTION` or `Companion`), and queue `UnibandEvent` messages (`queueUnibandEvent`). The RPC messages are in the `com.oculus.wearableinputservice` protobuf package.
- `emg2` and its consumer libraries (`libemg_device_status_consumer.so`, `libemg_gesture_consumer.so`, `libemg_quaternion_consumer.so`) receive the decoded device state, battery, detector and band-tightness events.

Not shown in code: the radio-level transport that carries bytes between the band and `libatc_service`. Observed for the rest of the chain.

`libmarvin-emg.meta.so` and `libemg_marvin-client.meta.so` use the name "Marvin". It is probably an internal codename for the model or the client. Unverified.

## Firmware containers in the vendor partition

The files in `vendor/firmware` are containers, and each one holds named sub-images. The table lists the main sub-image names; the full list is in `data/userspace/tub_contents.txt`:

Structure, from `case.default.cabo.tub` and `mcu.core1.default.rt700.tub` (observed):

- The first bytes are the name of the sub-image, NUL-padded (`case.bin`, `core1.bin`).
- The payload comes first. A JSON manifest follows at the end of the file, `mcu.default` carries many embedded JSON objects (logger and telemetry dictionaries, from 0x715606) before its manifest; `mcu.core1` has one manifest.
- The manifest has `deployment_methods` (`["RPC"]` in `case.default.tub`, `["TBSP"]` in the MCU, DSP and core1 files, `["ISP"]` in `spl2`; full table in `data/userspace/tub_md5_tests.txt`), `md5`, `platform` (`greatwhite-rt700` in the core1 file), `target_assets` (each with `name`, `type`, `layout.offset`, and a `signature` in the core1 file; `layout.load_addr` is present for `app.bin`, `dumptruck.bin` and `core1.bin` but absent for `offload_assets_ro.bin` and `romfs.bin`) and `version`.
- `layout.offset` values (for example `134807552`, which is `0x8090000` (the `app.bin` entry in `mcu.default.rt700.tub`)) are larger than the file. They are load positions for the target, not file offsets.
- The manifest `md5` did not match any tested range. The same holds for `mcu.default.rt700.tub` (manifest md5 `8589b5e414f8352e39106fc3796ad050`): its `app.bin` entry has `offset` 134807552, which is beyond the 8.5 MB file, and the file prefixes up to its two manifest openings do not match. Starts tried: 0, 0x10, 0x20, 0x40, 0x80, 0x100, 0x200, 0x400, 0x1000. Ends tried: each JSON opening brace and end of file. The hashed bytes are therefore not in the file as stored, or they are compressed or encrypted. Unverified.
- The same test on `mcu.core1.default.rt700.tub` (manifest md5 `3d498ec201781cb20dcead30ca031032`, 88 KB) also found no match over any tested start and end, nor over the manifest JSON with or without its `md5` key. Its payload has no compression magic and entropy of 6.6–7.1 bits in its first 0xC000 bytes, which fits encryption but also fits raw Arm code; the encryption reading is not established. Evidence: `data/userspace/tub_md5_tests.txt`. The same range test on the smaller files (`case.default.tub`, `.cabo`, `.cocos`, `touch.default.tub`, `spl2.default.rt700.tub`) also found no match. `case.default.tub` and `case.default.lynx.tub` are byte-identical (same md5 `cd101cf1ed50caf9ca47bdfacc44084d`).

| Container | Size | Sub-image names |
|---|---:|---|
| `mcu.default.rt700.tub` | 8.5 MB | `app.bin`, `display_calibration.bin`, `display_wpc_coeff.bin`, `touch-app-b0.cyacd2`, `boot_data.bin`, `pmic_reset_info.bin`, and 28 more (see `data/userspace/tub_contents.txt`) |
| `mcu.core1.default.rt700.tub` | 88 KB | `core1.bin`, `debug_frame.bin` |
| `spl2.default.rt700.tub` | 573 KB | `app.recovery.bin`, `app.signed.bin`, `spl2.bin`, `core1.bin`, `dumptruck.bin`, `dsp_app.bin`, `dsp_dtcm.bin`, `dsp_itcm.bin`, `spl2_secure_table.bin` |
| `dsp.default.rt700.tub` | 4.4 MB | `dsp_dtcm.bin`, `dsp_itcm.bin`, `dsp_app.bin`, `assets_ro.bin` |
| `touch.default.tub` | 105 KB | `touch-app-b0.cyacd2` |
| `case.default.tub` (and `.cabo`, `.cocos`, `.lynx` variants) | 56–90 KB | `case.bin` |

What the names suggest (inferred):

- The MCU runs an application (`app.bin`) with a recovery image (`app.recovery.bin`) and a signed image. `spl2` is a second-stage loader that holds its own copies of the core and DSP images.
- The touch controller uses `.cyacd2` files. The Cypress (now Infineon) PSoC attribution is external knowledge, not from the files.
- The RT700 part has a HiFi4 DSP (the source file `system_MIMXRT798S_hifi4.c` is in the image), with separate instruction and data memory (`dsp_itcm.bin` and `dsp_dtcm.bin`). The DSP container is 4.4 MB. Section 16 describes the DSP firmware.
- Display calibration data is stored in the MCU container, next to `pmic_reset_info.bin`.

The `.tub` container format itself is not decoded. The names sit at fixed offsets (in the DSP file, for example, at `0x0`, `0x600` and `0x8A00`), but the header layout is not yet known.

## Sensor, power and input HALs

These run on the MCU through `lpi_mcu_service`, so their hardware is the glasses rather than the phone SoC:

- Motion: `vendor.meta.hardware.sensor.imu`, `sensor.als`, and `libmotionservicehw.so` in `system_ext`.
- Display: `/dev/display/mock_als` and `/dev/display/location_info` are strings in `vendor/lib64/hw/vendor.meta.sensors@2.0-impl.so`, and `location_info` also appears in `system_ext/lib64/liblocationservice.so`. The names point to an ambient-light path and a location path.
- Camera: `/dev/camfsync` appears in `odm/lib64/libmcu-vendor.so`, `vendor/etc/ueventd.rc` and the SELinux file contexts. The overlays also have `oculus,cam_fsync`. A frame-sync signal between the cameras is the likely use. Inferred.
- Accessory authentication: `vendor/bin/hw/vendor.meta.hardware.mfi@1.0-service` uses `/dev/mfi-i2c`, and `ueventd.rc` sets its permissions. The `mfi343s00176` part is in the overlays (section 04).
- Battery: `init.metasoc.sh` writes the state of charge and a voltage alert to a `max17332-battery` power-supply node. The script's branch that does this runs only when the device name is `hammerhead`, so on `greatwhite` the branch is skipped. The name `hammerhead` is, from external knowledge, the code of another phone; the script is shared. Observed from the script.
- Time: `vendor.meta.hardware.time-service` binary.

## The app layer

`system_ext` and `product` carry 32 app packages named `Smartglass*Release`. The list has 66 entries: each of the 32 packages ships as both `.apk` and `.odex` (64 entries), plus `WindowManager-SplashScreen-Smartglasses-Res.apk` and `services.smartglass.odex` (`data/userspace/smartglass_apps.txt`). Examples from the list (`data/userspace/smartglass_apps.txt`): `SmartglassAccounts`, `SmartglassAiHistory`, `SmartglassAudioDataCollection`, `SmartglassBrowser`, `SmartglassCapture`, `SmartglassCommshub`, `SmartglassFiles`, `SmartglassGallery`, `SmartglassHandwritingPrototype`, `SmartglassInstagram`, `SmartglassLiveStream`, `SmartglassNabuPrompter`, `SmartglassNavigation`, `SmartglassOOBE`, `SmartglassPhone`, `SmartglassSensorLogger`, `SmartglassSettings`, `SmartglassSystemUI`, `SmartglassTalkback`, and games such as `SmartglassFallingWordsGame` and `SmartglassGame2048`.

Examples from the list: `SmartglassAccounts`, `SmartglassAiHistory`, `SmartglassAudioDataCollection`, `SmartglassBrowser`, `SmartglassCapture`, `SmartglassCommshub`, `SmartglassFiles`, `SmartglassGallery`, `SmartglassHandwritingPrototype`, `SmartglassInstagram`, `SmartglassLiveStream`, `SmartglassNabuPrompter`, `SmartglassNavigation`, `SmartglassOOBE`, `SmartglassPhone`, `SmartglassSensorLogger`, `SmartglassSettings`, `SmartglassSystemUI`, `SmartglassTalkback`, and the games `SmartglassFallingWordsGame` and `SmartglassGame2048`.

Also in `system_ext`: `MetaConstellationStateSDK.odex`, `DisplayOffloadManager.odex`, and a set of `com.meta.wearable.*` services.

The `Smartglass` prefix is the app family name for the glasses, observed in the package names.

## Init scripts and properties

- `data/userspace/init_rc_files.txt` lists the 163 `.rc` files found.
- The vendor properties relevant to the MCU are `persist.vendor.meta.enable_hyperoff`, `persist.vendor.meta.hyperoff.use_stp`, `vendor.meta.mcu_hal.stp_need_recovery`, `vendor.meta.stp_service.boot`, and `system_ext.meta.mobileconfig.service.emgrelay.receiver.enable`.
- `mobileconfig` properties turn services on and off. They appear in many `on property:` triggers. The mobile config is the server-side switch for features.

## Build references

- `odm/bin/hw_sync_timing.sh` says "Blueshark" in its header: "HW Sync Timing Analysis Script for Blueshark". It parses `gpio_mirror` lines in `dmesg`. So "Blueshark" is a product or project name that appears in the image. Observed.
- The copyright line in that script is "Meta Platforms, Inc. and affiliates. Confidential and proprietary". It is not used beyond noting the source.
