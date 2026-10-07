# 03 - Android 验证启动（AVB）

[English](03-avb-verified-boot.md)

验证启动遵循 libavb 1.x 格式。解析输出见 `data/avb/vbmeta_summary.txt`。签名与哈希的校验结果见 `data/avb/verify_results.txt`，由 `tools/avb_verify.py` 直接对解出的镜像进行计算。

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

## 已对照镜像进行的检查

脚本 `tools/avb_verify.py` 直接对解出的镜像进行签名与哈希校验。输出见 `data/avb/verify_results.txt`。

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
| `odm` dm-verity 根，SHA-1（52,924,416 字节） | 不一致 |
| `product` dm-verity 根，SHA-1（650,182,656 字节） | 不一致 |
| `system_ext` dm-verity 根，SHA-1（410,660,864 字节） | 不一致 |

因此，签名的元数据与出厂时 `boot`、`dtbo`、`vendor_boot`、`vendor` 和 `system` 的内容完全一致。已验证。

### SHA-1 hashtree

这三个 SHA-1 树在脚本采用的布局下不一致。该布局是标准的 v1 布局：每个块前加 salt，每个哈希块填充到 4096 字节。同一段代码对 SHA-256 树是一致的，因此代码对 SHA-256 是正确的。对于 `odm`，我还尝试了把 salt 放在末尾，结果同样不一致。

可能的解释（均未测试）：

- SHA-1 树使用了不同的布局或不同的哈希块打包方式；
- 描述符覆盖的数据范围与我计算的范围不同；
- 树本身是正确的，而我的布局有误。

这三个分区都启用了 FEC（`odm` 的 `fec_num_roots=2`）。FEC 不改变根哈希，因此不是原因。该不一致仍未解决，不应被理解为校验失败。

仍未检查的内容：chain 分区公钥的使用方式，以及 FEC 数据。
