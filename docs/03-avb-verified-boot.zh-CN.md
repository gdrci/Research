# 03 - Android 验证启动（AVB）

[English](03-avb-verified-boot.md)

验证启动遵循 libavb 1.x 格式。解析输出见 `data/avb/vbmeta_summary.txt`。签名与哈希的校验结果见 `data/avb/verify_results.txt`，直接对解出的镜像进行计算。

## vbmeta.img

| 字段 | 值 |
|---|---|
| libavb 版本 | 1.0 |
| 算法 | SHA256_RSA2048 |
| 回滚索引 | 1770249600，位置 0 |
| 标志 | 0x0（验证已开启） |
| 发布字符串 | `avbtool 1.2.0` |
| 公钥 | 520 字节，SHA-256 为 `0d5c1533678bc678252d94dbe5c9689ebdfe72f34c32fdbbcc87e3952c814abe` |

描述符按镜像中出现的顺序列出：

| 类型 | 分区 | 大小 | 哈希 | 说明 |
|---|---|---:|---|---|
| hash | `boot` | 30,208,000 | sha256 | 整镜像哈希 |
| hash | `dtbo` | 2,435,291 | sha256 | 整镜像哈希 |
| hash | `vendor_boot` | 13,946,880 | sha256 | 整镜像哈希 |
| hashtree | `vendor` | 453,591,040 | sha256 | dm-verity，格式 v1 |
| hashtree | `odm` | 52,924,416 | sha1 | dm-verity，格式 v1，启用 FEC |
| chain | `recovery` | | | 回滚位置 1 |
| chain | `vbmeta_system` | | | 回滚位置 2 |

镜像附带的属性：Android 12 分区的指纹和 `os_version`，全部为 `facebook/greatwhite/greatwhite:12/SQ3A.220605.009.A1/65394930092600080:user/release-keys`。

`odm` 的 hashtree 使用 SHA-1，`vendor` 使用 SHA-256。这种混用不寻常，原因未验证。

## vbmeta_system.img

| 类型 | 分区 | 大小 | 哈希 |
|---|---|---:|---|
| hashtree | `system` | 1,433,899,008 | sha256 |
| hashtree | `product` | 650,182,656 | sha1 |
| hashtree | `system_ext` | 410,660,864 | sha1 |

属性：指纹 `Meta/greatwhite/greatwhite:14/UKQ1.250303.001/...`，`os_version=14`，`security_patch=2026-02-05`。

`vbmeta_system` 与 `vbmeta` 使用相同的公钥，即两者由同一把密钥签名。该结论来自公钥哈希的比对，已验证。

## 回滚索引

数值 1770249600 是 2026 年 2 月 5 日 00:00 UTC 的 Unix 时间，与补丁日期相同。这说明它很可能是在构建镜像时根据补丁级别设置的。数值已验证；它与补丁日期的对应关系为已观察。

防回滚只有在设备同时保存一个由熔丝支撑的计数器副本时才有效。这个副本目前还没有找到，第 06 节说明了应该去哪里找。

## 依赖 AVB 的 fstab 条目

第一阶段 fstab（第 04 节）中，`vendor` 和 `odm` 使用 `avb=vbmeta`，`system`、`system_ext` 和 `product` 使用 `avb=vbmeta_system`。这些值就是验证器所遵循的链条。已验证。

### `uefi.img` 中的验证启动与设备状态

`uefi.img` 是一个固件卷（`0x1000` 处为 `_FVH`，长度 `0x289000`）。其 DXE 代码位于一个 GUID 定义的段（`1d301fe9-be79-4353-91c2-d23bc959ae0c`）中，该段的载荷是 gzip。解压后为 3,911,688 字节。字符串列表见 `data/strings/uefi_dxe_fv_strings.txt`（18,305 条）。

验证启动模块 `VerifiedBootDxe` 根据其字符串完成以下四项工作：
- 读写设备状态（`RWDeviceState`）。状态通过 QSEE 应用（`gQcomQseecomProtocolGuid`）、RPMB（`Succeed using rpmb`）或 devinfo 保存。
- 把启动状态和里程碑发送给 QSEE 应用（`Send_Milestone`、`Reset_State`、`SendBootState`）。
- 为锁定或解锁设备计算信任根摘要（`SendROT`、`vb_get_digest_locked_device`、`vb_get_digest_unlocked_device`），并用 OEM 证书或内嵌密钥校验签名，还计算证书指纹。
- 设备解锁时跳过校验（`Device is unlocked! Skipping verification!`）。

镜像中列出的软件熔丝范围有：`FUSE_CONTROLLER_SW_RANGE0`、`_SW_RANGE1`、`_SW_RANGE3`、`_SW_RANGE4`、`_SW_RANGE5`、`VIRT_FUSE_CONTROLLER_SW_RANGE3`，以及 `TME_FUSECONTROLLER`。防回滚状态应当位于这些范围内，但字符串没有说明哪个范围保存 `vbmeta` 索引。RPMB 相关字符串是写入计数器的读取（`rpmb_read_counter_pkt`），不是 `vbmeta` 索引。依据字符串观察得出。结论见 `data/secure/uefi_verified_boot_findings.txt`。

DXE 固件卷中的验证启动代码已反编译，见 `data/ghidra/uefi_verifiedboot_decompiled.txt`。`VerifyImage` 用 SHA-256 对镜像做摘要，用 OEM 证书校验签名，失败时回退到内嵌密钥，并设置启动状态。在这些函数中没有回滚索引比较：`VerifyImage`、`vb_verify_hash_oem_certificate` 和 `vb_verify_hash_embedded_key` 都不比较回滚索引。`RWDeviceState` 读取 `devinfo` 分区和 `SecurityFlag`；对于已锁定的设备，它启动 `keymaster` QSEE 应用，读写已保存的状态。因此已保存的安全状态保存在 Keymaster 之后，RPMB 是替代存储。已观察。在 UEFI 镜像中未找到把 `vbmeta` 回滚索引与已保存状态比较的位置，因此它很可能位于 Keymaster 应用或 Android 启动代码中，而这些不在这些镜像里。

`keymaster.img` 负责 Keymaster 的回滚保护。密钥 blob 携带 OS 版本，并与当前启动的 OS 版本比较（`Current boot osVersion` 和 `Key blob osVersion`）。未通过检查的密钥不会被升级。保存的状态（`sfs_rpmb_set` / `sfs_rpmb_get`）位于 RPMB 中。Keymaster 还为证明记录 `vbmeta` 摘要（`fill_vbmeta_digest`），并处理启动状态与信任根（`KEYMASTER_SET_ROT`、`KEYMASTER_SET_BOOT_STATE`、`KEYMASTER_SET_VERSION`）。这是密钥级别的回滚保护。`vbmeta` 索引比较不在该镜像中。依据字符串观察得出。证据见 `data/secure/keymaster_rollback_strings.txt`。

## 已对照镜像进行的检查

签名与哈希校验直接在解出的镜像上进行。输出见 `data/avb/verify_results.txt`。

| 检查项 | 结果 |
|---|---|
| `vbmeta` 对头部与辅助块的认证哈希 | 一致 |
| `vbmeta` RSA-2048 签名（PKCS#1 v1.5，SHA-256） | 有效 |
| `vbmeta_system` 认证哈希 | 一致 |
| `vbmeta_system` RSA 签名 | 有效 |
| `boot` 整镜像 SHA-256（30,208,000 字节） | 一致 |
| `dtbo` 整镜像 SHA-256（2,435,291 字节） | 一致 |
| `vendor_boot` 整镜像 SHA-256（13,946,880 字节） | 一致 |
| `vendor` dm-verity 根，SHA-256（453,591,040 字节） | 一致 |
| `system` dm-verity 根，SHA-256（1,433,899,008 字节） | 一致 |
| `odm` dm-verity 根，SHA-1（52,924,416 字节） | 一致（重建树，摘要槽为 32 字节） |
| `product` dm-verity 根，SHA-1（650,182,656 字节） | 一致（重建树，摘要槽为 32 字节） |
| `system_ext` dm-verity 根，SHA-1（410,660,864 字节） | 一致（重建树，摘要槽为 32 字节） |

因此，签名的元数据与出厂时 `boot`、`dtbo`、`vendor_boot`、`vendor`、`system`、`odm`、`product` 和 `system_ext` 的内容完全一致。已验证。

### SHA-1 hashtree

这三个 SHA-1 树（`odm`、`product`、`system_ext`）最初在标准布局下不一致，标准布局中每个摘要占一个 20 字节的槽。问题出在布局上，而不是数据上：每一层的摘要都存放在 32 字节的槽中，SHA-1 摘要之后补零。因此每个 4096 字节的块只容纳 128 个摘要，而不是 204 个。

证据：`odm` 的树在镜像中占 102 块，与每块 128 个摘要吻合（第 0 层 101 块加一个根块）。若按 20 字节槽计算，则应为 65 块。把每棵树都按 32 字节槽重建后，`odm`、`product` 和 `system_ext` 的根摘要都与描述符一致。同一次重建也与 `vendor`、`system` 的 SHA-256 根一致。按自顶向下的顺序，存储的树与重建的树逐字节相同。输出见 `data/avb/hashtree_rebuild.txt`。

FEC 数据未检查。FEC 不改变根哈希。

仍未检查的内容：chain 分区公钥的使用方式，以及 FEC 数据。
