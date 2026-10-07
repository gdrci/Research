# 04 - 内核、ramdisk、厂商分区与设备树

[English](04-android-kernel-and-vendor.md)

## boot.img

启动镜像为版本 4。头部的命令行为空，因为命令行由 `vendor_boot` 提供。

| 字段 | 值 |
|---|---|
| 内核大小 | 28,148,224 字节 |
| ramdisk 大小 | 2,049,602 字节（legacy LZ4） |
| 内核版本横幅 | `Linux version 5.10.240-perf-gd253e0b2f72b` |
| 内核格式 | ARM64 `Image` |

`-perf` 后缀是本内核构建的名称。`g` 前缀后面的哈希是 git 的惯用写法，说明内核是从 git 树构建的。

### init ramdisk 中的构建属性

init ramdisk 中的 `system/etc/ramdisk/build.prop` 内容如下：

```
ro.product.bootimage.device=greatwhite
ro.bootimage.build.date=Mon Jun  1 17:31:45 PDT 2026
ro.bootimage.build.version.release=12
ro.bootimage.build.version.sdk=32
ro.bootimage.build.type=user
ro.bootimage.build.tags=release-keys
```

SDK 32 对应 Android 12L。这些值已验证，与厂商指纹一致。

### init ramdisk

ramdisk 包含四个普通文件：`init`（2.7 MB）、`adb_debug.prop`、`system/bin/e2fsck` 和 `system/etc/ramdisk/build.prop`。文本文件位于 `data/android/boot_ramdisk/`。`init` 是第一阶段的 init 程序。已验证。

## vendor_boot.img

版本 4，页大小 4096。

| 字段 | 值 |
|---|---|
| 厂商 ramdisk | 13,523,624 字节，legacy LZ4，块大小 8 MiB |
| DTB | 408,428 字节，加载地址 `0x01F00000` |
| Bootconfig | 175 字节 |
| ramdisk 表 | 1 项 |

### 命令行

```
androidboot.memcg=1 androidboot.usbcontroller=a600000.dwc3 printk.devkmsg=on
log_buf_len=512k cgroup_disable=pressure sdhci_msm_scaling.default_perf_governor=1
androidboot.hardware=greatwhite firmware_class.path=/vendor/firmware/
androidboot.selinux=enforcing bootconfig buildvariant=user
```

`androidboot.selinux=enforcing` 表示 SELinux 以 enforcing 模式启动。`firmware_class.path` 指定内核查找固件文件的位置。

### Bootconfig

bootconfig 块（`data/android/vendor_boot/bootconfig.txt`）包含：

```
androidboot.hardware=greatwhite
androidboot.memcg=1
androidboot.usbcontroller=a600000.dwc3
androidboot.load_modules_parallel=true
androidboot.hibernation_resume_device=259:61
```

`259:61` 是用于休眠恢复的块设备的主设备号和次设备号。已验证。它对应哪个分区取决于设备的块设备编号，我尚未映射。

### 厂商 ramdisk 内容

共 224 个普通文件：

- `lib/modules/`：214 个内核模块。
- `first_stage_ramdisk/fstab.greatwhite`：第一阶段的 fstab。
- `avb/`：三个 AVB 公钥，分别为 `q-gsi.avbpubkey`、`r-gsi.avbpubkey` 和 `s-gsi.avbpubkey`。后缀 `gsi` 是 Android Generic System Image 的命名惯例。

### 设备属性

`ro.board.platform=neo`、`ro.hardware.egl=adreno`、`ro.hardware.camera=qcom`、`persist.vendor.qcom.bluetooth.soc=hamilton`。

`neo` 是厂商代码使用的板级平台名。`hamilton` 是厂商属性中指定的蓝牙/Wi-Fi 组合芯片，AOP 镜像也提到了它（第 05 节）。

## 第一阶段 fstab

文件：`data/android/vendor_ramdisk/fstab.greatwhite`。

| 挂载点 | 来源 | 类型 | 选项与标志 |
|---|---|---|---|
| `/system`、`/product`、`/system_ext` | 逻辑分区 | ext4，只读 | `avb=vbmeta_system`，`first_stage_mount` |
| `/vendor`、`/odm` | 逻辑分区 | ext4，只读 | `avb=vbmeta`，`first_stage_mount` |
| `/metadata` | `by-name/metadata` | ext4 | `data=journal`，`formattable`，第一阶段 |
| `/vendor/firmware_mnt` | `by-name/modem` | vfat，只读 | `context=u:object_r:firmware_file:s0` |
| `/vendor/dsp` | `by-name/dsp` | ext4，只读 | `context=...adsprpcd_file...` |
| `/vendor/bt_firmware` | `by-name/bluetooth` | vfat，只读 | `uid=1002`，`gid=3002` |
| `/data` | `by-name/userdata` | f2fs | `fileencryption=aes-256-xts:aes-256-cts:v2+emmc_optimized+wrappedkey_v0`，`inlinecrypt`，`checkpoint=fs` |
| `/mnt/vendor/persist` | `by-name/persist` | ext4 | `sync` |
| `/storage/usbotg` | USB 主机 | vfat | `voldmanaged=usbotg:auto` |
| zram 交换区 | `/dev/block/zram0` | swap | `zramsize=1610612736`（1.5 GB），后备设备 256 MB |

这里有三点值得注意：

- `/data` 使用硬件封装密钥（`wrappedkey_v0`）并配合内联加密。密钥处理由下面的 `hwkm` 与 `crypto-qti-hwkm` 完成。
- 基带、DSP 和蓝牙固件分别位于独立分区，运行时以只读方式挂载。内核从 `/vendor/firmware/` 加载它们。
- `/metadata` 在首次启动时可以被格式化，设备正是在这里创建加密元数据。

## 内核配置

文件：`data/android/kernel/config.txt`，共 7,581 行，其中 1,754 个选项为 `y`，184 个为 `m`。

| 选项 | 状态 | 作用 |
|---|---|---|
| `CONFIG_MODULE_SIG` | 未设置 | 内核不校验模块签名 |
| `CONFIG_CFI_CLANG` | 未设置 | 未启用 clang 控制流完整性 |
| `CONFIG_ARM64_PTR_AUTH` | y | 指针认证 |
| `CONFIG_ARM64_BTI_KERNEL` | y | 分支目标识别 |
| `CONFIG_SHADOW_CALL_STACK` | y | 影子调用栈 |
| `CONFIG_ARM64_MTE` | y | 内存标记扩展 |
| `CONFIG_RANDOMIZE_BASE` | y | KASLR |
| `CONFIG_STACKPROTECTOR_STRONG` | y | 栈金丝 |
| `CONFIG_HARDENED_USERCOPY` | y | 用户拷贝边界检查 |
| `CONFIG_STRICT_KERNEL_RWX` | y | 内核代码段只读 |
| `CONFIG_INIT_ON_ALLOC_DEFAULT_ON` | y | 分配时清零 |
| `CONFIG_SECURITY_SELINUX_DEVELOP` | y | 编入 SELinux 开发钩子 |
| `CONFIG_KGDB` | 未设置 | 无串口内核调试器 |
| `CONFIG_DYNAMIC_DEBUG` | 未设置 | |
| `CONFIG_MAGIC_SYSRQ` | y | 启用 SysRq 组合键 |
| `CONFIG_DEBUG_FS` | y | 挂载 debugfs |
| `CONFIG_KVM` | 未设置 | 无 KVM，虚拟化层为 Gunyah |
| `CONFIG_HIBERNATION` | y | 支持休眠 |
| `CONFIG_DM_VERITY_FEC` | y | dm-verity 前向纠错 |
| `CONFIG_FS_VERITY` | y | 文件级 verity |
| `CONFIG_PSTORE_RAM` | y | 崩溃日志保存在内存中 |
| `CONFIG_QCOM_QFPROM` | m | QFPROM 驱动，编译为模块 |
| `CONFIG_QCOM_QFPROM_SYS` | 未设置 | 未编译 `qfprom-sys` 接口 |
| `CONFIG_MSM_TMECOM_QMP` | m | 通过 QMP 与 TME 通信 |
| `CONFIG_META_OATMEAL`、`CONFIG_META_GRANOLA_OATMEAL` | 未设置 | Meta 专用选项，本构建均关闭 |
| `CONFIG_SECURITY_YAMA`、`CONFIG_SECURITY_LOCKDOWN_LSM` | 未设置 | |

有几点值得注意。内核启用了较强的利用缓解措施（PAC、BTI、MTE、影子栈、KASLR、栈金丝、用户拷贝加固）。模块签名关闭，这意味着厂商模块是靠所在分区和 AVB 的校验而被信任的，内核本身并不校验签名。`SELINUX_DEVELOP` 已编入，但命令行设定为 `enforcing`。

## 内核模块

文件：`data/android/vendor_ramdisk/modules_modinfo.tsv`，每个模块一行，包含许可证、描述、作者和依赖。共 214 个模块：199 个为 GPL v2，11 个为 GPL，4 个为双许可 BSD/GPL。106 个模块有依赖。每个模块的 vermagic 都与 `5.10.240-perf-gd253e0b2f72b SMP preempt mod_unload modversions aarch64` 一致。

与其他分析相关的模块：

| 模块 | 描述（来自 modinfo） | 依赖 | 与本分析的关系 |
|---|---|---|---|
| `nvmem_qfprom.ko` | Qualcomm QFPROM driver | 无 | 内核的熔丝读取驱动。作者 Srinivas Kandagatla（Linaro）。 |
| `tmecom-intf.ko` | TME communication interface | 无 | 内核与 TME 固件的连接。 |
| `hwkm.ko` | QTI Hardware Key Manager library | `tmecom-intf` | 密钥处理经由 TME。 |
| `crypto-qti-hwkm.ko` | Crypto HWKM library for storage encryption | `hwkm` | 存储加密密钥（`wrappedkey_v0` 路径）。 |
| `qcom-dload-mode.ko` | MSM Download Mode Driver | 无 | 下载模式，与 XBL 的 cookie 对应。 |
| `qcom-reboot-reason.ko` | MSM Reboot Reason Driver | 无 | 复位原因（设备树一侧见第 06 节）。 |
| `mfi_i2c_driver.ko` | MFi I2C driver | 无 | 配件认证的 I2C 接口。目标芯片见 DTBO。 |
| `cdsp-loader.ko`、`adsp_loader_dlkm.ko`、`q6_dlkm.ko`、`mdt_loader.ko` | DSP 加载器 | 视情况 | 从 `/vendor/dsp` 加载 DSP 固件。 |
| `msm_kgsl.ko` | 3D Graphics driver | 多个 | GPU 驱动，使用 `speed_bin` 字段。 |
| `camera.ko` | Camera Request Manager | 多个 | 摄像头管线。 |
| `gh_rm_drv.ko`、`gh_msgq.ko`、`mem_buf.ko` | Gunyah 资源与消息驱动 | `gh_msgq` | 虚拟化层侧的消息与共享内存。 |

`hwkm.ko` 依赖 `tmecom-intf.ko`，是这组模块中关于密钥流向最清楚的证据：内核请求 TME，由 TME 完成实际工作。TME 固件就是第 02 节提到的 XBL 一侧的组件。

## 设备树

厂商 DTB 的导出结果位于 `data/android/vendor_ramdisk/vendor_dtb_dump.txt`。相关节点如下：

- `/soc/qfprom@221c8000`：熔丝块。`reg = <0x221c8000 0x1000>`，标记为 `read-only`。
- `/soc/qfprom@221c8000/gpu_speed_bin@119`：熔丝字段，位于字节 `0x119`，第 5 到 12 位。
- `/soc/qfprom@0`：消费者，`compatible = "qcom,qfprom-sys"`，`nvmem-cell-names = "gpu_speed_bin"`。
- `/soc/qcom,kgsl-3d0@3d00000`：GPU。其 `nvmem-cell-names` 项为 `speed_bin`，指向同一字段。
- `/soc/reboot_reason`：从 PMIC SDAM（`sdam@b100/restart@48`，第 1 到 7 位）以及共享 IMEM（`msm-imem@146aa000/restart_reason@65c`）读取 `restart_reason`。
- `/soc/qcom,spmi@c42d000/qcom,pm8150@0`：PM8150 PMIC。

有两点说明。`qfprom-sys` 消费者指向的内核配置 `QCOM_QFPROM_SYS` 未设置，因此读取该节点的并不是这个接口。复位原因有两个存储位置，因此即使 PMIC 被复位，复位原因仍可能被保留。

## DTBO 覆盖层

文件：`data/android/dtbo/overlay_components.tsv`。`dtbo.img` 分区包含 18 个覆盖层。每个覆盖层都是完整的板级配置。18 个覆盖层的头部 `id` 和 `rev` 字段都是零，因此头部无法标识板型。覆盖层之间的差别在于启用了哪些组件。

以下按组件组列出，并给出 18 个覆盖层中启用它的数量：

| 组别 | 节点 | 启用情况 |
|---|---|---|
| 显示 | `qcom,dsi-display-primary`、`qcom,dsi-display-secondary`、`qcom,mdss_dsi_ctrl0/1`、`qcom,mdss_mdp`、`qcom,dp_display`、`qcom,wb-display`、`sde_rsc_rpmh` | 18 |
| LCoS 面板驱动 | `lcosOP02220BA@65`、`lcosOP03010@64`（`meta,lcos-i2c-OP02220`、`meta,lcos-i2c-OP03010`） | 各 18 个。`lcosOP02220BA` 在全部 18 个中为 `okay`；`lcosOP03010` 没有 status 属性。 |
| 显示电源 | `pmicOP02220@44`、`pmicOP03010@40` | `pmicOP02220` 在 18 个中；`pmicOP03010` 在 16 个中（另 2 个禁用） |
| 显示背光或偏置（根据名称推断） | `ktb8399@60`（`kinetic,ktb8399`） | 18 个，全部 `okay` |
| 显示温度 | `max31875@48`、`@49`、`@4A` | 6 个覆盖层中 `okay`，12 个中 `disabled` |
| 显示虚拟传感器 | `display-virtual-sensor`、`skin-virtual-sensor`、`outdoor-virtual-sensor`、`power-state-sensor` | `display-virtual-sensor` 在 7 个中为 `okay` |
| 温度 | `tmp114@4C`、`@4D`、`@4E` | 分别在 4、4、1 个覆盖层中 |
| 电量计 | `max17332@36` | 1 个 |
| 充电与电源管理 | `max77813@18`（13 个中 `disabled`，3 个中 `okay`）、`max77813_se8_i2c@18`（2 个）、`max77789@69`、`mp28167@60`、`rt6160@75`、`raa491901@29`、`pmicDA9172@6A`（1 个） | 各不相同 |
| 摄像头 | `qcom,cam-sensor0`、`qcom,eeprom0`、`oculus,cam_fsync`、`qcom,cam-res-mgr` | 18 |
| 输入 | `gpio_keys`、`camera_key`、`p1_power_slider`（13）、`rt685_detect`（13） | 各不相同 |
| 音频 | `rt685_detect`（`gpio-keys`，13 个）、`meta,rt600_ctrl` | 各不相同 |
| 配件与 USB | `mfi343s00176@10`（`meta,mfi-i2c`，18 个中 `okay`）、`ptn5150@1d`（18 个中 `disabled`）、`usb_conn_gpio` | 各不相同 |
| 指示灯 | `aw2026@64`（`awinic,aw2026_led`） | 18 |
| 外设链路 | `stp-interface`、`spi-stp@0`（`meta,spi-stp`）、`st60a3g1@6d`（`meta,st60-i2c`，18 个中 `disabled`） | 各不相同 |
| 电源与电池 | `metabattery`、`mcu_thermistor`、`ads1115@49`、`hw-comparator-sensor` | 18 |
| 其他 Meta 节点 | `amem`、`hyperoff@0`（11）、`reboot_reason`、`ramoops@a6c00000` | 各不相同 |

LCoS 的名称和 `meta,lcos-i2c` 兼容字符串指向 LCoS（硅基液晶）微显示驱动。哪个驱动驱动哪块面板，以及出厂设备实际使用哪一个，尚未确定。`ptn5150` USB-C 控制器和 `st60a3g1` 器件在全部 18 个覆盖层中都存在但处于禁用状态，我尚未确定它们的用途。

`mfi343s00176` 节点（`meta,mfi-i2c`）是 MFi 认证芯片。它在配件识别中的作用是根据名称推断的，未验证。

18 个覆盖层的数量，以及各覆盖层之间的差异，都已验证。每个覆盖层的根节点还带有型号名称和 `qcom,board-id`，因此每个覆盖层对应一种硬件版本。下一节给出对照表。

### 板级版本

每个覆盖层的根节点都有 `model`、`compatible`（`meta,greatwhite` 加上版本字符串）、`qcom,msm-id = <0x243 0x10000>`（18 个全部相同），以及 `qcom,board-id = <0x22 N>`。第二个值就是板级 ID。已验证。文件：`data/android/dtbo/board_ids.tsv` 与 `data/android/dtbo/board_component_matrix.tsv`（71 个组件 × 18 个板级版本）。

| 索引 | 型号名称 | 板级 ID |
|---:|---|---|
| 0 | Greatwhite Config Dev0 | 0xB0 |
| 1 | Greatwhite EVT1 Camera DOE | 0xBA |
| 2 | Greatwhite Dev0 2023 | 0xB3 |
| 3 | Greatwhite Dev1.0 | 0xBB |
| 4 | Protostar FF3 (RT700) | 0xD1 |
| 5 | Greatwhite DVT | 0xAE |
| 6 | Greatwhite Dev0.2 | 0xB7 |
| 7 | Greatwhite EVT2 | 0xBF |
| 8 | Greatwhite Config Dev0.1 | 0xB1 |
| 9 | Greatwhite Dev1.1 | 0xBD |
| 10 | Greatwhite PreP1 | 0xB2 |
| 11 | Greatwhite ULED | 0xB9 |
| 12 | Greatwhite PreP1+ | 0xB4 |
| 13 | Greatwhite PVT | 0xAF |
| 14 | Greatwhite P1 (RT700) | 0xB6 |
| 15 | Greatwhite P1 (RT600) | 0xB5 |
| 16 | Greatwhite EVT1 (RT700) | 0xB8 |
| 17 | Greatwhite EVT1 DOE2 (Onewire) | 0xBC |

名称给出了一条构建顺序：先是 Dev0 与 Dev1，然后是 PreP1、EVT1、EVT2、DVT 和 PVT，最后是 P1 版本。"Protostar FF3" 是原型标签。"ULED" 和 "Onewire" 只是名称，其硬件含义未确定。

P1 的 RT600 与 RT700 变体恰好在四个组件上不同。`hyperoff` 只存在于 RT700。`tmp114@4C` 和 `tmp114@4D` 只存在于 RT600。`display-virtual-sensor` 在 RT700 上禁用，在 RT600 上启用。`hyperoff` 的差异与软件一致：`mcu-properties.sh` 只在 RT700 配置中开启 hyperoff（第 09 节）。
