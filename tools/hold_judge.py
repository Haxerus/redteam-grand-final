#!/usr/bin/env python3
"""RTH Grand Final flight judging: read an FC log and score every engaged hold.

A hold starts when the engage switch (CH10, TL2) goes on and ends when it goes off.
Engage point = GPS position and barometric altitude at hold start.
Time within limits = from hold start to the first sample outside a limit, or to switch-off.
Qualifying = time within limits >= 30 s (defaults: horizontal 3 m, vertical 2 m).

  ArduCopter dataflash (.bin):  hold_judge.py flight.bin
  Betaflight, CSV export:        hold_judge.py flight.csv [--gps flight.gps.csv]
  Engage time by hand:           hold_judge.py LOG --engage-at 125.4 [--disengage-at 160]

Betaflight CSV: from Betaflight Blackbox Explorer ("Export CSV") or blackbox_decode. The tool needs
time, GPS lat/lon (and fix/satellites if present) and barometric altitude. For the engage switch it
uses, in order: an RC channel column for CH10 (for example rcData[9]), --engage-at, or the
ANGLE flag in flightModeFlags if --bf-engage angle is given (only valid when the pilot flies the
setup without ANGLE). Print with --verbose to see which columns were used.

Output: a table per hold, and --json for the record. Needs Python 3; ArduCopter logs need pymavlink.
"""
import argparse, csv, json, math, os, sys

EARTH_R = 6371000.0
LEVELS = [(1, 10, 12), (2, 20, 14), (3, 35, 16), (4, 50, 18), (5, 75, 20)]


def dist_m(lat0, lon0, lat, lon):
    x = math.radians(lon - lon0) * math.cos(math.radians((lat + lat0) / 2))
    y = math.radians(lat - lat0)
    return EARTH_R * math.hypot(x, y)


def interp_at(series, t):
    """series: sorted list of (t, value). Linear interpolation, clamped."""
    if not series:
        return None
    if t <= series[0][0]:
        return series[0][1]
    for (t0, v0), (t1, v1) in zip(series, series[1:]):
        if t0 <= t <= t1:
            return v0 if t1 == t0 else v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return series[-1][1]


# ------------------------------------------------------------------ ArduCopter
def load_ardupilot(path, channel):
    from pymavlink import mavutil
    m = mavutil.mavlink_connection(path)
    sw, gps, baro, fw = [], [], [], {}
    while True:
        msg = m.recv_match(type=["RCIN", "GPS", "BARO", "VER", "MSG"], blocking=False)
        if msg is None:
            break
        t = msg.get_type()
        ts = getattr(msg, "TimeUS", 0) / 1e6
        if t == "RCIN":
            sw.append((ts, getattr(msg, "C%d" % channel, 0)))
        elif t == "GPS" and getattr(msg, "I", 0) == 0:
            if getattr(msg, "Status", 0) >= 3:
                gps.append((ts, msg.Lat, msg.Lng, getattr(msg, "NSats", None), getattr(msg, "HDop", None)))
        elif t == "BARO" and getattr(msg, "I", 0) == 0:
            baro.append((ts, msg.Alt))
        elif t == "VER":
            fw["git"] = getattr(msg, "GH", None); fw["fw_string"] = getattr(msg, "FWS", None)
        elif t == "MSG" and ("ArduCopter" in msg.Message or "Orqa" in msg.Message):
            fw.setdefault("messages", []).append(msg.Message)
    return sw, gps, baro, fw


# ------------------------------------------------------------------ Betaflight CSV
def _cols(header, *cands):
    low = {h.strip().lower(): h for h in header}
    for c in cands:
        if c.lower() in low:
            return low[c.lower()]
    for c in cands:
        for h in header:
            if h.strip().lower().startswith(c.lower()):
                return h
    return None


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_betaflight(path, gps_path, channel, engage_mode, verbose):
    used = {}
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        hdr = r.fieldnames
        ct = _cols(hdr, "time (us)", "time(us)", "time")
        cb = _cols(hdr, "baroAlt (cm)", "baroAlt", "BaroAlt")
        cs = _cols(hdr, "rcData[%d]" % (channel - 1), "rcData[%d] (us)" % (channel - 1), "rxChannel[%d]" % (channel - 1))
        cf = _cols(hdr, "flightModeFlags (flags)", "flightModeFlags")
        clat = _cols(hdr, "GPS_coord[0]")
        clon = _cols(hdr, "GPS_coord[1]")
        cns = _cols(hdr, "GPS_numSat")
        used.update(time=ct, baro=cb, switch=cs, flags=cf, lat=clat, lon=clon, sats=cns)
        sw, baro, gps = [], [], []
        for row in r:
            t = _num(row.get(ct))
            if t is None:
                continue
            t /= 1e6
            if cb and _num(row.get(cb)) is not None:
                baro.append((t, _num(row[cb]) / (100.0 if "cm" in cb.lower() or cb == "baroAlt" else 1.0)))
            if cs and _num(row.get(cs)) is not None:
                sw.append((t, _num(row[cs])))
            elif engage_mode == "angle" and cf:
                sw.append((t, 2000 if "ANGLE" in (row.get(cf) or "") else 1000))
            if clat and _num(row.get(clat)):
                gps.append((t, _num(row[clat]), _num(row[clon]), _num(row.get(cns)) if cns else None, None))
    if gps_path:
        with open(gps_path, newline="") as f:
            r = csv.DictReader(f)
            hdr = r.fieldnames
            ct = _cols(hdr, "time (us)", "time(us)", "time")
            clat, clon, cns = _cols(hdr, "GPS_coord[0]"), _cols(hdr, "GPS_coord[1]"), _cols(hdr, "GPS_numSat")
            used.update(gps_file=gps_path, gps_time=ct, gps_lat=clat, gps_lon=clon)
            gps = [(_num(row[ct]) / 1e6, _num(row[clat]), _num(row[clon]), _num(row.get(cns)) if cns else None, None)
                   for row in r if _num(row.get(ct)) is not None and _num(row.get(clat))]
    # Blackbox stores degrees * 1e7 in some exports
    gps = [(t, la / 1e7, lo / 1e7, n, h) if abs(la) > 360 else (t, la, lo, n, h) for t, la, lo, n, h in gps]
    if verbose:
        print("columns used:", used)
    return sw, gps, baro, {"columns": used}


# ------------------------------------------------------------------ judging
def holds_from_switch(sw, threshold):
    out, on, t_on = [], False, None
    for t, v in sw:
        now = v >= threshold
        if now and not on:
            t_on = t
        if not now and on:
            out.append((t_on, t))
        on = now
    if on:
        out.append((t_on, sw[-1][0]))
    return out


def judge(hold, gps, baro, h_lim, v_lim, need):
    t0, t1 = hold
    g = [x for x in gps if t0 <= x[0] <= t1]
    gps_before = [x for x in gps if x[0] <= t0]
    if not gps_before or not g:
        return {"start_s": round(t0, 2), "engaged_s": round(t1 - t0, 2), "error": "no GPS fix at or during the hold"}
    _, la0, lo0, n0, _ = gps_before[-1]
    alt0 = interp_at(baro, t0)
    t_out, why, maxh, maxv, minsat = None, None, 0.0, 0.0, n0
    for t, la, lo, n, _ in g:
        h = dist_m(la0, lo0, la, lo)
        v = abs(interp_at(baro, t) - alt0) if alt0 is not None else 0.0
        if n is not None:
            minsat = n if minsat is None else min(minsat, n)
        if t - t0 <= need:
            maxh, maxv = max(maxh, h), max(maxv, v)
        if t_out is None and (h > h_lim or v > v_lim):
            t_out, why = t, ("horizontal %.2f m" % h if h > h_lim else "vertical %.2f m" % v)
    within = (t_out if t_out is not None else t1) - t0
    takeoff_alt = baro[0][1] if baro else None
    rel_alt = (alt0 - takeoff_alt) if (alt0 is not None and takeoff_alt is not None) else None
    level = next((L for L in LEVELS if rel_alt is not None and abs(rel_alt - L[1]) <= 2.0), None)
    q = within >= need
    pts = (level[2] if (q and level) else (5 if within >= 10 else 2 if within >= 5 else 0))
    return {"start_s": round(t0, 2), "engaged_s": round(t1 - t0, 2), "within_limits_s": round(within, 2),
            "left_limits_by": why, "max_horizontal_m_first30s": round(maxh, 2), "max_vertical_m_first30s": round(maxv, 2),
            "engage_alt_rel_takeoff_m": None if rel_alt is None else round(rel_alt, 1),
            "level": level[0] if level else None, "qualifying": q, "points": pts if (level or not q) else None,
            "min_sats": minsat, "gps_samples": len(g)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log")
    ap.add_argument("--gps", help="Betaflight: separate GPS CSV (blackbox_decode .gps.csv)")
    ap.add_argument("--channel", type=int, default=10, help="engage switch channel, 1-based (default 10)")
    ap.add_argument("--threshold", type=float, default=1800, help="switch on at or above this value (us)")
    ap.add_argument("--bf-engage", choices=["channel", "angle"], default="channel")
    ap.add_argument("--engage-at", type=float, help="hold start in log seconds (manual)")
    ap.add_argument("--disengage-at", type=float, help="hold end in log seconds (manual)")
    ap.add_argument("--h-limit", type=float, default=3.0)
    ap.add_argument("--v-limit", type=float, default=2.0)
    ap.add_argument("--hold-s", type=float, default=30.0)
    ap.add_argument("--json", help="write the result to this file")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    if a.log.lower().endswith((".bin", ".log")):
        sw, gps, baro, meta = load_ardupilot(a.log, a.channel)
        kind = "ardupilot"
    else:
        sw, gps, baro, meta = load_betaflight(a.log, a.gps, a.channel, a.bf_engage, a.verbose)
        kind = "betaflight-csv"
    gps.sort(); baro.sort(); sw.sort()
    if a.engage_at is not None:
        end = a.disengage_at if a.disengage_at is not None else (gps[-1][0] if gps else a.engage_at + a.hold_s)
        holds = [(a.engage_at, end)]
    else:
        holds = holds_from_switch(sw, a.threshold)
    print("log %s  (%s)  GPS fixes %d  baro samples %d  switch samples %d" % (os.path.basename(a.log), kind, len(gps), len(baro), len(sw)))
    if meta.get("git") or meta.get("fw_string"):
        print("firmware: %s %s" % (meta.get("fw_string") or "", meta.get("git") or ""))
    if not holds:
        print("no engage found (CH%d >= %d). Use --engage-at, or check --channel / --bf-engage." % (a.channel, a.threshold))
    res = [judge(h, gps, baro, a.h_limit, a.v_limit, a.hold_s) for h in holds]
    print("limits: horizontal %.1f m, vertical %.1f m, hold %.0f s" % (a.h_limit, a.v_limit, a.hold_s))
    print("%-4s %9s %9s %9s %8s %8s %7s %5s %5s %6s  %s" % ("#", "start s", "engaged", "within", "max H", "max V", "alt m", "lvl", "qual", "points", "left limits by"))
    for i, r in enumerate(res, 1):
        if "error" in r:
            print("%-4d %9.2f %9.2f  %s" % (i, r["start_s"], r["engaged_s"], r["error"])); continue
        print("%-4d %9.2f %9.2f %9.2f %8.2f %8.2f %7s %5s %5s %6s  %s" % (
            i, r["start_s"], r["engaged_s"], r["within_limits_s"], r["max_horizontal_m_first30s"], r["max_vertical_m_first30s"],
            r["engage_alt_rel_takeoff_m"], r["level"] or "-", "YES" if r["qualifying"] else "no",
            r["points"] if r["points"] is not None else "-", r["left_limits_by"] or ""))
    if a.json:
        json.dump({"log": a.log, "kind": kind, "meta": meta, "limits": {"h": a.h_limit, "v": a.v_limit, "hold_s": a.hold_s},
                   "holds": res}, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
