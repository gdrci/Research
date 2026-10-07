# 分区表

[English](partition_table.md)

| 序号 | 分区 | 字节数 | 类型 | SHA-256（前 16 位） | 作用（预期，详见文档） |
|---|---|---:|---|---|---|
| 1 | `abl` | 339,968 | ELF | `52ee2dc8b6647ef3` | Android 引导程序（ABL），ARM32 ELF |
| 2 | `aop` | 241,664 | ELF | `5dd8c9c8a091dbff` | 常开处理器固件（AOP.HO.4.0） |
| 3 | `aop_config` | 16,384 | ELF | `a1b676d12b48a399` | AOP 配置 |
| 4 | `bluetooth` | 1,224,704 | 其他 | `9f22be3a573bc190` | 蓝牙固件（FAT，/vendor/bt_firmware） |
| 5 | `boot` | 100,663,296 | Android 启动 | `1090962994e0f779` | Android GKI 启动镜像：内核 5.10.240 与 init ramdisk |
| 6 | `cpucp` | 106,496 | ELF | `5e5b7cccd5b7c06d` | CPU 控制处理器固件（RISC-V，SCMI） |
| 7 | `devcfg` | 57,344 | ELF | `e68dab205e07e54f` | DevCfg（电源管理与 QFPROM 标志，目标配置） |
| 8 | `dsp` | 67,108,864 | 其他 | `f5fcc454f532dd24` | 音频/计算/传感器 DSP 固件（ext4，/vendor/dsp） |
| 9 | `dtbo` | 24,117,248 | DTBO | `06f4125311547a8e` | 设备树覆盖层（18 个板级配置） |
| 10 | `featenabler` | 90,112 | ELF | `4fb8c054e494935b` | 功能使能器（按硬件版本的软件熔丝） |
| 11 | `hyp` | 1,228,800 | ELF | `2cccff6da124a373` | Hypervisor（smem 与 PIL 处理） |
| 12 | `imagefv` | 20,480 | ELF | `dfb6bb67b8cff059` | UEFI/镜像固件卷（ARM32） |
| 13 | `keymaster` | 368,640 | ELF | `5fd33a616ef98f48` | Keymaster 可信应用（密钥、系统版本） |
| 14 | `modem` | 38,522,880 | 其他 | `04030355fff6a1d9` | 基带固件（FAT，挂载于 /vendor/firmware_mnt） |
| 15 | `multiimgoem` | 16,384 | ELF | `549fdf6e632cca8e` | 多镜像容器（OEM） |
| 16 | `multiimgqti` | 12,288 | ELF | `adbf4e1889010b1f` | 多镜像容器（QTI） |
| 17 | `odm` | 53,850,112 | 其他 | `ac0b4ced2453ee3e` | ODM 分区 |
| 18 | `product` | 660,692,992 | 其他 | `fe4d2069f03080aa` | Android product 分区 |
| 19 | `qupfw` | 65,536 | ELF | `9a219b19e6a0654b` | Hexagon 固件（EM_QDSP6，作用未确认） |
| 20 | `recovery` | 104,857,600 | Android 启动 | `217ce83238d1d5ad` | 恢复模式镜像（boot v4，仅 ramdisk） |
| 21 | `shrm` | 61,440 | ELF | `66bb5cc9c5fbd4de` | 共享资源管理器固件（RISC-V，含 DDR 固件版本） |
| 22 | `system` | 1,456,967,680 | 其他 | `ab778a176c3b30fc` | Android 系统（Android 14） |
| 23 | `system_ext` | 417,329,152 | 其他 | `8665f5e948600d03` | Android system_ext 分区 |
| 24 | `tz` | 3,469,312 | ELF | `4e418f8343771347` | TrustZone（QSEE）安全世界，EL3 入口 |
| 25 | `uefi` | 2,670,592 | ELF | `f63acf3695c97d99` | UEFI（ARM64 ELF，启动设备检测，多核启动） |
| 26 | `uefisecapp` | 180,224 | ELF | `d6d3997f7bacf744` | UEFI 安全启动可信应用（证书与 PKCS7 处理） |
| 27 | `vbmeta` | 8,192 | AVB vbmeta | `340ffff6c7658bf2` | AVB 根：校验 boot、dtbo、vendor_boot 的哈希；vendor、odm 使用 dm-verity；链接 recovery 与 vbmeta_system |
| 28 | `vbmeta_system` | 4,096 | AVB vbmeta | `cd898111d5762a2d` | AVB：校验 system、system_ext、product |
| 29 | `vendor` | 460,947,456 | 其他 | `40e7f65885ef2b2b` | 厂商分区（Android 12 指纹） |
| 30 | `vendor_boot` | 100,663,296 | 厂商启动 | `586e4d32ed1b2cf0` | 厂商启动镜像：厂商 ramdisk（内核模块、fstab）与 DTB |
| 31 | `xbl` | 978,944 | ELF | `939e0acc0455b166` | 高通 XBL（二级引导程序，SRoT MBNv7 认证） |
| 32 | `xbl_config` | 147,456 | ELF | `641bcf3201b87e81` | XBL 平台与内存配置（覆盖层 pre-ddr-sxr-aurora） |
| 33 | `xbl_ramdump` | 708,608 | ELF | `0510b3aa53383829` | 带内存转储支持的 XBL 构建 |
