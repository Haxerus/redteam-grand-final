# Grand Final Participant Technical Package

#### STAGE 2 / EVENT CONFIGURATION AND JUDGING

`20 November 2026 | Revision 2.0`

**Contested Battlefield Aerial Operations Challenge**

**Stage 2 gives you the event configuration, the flight controller interface, and the judging criteria with exactly how each one is measured.** Use it with the Stage 1 package. Where Stage 2 is more specific, Stage 2 applies.

Everything else about the platform you will find on the aircraft itself. You receive your aircraft at check-in.

`IN THIS PACKAGE`

Event brief / Platform / Flight controller / Scoring / Bench test protocol / Flight test protocol / Bonus routes / Team questions

---

#### 01 / EVENT BRIEF

# What Stage 2 settles

| Stage 1 said | Stage 2 now states |
|---|---|
| All available compatible APB targets will be offered | **Betaflight is installed. ArduCopter is available: flash it yourself, or ask the organizers (section 03).** No PX4 or INAV build exists for the event board. |
| Stage 2 will publish points, thresholds and bonus rules | Sections 04 to 07. Every item is pass or fail. An organizer runs and reads every test. |
| GNSS-assisted setup is eligible; GNSS must not aid the scored hold | Unchanged. You may use GNSS before you engage. **No GNSS during the scored hold.** GPS stays connected because the organizers use it to measure drift. A GNSS-free start earns a bonus (section 07). |

## Camera use

The nadir Justice D must contribute materially to your flight solution. You may also use the forward Justice A.

## What has not changed

The challenge, the A to G areas and the fixed hardware configuration are as in Stage 1. No physical modifications. No additional sensors.

---

#### 02 / PLATFORM

# The event configuration

Each team receives one aircraft for the whole event. All aircraft have the same configuration.

| Item | Event configuration |
|---|---|
| Access | USB-C to the APB, USB Ethernet. `ssh root@192.168.75.1`, no password. |
| Nadir camera | Justice D on `/dev/video2`. 1920 × 1080, 60 fps, YUYV, rolling shutter. The sensor format is set at boot. |
| Forward camera | Justice A on `/dev/video3` through the ADV7282 decoder. 720 × 576, about 50 fps, PAL. 1 to 3 % of frames are partial. |
| APB IMU and barometer | ICM-42605 and DPS310 through Linux IIO |
| Timestamps | Cameras and IMU on CLOCK_MONOTONIC. Camera timestamps mark the end of the frame. No hardware sync. |
| Pilot video | Analog passthrough of the Justice A to the video transmitter, with the Betaflight OSD. The APB is not in the pilot video path. |
| Orqa OSD service | `orqa-digital-osd` is disabled. Do not enable it: it takes the cameras and the FC link. |
| Your files | Keep them in `/data`. The root filesystem is almost full and `/tmp` is lost at reboot. |

## Rules

- Do not change the APB device tree, kernel or boot configuration.
- Do not change the APB GPIO lines. They route the FC link and the pilot video.
- Not present: rangefinder, magnetometer.

---

#### 03 / FLIGHT CONTROLLER

# Betaflight (installed)

| Item | Value |
|---|---|
| Firmware | Orqa Betaflight 2025.12.5, board `APB` |
| Link | APB `/dev/ttymxc2`, 115200 baud, MSP v1 |
| How you command | `MSP_SET_RAW_RC`, 8 × uint16 µs in the order **roll, pitch, throttle, yaw**, AUX1 to AUX4. The FC uses only the first four. 50 Hz recommended. |
| Engage switch | CH10 (TL2) high. It selects MSP OVERRIDE and ANGLE together. Switch low returns control to the pilot at once. |
| Logging | Blackbox to the FC flash. The crew downloads it after each flight. |

## Safety rule: the FC has no command timeout

- **If your process stops sending while the switch is on, the FC keeps your last command.** Only the pilot's switch-off recovers.
- **Before your first command after an FC power-up, the four channels read minimum while the switch is on:** throttle cut and full tilt.
- So send continuously from start-up, ready or not. When not ready, send roll, pitch and yaw 1500 and a throttle that holds height.

# ArduCopter (optional)

You may flash ArduCopter yourself, or ask the organizers to do it. The files are in the Stage 2 download:

| File | Write to |
|---|---|
| `rth_orqaapb_bootloader_bid1189_load384k.bin` | `0x08000000` |
| `ardupilot_4.7.2_fb773567_apb-dual-icm42605-copter_app@0x08060000.bin` | `0x08060000` |

1. Back up the FC first: a 2 MB read from `0x08000000` in DFU mode.
2. Enter DFU: type `bl` in the Betaflight CLI. You do not need the boot button.
3. Mass erase, write both files, verify, start (for example with STM32CubeProgrammer).
4. Power-cycle the FC after the flash. The first start straight after the write can fail on USB.

The link to the APB is then MAVLink 2 on `/dev/ttymxc2` at 230400 baud. ArduCopter starts at default parameters: frame, motor order, receiver and tune are your work. The flight crew must approve the aircraft before it flies.

**Warning.** If a flash fails, recovery needs the FC boot button, which is inside the aircraft. Going back to Betaflight needs the organizers. Flash at your own risk, or ask us.

---

#### 04 / SCORING

# How you score

- **Every item is pass or fail.** An organizer runs every test and reads the result from organizer equipment.
- **Scoring is open from the start of the event.** Book a 10-minute judged bench session at the scoring desk when you are ready. Each team can book **up to 3 judged bench sessions** during the event.
- At the start of a session, **declare the items you claim**. The judge tests only those. You get 2 tries per item.
- **Passed items are banked.** A later failure does not remove them.
- **You may fly when D and E are banked.** Each team gets **2 scored flights**.
- Area F is scored at the presentations.

| Area | Item | Where | Points |
|---|---|---|---:|
| **A** Sensor data | Live camera and IMU data on the APB | Bench, step 1 | 5 |
| **B** Estimation | Measured displacement and return | Bench, steps 2 to 4 | 25 |
| **C** Onboard execution | Correct commands with your laptop unplugged | Bench, step 5 | 10 |
| **D** FC integration and handover | Engage, disengage and not-ready behaviour | Bench, step 6 | 15 |
| **E** Reliability | Camera loss and APB restart | Bench, steps 7 and 8 | 15 |
| **F** Engineering and explanation | Judges' panel | Presentations | 10 |
| **G** Live position hold | Measured hold, altitude ladder | Flight (section 06) | 20 |
| | | **Base total** | **100** |

Terms categories: Algorithm 30 (A + B), Technical Implementation 45 (C + D + G), Feasibility and Scalability 15 (E), Entrepreneurial Drive and Storytelling 10 (F).

## GNSS rule

GPS stays connected for drift measurement. You may use GNSS before you engage, for example to initialize. **From the moment the engage switch goes on until it goes off, your solution must not use GNSS** (Betaflight `MSP_RAW_GPS`, ArduCopter GPS messages or GPS-aided state). At your first bench session, show the judge where your solution gets its inputs and how it stops using GNSS at engage. The judges may inspect your code and logs at any time. **Use of GNSS during a hold voids that flight.**

---

#### 05 / BENCH TEST PROTOCOL

# Bench test protocol

**Equipment:** the judging-area floor as it is, with masking-tape start and distance marks; a tape measure; two tape marks on a wall or pole, 0.5 m apart; and an organizer laptop on the FC USB (Betaflight Receiver tab, or Mission Planner for ArduCopter). You can see the floor before your session. Team-supplied aids are not used in scored tests (Stage 1).

**Set-up:** props off, battery in, radio on. The judge holds your aircraft level, about 1 m above the floor. Your laptop shows your live estimate.

| Step | Item | Test | Pass condition | Pts |
|---|---|---|---|---:|
| 1 | **A** | Show your process on the APB reading the Justice D and the IMU | Both streams live at the same time, in your process | 5 |
| 2 | **B1** | The judge carries the aircraft from the start mark to a mark the judge chooses, 0.5 to 1.5 m away, any direction | Your displayed horizontal displacement is within 0.25 m of the taped distance | 10 |
| 3 | **B2** | The judge carries the aircraft around a loop of about 3 m on the floor marks and stops over the start mark | Your displayed position is within 0.3 m of zero | 10 |
| 4 | **B3** | Over the start mark, the judge raises the aircraft from the low mark to the high mark | Your displayed height change is within 0.15 m of 0.5 m | 5 |
| 5 | **C** | Your laptop is unplugged from the APB. Engage switch on. The judge moves the aircraft 0.5 m left, right, forward and back. | On the organizer laptop, your command responds to each move with the correct sign. Betaflight: roll and pitch oppose the move. ArduCopter: your position follows the move. | 10 |
| 6 | **D** | The judge turns the engage switch on and off, once with your solution ready and once with it not ready | Ready, switch on: your commands appear. Switch off: pilot control at once. Not ready: Betaflight receives roll, pitch and yaw 1500, never minimum values; ArduCopter receives no position. | 15 |
| 7 | **E1** | The judge covers the Justice D for 3 s | Within 1 s your solution shows not ready. Betaflight: roll, pitch and yaw at 1500 while covered. ArduCopter: no position while covered. Normal output only after the camera is uncovered. | 8 |
| 8 | **E2** | The judge power-cycles the APB | Your solution restarts by itself and shows ready within 60 s. Betaflight: safe values from its first command. | 7 |

**Recovery bonus (section 07)** is tested inside step 3.

---

#### 06 / FLIGHT TEST PROTOCOL

# Flight test protocol

## Before take-off

1. The crew checks the FC firmware identity: Orqa Betaflight 2025.12.5, or ArduCopter 4.7.2 fb773567 from the Stage 2 files. **Modified FC firmware voids the flight.** The crew also checks the FC log space.
2. You confirm that your solution is running and sending. The pilot does not engage without this confirmation.

## In the air

1. The pilot takes off and climbs to level 1. The pilot reads the altitude from the OSD (relative to take-off).
2. The pilot holds the aircraft steady within 2 m of the level and switches on the engage switch.
3. The hold runs until the pilot switches off. The pilot switches off after 30 s, or earlier for safety.
4. After a 30 s hold, the pilot climbs to the next level and engages again. The flight continues until a hold fails, the battery is low, or the top level is done.

| Level | Height | Full hold scores |
|---|---:|---:|
| 1 | 10 m | 12 |
| 2 | 20 m | 14 |
| 3 | 35 m | 16 |
| 4 | 50 m | 18 |
| 5 | 75 m | 20 |

The flight lead can lower the top levels for site reasons, for every team equally.

## How the hold is measured

After landing, the crew downloads the FC log (Betaflight blackbox or ArduCopter dataflash). From the log the judge reads the **hold start** (the engage switch going on), the **engage point** (GPS position and barometric altitude at hold start), the **horizontal error** (GPS distance from the engage point) and the **vertical error** (barometric altitude change from the engage point).

**A hold is qualifying when, for 30 s from hold start, the horizontal error stays within 3 m and the vertical error stays within 2 m.** The limits are much larger than the GPS and barometer noise, so the result is clear.

| Best result without a full hold | Points |
|---|---:|
| Within the limits for less than 5 s | 0 |
| Within the limits for 5 s to less than 10 s | 2 |
| Within the limits for 10 s to less than 30 s | 5 |

Only your best result counts. The time within the limits starts at hold start and ends at the first sample outside a limit, or at switch-off.

## Conditions and reflights

The flight lead decides whether conditions allow scored flights and can stop a flight. If the flight lead stops a flight for conditions, or the FC log is missing, you get an equal reflight.

## Winners and ties

**Overall:** highest base plus bonus (maximum 120). Ties: higher G, then the team that banked D and E first, then a shared result.

**Flight portion:** highest level with a qualifying hold. Ties: the longer time within the limits at the next level, then a shared result.

---

#### 07 / BONUS ROUTES

# Bonus routes

Each route is optional and earned once. A harder approach by itself earns nothing.

| Route | How it is measured | Points |
|---|---|---:|
| **Betaflight integration** | A qualifying hold (section 06) flown on Betaflight | **+5** |
| **GNSS-free start** | A qualifying hold in a flight in which your solution never used GNSS, from power-up to landing. Declare it before take-off and show your code and logs on request. | **+5** |
| **Timing and rolling shutter** | Judges' panel at the presentations: your treatment of camera timing and rolling shutter, with your measured evidence | **up to +5** |
| **Onboard recovery** | In bench step 3, the judge covers the Justice D for 3 s in the middle of the loop. At the start mark, your displayed position is within 0.5 m of zero. | **+5** |

**Maximum overall: 120 points** (100 base + 20 bonus).

---

#### 08 / TEAM QUESTIONS

# Answers that Stage 1 deferred to Stage 2

**Processor, operating system, ROS 2 and OpenCV**
i.MX8M Plus, 4 × A53, about 3.9 GB RAM, Orqa Yocto Linux, Python 3.12 with numpy. No compiler on the board. pip installs aarch64 wheels from local files. ROS 2 is not supported.

**Flight controller software and interface**
Betaflight 2025.12.5 with MSP OVERRIDE, or ArduCopter 4.7.2 with MAVLink (section 03).

**Justice D**
1920 × 1080 at 60 fps on `/dev/video2` (the datasheet says 1280 × 720), rolling shutter, no exposure control.

**IMU and height**
ICM-42605 up to 4 kHz and DPS310 on the APB. A second IMU and barometer on the FC, through MSP or MAVLink. No rangefinder.

**Practice data and flight time**
No simulator and no dataset. Practise on your own aircraft. Ask the flight crew for development flights; scored flights have priority.

**Site, aircraft access and damage**
The flight lead announces the site and the last flight time at check-in. You receive your aircraft at check-in. The event team confirms the equipment-handling and damage arrangements at handover.

**GNSS before the scored hold**
Yes. You may use GNSS before you engage. No GNSS during the scored hold. A GNSS-free start earns a bonus (sections 04 and 07).

Manufacturer safety restrictions continue to apply. Bench work, configuration changes and flight activity follow the event procedures and the instructions of the designated crew.
