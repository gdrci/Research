# 16 - Audio DSP firmware (RT700 HiFi4)

[中文](15-audio-dsp-firmware.zh-CN.md)

This section covers `vendor/firmware/dsp.default.rt700.tub`, the firmware for the audio DSP on the glasses' NXP RT700 part. It is the processing side of the audio stack that section 12 describes from the Android side. The symbol table inside the container names about 4,600 functions, so most of the content below is observed from names. The full symbol list is in `data/dsp/dsp_symbol_table.txt`, and the manifest and sub-image table are in `data/dsp/`.

Status labels: observed means read from the file; inferred means a reasonable reading the file does not state; not found means not in the OTA.

## Identity

- Core and toolchain: the DSP is a Cadence Xtensa core (`EM_XTENSA` in the symbol-table ELF). The build tree names `nxp_rt600_RI2021_6_newlib` (an Xtensa RI-2021.6 toolchain), and the source `system_MIMXRT798S_hifi4.c` names the MIMXRT798S part, which is the RT700 HiFi4 system. Observed. The RT700 part therefore has a HiFi4 DSP next to its Cortex-M33 MCU (section 14).
- RTOS: XOS (Cadence's RTOS for Xtensa), with `xos_*` functions for threads, queues, semaphores, mutexes and the tick handler. The source header is `xos.h` with version `2.0.9`. Observed.
- Platform path: `arvr/firmware/projects/smartglasses/platforms/greatwhite/rt700/dsp/`, the same platform tree as the MCU. Observed.
- Application: `arvr/firmware/projects/smartglasses/apps/dsp/app.c`. Observed.
- Manifest: `platform` is `greatwhite-rt700`, deployment method `TBSP`, and the manifest `md5` is `869a093ac9348d5b476eeafb4a910ab0` (section 09 has the md5 test). Observed.

## Container layout

The container is 4,429,312 bytes. Its sub-images (`data/dsp/dsp_tub_subimages.txt`):

| Sub-image | Offset | Role (from the name and the manifest) |
|---|---:|---|
| `dsp_dtcm.bin` | `0x000000` | Data tightly-coupled memory image, loaded at `0x24000000` (manifest `load_addr` `603979776`) |
| `dsp_itcm.bin` | `0x000600` | Instruction tightly-coupled memory image, loaded at `0x24020000` |
| `dsp_app.bin` | `0x008A00` | Application code, loaded at `0x20100000` |
| `configs.cfg`, `overrides.cfg` | `0x01E4FD`, `0x01E509` | Runtime configuration (the `overrides.cfg` name suggests the per-device override layer) |
| `assets_ro.bin` | `0x0F8A00` | Read-only assets (no load address in the manifest) |
| `logger_dict_generated.json`, `zephyr_log_dict_generated.json`, `tel_dict_generated.json` | `0x37CC00` to `0x3B0C00` | Log and telemetry dictionaries |
| `symbol_table.elf` | `0x3C1400` (ELF at `0x3C1600`) | The symbol table, an `EM_XTENSA` ELF with 6,799 named symbols and 4,602 functions |
| `metadata.json` | `0x438800` | Manifest (deployment, `md5`, `target_assets` with `layout.load_addr`, `layout.offset` and a 64-byte `signature` per asset) |

The manifest gives each code and data asset a 64-byte signature, written as 128 hex characters. The `offset` values are positions in a flash layout, not file offsets, as in section 09. The three memory images are placed 64 KB apart (`140378112`, `140443648`, `140509184`). Observed. The flash base for those offsets is not established.

The sub-image names and the symbol table are plain text in the file. The DSP firmware is not encrypted, the same as the MCU tub (section 14).

## Audio features, from the function names

The function names group into the features below. The counts are from the symbol table (`data/dsp/dsp_symbol_table.txt`). Each feature is observed from the names. Their behaviour is inferred.

### Wake word

- About 33 functions. Examples: `ww_status_init`, `xra_enable_wakeword`, `xra_set_ww_jarvis`, `xra_ww_publish_preroll_data_internal`, `xra_log_metrics_from_ww_header`, and `Xr2Messager::sendWakewordEnabled`.
- The telemetry variable names include `dsp_ww_decision`, `ww_detect`, `ww_detect_status`, `ww_label_id`, `ww_mode`, `ww_trans_mode` and `ww_uuid`. Observed in the telemetry dictionaries.
- `decline_ww_detect_event`, `set_ww_detected_flag` and `set_ww_reset_flag` show the event path. Observed.
- A pre-roll buffer keeps audio from before the trigger (`xra_ww_publish_preroll_data_internal`). Inferred from the name.
- `KwsComponent::checkSideTalk` appears in the symbol names. KWS is keyword spotting, and side talk is a check that the speech is directed at the device. Inferred from the names.
- A "small" custom wake-word configuration exists: `sgXraCustomWwSmallSetDefault` and `sgXraCustomWwSmallGetDefault`. Observed.

### Hearing

- About 34 functions. Examples: `xra_usecase_enable_hearing_setup`, `xra_set_hearing_feature`, `publish_hearing_histograms`, `capture_hearing_output_data_cb`, `Xr2Messager::getHearingVolume`, and `sgXr2QueryHearingHistogramsStub`.
- The telemetry names include `hearing_frames_processed`, `hearing_session_id`, `hearing_setup`, `hearing_cycles`, `hearing_mode_changed`, `hearing_health_audio_metrics` and `no_hearing_metrics`.
- The hearing path publishes histograms to the Android side. Observed from the names. The purpose (hearing assistance, or hearing health) is inferred. The telemetry name `hearing_health_audio_hist` suggests the health reading.

### Speaker protection and speaker model

- The speaker model is in the `meta::audio` and `facebook::xr::audio` C++ framework, as the `speaker_system_id` template family and its parameter tags.
- The parameter names of the speaker model are present: `Bdt`, `Adt`, `A1`, `A2`, `Zeta`, `F0`, `Reb`, `Bl` (back-EMF and motor constants), `SigMax`, `AlphaMean`, `AlphaVar`, `OptMu`, `Lambda`, `DownsamplingRatio`, `TriggerHoldFrames`, `ReleaseHoldFrames`, `WaterIngressDetected`, `RunAlgoEnabled`, `AccumulatedEnergyThreshold`, `StabilityConstraintMode`, `TempCompEnabled`, `TempRef`, `TempCoeffAlpha`, `Rtref`, `TempTarget`, and the fit coefficients `RebFitCoeffs`, `BlFitCoeffs`, `A1FitCoeffs`, `A2FitCoeffs`, `F0FitCoeffs`, `ZetaFitCoeffs`. Observed.
- These parameters describe an excursion-limiting speaker protection model, with temperature compensation and a water-ingress detection flag. Inferred from the names. The `SpeakerSystemID` template and the `Mechanical` and `Time` constants suggest the model is fitted per speaker. Inferred.
- `speaker_system_id` also appears as the parameter tag family. Observed.

### Speaker amplifier I/O

- About 29 functions for amplifier buffers and debug pins: `amp_tx_get_next_buffer`, `xra_amp_rx_get_next_buffer`, `debug_pin_set_amp_tx`, `debug_pin_clear_amp_rx`, and the `amp_buffer_underrun` counter. Observed.
- The amplifier TX and RX enables are telemetry fields: `amp_tx_en`, `amp_rx_en`, `amp_tx_checked_in`, `amp_rx_checked_in`. Observed. These are the feedback (RX) and drive (TX) paths for the speaker amplifiers, matching the WSA2 `VISENSE` path in section 12. Inferred from the names.

### Microphones (DMIC/PDM)

- About 96 functions: `dmic_pdm_start`, `dmic_pdm_buffer_callback`, `dmic_get_buffer_ptr_callback`, `dmic_trigger_next_roller`, `xra_dmics_set_dmic_clk_rate`, `xra_get_dmic_pwr_save_clk_gk_en`, `get_dmic_loopback_buffer_pingpong`, `copy_pdm_mic_data_to_scratch_buffer`. Observed.
- The telemetry shows `dmic_checkin_errors`, `dmic_dma_channel`, `dmic_submit`, `dmic_pdm_stop`, and `dmici2s` (the I2S-capable DMIC). Observed. The microphone count and mapping (`mic_id_0` to `mic_id_7`, `num_mics`) are set per board; section 12 lists the Android side of the same microphone map.
- ESD detection on the microphones: `esd_detection_on_mic1` and `esd_detection_on_mic2`. Observed.

### Bad-microphone detection and ESD

- `badmic_num_frames_analyzed` and `badmic_num_frames_detected` show a bad-microphone detector that counts frames. Observed. A `mic_mute_frames` counter exists too. Inferred: the detector mutes or flags a failing microphone.
- `module_audio_xra_set_amps_esd_detection`, `esd_detect_and_output_mute_stats`, `mdc_control_amps_esd_detection_status` and `mdc_control_mics_esd_detection_status`. Observed. ESD here means electrostatic-discharge detection on the amplifiers and microphones, inferred from the naming and the mute statistics.

### TDM and I2S

- About 52 functions: `tdm_start`, `tdm_pause`, `tdm_init`, `tdm_halt_info`, `tdm_edma_dump`, `tdm_rx_transfer_callback`, `tdm_tx_transfer_callback`, `SAI_RxEDMACallback`, `SAI_TxEDMACallback`, `PDM` and `EDMA` helpers. Observed.
- The telemetry names `tdm_instance`, `tdm_frame_count`, `tdm_halt`, `tdm_actions_status` and `set_tdm_ready_flag`. Observed. These are the TDM links to the codec (the `LPAIF` TDM backends in section 12).
- `xra_speech_send_frame_over_tdm` sends speech frames over TDM. Observed. This is the link from the DSP to the phone-side or codec path.

### Sound processing components

The `meta::xr::sonic` namespace and the mixer and render names (about 1,140 matching names, mostly template instances) contain the processing graph. Named components observed in the symbols:

- `GreatwhiteControlComponent`: the control component for this device.
- `WolaSynthesisComponent`: a weighted-overlap-add synthesis filter bank. WOLA is the usual filter-bank design for low-delay audio. Inferred from the name.
- `DownSamplerComponent`: sample-rate reduction.
- `SbAdaptiveVolumeComponent`: adaptive volume. The `Sb` prefix is not explained by the names.
- `KwsComponent`: keyword spotting (see wake word).
- `xraThreadMain`: the main thread of the `sonic` processing.

Observed as symbol names. Their algorithms are not in the file as text.

### Messages to the application processor

`Xr2Messager` exposes the messages the DSP sends to the Android side: `sendWakewordEnabled`, `sendSpatialImuEnabled`, `sendAvcGainAdjEnabled`, `getAvcMinGain`, `getHearingVolume`. Observed. `AVC` is automatic volume control, inferred from the name. `SpatialIMU` shows that the DSP uses the IMU for spatial audio (section 14 names the IMU). Inferred from the name.

The DSP also relays telemetry to the MCU: `_relay_telemetry_to_mcu`. Observed. So the DSP, the MCU and the phone each keep their own telemetry.

## Console and tesser

The DSP runs a module framework named `tesser` (about 125 functions): `tesser_module_create`, `tesser_module_handle_pipe`, `tesser_module_update_state`, `tesser_module_blocking_command_callback`, `tesser_console_help_cmd_handler`, `tesser_console_parse_args`, and the logger (`tesser_logger_log_text`, `tesser_logger_metrics_adjust_logs_dropped_buffer_full`). Observed. The console help handler names the commands; their list is in the symbol table and the `diags` source path (`arvr/firmware/lib/tesser/diags/`). The `LoggerIndexCorrupted` message is also in the configs area. Observed.

The `sml` (sample memory layer) functions, `tesser_module_sml_runner_create`, run the audio graphs. Inferred from the name.

## Relation to other sections

- Section 12 describes the Android side: the backends, the mixer paths, and the speaker and microphone configurations. The DSP firmware implements the processing behind those routes.
- Section 15 describes the MCU, which shares the RT700 platform tree and relays DSP telemetry.
- Section 17 describes the ADSP and CDSP, which are different processors (Hexagon) in the modem partition. The DSP here is a HiFi4 on the RT700.

## What is not found

- The algorithm code as readable text, beyond the names. Only the symbols and the machine code are present, and the machine code is not decoded here.
- The speaker-model fit values and the per-unit calibration. Those are in the device or in the configuration files, not in the OTA's DSP container.
- The keyword model weights and the hearing model. Only their parameter names are present.
- The XOS version history beyond `2.0.9`.

## Evidence

- `data/dsp/dsp_symbol_table.txt`: all 6,799 named symbols with address, size and type.
- `data/dsp/dsp_tub_manifest.json`: the DSP manifest (deployment, md5, platform, asset layouts and signatures).
- `data/dsp/dsp_tub_subimages.txt`: the sub-image table with offsets and the file hash.
- `data/userspace/init_rc_files.txt` and `data/android/audio/audio_config_summary.txt`: the Android audio configuration this firmware runs under (section 12).
