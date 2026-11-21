# hold_judge.py: flight hold scorer

The judges use this tool to score each engaged hold from the FC log (Stage 2, section 06). Run it on your own development flights to see what the judges will see.

## Use

| Log | Command |
|---|---|
| ArduCopter dataflash | `python3 hold_judge.py 00000012.BIN` (needs `pip install pymavlink`) |
| Betaflight blackbox | Export CSV in Betaflight Blackbox Explorer, then `python3 hold_judge.py LOG.csv --verbose` |
| Betaflight, blackbox_decode output | `python3 hold_judge.py LOG.01.csv --gps LOG.01.gps.csv` |
| Engage time set by hand | add `--engage-at <log seconds> [--disengage-at <s>]` |
| Machine-readable result | add `--json` |

`--verbose` prints the log columns that the tool used.

## Rules it applies

| Rule | Value |
|---|---|
| Hold start | CH10 (TL2) at or above 1800 µs |
| Engage point | GPS position and barometric altitude at hold start |
| Horizontal error | GPS distance from the engage point. Limit 3 m. |
| Vertical error | Barometric altitude change from the engage point. Limit 2 m. |
| Time within limits | From hold start to the first sample outside a limit, or to switch-off |
| Qualifying hold | 30 s within limits |
| Level | Engage altitude relative to take-off, within 2 m of 10, 20, 35, 50 or 75 m |

For ArduCopter logs, the tool also prints the firmware version (VER message).

If the tool and the Stage 2 package differ, the Stage 2 package applies. Report a difference to the scoring desk.
