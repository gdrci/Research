# 14 - MCU console, LCoS display controller and sensor drivers

[中文](14-mcu-console-and-lcos.zh-CN.md)

This section documents what the MCU firmware in `vendor/firmware/mcu.default.rt700.tub` exposes through its command console: the LCoS (liquid-crystal-on-silicon) display controller, the LED drivers that light it, the touch controller, the inertial and ambient-light sensors, the hinge, and the STP transport. It corrects two earlier points in section 09 and closes the open item "LCoS HAL binary not found" in section 13.

Status labels: observed means read from the file; inferred means a reasonable reading the file does not state; not found means not in the OTA. The console strings are in `data/mcu/mcu_console_strings.txt` with their file offsets.

## What the MCU is

- The MCU firmware's source paths name a platform `rt700` (`arvr/firmware/projects/smartglasses/platforms/greatwhite/rt700/`). The container does not name NXP; the NXP identity is external knowledge and is not shown in the files. Its peripheral drivers are in `arvr/firmware/lib/uhal/peripherals/rt700/` (`rt700_clock.c`, `rt700_gpio.c`, `rt700_edma.c`, `rt700_spi_peripheral.c`, `rt700_power_domain.c`, `rt700_wdt.c`). Observed.
- The RTOS is FreeRTOS v10.4.6, with the port `GCC/ARM_CM33_NTZ/non_secure/port.c`, so the core is an Arm Cortex-M33 in non-secure mode (the core identity follows from the port path, which is inferred). Observed.
- The firmware tree is named `arvr/firmware/projects/smartglasses/platforms/greatwhite/rt700/`. Observed in the DSP image too (section 15). So the `rt700` in the file names is the processor platform, not only an audio codec. This corrects an earlier draft of section 09, which called it an audio-codec variant.
- The console is a set of named commands with help text. The firmware contains the help text `xra: See https://fburl.com/wiki/xra_mcu_commands for usage` (TUB 0x15BF15), which sits inside the `case.bin` payload by header offset; the link to the console command table is not shown. Observed. The wiki is not in the OTA.

## The LCoS console

LCoS is the micro-display engine. The console has a group of `lcos` commands (observed, `data/mcu/mcu_console_strings.txt`, file offsets `0x13E000` to `0x142000`):

Power and mode
- `lcos poweron`: runs the GPIO and I2C power sequence, without the init sequence.
- `lcos send-init-sequence`: sends the I2C sequence that puts LCoS into PGEN mode. It assumes power is on.
- `lcos init`: initialises LCoS in MIPI mode.
- `lcos set-already-initialized`: sets the configuration when the display is already on.
- `lcos poweroff`, `lcos toggle <interval seconds> <number of toggles>` (the default interval is 5 s; the command logs `Test complete.`, a link inferred from the adjacent strings `toggle` and `Test complete.`, with no call site in the data).
- `lcos mipi_rx <1/0>`: starts or stops the MIPI receive pipeline.
- `lcos clearscreen`, `lcos clearbus` (clears the display I2C bus by toggling the clock lane).

Test patterns
- `lcos pgen <pattern_name> <r> <g> <b>`. Pattern names are `disabled`, `checkerboard`, `hcolorbar`, `vcolorbar`, `hramp`, `vramp` and `solid`. RGB applies only to `solid`. An unknown name falls back to `checkerboard`. Observed.

Voltages (the names are observed; the physical roles are inferred from the names)
- `lcos set-pixel-voltage <pixel_voltage_mV` (as printed in the binary) and `lcos get-pixel-voltage` (reported as `Pixel Voltage: %u mV`).
- `lcos set-ito-voltages <pos_red_mV> <pos_green_mV> <pos_blue_mV> <neg_red_mV> <neg_green_mV> <neg_blue_mV>` and `get-ito-voltages`. ITO is indium tin oxide, the electrode layer. Inferred from the abbreviation.
- `lcos get-led-voltages` (reported as `RED:%d GREEN:%d BLUE:%d BLANK:%d`).

LED drivers
- `lcos setledgains <r> <g> <b>` (max 1023), `getledgains`.
- `lcos setledcurrents <r> <g> <b>` in micro-amperes (integer values), `getledcurrents`.
- `lcos getledbitres` reports the LED bit resolution and the rsense GPIO value.
- `lcos set-led-bitres-setting <auto|low|high>`, `get-led-bitres-setting`, and `get-led-bitres-threshold`. The threshold is printed per colour in micro-amperes (`r:%u, g:%u, b:%u microAmps`). It sets when the driver switches between high and low resolution.
- `lcos set-led-mode <pfm|pwm>` and `get-led-mode`. PFM and PWM are the mode names (help text at 0x13EDAA and 0x13F8FD). The expansions (pulse-frequency and pulse-width modulation) are inferred.
- `lcos set-interp-coeffs <r/g/b> <low_slope> <low_offset> <high_slope> <high_offset>` and `get-interp-coeffs`. The coefficients are in micro-amperes, for low and high resolution. Observed.

Temperature and health
- `lcos readtemp <rb/g/lcos/schedule>`: reads the display IC temperature from the red and blue LEDs (`rb`), the green LED (`g`), or LCoS itself. `schedule` is also accepted. Observed.
- `lcos get-error-counts`: prints `SOT_ERROR_FLAG_COUNT`, `CRC_ERROR_FLAG_COUNT`, `ECC_SINGLE_ERR_FLAG_COUNT`, `ECC_FATAL_ERR_FLAG_COUNT`, `SOT0_ERROR_COUNT` and `CRC_FAILURE_COUNT`. SOT is the MIPI start-of-transmission error. Inferred from the names.
- `lcos dump-de-otp`: dumps the system-level DE OTP readback. The DE OTP is a one-time-programmable block in the display driver. Inferred from the name.
- `lcos get-pmic-rev`: reads the PMIC chip ID (`PMIC chip ID: %d`). The display PMIC is the one named in section 04 (`pmicOP03010`, `pmicOP02220`).

Bus access
- `lcos init-i2c`, `lcos deinit-i2c`, and raw register access `lcos i2c r <device addr> <reg> <num bytes>` and `lcos i2c w <device addr> <reg> <data(x,y,z,...)>`. All values are hex. Observed.

Calibration and identity
- The LCoS settings are printed as `LCOS settings: is_pwm = %d, r = %d, g = %d, b = %d`.
- Factory calibration fields are named in the firmware: `VF_1MA_R/G/B` and `VF_140MA_R/G/B` (LED forward voltage at 1 mA and 140 mA), `OFFSET_LOW_RES_*`, `SLOPE_LOW_RES_*`, `OFFSET_HIGH_RES_*`, `SLOPE_HIGH_RES_*` (per colour). The field names are observed; their meaning (forward voltage at 1 mA and 140 mA) and their role as per-unit interpolation inputs are inferred.
- The serial-number fields are `Display SN`, `LCOS SN`, `LED SN` and `DDB SN`. Observed. Their values are on the device, not in the OTA.

## Why the LCoS HAL is not in the Android partitions

The Android side has SELinux labels for the LCoS HAL (`hal_oculus_lcos` with `vendor.oculus.hardware.lcos::ILcos`, section 11), and `ueventd.rc` sets `/dev/lcos-i2c-OP03010` and `/dev/lcos-i2c-OP02220` to mode 0660, owner and group `system`, plus a sysfs `offload_enabled` node (`ueventd.rc` line 368; labelled in `vendor_file_contexts` line 713). Section 13 does not cover that node. The `lcos_init` and `lcos_uio` labels are present too. The display control commands above are in the MCU firmware, though, and the Android partitions do not contain a binary that runs them. A directory walk with `debugfs` of `vendor`, `odm`, `system_ext` and `product` found no LCoS binary. `system.img` was not walked for this, so it is not ruled out. So the LCoS control path in the OTA is: the MCU runs the controller and its console; Android has device nodes and labels for an I2C bridge. Inferred from the console location and the device-node names. The node-to-MCU link is not shown in the files.

## Touch controller (PSoC)

The console prints `psoc in %s mode`. The Cypress/Infineon attribution is external knowledge; section 09 says so, and the files do not name the vendor. The MCU runs the touch driver. The console includes:

- `touch probe`, `touch mode [tuner]`, `touch r <reg_addr> <num>`, `touch w <reg_addr> <val...>`, `touch g <dev_addr> <num>`, `touch t <dev_addr> <val...>` (raw register and device access).
- `touch reboot-dfu`, `touch dfu` (the bootloader route for the `touch-app-b0.cyacd2` image in `touch.default.tub`, section 09).
- `touch read-touch-points`, `touch get[-presense|-dondoff]-ppc [<slot_id>]` and `touch set[-presense|-dondoff]-ppc [<slot_id>] <n_sub> <decn> <cdac_comp>` (per-slot capacitance settings).
- `touch set-use-case <cpu_freq_mhz> <refresh_rate_hz> <wake_on_touch> <deep_sleep> <sleep_in_active> <centroid_mode>`, `touch set-configuration` and `set-lp-configuration` (with `cdac`, `row_cdac`, `n_sub`, `sns_clk`, `cicrate` and similar fields).
- `touch self-test`, `touch read-palm-gesture`, `touch update-gesture-config`, `touch raw-data`, `touch get-fw-version`, `touch stats`, `touch touchpad-capacitance [slot]`.
- Resets: `touch hard-reset`, `soft-reset`, `watchdog-reset`, `hardfault-reset`, `reset-reason` (prints the cause, the stack, and the CC and EC words).

Observed. `touch read-palm-gesture` shows the touch surface also reports a palm gesture. The palm gesture is the same class of input as the palm-authentication TA in section 16. Inferred.

## IMU and factory calibration

- `start`, `set-odr <data-rate-us> <batch-latency-us>`, `chip-id` (prints `Chip ID: 0x%X`), and `factory-cal` (prints a rectification matrix and offsets `x`, `y`, `z`). Observed.
- The IMU HAL in section 09 is `vendor.meta.hardware.sensor.imu.IImu`. The console does not name it; the link is inferred. The console command table does not name the IMU chip; the MCU firmware names IMU chips elsewhere (`LSM6DSV32X`, `lsm6dsr`, `icm45688`, `lsm6dsv`).

## ALS, hinge and events

- ALS strings: `als_sampling`, `als_stopped`, `als_data`, `als_read_failed`, `als_flicker_sampling`, `als_flicker_stopped`. These six names are entries in the logger, Zephyr and telemetry JSON dictionaries, not console commands. The name suggests a link to the `camflicker` binary (section 13); that link is inferred.
- Hinge: `system input hinge_open` and `hinge_close` are in the `boot_data.bin` span (0x15076C–0x15118C), not the console table; `hinge_status` is in the logger dictionary. Observed. The IHinge HAL (section 09) is the likely consumer; the link is inferred.
- Events: `stp_channel_available_change`, `stp_read_header`, `stp_read_payload`, `stp_header_ready`, `stp_data_available`, `stp_read_failed` are dictionary entries for the STP channel events (section 09 covers the STP transport), and `unknown audio stp channel: %u`. These are the STP channel events (section 09). The audio STP channel is named in the log.

## Other console groups

The console has battery heatmap commands (`Dump battery heatmap`, `Save battery heatmap`); the payloads `batt.bin`, `battery_heatmap.bin` and `battery_heatmap2.bin` are linked to them by name only (inferred), `hot_car_notif.bin` (a hot-car notification, inferred from the name), `factory_reset_telemetry.bin`, and the telemetry dictionaries (`logger_dict_generated.json`, `zephyr_log_dict_generated.json`, `tel_dict_generated.json`). Observed as sub-image names.

## Sub-image layout of the MCU tub

`mcu.default.rt700.tub` (8,483,328 bytes) contains 39 named sub-images (observed, offsets in `data/mcu/mcu_console_strings.txt`). The first is `app.bin` at offset 0, and it runs to about `0x1435E8` (1,324,520 bytes). The others follow it: the display calibration (`display_wpc_coeff.bin`, `display_calibration.bin`), the touch firmware (`touch-app-b0.cyacd2`), boot and shutdown records (`boot_data.bin`, `pmic_reset_info.bin`, `shutdown_state.bin`, `boot_shutdown_history.bin`), the `cf_*` coefficient sets (`cf_fixed_bf_weights_*`, which the name suggests are beamforming weights), the case firmware (`case.bin`, embedded three times for the `cocos`, `lynx` and `cabo` variants of the case), `dumptruck.bin`, `offload_assets_ro.bin`, `romfs.bin`, `debug_frame.bin`, and the JSON dictionaries and manifest (`configs.json`, `metadata.json`). Observed.

This means the `.tub` container is a sequence of named payloads with an ASCII name at each start, and the manifest in the tail. The payloads are mixed. Code and binary tables (`app.bin`, `dumptruck.bin`, `debug_frame.bin`) have entropy of about 5 to 7.3 bits per byte; `offload_assets_ro.bin` is mostly zero bytes; the JSON dictionaries are plain text. The files do not show whether any payload is encrypted, and `app.bin`'s entropy (7.27 bits per byte) fits both compiled code and encrypted data. Section 09 says the manifest md5 (`8589b5e414f8352e39106fc3796ad050`) did not match any range tested and that the hashed bytes are "not in the file as stored, or they are compressed or encrypted. Unverified." A test over the sub-image boundaries and the manifest offsets (1,927 start and end pairs) also found no match. Unresolved.

## What is not found

- The LCoS HAL service binary in Android. Not in the OTA's searched partitions.
- The wiki behind the `xra` commands. Not in the OTA; only the URL string is present.
- The sensor chip names for the ALS. No ALS chip name was found. The IMU chip is named elsewhere in the MCU firmware (`LSM6DSV32X`, `lsm6dsr`, `icm45688`, `lsm6dsv`).
- The panel-specific LCoS tables (the values, not the names). They are per unit, and the calibration data is not in the OTA.

## Evidence

- `data/mcu/mcu_console_strings.txt`: the console strings with offsets, and the sub-image name headers.
- `data/android/vendor_ramdisk/vendor_dtb_dump.txt`: the display nodes (`glinkpkt-disp-bus`, `disp0-gdsc`, `disp1-gdsc`, `display-fps`) and the camera pinctrl nodes. It has no IMU, ALS or hinge node.
- The `debugfs` path mapping (`icheck` and `ncheck`) for the LCoS strings: the strings are in the `/firmware/mcu.default.rt700.tub` inode of `vendor.img`.
