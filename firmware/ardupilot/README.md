# ArduCopter for the event aircraft (optional)

Use these files only if your team chooses ArduCopter. Betaflight is installed on every aircraft. You can flash ArduCopter yourself, or ask the organizers to do it. Read Stage 2, section 03, first.

| File | Write to | Source |
|---|---|---|
| `rth_orqaapb_bootloader_bid1189_load384k.bin` | `0x08000000` | ArduPilot bootloader built by the organizers from `rth_orqaapb_hwdef-bl.dat`: board ID 1189, application at 384 KiB, no microSD |
| `ardupilot_4.7.2_fb773567_apb-dual-icm42605-copter_app@0x08060000.bin` | `0x08060000` | ArduCopter 4.7.2, commit fb773567, target `OrqaAPB-DualICM42605`, from [Orqa_ArduPilot_Ports](https://github.com/DroneWuKong/Orqa_ArduPilot_Ports) v0.1.0-rc3 |
| `rth_orqaapb_hwdef-bl.dat` | (not flashed) | Bootloader hardware definition |

Check the files first: `sha256sum -c SHA256SUMS`.

## Status

| Item | Status |
|---|---|
| Boot, USB, MAVLink to the APB | Checked on an event aircraft |
| IMU orientation | Checked on an event aircraft |
| Receiver, motor order and direction, flight modes, tune | **Not done. This is your work.** ArduCopter starts at default parameters. |
| Flight | **Not flown by the organizers.** The flight crew must approve the aircraft before it flies. |

## Flash procedure (STM32CubeProgrammer CLI)

Props off. FC USB-C to your laptop. Close Betaflight Configurator and any ground station program, because they hold the FC port.

1. Enter DFU. In the Betaflight CLI, type `bl`. The FC shows as an STM32 DFU device. You do not need the boot button.
2. Back up the full FC flash. Keep this file. It is the only way back to the original Betaflight state.
   ```
   STM32_Programmer_CLI -c port=USB1 -u 0x08000000 0x200000 fc_backup_2MB.bin
   ```
3. Erase, write both files, verify, and start.
   ```
   STM32_Programmer_CLI -c port=USB1 -e all \
     -w rth_orqaapb_bootloader_bid1189_load384k.bin 0x08000000 -v \
     -w "ardupilot_4.7.2_fb773567_apb-dual-icm42605-copter_app@0x08060000.bin" 0x08060000 -v \
     -s 0x08000000
   ```
   Both writes must show `Download verified successfully`.
4. **Power-cycle the FC** (remove USB and battery). The first start straight after the write can hang on USB. A cold start works.
5. Connect from the APB: MAVLink 2 on `/dev/ttymxc2` at 230400 baud.

## Warnings

- If a flash fails, recovery needs the FC boot button, which is inside the aircraft. Ask the organizers.
- After ArduCopter is installed, the Betaflight `bl` command is not available. To go back to Betaflight, ask the organizers, and bring your backup file.
- Do not modify these images. The flight crew checks the FC firmware identity before every scored flight, and modified FC firmware voids the flight.

## Licence

ArduPilot and its bootloader are licensed under GPLv3. Source: [ArduPilot](https://github.com/ArduPilot/ardupilot), [Orqa_ArduPilot_Ports](https://github.com/DroneWuKong/Orqa_ArduPilot_Ports), and the hardware definition in this folder.
