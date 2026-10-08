# 11 - SELinux and vendor policy

[中文](11-selinux-and-vendor-policy.zh-CN.md)

This section covers the SELinux policy that ships in the vendor partition, and the files that map names to labels: service, HIDL service, property and file contexts, plus the app-side `seapp_contexts`, `mac_permissions.xml` and the denial metadata. The files are in `vendor/etc/selinux/` of the OTA. Every count below was taken from those files; the scan scripts are not kept. The summary and hashes are in `data/android/selinux/policy_summary.txt`.

## Scope and version

- `plat_sepolicy_vers.txt` is `32.0`. This is the platform policy version. Observed.
- The CIL names carry the version as a suffix: `init_32_0`, `hwservicemanager_32_0`, `servicemanager_32_0`, `system_server_32_0`, `tee_32_0`. The vendor policy is compiled against platform 32.0. Observed.
- Android 12 is the vendor base (section 04), and the platform policy version 32.0 matches the Android 12 release. Inferred from the version table; the mapping is not in the files.

The vendor policy sits on top of the platform policy. `plat_pub_versioned.cil` (13,860 lines, 1.0 MB) is the platform's public policy for version 32.0, which the vendor policy must not conflict with. Its contents are not decoded here. Observed as a file.

## vendor_sepolicy.cil

The file is 507,018 bytes and 5,325 lines of CIL. Top-level forms, counted:

| Form | Count | Meaning |
|---|---:|---|
| `allow` | 3,136 | Allowed access |
| `type` | 631 | Declared types |
| `roletype` | 631 | Role for each type |
| `typeattributeset` | 241 | Attribute membership |
| `genfscon` | 211 | Labels for `sysfs` (205) and `proc` (6) paths |
| `dontaudit` | 161 | Suppressed denial logs |
| `typetransition` | 147 | Automatic labels for new objects (144 parse with four fields) |
| `neverallow` | 82 | Compile-time prohibitions |
| `typeattribute` | 64 | Attribute declarations |
| `allowx` | 17 | Extended-permission allows |
| `expandtypeattribute` | 3 | Attribute expansions |

Of the 631 types, 258 start with `vendor_`, 175 with `hal_`, and 71 with `sysfs`. Observed.

### Largest allow sources

`init` (443 rules), `vendor_qti_init_shell` (130), `vendor_init` (101), `hwservicemanager` (97), `hal_oculus_sensors` (82), `hal_power_default` (73), `hal_audio_default` (70), `autobrightness` (59), `tee` (55), `vendor_hal_perf_default` (48), `servicemanager` (47), `system_server` (46), `vndservicemanager` (43), `hal_graphics_composer_default` (42), `mediacodec` (41). Observed. The top sources show where the vendor policy is widest: the init domains, the sensor HAL, the power and audio HALs, and the TEE.

### Domain pattern

Each HAL has a domain pair. For example `hal_audio_default` and `hal_audio_default_exec`. The `_exec` type labels the binary, and `init` changes to the domain on exec through a `typetransition`:

    typetransition init hal_audio_default_exec process hal_audio_default

Of the 144 `typetransition` rules with four fields, 132 start from `init_32_0`, and 128 of those follow this exec pattern. The other rules cover `postprocess_init` (5), `vendor_rfs_access` (2), and the graphics HALs' tmpfs files. Observed.

### Oculus and Meta domains

Meta and Oculus domains are the most distinctive part of the policy. The type list includes:

- `hal_oculus_backlight`, `hal_oculus_battery`, `hal_oculus_bluetooth`, `hal_oculus_catty`, `hal_oculus_devicecert`, `hal_oculus_display`, `hal_oculus_dock`, `hal_oculus_keyboxinstaller`, `hal_oculus_lcos`, `hal_oculus_remotethermal`, `hal_oculus_sensors`, `hal_oculus_sensors_iad`, `hal_oculus_wifi`, `hal_oculus_devicecert`, `hal_usb_oculus`. Observed.
- `hal_lpi_mcu`, the domain of the MCU-backed HALs (section 09).
- `hal_palmauth_vendor_data_file`, a data type whose name points to palm authentication. Inferred from the name.

`hal_oculus_sensors` is the source of 82 allow rules, the second-largest HAL. Observed.

### neverallow

The 82 `neverallow` rules constrain what the domains may do. A sample: `hal_secureclock_service` and `hal_sharedsecret_service` may not `add` or `find` on `service_manager`. Observed. These rules keep the secure-clock and shared-secret services out of the general service manager.

## Service, HIDL service, property and file contexts

These four files map names to labels. The counts are from `data/android/selinux/`.

| File | Entries | What it maps |
|---|---:|---|
| `vendor_service_contexts` | 42 | AIDL/binder service names to a service label |
| `vendor_hwservice_contexts` | 59 | HIDL interface names to a service label |
| `vendor_property_contexts` | 86 | Property name prefixes to a property label |
| `vendor_file_contexts` | 892 | File paths (regular expressions) to a file label |
| `vndservice_contexts` | 3 | Vendor binder service names |

### Service contexts

Examples (observed):

- `vendor.meta.hardware.time.ITime/default` to `hal_time_service`
- `vendor.meta.hardware.battery.IBattery/default` to `hal_battery_service`
- `vendor.meta.hardware.security.palmauth.IPalmAuthenticator/default` to `hal_palmauth_service`
- `meta.wearables.captureengine.ICaptureEngine/default` to `captureengineservice_service` and `.../wcs` to `wearablecameraservice_service`
- `meta.internal.xrwifi.IXrWifi/default` to `xrwifi_service`

Twenty of the 42 service entries map to `hal_lpi_mcu_service`, including the button, hinge, case, companion, light, mount, power and sensor interfaces. Observed. The MCU HAL names are described in section 09. The `lpi_mcu` service binary registers 20 AIDL interfaces, which matches the 20 service entries. Resolved: an earlier draft of section 09 said 17 and missed three.

### HIDL service contexts

Examples (observed):

- `vendor.oculus.hardware.display::IDisplayRefresh` to `hal_oculus_display_hwservice`
- `vendor.oculus.hardware.lcos::ILcos` to `hal_oculus_lcos_hwservice`
- `vendor.oculus.hardware.devicecert::IDeviceCert` to `hal_oculus_devicecert_hwservice`
- `vendor.meta.hardware.glasses.frames::IGlassesFrames` to `hal_mcu_default_hwservice`
- `vendor.oculus.hardware.graphics.composer::IComposer` to `hal_oculus_display_hwservice`

30 of the 59 HIDL entries are `oculus` interfaces, and 4 are `meta`. Observed.

### Property contexts

The 86 property entries are grouped by owner:

- `persist.vendor.meta.*`: uweb, audio HAL, displaymapping. Observed.
- `persist.vendor.ovr.*` and `vendor.ovr.*`: `vendor_oculus_prop`. Observed.
- `vendor.meta.palmauth.*`, `vendor.meta.palmcheck.*`, `vendor.meta.palmexp.session.id.*`: `vendor_palmauth_prop`. Observed.
- `vendor.meta.mcu_hal.*`: `vendor_meta_hal_lpi_mcu_prop`. Observed.

### File contexts

The 892 file rules are regular expressions. The path roots, counted by first directory, are `vendor` (478), `dev` (159), a `(vendor|system/vendor)` alternation (134), `sys` (48), `data` (25), `persist` (15), `mnt` (15) and `odm` (9). Observed.

The most used file label is `same_process_hal_file` (431 rules). It labels the HAL shared objects that run inside the HAL process. `vendor_custom_ab_block_device` (20) labels the A/B block devices, and `persist_cal_file` (7) labels calibration files in `/mnt/vendor/persist`. Observed.

## App-side contexts

- `vendor_seapp_contexts` has one entry: `user=_app seinfo=platform name=com.qualcomm.timeservice domain=vendor_timeservice_app type=app_data_file levelFrom=all`. Observed. This gives the time service app its own domain.
- `vendor_mac_permissions.xml` (2,197 bytes) holds one signer. The signer is the certificate that signs the `platform` seinfo tag. The certificate is `CN = Greatwhite_AOSP_Platform`, issued by `CN = Greatwhite_Aosp_Root`, both `O = "Meta Platforms Technologies, LLC"`, Menlo Park, California. It is valid from 2023-12-12 to 2063-12-02, uses an RSA 2048-bit key and SHA-256 with RSA. The SHA-256 fingerprint is `8F:66:39:8B:31:DF:70:9F:20:CE:BF:C8:5B:F9:46:79:46:9A:81:88:01:E5:CD:5D:51:34:07:77:1C:3B:5D:53`. Observed from the certificate in the file. Any app signed with this key receives the `platform` seinfo label.

The `vendor_mac_permissions.xml` file has the comment `AUTOGENERATED FILE DO NOT MODIFY`, so it is produced by the build. Observed.

## Denial metadata

`selinux_denial_metadata` (1,503 bytes, 35 rows) is a list of denial pairs that the build tracks, with a bug reference for each. Each row is `source-domain target-type class b/<bug>`. There are 17 distinct bug references. Examples: `system_server zygote process` (b/77856826), `untrusted_app untrusted_app netlink_route_socket` (b/155595000), `zygote labeledfs filesystem` (b/170748799). Observed.

These rows are the known denials for the platform, recorded so that the build can review them. They are not a list of current denials on the device.

## Boot-time SELinux

The kernel command line sets `androidboot.selinux=enforcing` (section 04). So the policy is loaded in enforcing mode. Observed. The kernel config enables `CONFIG_SECURITY_SELINUX_DEVELOP` (section 04), which is a build option; whether the development hooks are used at run time is not checked here.

## Hardware names in the policy

The `genfscon` sysfs paths name hardware that the device tree also names:

- `pm8150@0` PMIC and its RTC, `power-on@800` (the same PMIC as section 04)
- `remoteproc-adsp`, `remoteproc-cdsp` and `188101c.remoteproc-spss` remote processors (section 05)
- `max17332-battery` and `max17332-charger` fuel gauges
- `mhi0` on the PCIe bus, which is probably the Wi-Fi chip's transport (section 07). Inferred from the path and the `mhi` driver.

Observed. Some of these names come from a shared base policy, so they are not proof that the hardware is present on this device. The device-tree nodes in section 04 confirm the PMIC; the fuel gauges and PCIe paths are not checked separately.

## What is not found

- The compiled policy binary (`sepolicy`) is not in the OTA. The CIL files are the input to the build. Not found.
- The platform policy that the vendor policy extends (`plat_pub_versioned.cil` is only the public part). Not decoded.
- The runtime denial log from a device. Not in the OTA.

## Evidence

- `data/android/selinux/policy_summary.txt`: counts, hashes and the form table.
- `data/android/selinux/vendor_service_contexts`, `vendor_hwservice_contexts`, `vendor_property_contexts`, `vendor_seapp_contexts`, `vndservice_contexts`, `plat_sepolicy_vers.txt`, `selinux_denial_metadata`: copies of the small files.
- The large files (`vendor_sepolicy.cil`, `plat_pub_versioned.cil`, `vendor_file_contexts`, `vendor_mac_permissions.xml`) are not copied. Their SHA-256 hashes are in `policy_summary.txt` so they can be matched against the OTA.
