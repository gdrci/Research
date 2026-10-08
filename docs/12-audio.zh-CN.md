# 12 - 音频

[English](12-audio.md)

本节记录厂商分区中的音频协议栈：Android 音频 HAL 及其服务、其下的高通音频层、声卡与低功耗音频（LPI）路径、配置所描述的扬声器与麦克风硬件，以及 ACDB 校准数据。配置文件位于 OTA 的 `vendor/etc/` 中。计数来自解析这些 XML 文件；哈希与摘要位于 `data/android/audio/`。

状态标注：已观察表示直接从文件读取；推断表示文件未明说但合理的解读；未找到表示该内容不在 OTA 中。

## 协议栈，自底向上

依据 `vendor/lib64`、`vendor/bin` 与 `vendor/etc/init` 中的库名与服务名（已观察）。各层次的顺序为推断。

1. **硬件与传输。** LPASS 音频模块（`lpass-cdc` 宏、SoundWire 主控、LPI pinctrl、TDM 与 MI2S 链路）。见下文设备树。
2. **ALSA 风格驱动与声卡。** ASoC 机器驱动在设备树中为 `qcom,waipio-asoc-snd`。其卡定义位于 `card-defs.xml`。
3. **AGM（音频图管理器）。** `libagm.so`、`libagmmixer.so`、`libagmclient.so`、`libagm_*_plugin.so` 插件，以及 `vendor.qti.hardware.AGMIPC@1.0` HIDL 接口。
4. **PAL（平台音频层）。** `libar-pal.so`、`libpalclient.so`、HIDL `vendor.qti.hardware.pal@1.0`，以及蓝牙与 FM 的 PAL 库（`libbtsinkpal.so`、`libbtachatpal.so`、`libhfppal.so`、`libfmpal.so`）。
5. **ACDB（校准数据库）。** `libar-acdb.so` 与 `acdbdata/` 中的校准文件（见下文）。
6. **音频 HAL。** `vendor/bin/hw/android.hardware.audio.service`，以 `vendor.audio-hal` 启动。`vendor/lib64` 中有 `android.hardware.audio@x.0` 接口库，版本为 2.0、4.0、5.0、6.0 和 7.0（已观察为文件）；服务导出哪个版本未检查。
7. **辅助服务。** `low_power_audio_service`（LPI 音频，`libaoclpi-vendor.so`、`libaoclpiservice-vendor.so` 与 `aoclpi_aidl`）、`vendor.audioadsprpcd_audiopd`（`audioadsprpcd`，ADSP 的 FastRPC 守护进程），以及 `captureengineservice`。

蓝牙音频路径独立：`android.hardware.bluetooth.audio@2.0` 与 `@2.1`、`btaudio_offload_if.so` 以及 `libbluetooth_audio_session_qti.so`。已观察。

## 声卡与 LPASS

设备树（`data/android/vendor_ramdisk/vendor_dtb_dump.txt`）中的节点如下。已观察。

- 声卡兼容字符串：`qcom,waipio-asoc-snd`，位于 `/soc/spf_core_platform/sound` 下。
- LPASS 平台兼容字符串：`qcom,neo-lpass`。平台名为 `neo`（第 04 节，`ro.board.platform=neo`）。
- 编解码宏：`rx-macro@3200000`、`wsa-macro@3240000`、`wsa2-macro@31E0000` 与 `va-macro@33F0000`，各自带有一个 SoundWire 主控（`rx_swr_master`、`wsa_swr_master`、`wsa2_swr_master`、`va_swr_master`）。设备树另列出四个 SoundWire 控制器 `swr0` 至 `swr3`。
- LPI pinctrl 位于 `0x3440000`，包含 SoundWire 时钟与数据引脚（`tx_swr_*`、`rx_swr_*`、`wsa_swr_*`、`wsa2_swr_*`）以及 TDM 引脚（`quat_tdm_ws`、`quat_tdm_sd3`）。
- 两个时钟投票节点 `vote_lpass_audio_hw` 与 `vote_lpass_core_hw`，以及属性 `lpass_audio_hw_vote`。

`card-defs.xml` 中只有一张卡：id 100，名称 `waipiovirtualsndcard`，含 25 个 PCM 设备条目。已观察。名称 `waipiovirtualsndcard` 表明在卡定义层面该卡是虚拟的；与真实硬件的映射在下面的后端与混音器文件中。`waipio` 作为代号的含义此处未确定。

## 后端

`backend_conf.xml` 有 40 个 `device` 条目。每个条目命名一个后端端口，并给出采样率、声道数与位深。已观察。名称按链路类型分组：

- 编解码 DMA（LPAIF）：`CODEC_DMA-LPAIF_WSA-RX-0`、`-RX-1`，`CODEC_DMA-LPAIF_WSA-TX-0`，`CODEC_DMA-LPAIF_VA-TX-0`、`-TX-1`，`CODEC_DMA-LPAIF_RXTX-RX-0`、`-TX-3`。
- MI2S（LPAIF）：primary、tertiary，以及 `AUD`、`AXI`、`RXTX`、`VA`、`WSA` 变体。
- TDM（LPAIF）：primary 与 tertiary，并有虚拟条目 `TDM-LPAIF-RX-TERTIARY-VIRT-0`。
- SLIMbus：`SLIM-DEV1-RX-0` 与 `SLIM-DEV1-TX-0`。
- `DISPLAY_PORT-RX`（HDMI 或 DisplayPort 音频），以及 `USB_AUDIO-RX` / `USB_AUDIO-TX`。

## 混音器路径与编解码器

`audio/sku_neo/mixer_paths_neo_idp_sg.xml`（107,044 字节）含 1,253 个 `path` 块与 477 个 `ctl` 元素。已观察。控制项前缀显示了编解码模块：

| 前缀 | ctl 数量 | 模块 |
|---|---:|---|
| `TX` | 142 | 采集（TX 宏） |
| `VA` | 92 | 语音唤醒 |
| `WSA`、`WSA2` | 45、10 | 扬声器功放宏 |
| `RX` | 43 | 播放（RX 宏） |
| `IIR0` | 27 | IIR 滤波器 |
| `ADC2`、`ADC3`、`ADC4`、`ADC1` | 21、4、4、3 | 模数转换器 |
| `SpkrLeft`、`SpkrRight` | 15、9 | 扬声器输出 |
| `HPHL`、`HPHR` | 9、7 | 耳机输出 |
| `LPI` | 6 | LPI 控制 |

这些名称是高通 WCD 风格的编解码宏（`RX_MACRO`、`TX_MACRO`、`VA_MACRO`、`WSA_MACRO`）。其背后的芯片系列是根据名称推断的，未经编解码器 ID 寄存器确认。

### 扬声器

IDP 版本的 FTM（工厂测试）配置直接展示了扬声器路径（`data/android/audio/ftm_test_config_neo-idp-sg-snd-card`）。已观察：

- 两个声道：`#Left Speaker` 与 `#Right Speaker`。播放键为 `gkv_rx:PCM_LL_PLAYBACK-SPEAKER-INSTANCE1-DEVICEPP_RX_DEFAULT`，后端为 `CODEC_DMA-LPAIF_WSA-RX-0`，PCM id 为 100。
- 使能步骤把 `WSA2 RX0 MUX` 设为 `AIF1_PB`，将 `WSA2_RX0 INP0` 接到 `RX0`，打开 `WSA2_COMP1`、`SpkrLeft COMP`、`SpkrLeft VISENSE` 与 `SpkrLeft SWR DAC_Port`，并把 `WSA2_RX0 Digital Volume` 设为 78。
- `VISENSE` 是功放用于反馈的电压与电流检测通路。名称已观察；其功能根据名称推断。

### 麦克风

`microphone_characteristics.xml`（671 字节）把六个麦克风声道映射到位置。已观察：

| 声道 | 位置 |
|---:|---:|
| 0 | 0 |
| 1 | 3 |
| 2 | 4 |
| 3 | 1 |
| 4 | 2 |
| 5 | 5 |

`resourcemanager_neo_idp_sg.xml` 中的设备名说明了麦克风的用途。已观察：`handset-mic`、`handset-dmic-endfire`、`speaker-dmic-endfire`、`speaker-mic`、`headset-mic`、`headset-va-mic` 与 `va-mic`（语音唤醒）、`quad-mic`、`ext_ec_ref_tx`（回声消除参考）、`ultrasound-mic` 与 `ultrasound-handset`，以及四个 `unprocessed-hdr-mic-*` 变体（横屏、竖屏及其反向形式）。`hdr` 与 `landscape` 变体表明设备在固定朝向下从多个麦克风采集。根据名称推断。

设备命名涵盖 33 个不同的 `snd_device_name` 值。已观察。

## 路由：资源管理器与用例

`audio/sku_neo/resourcemanager_neo_idp_sg.xml`（55,347 字节）含 51 个 `usecase` 块。每个块对应一种 PAL 流类型：低延迟、深缓冲、超低延迟、VoIP 发送与接收、语音通话、超声、回环、代理、原始。已观察。文件还包含音量、低功耗模式、无缝播放、语音与唤醒平台信息的参数组。

`usecaseKvManager.xml`（65,071 字节）含 283 个 `graph_kv` 条目。每个条目把用例与设备映射到 AGM 图键。已观察。上面的 FTM 示例就用到其中一个。

`audio_policy_volumes.xml`（13,160 字节）含 70 条音量曲线，覆盖 14 种 Android 流类型：无障碍、闹钟、助手、蓝牙 SCO、DTMF、强制可闻、音乐、通知、patch、重路由、铃声、系统、TTS 与通话。已观察。`default_volume_tables.xml`（5,133 字节）含参考音量点。

## 音频策略

Android 音频策略分布在以下文件中（`data/android/audio/audio_config_summary.txt`）：

- `audio_policy_configuration.xml`（36,732 字节，版本 7.0）含两个模块。`primary` 有 25 个混音端口、24 个设备端口与 29 条路由。`usb` 各只有一个。已观察。
- `audio/sku_neo/audio_policy_configuration.xml` 与顶层文件完全相同（SHA-256 一致）。已观察。`audio/sku_neo_qssi/audio_policy_configuration.xml` 含相同的两个模块与相同版本。已观察。
- `a2dp_audio_policy_configuration.xml`、`bluetooth_qti_audio_policy_configuration.xml` 与 `bluetooth_qti_hearing_aid_audio_policy_configuration.xml` 用于蓝牙；`usb_audio_policy_configuration.xml` 用于 USB 音频；`r_submix_audio_policy_configuration.xml` 用于远程子混音设备。

primary 模块的设备端口包括：听筒、扬声器、有线耳机与耳机、线路输出、蓝牙 SCO（耳机与车载套件）、蓝牙 A2DP（耳机与扬声器）、电话 TX 与 RX、AUX 数字输出、代理、FM 调谐器、USB 设备与耳机、USB 配件、内置麦克风、后置麦克风、有线耳机麦克风与 USB 麦克风。已观察。

## 音效

`audio_effects.xml`（10,931 字节）列出 14 个音效与 13 个库。已观察。

- 音量与监听类：`volume`（bundle）、`music_helper`、`ring_helper`、`alarm_helper`、`voice_helper` 与 `notification_helper`（音量监听器）。
- 处理类：`downmix`、`loudness_enhancer`、`dynamics_processing`、`hw_acc`（卸载 bundle，`libqcompostprocbundle.so`）、`reverb`，以及软件与硬件形式的 `visualizer`（`libqcomvisualizer.so`）。
- 预处理类：`aec` 与 `ns`（`libqcomvoiceprocessing.so`），以及 `capture_audio_preproc`（`libcaptureaudiopreproc.so`）。
- `audiosphere`（`libasphere.so`）。名称已观察；其功能此处未确认。

## 校准（ACDB）

`acdbdata/neo_idp_sg/` 含两个文件（已观察）：

- `IDP_neo_sg_acdb_cal.acdb`（1,469,406 字节），即 `libar-acdb.so` 加载的校准数据库。
- `IDP_neo_sg_workspaceFileXml.qwsp`（660,048 字节），校准工具的工作区文件。

`audio/hw_info.xml`（5,185 字节）是唯一的硬件信息文件，SKU 目录为 `audio/sku_neo` 与 `audio/sku_neo_qssi`。校准文件名带有 `IDP`（参考板）与 `neo_sg` 标记。二进制校准表此处未解码。

## 测试配置

每种声卡配置各有一个 FTM（工厂测试）配置，共三个（已观察）：

- `ftm_test_config_neo-idp-sg-snd-card`（3,114 字节）：即上文所示的扬声器路径。
- `ftm_test_config_neo-idp-snd-card`（8,364 字节）。
- `ftm_test_config_neo-qxr-snd-card`（5,729 字节）。

`qxr` 后缀表示另一种板型变体。哪个设备使用哪个文件是根据文件名推断的；构建时的选择不在 OTA 中。

## 与其他章节的关系

- 第 09 节的 RT600 与 RT700 变体会改变编解码路径。此处的音频策略与混音器文件适用于 `neo` SKU；RT 变体的差异在这些文件中未解码。
- `low_power_audio_service` 与 LPI 链路是第 09 节所述 MCU 路径的音频一侧。
- 音频库通过 FastRPC 调用的 ADSP 固件位于 modem 分区中（第 05 节）。连接通过 `audioadsprpcd` 完成；固件本身此处未描述。

## 未找到的内容

- 编解码器固件或编解码器 ID 寄存器。不在 OTA 中。
- `audioadsprpcd` 加载的 ADSP 音频固件，超出第 05 节所述的段文件之外的部分。
- 编译后的音频 HAL 源码或策略引擎。XML 与二进制文件是唯一记录。
- 设备端的音频日志。

## 证据

- `data/android/audio/audio_config_summary.txt`：计数、哈希与设备端口列表。
- `data/android/audio/card-defs.xml`、`backend_conf.xml`、`audio_effects.xml`、`microphone_characteristics.xml`、`hw_info.xml`：较小配置文件的副本。
- `data/android/audio/ftm_test_config_*`：三个 FTM 配置。
- `data/android/vendor_ramdisk/vendor_dtb_dump.txt`：声音与 LPASS 节点。
- `data/userspace/init_rc_files.txt`：音频 init 服务。
