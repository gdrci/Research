"""Generate data/partition_table.md from data/inventory.json (run after tools/inventory.py)."""
import json, sys
ROLE = {
 "xbl":"Qualcomm XBL (secondary bootloader core, image auth via SRoT MBNv7)",
 "xbl_config":"XBL platform/memory config (overlay pre-ddr-sxr-aurora)",
 "xbl_ramdump":"XBL build with ramdump support",
 "abl":"Android Bootloader (ABL), ARM32 ELF","uefi":"UEFI (ARM64 ELF, boot device detection, SMP bootstrap)",
 "uefisecapp":"UEFI secure-boot TA (cert/PKCS7 handling)","tz":"TrustZone (QSEE) secure world, EL3 entry",
 "hyp":"Hypervisor (Qualcomm hyp, smem and PIL handling)","devcfg":"DevCfg (PM/QFPROM flags, tgt config)",
 "keymaster":"Keymaster TA (keys, OS version/patch)","featenabler":"Feature enabler (SW-fuse feature gating)",
 "imagefv":"UEFI/image firmware volume (ARM32)","aop":"Always-On Processor firmware (AOP.HO.4.0)",
 "aop_config":"AOP config","cpucp":"CPU Control Processor firmware (RISC-V, SCMI)",
 "shrm":"Shared resource manager firmware (RISC-V; DDR fw version string)",
 "qupfw":"Hexagon firmware (EM_QDSP6; role not verified)",
 "multiimgqti":"Multi-image container (QTI)","multiimgoem":"Multi-image container (OEM)",
 "modem":"Modem firmware (FAT, mounted /vendor/firmware_mnt)","dsp":"aDSP/cDSP firmware (ext4, /vendor/dsp)",
 "bluetooth":"Bluetooth firmware (FAT, /vendor/bt_firmware)",
 "boot":"Android GKI boot: kernel 5.10.240 + init ramdisk","recovery":"Recovery (boot v4 image, ramdisk only)",
 "vendor_boot":"Vendor boot: vendor ramdisk (kernel modules, fstab) + DTB",
 "dtbo":"DT overlays","vbmeta":"AVB root: hashes for boot, dtbo, vendor_boot; dm-verity for vendor/odm; chains recovery & vbmeta_system",
 "vbmeta_system":"AVB for system/system_ext/product",
 "system":"Android system (Android 14)","system_ext":"Android system_ext","product":"Android product",
 "vendor":"Vendor (Android 12 fingerprint)","odm":"ODM partition",
}
inv = json.load(open(sys.argv[1]))
rows = ["| # | Partition | Bytes | Kind | SHA-256 (first 16) | Role (expected; see docs) |","|---|---|---:|---|---|---|"]
for i, it in enumerate(sorted(inv, key=lambda x: x["image"]), 1):
    n = it["image"][:-4]
    rows.append(f"| {i} | `{n}` | {it['bytes']:,} | {it['kind']} | `{it['sha256'][:16]}` | {ROLE.get(n,'')} |")
open(sys.argv[2], "w").write("\n".join(rows) + "\n")
print(f"{len(rows)-2} rows -> {sys.argv[2]}")
