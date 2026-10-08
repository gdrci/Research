# 15 - MCU console, LCoS display controller and sensor drivers

[中文](14-mcu-console-and-lcos.zh-CN.md)

This section documents what the MCU firmware in `vendor/firmware/mcu.default.rt700.tub` exposes through its command console: the LCoS (liquid-crystal-on-silicon) display controller, the LED drivers that light it, the touch controller, the inertial and ambient-light sensors, the hinge, and the STP transport. It corrects two earlier points in section 09 and closes the open item "LCoS HAL binary not found" in section 13.

Status labels: observed means read from the file; inferred means a reasonable reading the file does not state; not found means not in the OTA. The console strings are in `data/mcu/mcu_console_strings.txt` with their file offsets.

## What the MCU is

- The MCU firmware is built for the NXP RT700 platform. Its peripheral drivers are in `arvr/firmware/lib/uhal/peripherals/rt700/` (`rt700_clock.c`, `rt700_gpio.c`, `rt700_edma.c`, `rt700_spi_peripheral.c`, `rt700_power_domain.c`, `rt700_wdt.c`). Observed.
- The RTOS is FreeRTOS v10.4.6, with the port `GCC/ARM_CM33_NTZ/non_secure/port.c`, so the core is an Arm Cortex-M33 in non-secure mode. Observed.
- The firmware tree is named `arvr/firmware/projects/smartglasses/platforms/greatwhite/rt700/`. Observed in the DSP image too (section 15). So the `rt700` in the file names is the processor platform, not only an audio codec. This corrects section 09, which called it an audio-codec variant.
- The console is a set of named commands with help text. The help text includes an external wiki reference, `xra: See https://fburl.com/wiki/xra_mcu_commands`. Observed. The wiki is not in the OTA.

## The LCoS console

LCoS is the micro-display engine. The console has a group of `lcos` commands (observed, `data/mcu/mcu_console_strings.txt`, file offsets `0x13E000` to `0x142000`):

Power and mode
- `lcos poweron`: runs the GPIO and I2C power sequence, without the init sequence.
- `lcos send-init-sequence`: sends the I2C sequence that puts LCoS into PGEN mode. It assumes power is on.
- `lcos init`: initialises LCoS in MIPI mode.
- `lcos set-already-initialized`: sets the configuration when the display is already on.
- `lcos poweroff`, `lcos toggle <interval seconds> <number of toggles>` (the default interval is 5 s, and the command logs `Test complete.`).
- `lcos mipi_rx <1/0>`: starts or stops the MIPI receive pipeline.
- `lcos clearscreen`, `lcos clearbus` (clears the display I2C bus by toggling the clock lane).

Test patterns
- `lcos pgen <pattern_name> <r> <g> <b>`. Pattern names are `disabled`, `checkerboard`, `hcolorbar`, `vcolorbar`, `hramp`, `vramp` and `solid`. RGB applies only to `solid`. An unknown name falls back to `checkerboard`. Observed.

Voltages (the names are observed; the physical roles are inferred from the names)
- `lcos set-pixel-voltage <pixel_voltage_mV>` and `lcos get-pixel-voltage` (reported as `Pixel Voltage: %u mV`).
- `lcos set-ito-voltages <pos_red_mV> <pos_green_mV> <pos_blue_mV> <neg_red_mV> <neg_green_mV> <neg_blue_mV>` and `get-ito-voltages`. ITO is indium tin oxide, the electrode layer. Inferred from the abbreviation.
- `lcos get-led-voltages` (reported as `RED:%d GREEN:%d BLUE:%d BLANK:%d`).

LED drivers
- `lcos setledgains <r> <g> <b>` (max 1023), `getledgains`.
- `lcos setledcurrents <r> <g> <b>` in micro-amperes (integer values), `getledcurrents`.
- `lcos getledbitres` reports the LED bit resolution and the rsense GPIO value.
- `lcos set-led-bitres-setting <auto|low|high>`, `get-led-bitres-setting`, and `get-led-bitres-threshold`. The threshold is printed per colour in micro-amperes (`r:%u, g:%u, b:%u microAmps`). It sets when the driver switches between high and low resolution.
- `lcos set-led-mode <pfm|pwm>` and `get-led-mode`. PFM and PWM are the two LED driver modes (pulse-frequency and pulse-width modulation). Observed.
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
- Factory calibration fields are named in the firmware: `VF_1MA_R/G/B` and `VF_140MA_R/G/B` (LED forward voltage at 1 mA and 140 mA), `OFFSET_LOW_RES_*`, `SLOPE_LOW_RES_*`, `OFFSET_HIGH_RES_*`, `SLOPE_HIGH_RES_*` (per colour). Observed. These are the per-unit calibration values that the interpolation coefficients use.
- The serial-number fields are `Display SN`, `LCOS SN`, `LED SN` and `DDB SN`. Observed. Their values are on the device, not in the OTA.

## Why the LCoS HAL is not in the Android partitions

The Android side has SELinux labels for the LCoS HAL (`hal_oculus_lcos` with `vendor.oculus.hardware.lcos::ILcos`, section 11), and the ueventd rules create `/dev/lcos-i2c-OP03010` and `/dev/lcos-i2c-OP02220` with `system` ownership, plus a sysfs `offload_enabled` node (section 13). The `lcos_init` and `lcos_uio` labels are present too. The display control commands above are in the MCU firmware, though, and the Android partitions do not contain a binary that runs them. A directory walk with `debugfs` of `vendor`, `odm`, `system_ext` and `product` found no LCoS binary. `system.img` was not walked for this, so it is not ruled out. So the LCoS control path in the OTA is: the MCU runs the controller and its console; Android has device nodes and labels for an I2C bridge. Inferred from the console location and the device-node names. The node-to-MCU link is not shown in the files.

## Touch controller (PSoC)

The touch controller is a Cypress/Infineon PSoC, as section 09 says, and the MCU runs its driver. The console includes:

- `touch probe`, `touch mode [tuner]`, `touch r <reg_addr> <num>`, `touch w <reg_addr> <val...>`, `touch g <dev_addr> <num>`, `touch t <dev_addr> <val...>` (raw register and device access).
- `touch reboot-dfu`, `touch dfu` (the bootloader route for the `touch-app-b0.cyacd2` image in `touch.default.tub`, section 09).
- `touch read-touch-points`, `touch get-presense-ppc` and `touch get-dondoff-ppc` (per-slot capacitance settings), `touch set-ppc <n_sub> <decn> <cdac_comp>`.
- `touch set-use-case <cpu_freq_mhz> <refresh_rate_hz> <wake_on_touch> <deep_sleep> <sleep_in_active> <centroid_mode>`, `touch set-configuration` and `set-lp-configuration` (with `cdac`, `row_cdac`, `n_sub`, `sns_clk`, `cicrate` and similar fields).
- `touch self-test`, `touch read-palm-gesture`, `touch update-gesture-config`, `touch raw-data`, `touch get-fw-version`, `touch stats`, `touch touchpad-capacitance [slot]`.
- Resets: `touch hard-reset`, `soft-reset`, `watchdog-reset`, `hardfault-reset`, `reset-reason` (prints the cause, the stack, and the CC and EC words).

Observed. `touch read-palm-gesture` shows the touch surface also reports a palm gesture. The palm gesture is the same class of input as the palm-authentication TA in section 16. Inferred.

## IMU and factory calibration

- `start`, `set-odr <data-rate-us> <batch-latency-us>`, `chip-id` (prints `Chip ID: 0x%X`), and `factory-cal` (prints a rectification matrix and offsets `x`, `y`, `z`). Observed.
- The HAL for this sensor is `vendor.meta.hardware.sensor.imu.IImu` (section 09). The console strings do not name the sensor chip.

## ALS, hinge and events

- ALS strings: `als_sampling`, `als_stopped`, `als_data`, `als_read_failed`, `als_flicker_sampling`, `als_flicker_stopped`. The flicker sampling mode matches the `camflicker` binary and the camera flicker work in section 13. Observed.
- Hinge: `system input hinge_open` and `hinge_close`, and the `hinge_status` field. Observed. This is the HAL `vendor.meta.hardware.hinge.IHinge` (section 09).
- Events: `stp_channel_available_change`, `stp_read_header`, `stp_read_payload`, `stp_header_ready`, `stp_data_available`, `stp_read_failed`, and `unknown audio stp channel: %u`. These are the STP channel events (section 09). The audio STP channel is named in the log.

## Other console groups

The console also has the `battery` group (`batt.bin`, `battery_heatmap.bin`, `battery_heatmap2.bin` in the sub-image table), `hot_car_notif.bin` (a hot-car notification, inferred from the name), `factory_reset_telemetry.bin`, and the telemetry dictionaries (`logger_dict_generated.json`, `zephyr_log_dict_generated.json`, `tel_dict_generated.json`). Observed as sub-image names.

## Sub-image layout of the MCU tub

`mcu.default.rt700.tub` (8,483,328 bytes) contains 39 named sub-images (observed, offsets in `data/mcu/mcu_console_strings.txt`). The first is `app.bin` at offset 0, and it runs to about `0x1435E8` (1,324,520 bytes). The others follow it: the display calibration (`display_wpc_coeff.bin`, `display_calibration.bin`), the touch firmware (`touch-app-b0.cyacd2`), boot and shutdown records (`boot_data.bin`, `pmic_reset_info.bin`, `shutdown_state.bin`, `boot_shutdown_history.bin`), the `cf_*` coefficient sets (`cf_fixed_bf_weights_*`, which the name suggests are beamforming weights), the case firmware (`case.bin`, embedded three times for the `cocos`, `lynx` and `cabo` variants of the case), `dumptruck.bin`, `offload_assets_ro.bin`, `romfs.bin`, `debug_frame.bin`, and the JSON dictionaries and manifest (`configs.json`, `metadata.json`). Observed.

This means the `.tub` container is a sequence of named payloads with an ASCII name at each start, and the manifest in the tail. The payloads are plain text and code, not encrypted. That corrects section 09, which said the manifest md5 could not be matched because the payloads were probably encrypted. The md5 still does not match any range tested, including the boundaries between the sub-images (section 09). Unresolved.

## What is not found

- The LCoS HAL service binary in Android. Not in the OTA's searched partitions.
- The wiki behind the `xra` commands. Not in the OTA.
- The sensor chip names for the IMU and ALS. Not in the console strings.
- The panel-specific LCoS tables (the values, not the names). They are per unit, and the calibration data is not in the OTA.

## Evidence

- `data/mcu/mcu_console_strings.txt`: the console strings with offsets, and the sub-image name headers.
- `data/android/vendor_ramdisk/vendor_dtb_dump.txt`: the display and sensor device-tree nodes (section 04).
- The `debugfs` path mapping (`icheck` and `ncheck`) for the LCoS strings: the strings are in the `/firmware/mcu.default.rt700.tub` inode of `vendor.img`.
