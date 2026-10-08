# 12 - Audio

[中文](12-audio.zh-CN.md)

This section covers the audio stack in the vendor partition: the Android audio HAL and its service, the Qualcomm audio layer below it, the sound-card and low-power-audio (LPI) paths, the speaker and microphone hardware the configuration describes, and the ACDB calibration data. The configuration files are in `vendor/etc/` of the OTA. Counts come from parsing those XML files; the hashes and the summary are in `data/android/audio/`.

Status labels: observed means read directly from a file; inferred means a reasonable reading that the files do not state; not found means the item is not in the OTA.

## Stack, from the bottom

From the library and service names in `vendor/lib64`, `vendor/bin` and `vendor/etc/init` (observed). The order is inferred from the names.

1. **Hardware and transport.** The LPASS audio block (`lpass-cdc` macros, SoundWire masters, LPI pinctrl, TDM and MI2S links). Described in the device tree below.
2. **ALSA-style driver and sound card.** The ASoC machine driver is `qcom,waipio-asoc-snd` in the device tree. Its card definition is in `card-defs.xml`.
3. **AGM (audio graph manager).** `libagm.so`, `libagmmixer.so`, `libagmclient.so`, the `libagm_*_plugin.so` plugins, and the `vendor.qti.hardware.AGMIPC@1.0` HIDL interface.
4. **PAL (platform audio layer).** `libar-pal.so`, `libpalclient.so`, the HIDL `vendor.qti.hardware.pal@1.0`, plus the Bluetooth and FM PAL libraries (`libbtsinkpal.so`, `libbtachatpal.so`, `libhfppal.so`, `libfmpal.so`).
5. **ACDB (calibration database).** `libar-acdb.so` and the calibration files in `acdbdata/` (below).
6. **Audio HAL.** `vendor/bin/hw/android.hardware.audio.service`, started as `vendor.audio-hal`. The `vendor/lib64` directory holds the `android.hardware.audio@x.0` interface libraries for versions 2.0, 4.0, 5.0, 6.0 and 7.0 (observed as files); which version the service exports is not checked.
7. **Side services.** `low_power_audio_service` (LPI audio, `libaoclpi-vendor.so`, `libaoclpiservice-vendor.so`, and `aoclpi_aidl`), `vendor.audioadsprpcd_audiopd` (`audioadsprpcd`, the FastRPC daemon for the ADSP), and `captureengineservice`.

The Bluetooth audio path is separate: `android.hardware.bluetooth.audio@2.0` and `@2.1`, `btaudio_offload_if.so`, and `libbluetooth_audio_session_qti.so`. Observed.

## Sound card and the LPASS

The device tree (`data/android/vendor_ramdisk/vendor_dtb_dump.txt`) gives these nodes. Observed.

- Sound card compatible: `qcom,waipio-asoc-snd`, under `/soc/spf_core_platform/sound`.
- LPASS platform compatible: `qcom,neo-lpass`. The platform name is `neo` (section 04, `ro.board.platform=neo`).
- Codec macros: `rx-macro@3200000`, `wsa-macro@3240000`, `wsa2-macro@31E0000` and `va-macro@33F0000`, each with a SoundWire master (`rx_swr_master`, `wsa_swr_master`, `wsa2_swr_master`, `va_swr_master`). The device tree also lists four SoundWire controllers, `swr0` to `swr3`.
- LPI pinctrl at `0x3440000` with the SoundWire clock and data pins (`tx_swr_*`, `rx_swr_*`, `wsa_swr_*`, `wsa2_swr_*`) and TDM pins (`quat_tdm_ws`, `quat_tdm_sd3`).
- Two clock votes, `vote_lpass_audio_hw` and `vote_lpass_core_hw`, and a `lpass_audio_hw_vote` property.

The card definition in `card-defs.xml` is one card, id 100, name `waipiovirtualsndcard`, with 25 PCM device entries. Observed. The name `waipiovirtualsndcard` shows the card is virtual at the card-definition level; the mapping to real hardware is in the backend and mixer files below. The meaning of `waipio` as a codename is not established here.

## Backends

`backend_conf.xml` has 40 `device` entries. Each names a back-end port with a rate, channel count and bit depth. Observed. The names group by link type:

- Codec DMA (LPAIF): `CODEC_DMA-LPAIF_WSA-RX-0`, `-RX-1`, `CODEC_DMA-LPAIF_WSA-TX-0`, `CODEC_DMA-LPAIF_VA-TX-0`, `-TX-1`, `CODEC_DMA-LPAIF_RXTX-RX-0`, `-TX-3`.
- MI2S (LPAIF): primary, tertiary and the `AUD`, `AXI`, `RXTX`, `VA`, `WSA` variants.
- TDM (LPAIF): primary and tertiary, with a `TDM-LPAIF-RX-TERTIARY-VIRT-0` virtual entry.
- SLIMbus: `SLIM-DEV1-RX-0` and `SLIM-DEV1-TX-0`.
- `DISPLAY_PORT-RX` (HDMI or DisplayPort audio) and `USB_AUDIO-RX` / `USB_AUDIO-TX`.

## Mixer paths and the codec

`audio/sku_neo/mixer_paths_neo_idp_sg.xml` (107,044 bytes) has 1,253 `path` blocks and 477 `ctl` elements. Observed. The control prefixes show the codec blocks:

| Prefix | ctl count | Block |
|---|---:|---|
| `TX` | 142 | Capture (TX macro) |
| `VA` | 92 | Voice activation |
| `WSA`, `WSA2` | 45, 10 | Speaker amplifier macros |
| `RX` | 43 | Playback (RX macro) |
| `IIR0` | 27 | IIR filter |
| `ADC2`, `ADC3`, `ADC4`, `ADC1` | 21, 4, 4, 3 | Analogue-to-digital converters |
| `SpkrLeft`, `SpkrRight` | 15, 9 | Speaker outputs |
| `HPHL`, `HPHR` | 9, 7 | Headphone outputs |
| `LPI` | 6 | LPI controls |

The names are the Qualcomm WCD-style codec macros (`RX_MACRO`, `TX_MACRO`, `VA_MACRO`, `WSA_MACRO`). The chip family behind them is inferred from the names. Not confirmed from a codec ID.

### Speakers

The FTM test configuration for the IDP build shows the speaker path directly (`data/android/audio/ftm_test_config_neo-idp-sg-snd-card`). Observed:

- Two channels, `#Left Speaker` and `#Right Speaker`. The playback key is `gkv_rx:PCM_LL_PLAYBACK-SPEAKER-INSTANCE1-DEVICEPP_RX_DEFAULT`, back end `CODEC_DMA-LPAIF_WSA-RX-0`, and PCM id 100.
- Enable steps set `WSA2 RX0 MUX` to `AIF1_PB`, route `WSA2_RX0 INP0` to `RX0`, turn on `WSA2_COMP1`, `SpkrLeft COMP`, `SpkrLeft VISENSE`, and `SpkrLeft SWR DAC_Port`, and set `WSA2_RX0 Digital Volume` to 78.
- `VISENSE` is the voltage-and-current sense path that the amplifier uses for feedback. The name is observed; its function is inferred from the name.

### Microphones

`microphone_characteristics.xml` (671 bytes) maps six microphone channels to positions. Observed:

| Channel | Position |
|---:|---:|
| 0 | 0 |
| 1 | 3 |
| 2 | 4 |
| 3 | 1 |
| 4 | 2 |
| 5 | 5 |

The device names in `resourcemanager_neo_idp_sg.xml` name the microphone uses. Observed: `handset-mic`, `handset-dmic-endfire`, `speaker-dmic-endfire`, `speaker-mic`, `headset-mic`, `headset-va-mic` and `va-mic` (voice activation), `quad-mic`, `ext_ec_ref_tx` (echo-cancellation reference), `ultrasound-mic` and `ultrasound-handset`, and four `unprocessed-hdr-mic-*` variants (landscape, portrait and their inverted forms). The `hdr` and `landscape` variants suggest the device captures from several microphones in fixed orientations. Inferred from the names.

The device naming covers 33 distinct `snd_device_name` values. Observed.

## Routing: resource manager and use cases

`audio/sku_neo/resourcemanager_neo_idp_sg.xml` (55,347 bytes) has 51 `usecase` blocks. Each is a PAL stream type: low latency, deep buffer, ultra-low latency, VoIP TX and RX, voice call, ultrasound, loopback, proxy, raw. Observed. It also has the parameter groups for volume, low-power mode, gapless playback, voice and sound-trigger platform info.

`usecaseKvManager.xml` (65,071 bytes) holds 283 `graph_kv` entries. Each maps a use case and device to an AGM graph key. Observed. The FTM example above uses one of them.

`audio_policy_volumes.xml` (13,160 bytes) has 70 volume curves for 14 Android stream types: accessibility, alarm, assistant, Bluetooth SCO, DTMF, enforced audible, music, notification, patch, rerouting, ring, system, TTS and voice call. Observed. `default_volume_tables.xml` (5,133 bytes) holds reference volume points.

## Audio policy

The Android audio policy is split across these files (`data/android/audio/audio_config_summary.txt`):

- `audio_policy_configuration.xml` (36,732 bytes, version 7.0) has two modules. `primary` has 25 mix ports, 24 device ports and 29 routes. `usb` has one of each. Observed.
- `audio/sku_neo/audio_policy_configuration.xml` is identical to the top-level file (same SHA-256). Observed. `audio/sku_neo_qssi/audio_policy_configuration.xml` has the same two modules, with the same version. Observed.
- `a2dp_audio_policy_configuration.xml`, `bluetooth_qti_audio_policy_configuration.xml` and `bluetooth_qti_hearing_aid_audio_policy_configuration.xml` for Bluetooth. `usb_audio_policy_configuration.xml` for USB audio. `r_submix_audio_policy_configuration.xml` for the remote-submix device.

The primary module's device ports cover: earpiece, speaker, wired headset and headphone, line out, Bluetooth SCO (headset and car kit), Bluetooth A2DP (headphones and speaker), telephony TX and RX, AUX digital, proxy, FM tuner, USB device and headset, USB accessory, built-in mic, back mic, wired headset mic, and USB mic. Observed.

## Effects

`audio_effects.xml` (10,931 bytes) lists 14 effects and 13 libraries. Observed.

- Volume and listener effects: `volume` (bundle), `music_helper`, `ring_helper`, `alarm_helper`, `voice_helper` and `notification_helper` (volume listeners).
- Processing: `downmix`, `loudness_enhancer`, `dynamics_processing`, `hw_acc` (offload bundle, `libqcompostprocbundle.so`), `reverb`, `visualizer` in software and hardware forms (`libqcomvisualizer.so`).
- Pre-processing: `aec` and `ns` (`libqcomvoiceprocessing.so`), and `capture_audio_preproc` (`libcaptureaudiopreproc.so`).
- `audiosphere` (`libasphere.so`). The name is observed; its function is not confirmed here.

## Calibration (ACDB)

`acdbdata/neo_idp_sg/` holds two files (observed):

- `IDP_neo_sg_acdb_cal.acdb` (1,469,406 bytes), the calibration database that `libar-acdb.so` loads.
- `IDP_neo_sg_workspaceFileXml.qwsp` (660,048 bytes), the workspace file for the calibration tool.

`audio/hw_info.xml` (5,185 bytes) is the only hardware-info file. The SKU directories are `audio/sku_neo` and `audio/sku_neo_qssi`. The calibration file names carry the `IDP` (reference board) and `neo_sg` tags. The binary calibration tables are not decoded here.

## Test configurations

Three FTM (factory test) configurations exist, one per sound-card configuration (observed):

- `ftm_test_config_neo-idp-sg-snd-card` (3,114 bytes): the speaker path shown above.
- `ftm_test_config_neo-idp-snd-card` (8,364 bytes).
- `ftm_test_config_neo-qxr-snd-card` (5,729 bytes).

The `qxr` suffix is a different board variant. Which device uses which file is inferred from the names; the build selection is not in the OTA.

## Relation to other sections

- The RT600 and RT700 variants in section 09 change the codec path. The audio policy and the mixer files here are for the `neo` SKU; the RT variant differences are not decoded in them.
- The `low_power_audio_service` and the LPI links are the audio side of the MCU path described in section 09.
- The ADSP firmware that the audio libraries call through FastRPC is in the modem partition (section 05). The link is through `audioadsprpcd`; the firmware itself is not described here.

## What is not found

- The codec firmware or the codec ID register. Not in the OTA.
- The ADSP audio firmware loaded by `audioadsprpcd`, beyond the segment files described in section 05.
- The compiled audio HAL source or the policy engine. The XML and the binaries are the only record.
- A device-side audio log.

## Evidence

- `data/android/audio/audio_config_summary.txt`: counts, hashes and the device-port list.
- `data/android/audio/card-defs.xml`, `backend_conf.xml`, `audio_effects.xml`, `microphone_characteristics.xml`, `hw_info.xml`: copies of the smaller configuration files.
- `data/android/audio/ftm_test_config_*`: the three FTM configurations.
- `data/android/vendor_ramdisk/vendor_dtb_dump.txt`: the sound and LPASS nodes.
- `data/userspace/init_rc_files.txt`: the audio init services.
