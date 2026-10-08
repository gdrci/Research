# 15 - 音频 DSP 固件（RT700 HiFi4）

[English](15-audio-dsp-firmware.md)

本节记录 `vendor/firmware/dsp.default.rt700.tub`，即眼镜 NXP RT700 芯片上音频 DSP 的固件。它是第 12 节从 Android 一侧描述的音频协议栈的处理端。容器内的符号表列出约 4,600 个函数，因此下文大部分内容依据函数名称观察得出。完整符号列表见 `data/dsp/dsp_symbol_table.txt`，清单与子镜像表见 `data/dsp/`。

状态标注：已观察表示直接从文件读取；推断表示文件未明说但合理的解读；未找到表示该内容不在 OTA 中。

## 身份

- 内核与工具链：DSP 为 Cadence Xtensa 内核（符号表 ELF 中为 `EM_XTENSA`）。构建树中写有 `nxp_rt600_RI2021_6_newlib`（Xtensa RI-2021.6 工具链），源文件 `system_MIMXRT798S_hifi4.c` 写明型号为 MIMXRT798S，即 RT700 的 HiFi4 系统。已观察。因此 RT700 芯片在 Cortex-M33 MCU（第 14 节）旁边还有一个 HiFi4 DSP。
- RTOS：XOS（Cadence 为 Xtensa 设计的 RTOS），其中 `xos_*` 函数负责线程、队列、信号量、互斥量与时钟中断。源头文件为 `xos.h`，版本 `2.0.9`。已观察。
- 平台路径：`arvr/firmware/projects/smartglasses/platforms/greatwhite/rt700/dsp/`，与 MCU 为同一平台树。已观察。
- 应用：`arvr/firmware/projects/smartglasses/apps/dsp/app.c`。已观察。
- 清单：`platform` 为 `greatwhite-rt700`，部署方式 `TBSP`，清单 `md5` 为 `869a093ac9348d5b476eeafb4a910ab0`（第 09 节有 md5 测试）。已观察。

## 容器布局

容器大小为 4,429,312 字节。其子镜像见 `data/dsp/dsp_tub_subimages.txt`：

| 子镜像 | 偏移 | 作用（依据名称与清单） |
|---|---:|---|
| `dsp_dtcm.bin` | `0x000000` | 数据紧耦合存储器镜像，加载地址 `0x24000000`（清单 `load_addr` 为 `603979776`） |
| `dsp_itcm.bin` | `0x000600` | 指令紧耦合存储器镜像，加载地址 `0x24020000` |
| `dsp_app.bin` | `0x008A00` | 应用代码，加载地址 `0x20100000` |
| `configs.cfg`、`overrides.cfg` | `0x01E4FD`、`0x01E509` | 运行时配置（`overrides.cfg` 名称表明存在按设备覆盖的一层） |
| `assets_ro.bin` | `0x0F8A00` | 只读资源（清单中无加载地址） |
| `logger_dict_generated.json`、`zephyr_log_dict_generated.json`、`tel_dict_generated.json` | `0x37CC00` 至 `0x3B0C00` | 日志与遥测字典 |
| `symbol_table.elf` | `0x3C1400`（ELF 位于 `0x3C1600`） | 符号表，`EM_XTENSA` ELF，含 6,799 个具名符号、4,602 个函数 |
| `metadata.json` | `0x438800` | 清单（部署、`md5`、`target_assets`，每项含 `layout.load_addr`、`layout.offset` 与 64 字节 `signature`） |

清单为每个代码与数据资源给出 64 字节签名，以 128 个十六进制字符表示。`offset` 值是闪存布局中的位置，而非文件偏移，与第 09 节相同。三个存储器镜像相隔 64 KB（`140378112`、`140443648`、`140509184`）。已观察。这些偏移所基于的闪存基址未确定。

子镜像名称与符号表在文件中都是明文。DSP 固件未加密，与 MCU tub 相同（第 14 节）。

## 依据函数名称得出的音频功能

函数名称按下列功能分组。计数来自符号表（`data/dsp/dsp_symbol_table.txt`）。每项功能都依据名称观察得出，其行为为推断。

### 唤醒词

- 约 33 个函数。例如：`ww_status_init`、`xra_enable_wakeword`、`xra_set_ww_jarvis`、`xra_ww_publish_preroll_data_internal`、`xra_log_metrics_from_ww_header`，以及 `Xr2Messager::sendWakewordEnabled`。
- 遥测变量名包括 `dsp_ww_decision`、`ww_detect`、`ww_detect_status`、`ww_label_id`、`ww_mode`、`ww_trans_mode` 与 `ww_uuid`。已观察。
- `decline_ww_detect_event`、`set_ww_detected_flag` 与 `set_ww_reset_flag` 显示了事件路径。已观察。
- 预缓冲区保留触发之前的音频（`xra_ww_publish_preroll_data_internal`）。根据名称推断。
- 符号名中有 `KwsComponent::checkSideTalk`。KWS 即关键词检测，side talk 指检查语音是否是对设备说的。根据名称推断。
- 存在一套"small"自定义唤醒词配置：`sgXraCustomWwSmallSetDefault` 与 `sgXraCustomWwSmallGetDefault`。已观察。

### 听力

- 约 34 个函数。例如：`xra_usecase_enable_hearing_setup`、`xra_set_hearing_feature`、`publish_hearing_histograms`、`capture_hearing_output_data_cb`、`Xr2Messager::getHearingVolume`，以及 `sgXr2QueryHearingHistogramsStub`。
- 遥测名包括 `hearing_frames_processed`、`hearing_session_id`、`hearing_setup`、`hearing_cycles`、`hearing_mode_changed`、`hearing_health_audio_metrics` 与 `no_hearing_metrics`。已观察。
- 听力路径会把直方图发布给 Android 一侧。依据名称观察得出。其用途（听力辅助还是听力健康）为推断；遥测名 `hearing_health_audio_hist` 表明是健康读数。

### 扬声器保护与扬声器模型

- 扬声器模型位于 `meta::audio` 与 `facebook::xr::audio` C++ 框架中，表现为 `speaker_system_id` 模板族及其参数标签。
- 扬声器模型的参数名存在：`Bdt`、`Adt`、`A1`、`A2`、`Zeta`、`F0`、`Reb`、`Bl`（反电动势与电机常数）、`SigMax`、`AlphaMean`、`AlphaVar`、`OptMu`、`Lambda`、`DownsamplingRatio`、`TriggerHoldFrames`、`ReleaseHoldFrames`、`WaterIngressDetected`、`RunAlgoEnabled`、`AccumulatedEnergyThreshold`、`StabilityConstraintMode`、`TempCompEnabled`、`TempRef`、`TempCoeffAlpha`、`Rtref`、`TempTarget`，以及拟合系数 `RebFitCoeffs`、`BlFitCoeffs`、`A1FitCoeffs`、`A2FitCoeffs`、`F0FitCoeffs`、`ZetaFitCoeffs`。已观察。
- 这些参数描述一个限制振膜位移的扬声器保护模型，带有温度补偿与进水检测标志。根据名称推断。`SpeakerSystemID` 模板及 `Mechanical`、`Time` 常数表明模型按扬声器拟合。推断。

### 扬声器功放 I/O

- 约 29 个函数涉及功放缓冲区与调试引脚：`amp_tx_get_next_buffer`、`xra_amp_rx_get_next_buffer`、`debug_pin_set_amp_tx`、`debug_pin_clear_amp_rx`，以及 `amp_buffer_underrun` 计数。已观察。
- 功放 TX 与 RX 使能是遥测字段：`amp_tx_en`、`amp_rx_en`、`amp_tx_checked_in`、`amp_rx_checked_in`。已观察。它们分别是扬声器功放的反馈（RX）与驱动（TX）通路，与第 12 节中 WSA2 的 `VISENSE` 通路相符。根据名称推断。

### 麦克风（DMIC/PDM）

- 约 96 个函数：`dmic_pdm_start`、`dmic_pdm_buffer_callback`、`dmic_get_buffer_ptr_callback`、`dmic_trigger_next_roller`、`xra_dmics_set_dmic_clk_rate`、`xra_get_dmic_pwr_save_clk_gk_en`、`get_dmic_loopback_buffer_pingpong`、`copy_pdm_mic_data_to_scratch_buffer`。已观察。
- 遥测显示 `dmic_checkin_errors`、`dmic_dma_channel`、`dmic_submit`、`dmic_pdm_stop`，以及 `dmici2s`（支持 I2S 的 DMIC）。已观察。麦克风数量与映射（`mic_id_0` 至 `mic_id_7`、`num_mics`）按板型设置；第 12 节列出了同一麦克风映射的 Android 一侧。
- 麦克风的 ESD 检测：`esd_detection_on_mic1` 与 `esd_detection_on_mic2`。已观察。

### 坏麦克风检测与 ESD

- `badmic_num_frames_analyzed` 与 `badmic_num_frames_detected` 表明存在按帧计数的坏麦克风检测器。已观察。还有 `mic_mute_frames` 计数。推断：检测器会静音或标记故障麦克风。
- `module_audio_xra_set_amps_esd_detection`、`esd_detect_and_output_mute_stats`、`mdc_control_amps_esd_detection_status` 与 `mdc_control_mics_esd_detection_status`。已观察。这里的 ESD 指功放与麦克风上的静电放电检测，根据命名与静音统计推断。

### TDM 与 I2S

- 约 52 个函数：`tdm_start`、`tdm_pause`、`tdm_init`、`tdm_halt_info`、`tdm_edma_dump`、`tdm_rx_transfer_callback`、`tdm_tx_transfer_callback`、`SAI_RxEDMACallback`、`SAI_TxEDMACallback`，以及 PDM 与 EDMA 辅助函数。已观察。
- 遥测名 `tdm_instance`、`tdm_frame_count`、`tdm_halt`、`tdm_actions_status` 与 `set_tdm_ready_flag`。已观察。它们是通向编解码器的 TDM 链路（第 12 节的 `LPAIF` TDM 后端）。
- `xra_speech_send_frame_over_tdm` 通过 TDM 发送语音帧。已观察。这是从 DSP 到电话侧或编解码器通路的链路。

### 声音处理组件

`meta::xr::sonic` 命名空间，以及 mixer 与 render 相关名称（约 1,140 个匹配名，多为模板实例），构成处理图。在符号中观察到的具名组件：

- `GreatwhiteControlComponent`：本设备的控制组件。
- `WolaSynthesisComponent`：加权重叠相加（WOLA）合成滤波器组，是低延迟音频常用的滤波器组设计。根据名称推断。
- `DownSamplerComponent`：采样率降低。
- `SbAdaptiveVolumeComponent`：自适应音量。名称中的 `Sb` 前缀未被解释。
- `KwsComponent`：关键词检测（见唤醒词）。
- `xraThreadMain`：`sonic` 处理的主线程。

以上为符号名称的观察结果。其算法不以可读文本形式存在于文件中。

### 发往应用处理器的消息

`Xr2Messager` 暴露了 DSP 发往 Android 一侧的消息：`sendWakewordEnabled`、`sendSpatialImuEnabled`、`sendAvcGainAdjEnabled`、`getAvcMinGain`、`getHearingVolume`。已观察。`AVC` 即自动音量控制，根据名称推断。`SpatialIMU` 表明 DSP 使用 IMU 做空间音频（第 14 节记录了 IMU）。根据名称推断。

DSP 还会把遥测转发给 MCU：`_relay_telemetry_to_mcu`。已观察。因此 DSP、MCU 与手机各自保存自己的遥测。

## 控制台与 tesser

DSP 运行一个名为 `tesser` 的模块框架（约 125 个函数）：`tesser_module_create`、`tesser_module_handle_pipe`、`tesser_module_update_state`、`tesser_module_blocking_command_callback`、`tesser_console_help_cmd_handler`、`tesser_console_parse_args`，以及日志器（`tesser_logger_log_text`、`tesser_logger_metrics_adjust_logs_dropped_buffer_full`）。已观察。控制台帮助处理函数给出命令名；完整列表在符号表与 `diags` 源路径（`arvr/firmware/lib/tesser/diags/`）中。配置区域中也有 `LoggerIndexCorrupted` 消息。已观察。

`sml`（样本内存层）相关函数 `tesser_module_sml_runner_create` 运行音频图。根据名称推断。

## 与其他章节的关系

- 第 12 节描述 Android 一侧：后端、混音器路径、扬声器与麦克风配置。DSP 固件实现了这些路由背后的处理。
- 第 14 节描述 MCU，它与 DSP 共享 RT700 平台树，并转发 DSP 遥测。
- 第 16 节描述调制解调器分区中的 ADSP 与 CDSP，它们是另外的处理器（Hexagon）。此处的 DSP 是 RT700 上的 HiFi4。

## 未找到的内容

- 超出名称之外的算法可读代码。文件中只有符号与机器码，此处未解码机器码。
- 扬声器模型的拟合值与每台设备的校准数据。它们在设备上或配置文件中，不在 OTA 的 DSP 容器中。
- 唤醒词模型权重与听力模型。只有参数名存在。
- 超出 `2.0.9` 的 XOS 版本历史。

## 证据

- `data/dsp/dsp_symbol_table.txt`：全部 6,799 个具名符号，附地址、大小与类型。
- `data/dsp/dsp_tub_manifest.json`：DSP 清单（部署、md5、平台、资源布局与签名）。
- `data/dsp/dsp_tub_subimages.txt`：子镜像表，附偏移与文件哈希。
- `data/userspace/init_rc_files.txt` 与 `data/android/audio/audio_config_summary.txt`：本固件运行所在的 Android 音频配置（第 12 节）。
