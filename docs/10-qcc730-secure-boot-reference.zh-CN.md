# 10 - QCC730 安全启动参考（外部资料）

[English](10-qcc730-secure-boot-reference.md)

本文档收录 Qualcomm 和 OP-TEE 的外部参考资料。它不描述 `greatwhite` 设备。QCC730 是另一款高通芯片（M4F，配 RRAM 与外部闪存）。它的 OTP 布局和签名格式，是高通如何编码安全启动与防回滚状态的最完整的公开范例。这些内容可作为与 `greatwhite` 证据对照的模型，而不是对 `greatwhite` 的描述。

## 来源

| 来源 | 版本 | 用途 |
|---|---|---|
| Qualcomm，*Enable Secure Boot on QCC730 Application Note*，80-Y8730-8，rev AB，2026 年 2 月 10 日更新。四个页面：*OTP format and configuration*、*SecImage configuration file*、*Secure boot key features on QCC730*、*Examples for secure boot configuration* | AB | 下文第 1 至 4 节 |
| OP-TEE 文档，*Hoya architecture*（`architecture/platforms/qualcomm/hoya.rst`），由用户提供 | 当前 | 第 5 节 |

Qualcomm 页面由用户以保存的 HTML 形式提供。其图片位于 `docs/images/qcc730/`。每张图片都是 WebP 格式（保存时文件名为 `.png`，但实际是 WebP）。

## 1. OTP 格式与配置

QCC730 的 OTP 熔丝在烧录前为 0，烧录后为 1。在所在区域锁定之前，字段可以被清回 0。

![安全启动的 OTP 格式](images/qcc730/otp-format.webp)

*图：QCC730 安全启动的 OTP 格式。*

### 读写权限

| 字节 | 位 | 名称 | 含义 | 建议值 |
|---|---|---|---|---|
| 48 | 4 | READ_PERMISSION_HW_ENCRYPTION_KEY | 置 1 禁止软件读取硬件加密密钥 | 1 |
| 51 | 2 | WRITE_PERMISSION_READ_WRITE_PEMRIONS | 置 1 禁止软件写入读写权限区域 | 1 |
| 4 | | WRITE_PERMISSION_HW_ENCRYPTION_KEY | 置 1 禁止软件写入硬件加密密钥 | 1 |
| 5 | | WRITE_PERMISSION_PK_HASH | 置 1 禁止软件写入 RoT 哈希区域 | 1 |
| 7 | | WRITE_PERMISSION_OEM_SECURE_BOOT | 置 1 禁止软件写入 OEM 安全启动区域 | 1 |
| 52 | 0 | WRITE_PERMISSION_ANTI_ROLL_BACK | 置 1 禁止软件写入防回滚区域 | 1 |

文档表格中的字段名拼写为 `WRITE_PERMISSION_READ_WRITE_PEMRIONS`，此处保留原文拼写。

### 密钥

| 字节 | 名称 | 含义 |
|---|---|---|
| 64-79 | HW_DEVICE_KEY | 128 位设备唯一密钥，由 Qualcomm 写入，供 KDF 使用 |
| 80-95 | USER_DATA_KEY | 128 位随机密钥，与设备密钥一起供 KDF 生成安全存储密钥。由 Qualcomm 写入，且不保存每台设备的跟踪信息 |
| 96-111 | HW_ENCRYPTION_KEY | 128 位密钥，多台设备共用，供 KDF 使用 |

### RoT 哈希

| 字节 | 名称 | 含义 |
|---|---|---|
| 112-143 | PK_HASH | 镜像签名所用根证书的 SHA-256。按 TOTAL_ROT_NUM 给出的根证书数量计算 |

### OEM 安全启动

| 字节 | 位 | 名称 | 含义 | 建议值 |
|---|---|---|---|---|
| 160 | 7:4 | TOTAL_ROT_NUM[3:0] | 计算 RoT 哈希所用的 RoT 数量。QCC730 只支持 1 个 | 1 |
| 162-163 | | MODEL_ID | 源资料未作说明 | |
| 164 | 2:0 | SECURE_BOOT_ENFORCE[2:0] | 置 0x7 启用强制策略：镜像认证与防回滚检查 | 7 |
| 165-166 | | OEM_ID | Qualcomm 分配的 16 位标识，供镜像认证使用 | 烧录分配的值 |
| 167 | 7 | OEM_DEBUG_DISABLE | 置 1 禁用 JTAG 调试 | 1 |
| 168 | 2 | HASH_INTG_CHK_DISABLE | 在强制策略关闭时，置 1 禁用哈希完整性检查 | 0 |
| 0 | | DISABLE_QC_RMA | 置 1 禁用用于开启硬件调试的 QC RMA 密码 | 0 |

### 防回滚

| 字节 | 位 | 名称 | 含义 |
|---|---|---|---|
| 176 | 7:0 | ANTI_ROLLBACK[7:0] | 该字段中**置 1 的位数之和**，即安全启动允许运行的最低防回滚镜像版本 |
| 177 | 7:0 | ANTI_ROLLBACK[15:8] | |
| 178 | 7:0 | ANTI_ROLLBACK[23:16] | |
| 179 | 7:0 | ANTI_ROLLBACK[31:24] | |
| 180 | 7:0 | ANTI_ROLLBACK[39:32] | |
| 181 | 7:0 | ANTI_ROLLBACK[47:40] | |
| 182 | 7:0 | ANTI_ROLLBACK[55:48] | |
| 183 | 7:0 | ANTI_ROLLBACK[63:56] | |

源资料将版本定义为该字段中置 1 位的数量之和，即统计置位数。源资料未描述温度计式编码。确切的熔丝写入规则在编程指南中，不在本资料内。

### 熔丝烧录

NVM 编程器（`nvm_programmer.py`）用于读写 QCC730 的 OTP、RRAM 与闪存。编程指南为 QCC730.FR.1.0（80-Y8730-2），不在所提供的资料中。

## 2. SecImage 配置文件

SecImage 配置（`qcc730_secimage.xml`）用于签名、后处理和校验安全镜像。它包含四个部分：`metadata`、`general_properties`、`data_provisioning` 和 `image_list`。

- `metadata`：`<chipset>qcc730</chipset>`，`<version>2.0</version>`。
- `general_properties`：`selected_signer`（默认：本地签名器；示例值 `local_v2`）、`selected_cert_config`、`cass_capability`（`secboot_sha2_root`，即 SHA-256 签名的根证书）、`key_size`（2048）、`exponent`（257 或 65537）、`mrc_index`、`num_root_certs`、`msm_part`、`oem_id`、`model_id`、`debug`、`max_cert_size`、`num_certs_in_certchain`。
- `image_list`：每个镜像包含 `sign_id`、`name`、`image_type`（`elf_has_ht`）和 `sw_id` 覆盖项。

本地签名器使用 Qualcomm 平台签名应用（QPSA）的测试 PKI。若要使用本地预签名证书，需在 `sectools\resources\data_prov_assets\Signing\Local\` 下创建一个单词命名的文件夹，并在 `selected_cert_config` 中填写该名称。其 `config.xml` 设置 `is_mrc`、`root_pre`、`attest_ca_pre`、`attest_pre`、`root_cert` 和 `root_private_key`。

### 证书 OU 字段

| OU 字段 | 位数 | 布局 |
|---|---|---|
| SW_ID | 64 | 高 32 位：防回滚版本。低 32 位：镜像 ID（软件类型）。镜像版本与 OTP 中的防回滚版本比较 |
| HW_ID | 64 | 高 32 位：硬件 SoC 版本。16 位：OEM_ID。低 16 位：MODEL_ID |
| DEBUG | 64 | 高 32 位：芯片序列号的低 32 位。低 32 位：调试向量 |
| OEM_ID | 16 | 默认 0x0000 |
| MODEL_ID | 16 | 默认 0x0000 |

**SW_ID 软件类型**（低 32 位）：`FERMION_SBL = 0x00`（SBL 镜像），`FERMION_APP = 0x01`（APP 镜像）。示例镜像列表中，golden 镜像分别使用 `sbl_golden` = 0x02 和 `app_golden` = 0x03。

**示例。** `<sw_id>0x0000000100000000</sw_id>` 为带防回滚检查的 SBL 镜像设置软件版本 0x01。

**HW_ID** 在 `in_use_soc_hw_version` = 1 时，把 SoC 版本放在高 32 位。OEM_ID 和 MODEL_ID 与 OTP 中相同字段比较。

**DEBUG** 用于覆盖 OEM 调试禁用 OTP。商用镜像使用全 0。调试标志 `0x2` 会把 0 写入一次性调试覆盖寄存器。标志 `0x3` 仅当高 32 位中的序列号与芯片匹配时，才写入 1。例如 `0x1234567800000003` 是针对序列号 `0x12345678` 的调试证书。若该字段缺失，则使用默认值 `0x0000000000000000`。

## 3. 安全启动关键特性

QCC730 对从 RRAM 或外部闪存加载、运行于 M4F 的固件进行认证。特性包括：
- 两个分别签名的镜像，SBL 和 APP；
- SHA-256 哈希；
- RSA 2048 位签名；
- JTAG 调试覆盖；
- 防回滚。

**签名。** Sectools 为固件镜像生成证书。证书包含公钥、整个镜像的摘要，以及烧录在 OTP 中的 OEM ID 和型号 ID。Sectools 用私钥对证书签名。

**复位后认证。**
1. 校验镜像内嵌的证书链。
2. 将证书中保存的镜像摘要与 ROM 计算出的摘要比较。
3. 根证书通过 SHA-256 哈希后与 OTP 中的哈希（PK_HASH）比较。

**启动链。** 上电后，PBL（位于 ROM）加载并认证 SBL，SBL 加载并认证 APP，然后运行 APP。

![安全启动流程图](images/qcc730/secure-boot-flowchart.webp)

*图：QCC730 的安全启动流程。*

![镜像认证组件](images/qcc730/image-authentication-components.webp)

*图：镜像认证组件。安全启动数据保存在 OTP、RRAM 和闪存中。*

## 4. 安全启动配置示例

**单根证书。** `qcc730_secimage.xml` 的通用属性为：`cass_capability` = `secboot_sha2_root`，`key_size` = 2048，`exponent` = 257，`num_root_certs` = 1，`oem_id` = 0x0000，`model_id` = 0x0000，`debug` = 0x2，`num_certs_in_certchain` = 2。

**在 OTP 中启用安全启动。**
```
python nvm_programmer.py -n otp -k SECURE_BOOT_ENFORCE=0x7 -s ch347
python nvm_programmer.py -n otp -k TOTAL_ROT_NUM=0x1 -s ch347
python nvm_programmer.py -n otp -k PK_HASH=<根证书的 SHA-256> -s ch347
```
示例中 `qpsa_rootca.cer` 的 SHA-256 为 `de5480d49ed1cbe0813755f06324fce56e3eb391a9a40ffba8df9fd16c717744`。该值取自本地证书文件夹中的 `sha256rootcert.txt`。

**关闭 JTAG。** `python nvm_programmer.py -n otp -k OEM_DEBUG_DISABLE=0x80 -s ch347`。如需重新开启，在 `qcc730_secimage.xml` 中把调试字段设为 `0x...03`，并使用对应的序列号（见上文 DEBUG）。

**提升防回滚版本。** 示例将 SBL 的 `sw_id` 设为 `0x0000000100000000`，APP 设为 `0x0000000100000001`，两个镜像的软件版本均为 1。示例只展示了 SecImage 一侧。对应的 OTP 写入不在所提供的资料中。

## 5. OP-TEE 文档：Hoya 架构（由用户提供）

Hoya 系列面向 Qualcomm 应用处理器，目前包括 `kodiak` 和 `lemans`。在通用 Qualcomm 平台功能之上，它启用了 8 核 Cortex-A（ARMv8）配置和 GICv3 中断控制器（`CFG_ARM_GICV3`）。

**驱动与服务：**
- RAMBLUR 内联内存保护 v3（`CFG_QCOM_RAMBLUR_PIMEM_V3`），为安全内存窗口提供防回滚、完整性和机密性保护。
- 安全 RNG（`CFG_QCOM_CSRNG`），是 `hw_get_random_bytes()` 的熵源。
- Qualcomm 时钟驱动（`CFG_DRIVERS_QCOM_CLK`），基于 OP-TEE 时钟框架。
- QFPROM（`CFG_QCOM_QFPROM`），用于读取 OTP 熔丝。启动时的写入由 `CFG_QCOM_QFPROM_FUSEPROV` 控制。
- 外设认证服务 PAS（`CFG_QCOM_PAS_PTA`），用于认证并启动远程子系统固件。

QFPROM 提供基于熔丝的认证数据，并支持启动时写入。Kodiak 和 Lemans 都使用 Command DB 查找共享电源资源，并使用 RPMh 请求编程电源。Kodiak 还需要与始终在线处理器（AOP）协调的 MX 电源轨投票。

| 芯片 | 签名认证 | 硬件唯一密钥 |
|---|---|---|
| Kodiak | 未启用 | 默认测试密钥 |
| Lemans | 支持 | 硬件（HWKM） |

**Kodiak。** PAS 启动音频 DSP（LPASS/QDSP6）、计算 DSP（Turing）、视频编解码器（IRIS）和 WPSS，且不做基于证书的签名认证。安全构建（非 `CFG_INSECURE`）默认启用启动时熔丝写入，并启用 QFPROM。默认不启用 PAS 熔丝读取服务。

**Lemans。** PAS 启动音频 DSP、两个 Turing 计算 DSP、两个 GPDSP、IRIS 和摄像头子系统。基于证书的签名认证已启用（`CFG_QCOM_PAS_AUTH`），由受限的熔丝读取服务（`CFG_QCOM_FUSE_PTA`）支持。启用后，只有当安全启动熔丝表明安全启动已关闭时，才跳过证书和签名检查；固件段哈希仍会检查。其硬件唯一密钥来自硬件密钥管理器（`CFG_QCOM_HWKM`）。

QFPROM 在启动时写入或 PAS 熔丝读取服务启用时被启用。安全构建默认启用启动时写入，PAS 熔丝读取路径在非安全构建上也可能启用 QFPROM。

## 6. 与 greatwhite 证据的对照（假设，而非结论）

以下是待验证的对应关系。在 `greatwhite` 上均未得到确认。

| QCC730 概念 | greatwhite 证据（见文档 02、03、06） | 状态 |
|---|---|---|
| OTP 中以 64 位编码表示的防回滚（置位数之和） | UEFI 熔丝库中的软件熔丝范围 `FUSE_CONTROLLER_SW_RANGE0`、`_RANGE1`、`_RANGE3`、`_RANGE4` 与 `_RANGE5`（区域表与字符串中没有 `_RANGE2`），位于 `0x221C` 块（文档 06）。虚拟化层的早期启动代码把范围 4 的三个字（`0x221C8610`、`0x221C8700`、`0x221C8744`）复制到全局变量 `0x9D4D0`、`0x9D4CC` 与 `0x9D4C8` 中。据报告，虚拟化层对这些字的唯一位测试是 4 位枚举掩码（`0x4883`），没有置位计数；此项未经重新检视。尚未找到复制后全局变量的读取者 | 假设：目前读到的代码既不支持也不否定。需要复制全局变量的读取者或熔丝转储 |
| 镜像 SW_ID 的类型字段（SBL、APP、golden） | 虚拟化层的 `PILSubsys_getArbFuseBank` 提供按子系统划分的 arb 熔丝组（文档 06） | 假设：同类存储体中按子系统的索引 |
| PK_HASH，根证书的 SHA-256 | TZ 与 devcfg 中的 `OEM_rot_pk_hash1_fuse_values`（文档 06） | 假设：相同作用；读取者仍未找到 |
| SECURE_BOOT_ENFORCE 及其使能位 | 安全启动状态字第 0 至 11 位，第 3 位为防回滚（文档 06） | 结构上相似；状态服务未确定 |
| 调试覆盖与 DEBUG 字段 | 安全调试熔丝检查，第 8 至 11 位（文档 06） | 结构上相似 |
| 熔丝区域的读写权限位 | `FUSE_CONTROLLER` 与 `QFPROM_CORR` 区域（文档 06）。UEFI 区域表只有名称、基址与大小，没有权限字段（`data/secure/uefi_fuse_region_table.txt`）。唯一找到的权限值是 OEM 备用熔丝写入函数中对 `/ac/oem_regions_config` 的 `0x12` 检查（`data/secure/tz_oem_spare_fuse_writer_decomp.txt`），那是配置检查，而非逐区域的位 | 已比较：greatwhite 的区域表中不存在逐区域的权限位。QCC730 的位布局不能直接适用 |

QCC730 的布局不能直接套用到 `greatwhite`，需要逐项核对。它是另一款芯片，上面列出的 OTP 字节偏移都是 QCC730 自己的。
