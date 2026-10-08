# 17 - Modem partition firmware: ADSP, CDSP and trusted applications

[中文](16-modem-partition-firmware.zh-CN.md)

`modem.img` is a FAT16 image with 165 files (section 05). Besides the modem and Wi-Fi set, it holds the firmware for two Hexagon processors (the application DSP, ADSP, and the compute DSP, CDSP) and about ten signed applications that run in TrustZone. This section covers their structure, their signatures, and what each application does. The file list is in `data/remote/modem_listing.txt`, and the signature evidence is in `data/remote/modem_firmware_signatures.txt`.

Status labels: observed means read from the file; inferred means a reasonable reading the file does not state; not found means not in the OTA.

## How these images are laid out

Each image is split into a header file (`.mdt`) and numbered segment files (`.bNN`). The `.mdt` file holds the ELF header and the program headers. Segment `NN` is in `.bNN` and its size equals the program header `p_filesz`. Observed for ADSP: `adsp.b01` is 6,804 bytes, the same as segment 1's `p_filesz` (`0x1A94`). The header file itself is the segment 0 file (`adsp.b00`, 1,396 bytes, the ELF header and 42 program headers).

Some program headers have no data. Segment 0 (flags `0x7000000`) is the header segment: its file `.b00` is the ELF header and the program headers, observed as 1,396 bytes. The last segment with flags `0x2000000` is the signature segment, and its file holds the hash table and the certificate chain.

**The hash table.** The signature segment contains one SHA-384 digest (48 bytes) for each non-empty program segment. The digests are at offset 288 plus 48 times the segment index. Observed for ADSP. A check of every non-empty segment of every image found its digest in the signature segment. For ADSP, all 39 non-empty data segments match; the signature segment itself is not hashed. The same holds for CDSP (11 of 11), and for the trusted applications (7 of 7 data segments each, for the eight split images). Observed. So the files are internally consistent: each segment is the one the signature covers.

**The certificates.** The signature segment also holds a DER certificate chain, which is readable with `openssl`. Observed. The chains are in `data/remote/modem_firmware_signatures.txt`.

## The processors

### ADSP (application DSP): `adsp.mdt` and `adsp.b00` to `adsp.b41`

- ELF32, machine `0xA4` (Hexagon), entry `0x87600000`, 42 program headers, 40 loadable segments, physical range `0x87600000` to `0x89300000`. Observed.
- Segments `24` and `40` are empty (`p_filesz` zero). The signature segment is `41`.
- The image holds the audio framework. Its strings include the module names `AudioSphereModule.so.1`, `CFCM.so.1`, `SAPlusCmnModule.so.1`, `aac_dec_module.so.1` and `aac_enc_etsi_module.so.1`. Observed. This is the Qualcomm signal-processing framework (SPF), which loads the audio processing modules that the Android-side audio routes call (section 12).
- The QuRT kernel functions (`qurt_api_version`, `adsp_pls_add_lookup`, `adsp_mmap_fd_getinfo`) are in the image, as are the memory-mapping functions. Observed.
- The ADSP image also has the string `SigVerify_HaveTestRoot`. Observed. The verifier therefore has a code path for a test root in addition to the production root (see the signing section below).

### CDSP (compute DSP): `cdsp.mdt` and `cdsp.b00` to `cdsp.b12`

- ELF32, machine `0xA4` (Hexagon), entry `0x89400000`, 13 program headers, 11 loadable segments, range `0x89400000` to `0x89E00000`. Observed. Segment `11` is empty and segment `12` is the signature segment.
- The image contains the same `wpss` and QDSS strings as the ADSP (QDSS trace configuration for the WPSS and Q6 blocks). Observed. This is the link to the WPSS subsystem noted in section 07: the WPSS firmware is not in the OTA, but its debug configuration strings are in the compute image.

### Trusted applications (TAs)

The trusted applications are AArch64 ELF64 images (machine `0xB7`), which the secure world loads. They are in two forms. Most have a split form (`.mdt` and `.bNN`) with eight data segments and a signature segment. Some also have a single `.mbn` file.

| Application | Form | Signer | What the strings show |
|---|---|---|---|
| `featenabler` | `.mdt` (9 headers, 5 loads) | Qualcomm SRoT MBNv7 and CASS-SBL4, with the Meta Greatwhite_FW chain | Feature enabler (section 06): feature IDs and SoC gating |
| `hdcp1` | `.mdt` | SECTOOLS test root | HDCP 1.x content protection |
| `hdcp2p2` | `.mdt` | SECTOOLS test root | HDCP 2.2 content protection |
| `hdcpsrm` | `.mdt` | SECTOOLS test root | HDCP system renewability message (revocation list) |
| `loadalgota64` | `.mdt` | SECTOOLS test root | An image loader: it checks the ELF and hash segment with `IIPProtector_verifySignature` and an anti-rollback version, and reports `Segment %d overlaps with ELF + PHT segment` |
| `mldapta` | `.mdt` | SECTOOLS test root | Certificate and key provisioning for an ML device-attestation identity. Its files are `/persist/data/mldapta/MlsDapCCCDeviceCert.crt`, `MlsDapCCCDevicePvKey.key` and `MlsDapCCCManuCert1.crt`. The purpose of "DAP" is not expanded in the image |
| `ovrtz64` | `.mdt` (test root) and `.mbn` (Meta chain) | both | `OVRTZ` (an Oculus/Meta TZ application). Secure hibernation HMAC key context and label |
| `palmprintengine64` | `.mdt` (test root) and `.mbn` (Meta chain) | both | Palm-print engine: `GATEKEEPER_*` errors and `PALMPRINT_CANCEL_ERROR`. It is a palm authentication app; the gatekeeper link is inferred from the error names |
| `soter64` | `.mdt` | SECTOOLS test root | SOTER key attestation: `ATTK` (attestation key), `KM SOTER SN UNIQUE ID`, and `/persist/data/soter/` |
| `sp_license` | `.mbn` | SECTOOLS test root | License application: `IPFM_CheckLicenseBuffer`, `Fail to install license by SKP` (the installation check for feature licences) |
| `widevine` | `.mbn` | SECTOOLS test root | Widevine DRM: `/persist/data/widevine/keybox_lvl1.dat`, `cert.dat`, `private_key.dat`, `master_gen_num.dat`, `provision_method.dat` |
| `smplap64` | `.mbn` (1,962,072 bytes) | SECTOOLS test root | A sample and test application: its strings are encryption, signing and RSA-OAEP test totals (`Total Encrypt/Decrypt Tests`) |

All of these are observed from the names and strings. The purpose lines are based on the strings, not on the code.

## Signing

Two signing hierarchies appear.

**The Meta chain.** The certificates are `Greatwhite_FW_Signing_3`, issued by `Greatwhite_FW_Root_3`, with `Greatwhite_FW_Root_0`, `_1`, `_2` and `_3` also present. All are issued by Meta Platforms Technologies, LLC, in Menlo Park, California. Valid 2023-12 to 2063-11. Observed. It signs the ADSP, the CDSP, `featenabler` (above the Qualcomm chain), and the `.mbn` forms of `ovrtz64` and `palmprintengine64`.

**The SECTOOLS test root.** The certificates are `SecTools Test User`, `SECTOOLS SECP384R1 CURVE TEST ROOT0` and `SECTOOLS SECP384R1 CURVE TEST ROOT`, issued by Qualcomm (`O = QUALCOMM`, `OU = CDMA Technologies`), with a SECP384R1 curve. Observed. It signs `hdcp1`, `hdcp2p2`, `hdcpsrm`, `loadalgota64`, `mldapta`, `soter64`, `sp_license`, `widevine` and `smplap64`, and the `.mdt` forms of `ovrtz64` and `palmprintengine64`.

This is an observed fact that matters for the documentation. Several shipped trusted applications are signed with a Qualcomm test root, not a production chain. The zap shader for the GPU carries the same test-root strings (section 08). The ADSP verifier includes the test-root branch (`SigVerify_HaveTestRoot`). Whether the device accepts the test root at run time is a property of the secure-world verifier, which is in the TrustZone image. Not checked here. The OTA does not show a run-time result.

## Relation to other sections

- `featenabler` is the TA that section 06 describes for the display SW-fuse feature IDs.
- The palm-print engine (`palmprintengine64`) is the authentication counterpart of the palm gesture that section 14 reports from the touch controller. Inferred from the names.
- The Widevine and HDCP apps are the content-protection side of the display (section 13).
- The ADSP's audio modules are the processing side of the Android routes in section 12. The NXP RT700 DSP (section 15) is a separate processor.
- `sp_license` is the feature-licence path. Section 03 covers the boot verification of the images; this is the run-time check for feature licences.

## What is not found

- The purpose of `mldapta`'s "DAP" acronym. Not expanded in the image.
- The TA source or the TA's command interface beyond the strings.
- The run-time check that accepts or rejects the test root. It is in the TrustZone verifier, not in these images.
- The ADSP's audio module code, beyond the names. The binary is in the segments.

## Evidence

- `data/remote/modem_listing.txt`: the file list of `modem.img`.
- `data/remote/modem_firmware_signatures.txt`: the ELF header fields, the SHA-384 coverage, and the certificate subjects for every split image and single-file TA.
- `data/remote/modem_verinfo.txt`: the build manifest of `modem.img`.
