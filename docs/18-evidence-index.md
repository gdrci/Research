# 18 - Evidence index

[中文](18-evidence-index.zh-CN.md)

This index lists every file under `data/` in the repository, the sections that cite it, and the first line of the file so a reader can tell what it holds. A file is cited **by name** when a section names it. A file is cited **by directory** when a section describes its directory, but the file itself is not named. A file marked **none** is not cited anywhere yet.

Counts are from the repository at the time of writing: 145 files, 2,862,270 bytes.

## By directory

| Directory | Files | Bytes |
|---|---:|---:|
| `data/analysis/` | 4 | 3,241 |
| `data/android/` | 41 | 918,306 |
| `data/avb/` | 3 | 6,405 |
| `data/dsp/` | 3 | 535,090 |
| `data/ghidra/` | 18 | 151,030 |
| `data/inventory.json/` | 1 | 33,943 |
| `data/mcu/` | 1 | 12,733 |
| `data/partition_table.md/` | 1 | 3,504 |
| `data/partition_table.zh-CN.md/` | 1 | 3,679 |
| `data/qfprom_literal_candidates.json/` | 1 | 839 |
| `data/remote/` | 9 | 21,350 |
| `data/secure/` | 27 | 47,671 |
| `data/strings/` | 20 | 1,097,518 |
| `data/userspace/` | 9 | 23,781 |
| `data/xbl/` | 6 | 3,180 |

## By file

| File | Bytes | Used in | Cited by | Content (first line) |
|---|---:|---|---|---|
| `data/analysis/decode_calibration.txt` | 116 | 02 | directory | NOTE: invalid control (adsp.b02 is data). |
| `data/analysis/isa_tests.txt` | 1,083 | 02 | file name | NOTE: the Hexagon control adsp.b02 is 62% zero words (data, not code). Its Hexagon rows... |
| `data/analysis/qupfw_decode.txt` | 874 | 02 | directory | NOTE: superseded. High decode rates here come from zero-filled and repetitive data, not... |
| `data/analysis/thumb_arm_tests.txt` | 1,168 | 02 | directory | Function-boundary statistics (per 1000 items). Random baseline: Thumb halfword bx lr 0x... |
| `data/android/audio/audio_config_summary.txt` | 4,842 | 12, 15 | file name | Vendor audio configuration summary (fs/vendor/etc of greatwhite.zip). Counts from XML p... |
| `data/android/audio/audio_effects.xml` | 10,931 | 12 | file name | <?xml version="1.0" encoding="UTF-8"?> |
| `data/android/audio/backend_conf.xml` | 8,209 | 12 | file name | <?xml version="1.0" encoding="ISO-8859-1"?> |
| `data/android/audio/card-defs.xml` | 13,799 | 12 | file name | <!--  Copyright (c) 2019,2021 The Linux Foundation. All rights reserved.      --> |
| `data/android/audio/ftm_test_config_neo-idp-sg-snd-card` | 3,114 | 12 | file name | tc 1 |
| `data/android/audio/ftm_test_config_neo-idp-snd-card` | 8,364 | 12 | file name | tc 1 |
| `data/android/audio/ftm_test_config_neo-qxr-snd-card` | 5,729 | 12 | file name | tc 1 |
| `data/android/audio/hw_info.xml` | 5,185 | 12 | file name | <?xml version="1.0" encoding="UTF-8"?> |
| `data/android/audio/max98388_v2.sh` | 4,849 | 12, 17 | file name | #!/bin/sh |
| `data/android/audio/microphone_characteristics.xml` | 671 | 12 | file name | <?xml version="1.0" encoding="ISO-8859-1"?> |
| `data/android/boot_ramdisk/adb_debug.prop` | 373 | 04 | file name | # Note: This file will be loaded with highest priority to override |
| `data/android/boot_ramdisk/build.prop` | 931 | 01, 04 | file name | #################################### |
| `data/android/camera_display/cameraserver.greatwhite.rc` | 528 | 08, 13 | file name | # Override of default frameworks/av/camera/cameraserver/cameraserver.rc behavior. |
| `data/android/camera_display/continuousaicamera_nova.rc` | 527 | 13 | file name | service continuousaicamera /system_ext/bin/continuousaicamera_nova |
| `data/android/camera_display/display_settings.xml` | 419 | 13 | file name | <?xml version='1.0' encoding='utf-8' standalone='yes' ?> |
| `data/android/camera_display/fix-gw-display-pmic.rc` | 176 | 13, 17 | file name | # When /vendor/hw/bin/ is available, fix-up the display power setting  ASAP: |
| `data/android/camera_display/init.hw.camera.rc` | 922 | 08, 13 | file name | on init |
| `data/android/camera_display/init.qti.display_boot.sh` | 11,773 | 13 | file name | #!/vendor/bin/sh |
| `data/android/camera_display/procamera.rc` | 405 | 13 | file name | service procamera /system_ext/bin/procamera |
| `data/android/camera_display/stubcameraservice.rc` | 214 | 13 | file name | on property:persist.vendor.media.enableStubCamera=1 |
| `data/android/camera_display/summary.txt` | 760 | 03, 11, 12, 13, 15 | file name | Camera and display userspace summary (fs/system_ext, fs/vendor, fs/odm of greatwhite.zi... |
| `data/android/camera_display/vendor.qti.hardware.display.composer-service.rc` | 369 | 13 | file name | service vendor.qti.hardware.display.composer /vendor/bin/hw/vendor.qti.hardware.display... |
| `data/android/dtbo/board_component_matrix.tsv` | 7,832 | 04 | file name | component	0:Greatwhite Config Dev0	1:Greatwhite EVT1 Camera DOE	2:Greatwhite Dev0 2023	... |
| `data/android/dtbo/board_ids.tsv` | 1,826 | 04 | file name | index	model	compatible	qcom,msm-id	qcom,board-id	nodes	dtbo_bytes |
| `data/android/dtbo/overlay_components.tsv` | 2,814 | 04 | file name | node	compatible	overlays_present (of 18) |
| `data/android/kernel/config.txt` | 214,061 | 04, 07, 08 | file name | # |
| `data/android/kernel/security_options.tsv` | 862 | 04, 08 | directory | option	state |
| `data/android/selinux/plat_sepolicy_vers.txt` | 5 | 11 | file name | 32.0 |
| `data/android/selinux/policy_summary.txt` | 2,347 | 11 | file name | SELinux vendor policy summary (fs/vendor/etc/selinux of greatwhite.zip). Counts from te... |
| `data/android/selinux/selinux_denial_metadata` | 1,503 | 11 | file name | dnsmasq netd fifo_file b/77868789 |
| `data/android/selinux/vendor_hwservice_contexts` | 5,853 | 11 | file name | android.hardware.media.c2::IConfigurable                           u:object_r:hal_codec... |
| `data/android/selinux/vendor_property_contexts` | 7,652 | 11 | file name | #line 1 "out/soong/.intermediates/system/sepolicy/vendor_property_contexts/android_comm... |
| `data/android/selinux/vendor_seapp_contexts` | 119 | 11 | file name | user=_app seinfo=platform name=com.qualcomm.timeservice domain=vendor_timeservice_app t... |
| `data/android/selinux/vendor_service_contexts` | 4,017 | 11 | file name | vendor.qti.hardware.display.config.IDisplayConfig/default u:object_r:vendor_hal_vnddisp... |
| `data/android/selinux/vndservice_contexts` | 196 | 11 | file name | manager                 u:object_r:service_manager_vndservice:s0 |
| `data/android/vendor_boot/bootconfig.txt` | 175 | 04 | file name | androidboot.hardware=greatwhite |
| `data/android/vendor_ramdisk/fstab.greatwhite` | 4,894 | 04 | file name | # Copyright (c) 2019-2020 The Linux Foundation. All rights reserved. |
| `data/android/vendor_ramdisk/kernel_modules.txt` | 3,386 | 04, 07, 12, 13, 14, 17 | directory | adsp_loader_dlkm.ko |
| `data/android/vendor_ramdisk/modules_modinfo.tsv` | 14,566 | 04, 07, 17 | file name | module	license	description	author	depends |
| `data/android/vendor_ramdisk/vendor_dtb_dump.txt` | 562,388 | 04, 07, 12, 13, 14, 17 | file name | / |
| `data/android/vendor_ramdisk/wpss_dt_nodes.txt` | 720 | 07 | file name | Device-tree nodes naming WPSS (data/android/vendor_ramdisk/vendor_dtb_dump.txt, binary-... |
| `data/avb/hashtree_rebuild.txt` | 2,271 | 03 | file name | dm-verity tree rebuild, from vbmeta*.img descriptors and the partition images |
| `data/avb/vbmeta_summary.txt` | 2,976 | 03 | file name | == vbmeta.img |
| `data/avb/verify_results.txt` | 1,158 | 03 | file name | == vbmeta.img |
| `data/dsp/dsp_symbol_table.txt` | 533,006 | 15, 17 | file name | DSP app symbol table (symbol_table.elf inside dsp.default.rt700.tub, EM_XTENSA). Column... |
| `data/dsp/dsp_tub_manifest.json` | 1,589 | 15 | file name | { |
| `data/dsp/dsp_tub_subimages.txt` | 495 | 15 | file name | dsp.default.rt700.tub: 4429312 bytes, sha256 da8ae200fbab870b166d97e778da88b9d2925dfe94... |
| `data/ghidra/aop_entry_thumb2_disasm.txt` | 389 | 05 | file name | # program aop.img lang ARM:LE:32:v8T |
| `data/ghidra/import_map.json` | 20,955 | 01 | file name | [ |
| `data/ghidra/sbl1_appsbl_record.txt` | 656 | 02 | file name | SBL1 image-descriptor records (sbl1.elf, data at 0x148B6A40..0x148B6CE0). |
| `data/ghidra/sbl1_elf_loader_and_el3_handoff.txt` | 1,298 | 02 | file name | SBL1 ELF loader object and EL3 hand-off (sbl1.elf, Ghidra decompiles). |
| `data/ghidra/sbl1_fn148298a4_decompiled.txt` | 1,755 | 01, 02, 03, 05, 06 | directory | SBL1 FUN_148298A4 (protocol registry lookup). Ghidra decompile, headless, program sbl1.... |
| `data/ghidra/sbl1_fn1482d254_wrapper_decompiled.txt` | 248 | 01, 02, 03, 05, 06 | directory | # program sbl1.elf lang AARCH64:LE:64:v8A |
| `data/ghidra/sbl1_fn14839ae4_uefi_ref_decompiled.txt` | 30,282 | 01, 02, 03, 05, 06 | directory | # program sbl1.elf lang AARCH64:LE:64:v8A |
| `data/ghidra/sbl1_fn1485ef90_decompiled.txt` | 2,444 | 01, 02, 03, 05, 06 | directory | # program sbl1.elf lang AARCH64:LE:64:v8A |
| `data/ghidra/sbl1_fn148612ec_boot_ram_partition_decompiled.txt` | 3,834 | 01, 02, 03, 05, 06 | directory | # program sbl1.elf lang AARCH64:LE:64:v8A |
| `data/ghidra/sbl1_memmap_decompiled.txt` | 5,561 | 02, 06 | file name | # program sbl1.elf lang AARCH64:LE:64:v8A |
| `data/ghidra/sbl1_proto3e_mmu_decompiled.txt` | 7,022 | 02 | file name | SBL1 protocol 0x3E object (vtable at 0x148B72C0), Ghidra decompile. |
| `data/ghidra/sbl1_protocol_table.txt` | 3,122 | 02 | file name | SBL1 bulk protocol registration table at 0x148B5060 (51 entries, stride 0x30) |
| `data/ghidra/sbl1_xblconfig_partition_evidence.txt` | 4,864 | 02 | file name | SBL1 boot step that registers image regions (sbl1_config.c). Ghidra decompiles. |
| `data/ghidra/tz_fuse_paths_decompiled.txt` | 14,483 | 01, 02, 03, 05, 06 | directory | # program tz.img lang AARCH64:LE:64:v8A |
| `data/ghidra/tz_mmio_mapper_decompiled.txt` | 32,951 | 02, 06 | file name | # program tz.img lang AARCH64:LE:64:v8A |
| `data/ghidra/uefi_vb_protocol_methods_decompiled.txt` | 1,985 | 03 | file name | # program vb.pe lang AARCH64:LE:64:v8A |
| `data/ghidra/uefi_verifiedboot_decompiled.txt` | 17,430 | 03 | file name | VerifiedBootDxe (uefi.img DXE volume, PE image at decompressed offset 0x74804, 61,504 b... |
| `data/ghidra/xbl_primary_stub_thumb2_disasm.txt` | 1,751 | 02 | file name | # program stub.bin lang ARM:LE:32:v8T |
| `data/inventory.json` | 33,943 | 01 | file name | [ |
| `data/mcu/mcu_console_strings.txt` | 12,733 | 14, 17 | file name | MCU firmware console strings (mcu.default.rt700.tub, file offsets). Extracted by printa... |
| `data/partition_table.md` | 3,504 | 01 | file name | # Partition table |
| `data/partition_table.zh-CN.md` | 3,679 | 01, 02, 03, 04, 05, 06, 07, 08, 09, 11, 12, 13, 14, 15, 16, 17 | directory | # 分区表 |
| `data/qfprom_literal_candidates.json` | 839 | 06 | file name | { |
| `data/remote/bluetooth_listing.txt` | 1,827 | 05, 07 | file name | type=FAT16/12 dirs=1 files=51 total_bytes=780143 |
| `data/remote/bluetooth_version_files.txt` | 700 | 07 | file name | bluetooth.img (FAT16, extracted with a local FAT16 helper; 8.3 names shown as stored) |
| `data/remote/dsp_adsp_files.txt` | 809 | 05, 07, 08, 16 | directory | AudioSphereModule.so.1 |
| `data/remote/dsp_cdsp_files.txt` | 381 | 05, 07, 08, 16 | directory | fastrpc_shell_3 |
| `data/remote/dsp_map_adsp.txt` | 492 | 05, 07, 08, 16 | directory | ../../build/ms/dynamic_modules/aurora.adsp_la.prod/libsysmon_skel.so |
| `data/remote/dsp_map_cdsp.txt` | 1,159 | 05, 07, 08, 16 | directory | ../../build/ms/dynamic_modules/aurora.cdsp.prod/libevadsp_3_0.so |
| `data/remote/modem_firmware_signatures.txt` | 9,319 | 16 | file name | Modem-partition firmware sets: split images (.mdt + .bNN), ELF headers, signature-segme... |
| `data/remote/modem_listing.txt` | 5,832 | 05, 07, 16 | file name | type=FAT16/12 dirs=3 files=165 total_bytes=36487937 |
| `data/remote/modem_verinfo.txt` | 831 | 07, 08, 16 | file name | { |
| `data/secure/featenabler_display_swfuse_decompiled.txt` | 5,618 | 06 | file name | featenabler.img (AArch64 TA), Ghidra analysis (program featenabler.img). Decompiled rou... |
| `data/secure/featenabler_summary.txt` | 1,606 | 02, 03, 06 | directory | featenabler.img (ELF64 AArch64, TA). Evidence from the image; disassembly by capstone. |
| `data/secure/hyp_mmio_map.tsv` | 1,579 | 02, 06 | file name | va	pa	attr	perm	size |
| `data/secure/hyp_pil_arb_fuse_table.txt` | 3,133 | 06 | file name | hyp.img: PILSubsys_getArbFuseBank and its subsystem table. Observed by AArch64 disassem... |
| `data/secure/hyp_rm_objects_and_arb_fuse.txt` | 1,590 | 06 | file name | hyp.img is the Gunyah/QTEE hypervisor resource manager (AArch64 ELF, entry 0x80000000). |
| `data/secure/hyp_arb_fuse_xref_scan.txt` | 19 | 06 | file name | hyp.img cross-references to the arb-fuse table; no writer of the bank field found |
| `data/secure/hyp_arb_fuse_reference_check.txt` | 12 | 06 | file name | Ghidra reference check on getArbFuseBank and the table getter; no references to the getter |
| `data/secure/tz_object_0x91_provider_scan.txt` | 21 | 06 | file name | tz.img object-0x91 invoke path and store scans; provider not found |
| `data/secure/tz_context_creator_decomp.txt` | 107 | 06 | file name | Decompiled tz.img context wrapper, list-node registration callers and switch-in; no thread-block pair store |
| `data/secure/tz_switch_in_entry_scan.txt` | 12 | 06, 02 | file name | tz.img branch and pointer scan for the switch-in function; no in-image caller |
| `data/secure/sbl1_tz_entry_context_chain.txt` | 13 | 02, 06 | file name | SBL1 loader objects and the TrustZone entry context; the object at loader +0x28 not identified |
| `data/secure/sbl1_loader_context_chain.txt` | 5 | 02 | file name | SBL1 loader context: protocol services 0x0E and 0x11, boot image driver, selector |
| `data/secure/sbl1_loader_ctx_slot.txt` | 16 | 02 | file name | Config-object layout: the loader transfer slot at +0x28 is config entry 1; record table still unresolved |
| `data/secure/sbl1_image_record_table.txt` | 17 | 02 | file name | SBL1 per-image record table: layout, ids, zero transfer values |
| `data/ghidra/sbl1_boot_image_driver_decompiled.txt` | 410 | 02 | file name | Ghidra decompile of the SBL1 boot image driver FUN_14825980 |
| `data/secure/keymaster_rollback_strings.txt` | 1,061 | 03 | file name | keymaster.img (ELF, 368,640 bytes), strings related to rollback, version, boot state an... |
| `data/secure/object_0x91_firmware_scan.txt` | 638 | 02, 03, 06 | directory | Firmware-wide scan for table rows keyed by object ID 0x91 (low 32 bits 0x91, high 32 bi... |
| `data/secure/oem_key_pointer_search.txt` | 1,137 | 06 | file name | Search for references to the OEM configuration key names (TrustZone, tz.img; devcfg.img). |
| `data/secure/oem_rot_key_xref_search.txt` | 846 | 06 | file name | Search for the reader of OEM_rot_pk_hash1_fuse_values (tz.img file 0x13A3AC, vaddr 0x1C... |
| `data/secure/sbl1_cpr_fuse_getters.txt` | 2,365 | 06 | file name | SBL1 fuse-field getters (sbl1.elf, AArch64). Observed from disassembly. Ghidra did not ... |
| `data/secure/tme_antirollback_location.txt` | 571 | 06 | file name | Anti-rollback manager location (xbl.img, TME RISC-V ELF at offset 0x1C2F4) |
| `data/secure/tme_ghidra_rollback_search.txt` | 1,074 | 06 | file name | TME firmware (RISC-V32 IMC) analysis, from xbl.img TME ELF. Ghidra import with auto-ana... |
| `data/secure/tz_antirollback_path.txt` | 5,047 | 06 | file name | TrustZone anti-rollback flag path (tz.img, AArch64). Disassembly by capstone; Ghidra ha... |
| `data/secure/tz_context_creation_search.txt` | 731 | 06 | file name | TrustZone object-invoke context: creation search (tz.img). |
| `data/secure/tz_dispatch_table.txt` | 721 | 06 | file name | TrustZone static dispatch table (tz.img), 16-byte rows: 8-byte key (type << 16 / method... |
| `data/secure/tz_mmio_table.tsv` | 243 | 02, 03, 06 | directory | TrustZone table at tz.img vaddr 0x1c141c40 (16-byte entries: base, count) |
| `data/secure/tz_mmio_table_users.txt` | 1,849 | 02, 06 | file name | TrustZone MMIO table at 0x1C141C40 (tz.img), 5 entries of (base u32, count u32): |
| `data/secure/tz_object_0x91_and_oem_key_search.txt` | 929 | 06 | file name | TrustZone object 0x91 and OEM key reader searches (tz.img, devcfg.img) |
| `data/secure/tz_object_0x91_requests.txt` | 1,476 | 06 | file name | tz.img: every code site that loads the value 0x91 (MOVZ w/x, imm16 = 0x91), with a disa... |
| `data/secure/tz_object_invoke_chain.txt` | 2,221 | 06 | file name | TrustZone object-invoke chain (tz.img, Ghidra analysis project tzana and capstone disas... |
| `data/secure/tz_pkhash_path.txt` | 3,449 | 06 | file name | TrustZone (tz.img) PK-hash ("PKHashExt") path, root-of-trust key. Observed by AArch64 d... |
| `data/secure/tz_sw_fuse_check_area.txt` | 4,027 | 06 | file name | TrustZone SW-fuse check area (tz.img), disassembly by capstone (verified by reading the... |
| `data/secure/tz_thread_block_setter.txt` | 2,080 | 06 | file name | tz.img: writers of the per-thread block pointer (tpidrro_el0). Observed by AArch64 disa... |
| `data/secure/uefi_fuse_region_table.txt` | 1,653 | 06 | file name | Region table in the UEFI fuse-controller PE (decompressed DXE volume, PE at 0x168E84). |
| `data/secure/uefi_fv_header.txt` | 682 | 02, 03, 06 | directory | uefi.img firmware volume (verified header fields): |
| `data/secure/uefi_verified_boot_findings.txt` | 811 | 03 | file name | uefi.img DXE volume (gzip section, uncompressed 3,911,688 bytes). Evidence: data/string... |
| `data/secure/avb_rollback_string_search.txt` | 31 | 03 | file name | AVB rollback string search over boot-time images; gzip DXE volume decoded; system.img libavb strings |
| `data/secure/xbl_companion_digest_test.txt` | 534 | 02, 03, 06 | directory | XBL companion segment (xbl.img 0x1C074, 0x280 bytes) digest test. |
| `data/strings/abl.txt` | 1,856 | 03, 07 | directory | A7s`smIO |
| `data/strings/aop.txt` | 4,568 | 03, 07 | directory | 0hJF;FAi |
| `data/strings/aop_config.txt` | 1,270 | 03, 07 | directory | vrm.aoss |
| `data/strings/cpucp.txt` | 2,265 | 03, 07 | directory | o` Ro` lo` |
| `data/strings/devcfg.txt` | 10,171 | 03, 07 | directory | */+J0Xg: |
| `data/strings/featenabler.txt` | 11,340 | 03, 07 | directory | +5@).=A) |
| `data/strings/hyp.txt` | 101,769 | 03, 07 | directory | hih8(i58 |
| `data/strings/imagefv.txt` | 1,197 | 03, 07 | directory | z%qd$f)X |
| `data/strings/keymaster.txt` | 34,846 | 03, 07 | directory | @9))B)K6 |
| `data/strings/multiimgoem.txt` | 1,178 | 03, 07 | directory | Greatwhite_FW_Root_31)0' |
| `data/strings/multiimgqti.txt` | 698 | 03, 07 | directory | &YCGeb9< |
| `data/strings/qupfw.txt` | 2,383 | 03, 07 | directory | @ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmno |
| `data/strings/shrm.txt` | 1,910 | 03, 07 | directory | s0&:s %: |
| `data/strings/tz.txt` | 200,583 | 03, 07 | directory | +5@).=A) |
| `data/strings/uefi.txt` | 44,594 | 03, 07 | directory | hc8"hc8c |
| `data/strings/uefi_dxe_fv_strings.txt` | 556,915 | 03 | file name | Strings from the decompressed UEFI DXE firmware volume (uefi.img, GUID-defined section ... |
| `data/strings/uefisecapp.txt` | 10,218 | 03, 07 | directory | ()@)+%A) |
| `data/strings/xbl.txt` | 36,536 | 03, 07 | directory | CHIP_PROD_PROV_K_LBL |
| `data/strings/xbl_config.txt` | 27,668 | 07 | file name | /A006_7_0100_0_dcb.bin |
| `data/strings/xbl_ramdump.txt` | 45,553 | 03, 07 | directory | T)hj8	h*8 |
| `data/userspace/init_rc_files.txt` | 6,949 | 08, 09, 12, 13, 15 | file name | odm/etc/init/android.hardware.thermal-service.pixel.rc |
| `data/userspace/meta_hal_names.txt` | 2,840 | 07, 08, 09, 12, 13, 15 | directory | vendor.meta.airship.enable_multi_scope |
| `data/userspace/peripheral_firmware_headers.txt` | 1,875 | 08 | file name | Peripheral firmware headers (fs/vendor/firmware of greatwhite.zip). ELF fields via pyel... |
| `data/userspace/smartglass_apps.txt` | 2,099 | 09 | file name | SmartglassAccountsRelease.apk |
| `data/userspace/tub_contents.txt` | 2,153 | 09 | file name | case.default.cabo.tub (89600 bytes) |
| `data/userspace/tub_md5_tests.txt` | 3,036 | 09 | file name | mcu.core1.default.rt700.tub (87,552 bytes), manifest at file offset 0x14E00 (the JSON w... |
| `data/userspace/vendor_firmware_files.txt` | 661 | 08 | file name | CAMERA_ICP.b00 |
| `data/userspace/wifi_bt_init_and_modules.txt` | 1,937 | 07 | file name | Wireless kernel modules (data/android/vendor_ramdisk/modules_modinfo.tsv): |
| `data/userspace/wifi_config_and_symlinks.txt` | 2,231 | 07 | file name | vendor/etc/wifi listing and WCNSS_qcom_cfg.ini head (extracted): |
| `data/xbl/sbl1_memmap_function.txt` | 616 | 02, 07 | directory | SBL1 (xbl.img offset 0x4AFC4 program, vaddr base 0x14824000 region) |
| `data/xbl/sbl1_qfprom_xref.txt` | 590 | 02, 07 | directory | SBL1 (AArch64) references to 0x221C8000 (tools/aarch64_xref.py) |
| `data/xbl/string_regions.txt` | 464 | 02 | file name | String locations in xbl.img (file offsets) |
| `data/xbl/tme_lui_scan.txt` | 205 | 02 | file name | TME (RISC-V) image: LUI with immediates 0x221c8, 0x221c2, 0x221c4, 0x221c0 -> 0 hits. |
| `data/xbl/wpss_config_sections.txt` | 783 | 07 | file name | xbl config sections for WPSS (data/strings/xbl_config.txt, extracted): |
| `data/xbl/xbl_container.txt` | 522 | 02 | file name | XBL container (xbl.img, 978,944 bytes) - three embedded ELF programs |

## Files not copied

The OTA itself holds the large firmware and configuration files that the sections describe but the repository does not copy. Their hashes are in the evidence files of each section. Examples: `vendor_sepolicy.cil` (section 11, hash in `data/android/selinux/policy_summary.txt`), the audio policy and calibration files (section 12, hashes in `data/android/audio/audio_config_summary.txt`), the MCU and DSP tubs (sections 14 and 15, hashes in `data/dsp/dsp_tub_subimages.txt`), and the modem firmware images (section 16, hashes in `data/remote/modem_firmware_signatures.txt`).

## Tools

The scripts that produced these files are not part of the repository. The outputs are.
