# 署名与第三方声明

[English](NOTICE.md)

## 作者

原创分析与文档：**gdrci**。

这包括 `docs/` 下除第 10 节和 `docs/images/` 之外的文档、README 文件，以及分析过程中撰写的证据说明。这些内容按 [CC BY 4.0](LICENSE) 授权。

## 不在 CC BY 4.0 授权范围内的内容

以下内容被排除在 [LICENSE](LICENSE) 的授权之外，其权利仍归原权利人所有。

| 材料 | 位置 | 权利人 | 依据 |
|---|---|---|---|
| Ray-Ban Display 固件：摘录、字符串、符号表、反汇编与反编译输出、十六进制提取物与元数据 | `data/` | Meta Platforms, Inc. 及固件中第三方组件的权利人 | 作为分析的证据收录 |
| Qualcomm《Enable Secure Boot on QCC730 Application Note》（80-Y8730-8，rev AB）中的三张图 | `docs/images/qcc730/` | Qualcomm Technologies, Inc. | 保存的 HTML 页面提供；仅供参考引用 |
| 第 10 节，QCC730 安全启动参考，中英文版 | `docs/10-qcc730-secure-boot-reference*.md` | Qualcomm Technologies, Inc. 与 OP-TEE 项目 | 摘自 Qualcomm 应用笔记与 OP-TEE *Hoya architecture* 文档 |
| Analog Devices MAX98388/MAX98389 数据手册（Rev. 2，6/24） | 引用于 `docs/12-audio.md`、`docs/17-chip-inventory.md` | Analog Devices, Inc. | 引用其规格数值 |
| Qualcomm FastConnect 7800 产品简介（87-PW329-1 Rev. B） | 引用于 `docs/17-chip-inventory.md` | Qualcomm Technologies, Inc. | 引用其产品特性 |

## 使用的工具与项目

- **Ghidra** 12.1.3（无界面分析与反编译），Apache License 2.0。
- **Capstone** 5.0.7（反汇编），BSD 许可。
- **Python** 标准库（解析 ELF、FDT 与 AVB 结构）。
- **Linux 内核**（GPL-2.0）。`data/android/` 中的模块名与元数据来自固件中的内核模块。
- **OP-TEE** 文档（*Hoya architecture* 页面），用于第 10 节的参考。其文档的许可证请参阅 OP-TEE 仓库。

## 商标

Meta、Ray-Ban、Oculus、Qualcomm、Snapdragon、FastConnect、Android、Linux、NXP、Analog Devices、Maxim、Texas Instruments、Apple（MFi）、Visionox、Novatek、Sharp 以及其他产品或公司名称，仅用于标识本仓库中的器件、固件与组件。使用这些名称不代表背书或任何关联。

## 关联声明

本仓库是独立分析。它不隶属于、不受赞助于、也未获得 Meta Platforms, Inc.、Qualcomm 或文中提及的任何其他厂商的认可。
