# 06 - QFPROM and fuses

[中文版](06-qfprom-and-fuses.zh-CN.md)

QFPROM is the fuse block on the SoC. Its bits are one-time-programmable. The boot chain, the kernel and the secure world all read values from it. This document lists what is known about the block, where each reader is, and what remains unknown. It describes how the system uses fuses. It does not describe any weakness.

## The block

The vendor device tree defines the block at `0x221C8000` with a 4 KB window:

```
qfprom@221c8000
    compatible = "qcom,qfprom"
    reg = <0x221c8000 0x1000>
    read-only
```

`read-only` means the kernel does not write fuses through this node. Writes happen in the secure world. Verified.

The device tree names one fuse cell:

| Cell | Offset | Bits | Users |
|---|---|---|---|
| `gpu_speed_bin` | `0x119`, 2 bytes | bit 5, 8 bits wide | GPU (`kgsl-3d0`, name `speed_bin`), and `qfprom@0` (`qcom,qfprom-sys`) |

The field gives the GPU speed bin, which the GPU driver uses to choose an operating point. It spans bits 5 to 12 of the two bytes at `0x119`. Verified from the device tree. What each value means is not known until the driver is read.

## The block's neighbours

Three other blocks sit next to the QFPROM window. The TrustZone table and SBL1's memory map both list them:

| Base | Where it appears | Count or size in that table |
|---|---|---|
| `0x221C0000` | TrustZone MMIO table, index 0 | count 8 |
| `0x221C4000` | TrustZone MMIO table, index 1 | count 4 |
| `0x221C2000` | TrustZone MMIO table, index 2; SBL1 region map | count 8 |
| `0x221C8000` | TrustZone MMIO table, index 3; hypervisor map; SBL1 region map; device tree | count 8 (TZ, 8 KB); 3 pages (hyp); 1 page (DTB) |

Only `0x221C8000` has a device-tree node. The names of the other three blocks are not known. The addresses are verified; the names are not.

## The TrustZone MMIO table

TrustZone has a table of five 16-byte entries at `0x1C141C40`: a 32-bit base and a 32-bit count per entry. Index 4 is `0x010C0000`.

Two functions read the table. `FUN_1C067548` passes flag `0x9041` and `FUN_1C067598` passes flag `0x9061`. Each rejects indices above 4, then maps the entry through `FUN_1C03ACAC`. Both have 16 call sites: 15 `BL` and one tail `B` each. Every index from 0 to 4 is used with both flags (`data/secure/tz_mmio_table_users.txt`).

The decompiled chain is `FUN_1C03ACAC`, which takes a lock, calls `FUN_146816F4`, and releases the lock. `FUN_146816F4` calls `FUN_14681A68`, a stage-1 translation-table mapper. That mapper writes block and page descriptors into the live tables and issues the `TLBI`, `DSB` and `ISB` maintenance instructions. No `SMC` instruction is involved, so the mapping stays in TrustZone (`data/ghidra/tz_mmio_mapper_decompiled.txt`).

What the flags select, from `FUN_14682D04`:

- `0x9041` maps the range read-write at EL1. `0x9061` differs only in bit 5, which sets `AP[2]` (the read-only bit). So `0x9061` maps it read-only.
- Both set execute-never (`UXN` and `PXN`), inner-shareable and the access flag, and both select MAIR attribute index 1. Index 1 is probably the device memory type. That is inferred.

The count's unit is KB. The mapper checks that the count is a multiple of four (whole 4 KB pages) and computes the end address as `base + count × 0x400`. So the QFPROM entry maps 8 KB in TrustZone. This is inferred from the mapper's arithmetic.

The mapper treats the two base arguments as virtual and physical. Both are the same here, so the mapping is an identity mapping.

## Mapping sizes disagree

- The device tree gives `0x1000` (one page).
- TrustZone's table gives 8 KB (inferred from the mapper's arithmetic above).
- The hypervisor's memory map gives `0x3000` (three pages) for `0x221C8000`, with attribute 4 and permission `0xF`. The record is `(va=0x221C8000, pa=0x221C8000, attr=0x4, perm=0xF, size=0x3000)` (`data/secure/hyp_mmio_map.tsv`).

These three can all be true. The hypervisor maps the whole neighbourhood, TrustZone maps 8 KB, and the device tree describes only the part the kernel uses. The values are verified; the reading that they are all consistent is an interpretation.

## Readers in the kernel

| Reader | Evidence | Status |
|---|---|---|
| `nvmem_qfprom.ko` | `CONFIG_QCOM_QFPROM=m`, description "Qualcomm QFPROM driver", author Srinivas Kandagatla (Linaro) | the main path |
| `msm_kgsl.ko` | GPU driver; the device tree gives `nvmem-cell-names = "speed_bin"` | uses `gpu_speed_bin` |
| `qfprom@0` consumer | `compatible = "qcom,qfprom-sys"` | `CONFIG_QCOM_QFPROM_SYS` is not set, so this is not a built driver interface |
| `qcom-reboot-reason.ko` | reboot reason from the PMIC SDAM and IMEM (section 04) | not the fuse block; listed for the restart path |

The NVMEM framework exposes each cell by name. A consumer asks for a cell and never addresses the fuse block directly. Not every `nvmem-cells` consumer reads QFPROM: the reboot-reason node reads the PMIC SDAM, while the GPU and the `qfprom-sys` node read the fuse block.

## Readers in the boot chain and the secure world

### SBL1

SBL1 (the AArch64 program inside `xbl.img`) has one direct reference to `0x221C8000`: a `mov w13, #0x8000` and `movk w13, #0x221c, LSL #16` pair at `0x1482CED4`. That code is in the memory-map function `FUN_1482CD30`, which has one caller at `0x14825B3C`. The function builds a table of region records that includes `0x221C2000` and `0x221C8000`, and it hands the table to a service found through protocol ID `0x3E` (`data/ghidra/sbl1_memmap_decompiled.txt`). The service is not decompiled yet.

### TrustZone

TrustZone (`tz.img`) holds the table above and two literal-pool slots with `0x221C8000`. TrustZone also has these names. They are strings, so their use is observed:

- `qsee_fuse_read`, `qsee_fuse_write`: the read and write API.
- `qsee_blow_sw_fuse`: blows a software fuse.
- `qsee_is_sw_fuse_blown`: checks whether a software fuse is already blown.
- `OEM_rot_pk_hash1_fuse_values`: the root-of-trust public key hash.
- `OEM_rot_enc_key1_fuse_values`: the root-of-trust encryption key entry.
- `oem_defer_fuse_prov_operation`: a deferred provisioning operation.
- `invoke-oem-spare-fuses failed: 0x%x, 0x%x, 0x%x`: the spare-fuse path.
- `qfprom_data`: a buffer for fuse data.

The PK-hash path in TrustZone (`data/secure/tz_pkhash_path.txt`) is observed as follows. The `PKHashExt` handler registers the name `GetPKHash` (function `0x1C395930`) and copies 32 bytes into its object at offset `+0x58` through `0x1C395C20` (`PKHashExtHandler_copyHash`, which calls a bounded copy `0x1C3AED14`). In the initialisation path the source is a constant in `.rodata` at `0x1C3BE01E`, next to a DER attribute for the license path `/persist/data/pfm/licen...`. So this path copies a value from the image, not from QFPROM. The function `0x1C396908` (the `GetPKHash`/`GetDeviceID` handler) takes a 16-byte device ID from a runtime object through method 6, and logs `IDeviceID_getClientDeviceID failed`. The provider of method 6 is not identified. The reader that turns `OEM_rot_pk_hash1_fuse_values` into the hash is therefore not found. Observed from disassembly; the copy source is the DER length byte `0x20`, so the copy may start one byte early, which is not verified.

DevCfg (`devcfg.img`) and TrustZone both have `PM_QFPROM_FLAG`, a flag that power management reads from the fuse block. Observed.

Featenabler (`featenabler.img`) uses software fuses to enable features per hardware revision (strings `soc_hw_version`, `ConfigureSwFuse failed for feature_id`, `DisplayCore_EnableSwFuse`). Observed.

### Hypervisor

The hypervisor has 8 literal-pool slots with `0x221C8000`, and its memory map has the `0x3000` record above. It is the most complete picture of the block's mapping. A scan of `hyp.img` finds no other constant in `0x221C8000`–`0x221CAFFF`: every slot is exactly `0x221C8000`, and there is one `movk` site with `0x221C`. So no code in the image addresses the extra pages by absolute address. Observed. The `0x3000` size may still cover them through a computed offset, which is not checked.

### TME

The TME firmware has no reference to the block: no `LUI` with the QFPROM immediates and no literal. Verified by search.

### SBL1 fuse getters (CPR)

SBL1 has a family of fuse-field getters in the `0x14881880`–`0x14881A30` range. They read 5-bit fields from the words `0x221C27F8`, `0x221C27FC` and `0x221C2800`, which lie in the `0x221C2000` block, not in the QFPROM block at `0x221C8000`. A dispatcher selects one of 15 fields from a jump table at `0x148AC670`. The table and bit positions are in `data/secure/sbl1_cpr_fuse_getters.txt`. Observed.

One caller uses the fields with a 0xF8-byte record stride, signed 16-bit limits, and a divide. SBL1 also contains the strings `CPR rev %d data not found in voltage plan` and `/cpr.bin`. So these getters read the CPR (core power reduction) calibration fields. Inferred from the strings and the arithmetic; the record and field names are not in the image.

SBL1 also reads four words of the QFPROM block directly through small getters at `0x14853EF4`–`0x14853F30`: `0x221C8780`, `0x221C8784`, `0x221C8788` and `0x221C878C`. Their consumers are not identified. Observed.

### TrustZone anti-rollback flag

The function behind `qsee_sfs_is_anti_rollback_enabled` is at `0x1C32D6E0` (the string reference is at `0x1C32D710`, source line `0x356`). It asks `FUN_1C32516C` for a one-byte flag. `FUN_1C32516C` keeps a per-thread cache in the TLS block (`tpidrro_el0`, byte `+0x18AB` is the valid marker, `+0x18AC` is the value). On a cache miss, it obtains an object for interface ID `0x91` through `FUN_1C32E024` and `FUN_1C32DFB0`. The second function invokes the object with the ID as a 4-byte buffer, through `FUN_1C302990`. The flag itself comes from the object for ID `0x91`. Its provider is not identified. Observed for the cache and the lookup; the source of the flag is not found. Disassembly is in `data/secure/tz_antirollback_path.txt`.

The request path for object `0x91` is now mapped (`data/secure/tz_object_0x91_requests.txt`). Only two code sites request it (`0x1C3251E0` and `0x1C325960`). Both call `FUN_1C32E024`, which first looks in a per-thread cache at `tpidrro_el0 + 0x28`. On a miss, `FUN_1C32DFB0` invokes the thread's root object: the function pointer at `tpidrro_el0 + 0x18` and the handle at `+0x20`, with operation `0x1001` and the 4-byte ID. So the provider of `0x91` is whatever function the thread context installed at `+0x18`. That makes the context creator the same open question as the provider. Observed from disassembly. The other sites that load `0x91` are log line numbers.

The object-invoke entry (`FUN_1C302990`) is a trampoline that jumps through a register, so object `0x91` is dispatched outside the code in `tz.img`. Its provider is not found. The object model is the same as the SBL1 protocol registry (`0x3E`, section 02), whose provider is now identified. The flag matters for `vbmeta`: a rollback counter for applications lives in RPMB (`tzbsp application rpmb version rollback label` in `tz.img`). That link is not yet confirmed in code.

### Where the rollback manager runs

The source name `AntiRollbackMgr.cpp` is in the TME firmware, inside `xbl.img`, next to GLink, SMEM and FreeRTOS strings, not in TrustZone. So the anti-rollback manager is a TME service. The link to the TrustZone flag (object `0x91`) is not confirmed: the TME is a separate processor, and the GLink channel from TZ to TME is the likely path, but that is unverified. A search for code that loads the string through RISC-V `auipc` pairs found 15 pairs in the whole TME image and none at that address, so the reference is probably in a table. Data: `data/secure/tme_antirollback_location.txt`.

TME code has no constant build of a QFPROM or TrustZone MMIO address (`lui`/`addi` pairs reconstructing `0x221C0000`–`0x221CFFFF` or `0x010C0000`–`0x010CFFFF`: none). So the TME does not read the fuse block directly in this image. Its rollback counter access must go through another component, most likely the TrustZone object model. This is inferred, not shown. Ghidra analysis of the TME is in `data/secure/tme_ghidra_rollback_search.txt`.

### Featenabler display software fuses

`featenabler.img` is a TrustZone application that enables display features from licences. Its software fuses are not qsee fuses. They are 32-bit words in a display hardware block, reached through `HWIOUtils_Read` and `HWIOUtils_Write`. Observed from the Ghidra decompile (`data/secure/featenabler_display_swfuse_decompiled.txt`).

Mapping from the licence's `FeatureID` to the fuse index (`DisplayCore_ConfigureSwFuse`):

| FeatureID | Index | Feature | Word offset |
|---|---|---|---|
| 1000 (0x3E8) | 2 | `Display_QLTM` | index * 4 + 8 = 0x10 |
| 1002 (0x3EA) | 12 | `Display_SPR` | 0x38 |
| 1003 (0x3EB) | 13 | `Display_Demura` | 0x3C |
| 1004 (0x3EC) | 14 | `Display_Allocate_Cache_Signal` | 0x40 |

Enabling writes `1` to the word. The status read (`DisplayCore_ReadSwFuseStatus`) returns true when the word has `(value & 0x11) == 1`.

Gating by `soc_hw_version` (`DisplayCore_IsFeatureSupported`, the value masked with `0xFFFFFF00`):
- `0xA0010100`, `0xA0010200`, `0xA0040100`, `0xA0080100`, `0x600F0100`, `0x600F0200`: features 1000, 1002, 1003 and 1004 are supported (mask `0x1D`). Feature 1001 is not.
- `0x60080100`, `0x60080200`, `0x600D0100`, `0x600D0200`, `0x60170100`: only feature 1000 is supported.
- Any other value: nothing is supported.

Not established: where the display block's base address comes from (`IDeviceRegionFinder` with a region name), the licence signature check, and which SoC is which `soc_hw_version`.

The object-invoke chain in `tz.img` (`data/secure/tz_object_invoke_chain.txt`): `FUN_1C32E024` is called with object IDs `0x30`, `0x12`, `0x61`, `0x114`, `0x91` (twice), `0xB` and `0x16`. The lookup `FUN_1C32DFB0` jumps through the function pointer stored at `tpidrro_el0 + 0x18` of the current thread block, with the handle at `+0x20`. The routine at `0x1C304010` loads that pair from a context block when a thread is switched in, after a magic check. So the object dispatcher is a function that the context supplies. Which function it is for each context, and how the contexts are created, is not yet established.

The context creator is still not found. The switch-in routine (`0x1C304010`) checks that the halfword at `+2` is `0x0002`. No simple constant store writes that value, and ten sites load `0x20000` into unrelated fields. Search log: `data/secure/tz_context_creation_search.txt`.

The thread-block pointer is written in a small set of places (`data/secure/tz_thread_block_setter.txt`). The setter `0x1C1399F8` is `msr tpidrro_el0, x0`; its only direct caller is the switch-in function at `0x1C108368`, which loads the block pointer from a context object at `+0x48`. The block is not allocated there. Its function-pointer slot is not found, so the switch-in function is probably reached through an object table. Two functions that set up context objects (around `0x1C07F848` and `0x1C096B08`) call the wrapper `0x1C108320`. They are candidates for the creator, but no code was found that writes the `+0x18` invoke function or the `+0x20` handle into a new block. The creator is therefore still open. The switch-in function `0x1C108368` has no caller inside `tz.img`: no branch, pointer or address-forming instruction reaches it. It is entered from outside the image, so the context that TrustZone receives at entry is supplied by code outside `tz.img` (`data/secure/tz_switch_in_entry_scan.txt`). Observed. The boot thread's block is the `x0` that SBL1 passes at the TrustZone entry (section 02, "The TrustZone entry context and its loader"). The loader path that receives that block runs through the `MBRD` driver object and is still not fully traced (section 02, "The TrustZone entry context and its loader"), so the origin of the `+0x18` invoke pair remains open. A static scan of `tz.img` for stores of a function address at `+0x18`, and for the object ID `0x91`, found no store of the invoke pair into a thread block (`data/secure/tz_object_0x91_provider_scan.txt`). Observed; the scan is not exhaustive.

The static dispatch table in `tz.img` has 61 rows of 16 bytes: an 8-byte key `(type << 16) | method` and a handler pointer. The type tag 2 matches the thread-context check in the switch-in routine. Object ID `0x91` is not a key in this table, so the object is resolved at run time. Observed. Evidence: `data/secure/tz_dispatch_table.txt`.

The UEFI fuse library has a table of named regions (`data/secure/uefi_fuse_region_table.txt`). Each row holds a name, a base and a size. The base is stored as physical address minus `0x20000000`, which is why the raw values look like `0x21C2000`. Restored, the regions are: `QFPROM_CORR` at `0x221C2000` (size `0x2000`); `FUSE_CONTROLLER_SW_RANGE0` at `0x221C4000`, `_RANGE1` at `0x221C5000`, `_RANGE3` at `0x221C7000`, `_RANGE4` at `0x221C8000`, `_RANGE5` at `0x221C9000` (each `0x1000`); `VIRT_FUSE_CONTROLLER_SW_RANGE3` at `0x221CA000`; TME RNG at `0x221D0000`; TME crypto at `0x221E4000`; RSCC at `0x22200000` and `0x22220000`; TME XPU at `0x22240000`. The `QFPROM_CORR` and `SW_RANGE4` addresses agree with the TrustZone MMIO table (`0x221C2000`, `0x221C8000`). The software-fuse ranges that hold anti-rollback state are therefore 4 KB windows inside the `0x221C` block. Observed. Which window holds the `vbmeta` index is not yet identified.

The TrustZone code that logs `qsee_is_sw_fuse_blown` results is in `data/secure/tz_sw_fuse_check_area.txt`. One function at `0x1C3ECD78` unpacks a 9-byte record into two big-endian 32-bit words and writes it back, so it is a record serialiser, not a fuse read. The routine that logs the fuse-blown result loops over a list read with `ldr w0,[x27,x8,lsl #2]`, which decodes as ASCII text, so the list is not a table of fuse IDs. Which SW fuse IDs the check uses is therefore still open.

`hyp.img` is a Gunyah/QTEE hypervisor resource manager, not a plain hypervisor. Its strings name the RPC, VM-creation, memparcel and SMC wait-queue sources, and a local and a remote object table (`localObjTable`, `remoteObjTable`, `LocalObj_retrieve`). That makes it a candidate for the object-invoke provider behind TrustZone's lookups, but no object-`0x91` row was found in it, so this is not confirmed. It also contains `PILSubsys_getArbFuseBank`, which suggests that peripheral images (PIL) are checked against a per-subsystem anti-rollback fuse bank. If that bank is one of the SW fuse ranges in the `0x221C` block, it is where the rollback state lives; the bank-to-subsystem mapping is decoded in part (see below). Observed from strings. Evidence: `data/secure/hyp_rm_objects_and_arb_fuse.txt`.

Cross-references for the bank table (`data/secure/hyp_arb_fuse_xref_scan.txt`). The table is a static array of 19 records at `0x2007E8` in `hyp.img`. The getter at `0x260C4` returns it. Its only code users are the lookup routines at `0x26000` and `0x26060` and `PILSubsys_getArbFuseBank` (`0x3EB4C`). No code in `hyp.img` writes the bank field (`+0xD8`) through a static address, and the file image has zero in every bank field. `PILSubsys_getArbFuseBank` has no reference of any kind in the image set. Ghidra's reference manager, run after forced disassembly of the code block, finds no reference to its entry. There is no direct call, no absolute or relative pointer, and no `ADR` or `ADRP`+`ADD` to it, and the name appears in no other image. Its callers are therefore outside the images analysed here. The bank values are set at run time by a path that is not in this image set, or they come from a source not yet located. Observed. Evidence: `data/secure/hyp_arb_fuse_reference_check.txt`, `data/ghidra/arb_fuse_refs_check.java`.

The TrustZone secure-boot status word has named bits, reported by one routine (at `0x1C3DFF30`, which calls the status service and logs each bit): bit 0 secboot enabling check, bit 1 secure HW key programmed, bit 2 debug-disable check, bit 3 anti-rollback check, bit 4 fuse configuration check, bit 5 RPMB provisioned check, bit 6 debug check in the image certificate, bit 8 TZ secure-debug fuse, bit 9 MSS secure-debug fuse, bit 10 CP secure-debug fuse, bit 11 non-secure secure-debug fuse. The status service is reached through an indirect slot at `0x1C401090`, which is zero in the file and filled at run time, so the function that computes bit 3 is not identified. Observed from strings and the reporter's code.

The hypervisor reads words of the software-fuse range that the UEFI region table names `FUSE_CONTROLLER_SW_RANGE4` (`0x221C8000`, 4 KB). Its boot code loads `0x221C8610`, `0x221C8700`, `0x221C8744` (from base `0x221C8000`) and `0x221C873C`. The `0x221C873C` word is tested: its low nibble is compared with the bit mask `0x4883` (bits 0, 1, 7, 11 and 14), and the result sets bits in a hypervisor state word. Observed from disassembly of `hyp.img` (AArch64, auto-analysed). Which fields those words hold, and whether they include the PIL arb-fuse-bank value, is not decoded. A flag at `0x9D4D4` gates the reads at seven sites; the copied words have no reader found yet (`data/secure/hyp_rm_objects_and_arb_fuse.txt`).

The PIL arb-fuse lookup is decoded in part (`data/secure/hyp_pil_arb_fuse_table.txt`). `PILSubsys_getArbFuseBank` (function `0x3EB4C`) takes a subsystem ID and an output pointer. It scans a table of 19 records of `0x148` bytes at `0x2007E8` (count in `0x93AD8`). The ID is matched at record offset `+0xD0`. The bank value is returned from `+0xD8` and the record flag `+0x118` controls the result: flag 1 returns error `0x300068`, and a normal match returns 0 with the value. A missing ID returns `0x300067`. Observed from disassembly. In the file image every bank value is zero, and no store to `+0xD8` was found, so the bank values are set at run time by code not located. Only the record with ID `0x2` has the flag set. The subsystem names for the IDs are not in the image, so the bank-to-subsystem mapping is not complete.

## Where the literal appears

Counts from a literal scan (`data/qfprom_literal_candidates.json`):

| Image | Occurrences | Note |
|---|---:|---|
| `hyp.img` | 8 | hypervisor memory map |
| `xbl.img` | 2 | both in SBL1, the AArch64 program |
| `xbl_ramdump.img` | 2 | same pattern as SBL1 |
| `tz.img` | 2 | TrustZone table |
| `recovery.img` | 5 | probably DTB data; not confirmed |
| `boot.img` | 2 | probably DTB data; not confirmed |

The counts in `boot` and `recovery` are most likely copies of the device tree, since those images contain device-tree blobs. The hits in `xbl`, `xbl_ramdump`, `tz` and `hyp` are the ones to follow.

The same scan found `0x00784000` in `qupfw` (once), `boot` (twice), `recovery` (seven times) and `vendor_boot` (twice). That is not the device-tree base, so it is not QFPROM. Earlier notes listed `0x00780000` as a candidate. Those hits are mostly device-tree data.

## The reboot-reason path

Reboot reasons are stored in two places. The device-tree node `/soc/reboot_reason` lists both:

1. `sdam@b100/restart@48` on the PM8150 PMIC, bits 1 to 7 of the SDAM byte at `0x48`. SDAM is a small register bank on the PMIC that keeps data across resets.
2. `msm-imem@146aa000/restart_reason@65c`, in shared IMEM at `0x146AA000`. The XBL config has the same base (`SharedIMEMBaseAddr = 0x146AA000`).

The second copy is in memory that survives a warm reset. Verified from both files. The reason-code values are not decoded yet.

## Link to verified boot

The rollback index in `vbmeta` is `1770249600` (section 03). Anti-rollback needs a counter that cannot be lowered, and the usual way to get one is a fuse-backed counter. The device's counter table has not been read, so the link between the vbmeta index and a fuse is a reasonable expectation, not a fact.

## Unresolved points

- The lock taken by `FUN_1C03ACAC` (through `FUN_1C062D44`), and the callers of `FUN_14681A68` outside the MMIO path.
- The per-record meaning of the SBL1 region table. The receiving service (protocol `0x3E`, the page-table builder) is identified in section 02, but the field layout of each record is not confirmed.
- Whether the extra two pages of the hypervisor's `0x3000` record are used through computed offsets. No absolute address in `hyp.img` points there.
- The byte `0x221C8119` and its neighbours, to confirm the `gpu_speed_bin` field and what else sits in those bytes.
- The reader of `OEM_rot_pk_hash1_fuse_values`, and its QFPROM offset. A further search found no pointer, relative pointer or adrp reference to any key name in `tz.img` or `devcfg.img`, so the key block is read by a non-pointer method (`data/secure/oem_key_pointer_search.txt`). The name is a key in the OEM configuration block of `tz.img` (around `0x13A295`–`0x13A7XX`, about 40 keys), and it also appears in `devcfg.img`. No code reference to it was found by ADRP+ADD, ADR, absolute pointer or relocation search (`data/secure/oem_rot_key_xref_search.txt`). The PK-hash handler path (`data/secure/tz_pkhash_path.txt`) does not read QFPROM directly, and its device-ID input comes from runtime object method 6. The reader is probably a name-based lookup over the OEM block, reached through that object. Not found.
- The provider of object `0x91` (the anti-rollback flag object, section above) and the code that builds the TrustZone thread context (`0x14680000` entry block). Neither is found in the images; searches are in `data/secure/tz_object_0x91_and_oem_key_search.txt` and `data/secure/tz_context_creation_search.txt`.
- The code that compares the vbmeta rollback index with a stored value.
- The featenabler display-block base address (`IDeviceRegionFinder` region name), the licence signature check, and the SoC name for each `soc_hw_version`.

The device tree and overlay check is done. The base device tree defines one fuse cell (`gpu_speed_bin`). The 18 overlays in `dtbo.img` reference only one nvmem cell, the restart reason, so they add no fuse cells. Verified.
