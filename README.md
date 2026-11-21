# Red Team Grand Final: Stage 2 participant download

This repository is the Stage 2 download for the Contested Battlefield Aerial Operations Challenge. Read the Stage 2 package first. It states the event configuration, the scoring, and how each item is measured.

## Contents

| Path | What it is |
|---|---|
| `docs/Red-Team-Grand-Final-Stage-2.pdf` | **Stage 2 participant technical package.** The rules for scoring and flights. |
| `docs/Red-Team-Grand-Final-Stage-2.md` | The same text as Markdown, for search and for your tools. If the two differ, the PDF applies. |
| `docs/Red-Team-Grand-Final-Stage-1.pdf` | Stage 1 package, for reference. Where Stage 2 is more specific, Stage 2 applies. |
| `firmware/ardupilot/` | ArduCopter files for teams that choose ArduCopter (Stage 2, section 03). See its README. |
| `tools/hold_judge.py` | The flight hold scorer that the judges use (Stage 2, section 06). Run it on your own FC logs. See `tools/README.md`. |

## Quick facts

| Item | Value |
|---|---|
| APB access | USB-C, USB Ethernet, `ssh root@192.168.75.1` |
| Default FC firmware | Orqa Betaflight 2025.12.5, MSP on APB `/dev/ttymxc2` at 115200 |
| Optional FC firmware | ArduCopter 4.7.2, MAVLink 2 on APB `/dev/ttymxc2` at 230400 |
| Engage switch | CH10 (TL2) high |
| GNSS | Allowed before you engage. **Not allowed during a scored hold.** |
| Maximum score | 120 (100 base + 20 bonus) |

## Safety

**Test everything with props off before you ask for outdoor flight time.** This applies to development and scored flights. Pilot time is limited, and safety comes first.

The Betaflight FC has no command timeout. While the engage switch is on, it keeps your last command until the pilot switches off. Read Stage 2, section 03, before you connect to the FC.

Manufacturer safety restrictions apply. Bench work, configuration changes and flights follow the event procedures and the instructions of the flight crew.

## Integrity

`SHA256SUMS` lists every file in this repository. Check it with:

```
sha256sum -c SHA256SUMS
```

Questions go to the scoring desk.
