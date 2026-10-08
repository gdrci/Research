# 17 - 调制解调器分区固件：ADSP、CDSP 与可信应用

[English](16-modem-partition-firmware.md)

`modem.img` 是一个含 165 个文件的 FAT16 镜像（第 05 节）。除调制解调器与 Wi-Fi 组件外，它还包含两个 Hexagon 处理器的固件（应用 DSP，即 ADSP；计算 DSP，即 CDSP），以及约十个运行在 TrustZone 中的已签名应用。本节记录它们的结构、签名以及每个应用的功能。文件列表见 `data/remote/modem_listing.txt`，签名证据见 `data/remote/modem_firmware_signatures.txt`。

状态标注：已观察表示直接从文件读取；推断表示文件未明说但合理的解读；未找到表示该内容不在 OTA 中。

## 这些镜像的布局

每个镜像都分为一个头文件（`.mdt`）与编号的段文件（`.bNN`）。`.mdt` 文件包含 ELF 头与程序头。第 `NN` 段位于 `.bNN` 中，其大小等于程序头的 `p_filesz`。ADSP 已观察：`adsp.b01` 为 6,804 字节，与第 1 段的 `p_filesz`（`0x1A94`）相同。头文件本身即第 0 段文件（`adsp.b00`，1,396 字节，即 ELF 头与 42 个程序头）。

部分程序头没有数据。第 0 段（标志 `0x7000000`）是头部段：其文件 `.b00` 为 ELF 头与程序头，已观察为 1,396 字节。标志为 `0x2000000` 的最后一段是签名段，其文件中包含哈希表与证书链。

**哈希表。** 签名段为每个非空程序段包含一个 SHA-384 摘要（48 字节）。摘要位于偏移 288 加上 48 乘以段索引处。ADSP 已观察。对每个镜像的每个非空段进行检查，均能在签名段中找到其摘要：ADSP 的 39 个非空数据段全部匹配（签名段自身不参与哈希）；CDSP 为 11/11；八个分段形式的可信应用各为 7/7 个数据段。已观察。因此这些文件内部一致：每个段都是签名所覆盖的那一段。

**证书。** 签名段还包含一条 DER 证书链，可用 `openssl` 读取。已观察。证书链列于 `data/remote/modem_firmware_signatures.txt`。

## 各处理器

### ADSP（应用 DSP）：`adsp.mdt` 与 `adsp.b00` 至 `adsp.b41`

- ELF32，机器码 `0xA4`（Hexagon），入口 `0x87600000`，42 个程序头，40 个可加载段，物理范围 `0x87600000` 至 `0x89300000`。已观察。
- 第 `24` 与 `40` 段为空（`p_filesz` 为零）。签名段为第 `41` 段。
- 镜像包含音频框架。其字符串包括模块名 `AudioSphereModule.so.1`、`CFCM.so.1`、`SAPlusCmnModule.so.1`、`aac_dec_module.so.1` 与 `aac_enc_etsi_module.so.1`。已观察。这是高通信号处理框架（SPF），负责加载 Android 侧音频路由所调用的音频处理模块（第 12 节）。
- 镜像中有 QuRT 内核函数（`qurt_api_version`、`adsp_pls_add_lookup`、`adsp_mmap_fd_getinfo`）以及内存映射函数。已观察。
- ADSP 镜像中含有字符串 `SigVerify_HaveTestRoot`。已观察。因此验证器除生产根之外还有测试根的代码路径（见下文签名部分）。

### CDSP（计算 DSP）：`cdsp.mdt` 与 `cdsp.b00` 至 `cdsp.b12`

- ELF32，机器码 `0xA4`（Hexagon），入口 `0x89400000`，13 个程序头，11 个可加载段，范围 `0x89400000` 至 `0x89E00000`。已观察。第 `11` 段为空，第 `12` 段为签名段。
- 镜像中含有与 ADSP 相同的 `wpss` 与 QDSS 字符串（针对 WPSS 与 Q6 模块的 QDSS 跟踪配置）。已观察。这是与第 07 节所述 WPSS 子系统的联系：WPSS 固件不在 OTA 中，但其调试配置字符串位于计算镜像中。

### 可信应用（TA）

可信应用为 AArch64 ELF64 镜像（机器码 `0xB7`），由安全世界加载。它们有两种形式。多数为分段形式（`.mdt` 与 `.bNN`），含八个数据段与一个签名段；部分还有单个 `.mbn` 文件。

| 应用 | 形式 | 签名者 | 字符串所示功能 |
|---|---|---|---|
| `featenabler` | `.mdt`（9 个程序头，5 个加载段） | 高通 SRoT MBNv7 与 CASS-SBL4，以及 Meta Greatwhite_FW 链 | 功能使能器（第 06 节）：功能 ID 与 SoC 门控 |
| `hdcp1` | `.mdt` | SECTOOLS 测试根 | HDCP 1.x 内容保护 |
| `hdcp2p2` | `.mdt` | SECTOOLS 测试根 | HDCP 2.2 内容保护 |
| `hdcpsrm` | `.mdt` | SECTOOLS 测试根 | HDCP 系统更新消息（吊销列表） |
| `loadalgota64` | `.mdt` | SECTOOLS 测试根 | 镜像加载器：用 `IIPProtector_verifySignature` 与防回滚版本检查 ELF 与哈希段，并报告 `Segment %d overlaps with ELF + PHT segment` |
| `mldapta` | `.mdt` | SECTOOLS 测试根 | 面向 ML 设备认证身份的证书与密钥供应。其文件为 `/persist/data/mldapta/MlsDapCCCDeviceCert.crt`、`MlsDapCCCDevicePvKey.key` 与 `MlsDapCCCManuCert1.crt`。镜像中未展开 "DAP" 的含义 |
| `ovrtz64` | `.mdt`（测试根）与 `.mbn`（Meta 链） | 两者 | `OVRTZ`（Oculus/Meta 的 TZ 应用，名称为推断）。安全休眠 HMAC 密钥上下文与标签 |
| `palmprintengine64` | `.mdt`（测试根）与 `.mbn`（Meta 链） | 两者 | 掌纹引擎：`GATEKEEPER_*` 错误与 `PALMPRINT_CANCEL_ERROR`。这是掌纹认证应用；与 gatekeeper 的联系根据错误名推断 |
| `soter64` | `.mdt` | SECTOOLS 测试根 | SOTER 密钥认证：`ATTK`（认证密钥）、`KM SOTER SN UNIQUE ID`，以及 `/persist/data/soter/` |
| `sp_license` | `.mbn` | SECTOOLS 测试根 | 许可证应用：`IPFM_CheckLicenseBuffer`、`Fail to install license by SKP`（功能许可证的安装检查） |
| `widevine` | `.mbn` | SECTOOLS 测试根 | Widevine DRM：`/persist/data/widevine/keybox_lvl1.dat`、`cert.dat`、`private_key.dat`、`master_gen_num.dat`、`provision_method.dat` |
| `smplap64` | `.mbn`（1,962,072 字节） | SECTOOLS 测试根 | 示例与测试应用：字符串为加解密、签名与 RSA-OAEP 测试的统计（`Total Encrypt/Decrypt Tests`） |

以上均依据名称与字符串观察得出。用途说明基于字符串，而非代码。

## 签名

镜像中出现两套签名体系。

**Meta 链。** 证书为 `Greatwhite_FW_Signing_3`（由 `Greatwhite_FW_Root_3` 签发），另有 `Greatwhite_FW_Root_0`、`_1`、`_2` 与 `_3`。均由 Meta Platforms Technologies, LLC 签发，位于加利福尼亚州门洛帕克。有效期约为 2023 年 12 月至 2063 年 11 月。已观察。该链签署 ADSP、CDSP、`featenabler`（位于高通链之上），以及 `ovrtz64` 与 `palmprintengine64` 的 `.mbn` 形式。

**SECTOOLS 测试根。** 证书为 `SecTools Test User`、`SECTOOLS SECP384R1 CURVE TEST ROOT0` 与 `SECTOOLS SECP384R1 CURVE TEST ROOT`，由高通签发（`O = QUALCOMM`，`OU = CDMA Technologies`），使用 SECP384R1 曲线。已观察。该链签署 `hdcp1`、`hdcp2p2`、`hdcpsrm`、`loadalgota64`、`mldapta`、`soter64`、`sp_license`、`widevine` 与 `smplap64`，以及 `ovrtz64` 与 `palmprintengine64` 的 `.mdt` 形式。

这是对文档有重要意义的已观察事实：多个出货的可信应用由高通测试根签名，而非生产链。GPU 的 zap 着色器含有相同的测试根字符串（第 08 节）。ADSP 验证器包含测试根分支（`SigVerify_HaveTestRoot`）。设备运行时是否接受测试根，取决于安全世界验证器，它位于 TrustZone 镜像中。此处未检查，OTA 中也没有运行时结果。

## 与其他章节的关系

- `featenabler` 即第 06 节所述、用于显示软件熔丝功能 ID 的可信应用。
- 掌纹引擎（`palmprintengine64`）是第 14 节所述触控控制器报告的手掌手势的认证对应者。根据名称推断。
- Widevine 与 HDCP 应用属于显示的内容保护部分（第 13 节）。
- ADSP 的音频模块是第 12 节 Android 路由的处理端。NXP RT700 DSP（第 15 节）是另一个独立处理器。
- `sp_license` 是功能许可证路径。第 03 节涵盖镜像的启动验证；此处是功能许可证的运行时检查。

## 未找到的内容

- `mldapta` 中 "DAP" 缩写的含义。镜像中未展开。
- 超出字符串之外的可信应用源码或命令接口。
- 接受或拒绝测试根的运行时检查。它在 TrustZone 验证器中，而不在这些镜像里。
- ADSP 音频模块的代码（超出名称之外）。二进制位于各段中。

## 证据

- `data/remote/modem_listing.txt`：`modem.img` 的文件列表。
- `data/remote/modem_firmware_signatures.txt`：每个分段镜像与单文件可信应用的 ELF 头字段、SHA-384 覆盖情况与证书主体。
- `data/remote/modem_verinfo.txt`：`modem.img` 的构建清单。
