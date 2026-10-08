# 11 - SELinux 与厂商策略

[English](11-selinux-and-vendor-policy.md)

本节记录厂商分区中随附的 SELinux 策略，以及将名称映射到标签的文件：服务、HIDL 服务、属性与文件上下文，还有应用侧的 `seapp_contexts`、`mac_permissions.xml` 与拒绝元数据。文件位于 OTA 的 `vendor/etc/selinux/` 中。下文所有计数均取自这些文件；扫描脚本未保留。摘要与哈希见 `data/android/selinux/policy_summary.txt`。

## 范围与版本

- `plat_sepolicy_vers.txt` 为 `32.0`，即平台策略版本。已观察。
- CIL 名称带有版本后缀：`init_32_0`、`hwservicemanager_32_0`、`servicemanager_32_0`、`system_server_32_0`、`tee_32_0`。厂商策略针对平台 32.0 编译。已观察。
- Android 12 是厂商基线（第 04 节）。厂商 `build.prop` 设置 `ro.vendor.build.version.release=12`、`ro.vendor.build.version.sdk=32` 与 `ro.vndk.version=32`，因此平台策略 32.0 与厂商 SDK 级别 32 相符。SDK 32 对应 Android 12L 的名称来自 AOSP 发布历史，而非这些文件。

厂商策略叠加在平台策略之上。`plat_pub_versioned.cil`（13,860 行，1.0 MB）是 32.0 版本的平台公共策略，厂商策略不能与之冲突。其内容此处未解码。已作为文件观察。

## vendor_sepolicy.cil

该文件为 507,018 字节，5,325 行 CIL。顶层形式计数如下：

| 形式 | 数量 | 含义 |
|---|---:|---|
| `allow` | 3,136 | 允许的访问 |
| `type` | 631 | 声明的类型 |
| `roletype` | 631 | 每个类型对应的角色 |
| `typeattributeset` | 241 | 属性成员关系 |
| `genfscon` | 211 | `sysfs`（205）与 `proc`（6）路径的标签 |
| `dontaudit` | 161 | 被抑制的拒绝日志 |
| `typetransition` | 147 | 新对象的自动标签（144 条解析为四个字段；3 条为五个字段） |
| `neverallow` | 82 | 编译期禁令 |
| `typeattribute` | 64 | 属性声明 |
| `allowx` | 17 | 扩展权限允许 |
| `expandtypeattribute` | 3 | 属性展开 |

在 631 个类型中，258 个以 `vendor_` 开头，175 个以 `hal_` 开头，71 个以 `sysfs` 开头。已观察。

### 最大的 allow 来源

`init`（443 条规则）、`vendor_qti_init_shell`（130）、`vendor_init`（101）、`hwservicemanager`（97）、`hal_oculus_sensors`（82）、`hal_power_default`（73）、`hal_audio_default`（70）、`autobrightness`（59）、`tee`（55）、`vendor_hal_perf_default`（48）、`servicemanager`（47）、`system_server`（46）、`vndservicemanager`（43）、`hal_graphics_composer_default`（42）、`mediacodec`（41）。已观察。这些来源显示厂商策略最宽的部分：init 域、传感器 HAL、电源与音频 HAL，以及 TEE。

### 域的模式

每个 HAL 都有一对域，例如 `hal_audio_default` 与 `hal_audio_default_exec`。`_exec` 类型标记可执行文件，`init` 在执行时通过 `typetransition` 切换到该域：

    typetransition init_32_0 hal_audio_default_exec process hal_audio_default

在 144 条四个参数的 `typetransition` 规则中，132 条以 `init_32_0` 为起点。这 132 条都转换到名称含 `exec` 的进程类型：其中 128 条以 `_exec` 结尾，3 条以 `_exec_32_0` 结尾，1 条为 `postprocess_exec_file`。其余 12 条规则为 `postprocess_init`（5）、`vendor_rfs_access`（2）、`hal_graphics_allocator_default` 与 `hal_graphics_composer_default` 的 tmpfs 转换（各 1）、`init-systemstart-sh` 到 `bootstat_exec_32_0`（1）、`vendor_timeservice_app` 的 tmpfs（1），以及 `shell_32_0` 到 `wattsup_exec`（1）。已观察。

### Oculus 与 Meta 域

Meta 与 Oculus 的域是策略中最具特征的部分。类型列表包括：

- `hal_oculus_backlight`、`hal_oculus_battery`、`hal_oculus_bluetooth`、`hal_oculus_catty_default`、`hal_oculus_devicecert`、`hal_oculus_display`、`hal_oculus_dock`、`hal_oculus_keyboxinstaller`、`hal_oculus_lcos`、`hal_oculus_remotethermal`、`hal_oculus_sensors`、`hal_oculus_sensors_iad`、`hal_oculus_wifi`、`hal_usb_oculus`。已观察。
- `hal_lpi_mcu`，即 MCU 支持的 HAL 所在域（第 09 节）。
- `hal_palmauth_vendor_data_file`，一个名称指向掌纹认证的数据类型。根据名称推断。

`hal_oculus_sensors` 是 82 条 allow 规则的来源，是最大的 HAL 来源。已观察。

### neverallow

82 条 `neverallow` 规则限制各域的行为。例如：`hal_secureclock_service` 与 `hal_sharedsecret_service` 不得对 `service_manager` 执行 `add` 或 `find`。已观察。这些规则使安全时钟与共享密钥服务无法进入通用服务管理器。

## 服务、HIDL 服务、属性与文件上下文

这四个文件将名称映射到标签。计数取自 `data/android/selinux/`。

| 文件 | 条目数 | 映射内容 |
|---|---:|---|
| `vendor_service_contexts` | 42 | AIDL/binder 服务名到服务标签 |
| `vendor_hwservice_contexts` | 59 | HIDL 接口名到服务标签 |
| `vendor_property_contexts` | 86 | 属性名前缀到属性标签 |
| `vendor_file_contexts` | 892 | 文件路径（正则表达式）到文件标签 |
| `vndservice_contexts` | 3 | 厂商 binder 服务名 |

### 服务上下文

示例（已观察）：

- `vendor.meta.hardware.time.ITime/default` 对应 `hal_time_service`
- `vendor.meta.hardware.battery.IBattery/default` 对应 `hal_battery_service`
- `vendor.meta.hardware.security.palmauth.IPalmAuthenticator/default` 对应 `hal_palmauth_service`
- `meta.wearables.captureengine.ICaptureEngine/default` 对应 `captureengineservice_service`，`.../wcs` 对应 `wearablecameraservice_service`
- `meta.internal.xrwifi.IXrWifi/default` 对应 `xrwifi_service`

42 个服务条目中有 20 个映射到 `hal_lpi_mcu_service`，包括按键、铰链、机壳、配套设备、灯光、支架、电源与传感器接口。已观察。`lpi_mcu` 服务二进制注册了 20 个 AIDL 接口，与 20 个服务条目一致。已解决：第 09 节早期草稿写的是 17，漏掉了三个。

### HIDL 服务上下文

示例（已观察）：

- `vendor.oculus.hardware.display::IDisplayRefresh` 对应 `hal_oculus_display_hwservice`
- `vendor.oculus.hardware.lcos::ILcos` 对应 `hal_oculus_lcos_hwservice`
- `vendor.oculus.hardware.devicecert::IDeviceCert` 对应 `hal_oculus_devicecert_hwservice`
- `vendor.meta.hardware.glasses.frames::IGlassesFrames` 对应 `hal_mcu_default_hwservice`
- `vendor.oculus.hardware.graphics.composer::IComposer` 对应 `hal_oculus_display_hwservice`

59 个 HIDL 条目中 30 个是 `oculus` 接口，4 个是 `meta` 接口。已观察。

### 属性上下文

86 个属性条目按所有者分组：

- `persist.vendor.meta.*`：uweb、音频 HAL、displaymapping。已观察。
- `persist.vendor.ovr.*` 与 `vendor.ovr.*`：`vendor_oculus_prop`。已观察。
- `vendor.meta.palmauth.*` 与 `vendor.meta.palmexp.session.id.*`：`vendor_palmauth_prop`；`vendor.meta.palmcheck.*`：`vendor_palmcheck_prop`。已观察。
- `vendor.meta.mcu_hal.*`：`vendor_meta_hal_lpi_mcu_prop`。已观察。

### 文件上下文

892 条文件规则是正则表达式。按第一级目录统计，路径根为 `vendor`（478）、`dev`（159）、`(vendor|system/vendor)` 选择式（134）、`sys`（48）、`data`（25）、`persist`（15）、`mnt`（15）与 `odm`（9）。其余 9 条规则为 `system`（3）、`res`（2）、`(vendor|system_ext)`（2）、`(/system)?/system_ext`（1）与 `(vendor|sustem)`（1）。已观察。

使用最多的文件标签是 `same_process_hal_file`（431 条规则），用于标记运行在 HAL 进程内的共享对象。`vendor_custom_ab_block_device`（20）标记 A/B 块设备，`persist_cal_file`（7）标记 `/persist` 下的校准与序列号文件，例如 `/persist/calibration(/.*)?` 与 `/persist/wlan_mac.bin`。`/mnt/vendor/persist` 下的校准路径使用标签 `vendor_persist_cal_file`。已观察。

## 应用侧上下文

- `vendor_seapp_contexts` 只有一条：`user=_app seinfo=platform name=com.qualcomm.timeservice domain=vendor_timeservice_app type=app_data_file levelFrom=all`。已观察。这让时间服务应用拥有自己的域。
- `vendor_mac_permissions.xml`（2,197 字节）只含一个签名者。该签名者是为 `platform` seinfo 标签签名的证书。证书为 `CN = Greatwhite_AOSP_Platform`，由 `CN = Greatwhite_Aosp_Root` 签发，两者的 `O` 均为 `"Meta Platforms Technologies, LLC"`，位于加利福尼亚州门洛帕克。有效期为 2023-12-12 至 2063-12-02，使用 RSA 2048 位密钥与 SHA-256-with-RSA 签名。SHA-256 指纹为 `8F:66:39:8B:31:DF:70:9F:20:CE:BF:C8:5B:F9:46:79:46:9A:81:88:01:E5:CD:5D:51:34:07:77:1C:3B:5D:53`。根据文件中的证书观察。使用此密钥签名的应用会获得 `platform` seinfo 标签。

`vendor_mac_permissions.xml` 带有注释 `AUTOGENERATED FILE DO NOT MODIFY`，说明它由构建生成。已观察。

## 拒绝元数据

`selinux_denial_metadata`（1,503 字节，35 行）是构建跟踪的拒绝对列表，每条附带一个缺陷引用。每行格式为 `源域 目标类型 类 b/<缺陷号>`。共有 17 个不同的缺陷引用。示例：`system_server zygote process`（b/77856826）、`untrusted_app untrusted_app netlink_route_socket`（b/155595000）、`zygote labeledfs filesystem`（b/170748799）。已观察。

这些行是平台已知的拒绝记录，供构建审查，并非设备上当前的拒绝日志。

## 启动时的 SELinux

内核命令行设置了 `androidboot.selinux=enforcing`（第 04 节），因此策略以强制模式加载。已观察。内核配置启用了 `CONFIG_SECURITY_SELINUX_DEVELOP`（第 04 节），这是构建选项；运行时是否使用了开发钩子，此处未检查。

## 策略中的硬件名称

`genfscon` 的 sysfs 路径中包含设备树也使用的硬件名称：

- `pm8150@0` PMIC 及其 RTC、`power-on@800`（与第 04 节为同一 PMIC）
- `remoteproc-adsp`、`remoteproc-cdsp` 与 `188101c.remoteproc-spss` 远程处理器（第 05 节）
- `max17332-battery` 与 `max17332-charger` 电量计
- PCIe 总线上的 `mhi0`，很可能是 Wi-Fi 芯片的传输通道（第 07 节）。根据路径与 `mhi` 驱动推断。

已观察。其中一些名称来自共享的基础策略，因此并不能证明该硬件在本设备上存在。第 04 节的设备树节点确认了 PMIC；电量计与 PCIe 路径未另行核实。

## 未找到的内容

- 厂商分区只含 CIL 输入，`vendor/etc/selinux` 中没有编译后的 `sepolicy`。odm 分区含有编译后的策略 `odm/etc/selinux/precompiled_sepolicy`（1,208,319 字节，SELinux 策略魔数 `0xF97CFF8C`），此处未解码。
- 厂商策略所扩展的平台策略（`plat_pub_versioned.cil` 只是其公共部分）。未解码。
- 设备上的运行时拒绝日志。不在 OTA 中。

## 证据

- `data/android/selinux/policy_summary.txt`：计数、哈希与形式表。
- `data/android/selinux/vendor_service_contexts`、`vendor_hwservice_contexts`、`vendor_property_contexts`、`vendor_seapp_contexts`、`vndservice_contexts`、`plat_sepolicy_vers.txt`、`selinux_denial_metadata`：小文件副本。
- 大文件（`vendor_sepolicy.cil`、`plat_pub_versioned.cil`、`vendor_file_contexts`、`vendor_mac_permissions.xml`）未复制。它们的 SHA-256 哈希记录在 `policy_summary.txt` 中，便于与 OTA 对照。
