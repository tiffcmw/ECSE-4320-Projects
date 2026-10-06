"""Shared experiment runner.

Runs a list of configurations (each = one benchmark invocation) in several
rounds. The order is shuffled every round to avoid thermal-drift bias. Thermal
state (pmset -g therm) and power source are recorded before and after every
invocation and stored in the raw CSV. Invocations whose thermal state shows a
speed limit or warning are flagged (throttled=1) but kept in the raw data.
"""
import csv
import os
import random
import re
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "data", "raw")
BUILD = os.path.join(ROOT, "build")


def _sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout


def thermal_state():
    """Return (compact_string, throttled_bool)."""
    t = _sh("pmset -g therm")
    batt = _sh("pmset -g batt")
    throttled = False
    m = re.search(r"CPU_Speed_Limit\s*=\s*(\d+)", t)
    if m and int(m.group(1)) < 100:
        throttled = True
    m = re.search(r"CPU_Available_CPUs\s*=\s*(\d+)", t)
    if m and int(m.group(1)) < int(_sh("sysctl -n hw.ncpu") or 0):
        throttled = True
    # Any recorded warning level other than the "No ... recorded" notes.
    for line in t.splitlines():
        if "warning level" in line.lower() and "no " not in line.lower():
            throttled = True
    ac = "AC" if "AC Power" in batt else "BATT"
    lpm = "LPM" if re.search(r"lowpowermode\s+1", _sh("pmset -g")) else "noLPM"
    if ac != "AC" or lpm == "LPM":
        throttled = True
    compact = "|".join(l.strip() for l in t.splitlines() if l.strip() and not l.startswith("Note:"))
    compact = compact or "no_thermal_events"
    return f"{ac};{lpm};{compact}", throttled


def run_experiment(name, binary, configs, rounds=3, seed=1, extra_cols=None, out_dir=RAW):
    """configs: list of dicts {'label': {col: val, ...}, 'args': [str, ...]}.
    The first binary invocation supplies the CSV header (first line starting
    with a non-data header). Returns path of raw CSV."""
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"{name}_{stamp}.csv")
    rng = random.Random(seed)
    exe = os.path.join(BUILD, binary)
    writer = None
    fh = open(path, "w", newline="")
    total = rounds * len(configs)
    done = 0
    t_start = time.time()
    for rnd in range(rounds):
        order = list(range(len(configs)))
        rng.shuffle(order)
        for ci in order:
            cfg = configs[ci]
            before, thr_b = thermal_state()
            ts = datetime.now().isoformat(timespec="seconds")
            res = subprocess.run([exe, "--header"] + cfg["args"], capture_output=True, text=True)
            after, thr_a = thermal_state()
            done += 1
            if res.returncode != 0:
                print(f"[{name}] FAILED rc={res.returncode} args={cfg['args']}: {res.stderr.strip()}", file=sys.stderr)
                continue
            lines = res.stdout.strip().splitlines()
            header, rows = lines[0].split(","), [l.split(",") for l in lines[1:]]
            if writer is None:
                lab_cols = list((cfg.get("label") or {}).keys())
                writer = csv.writer(fh)
                writer.writerow(["timestamp", "experiment", "round", "config_id", "therm_before",
                                 "therm_after", "throttled"] + lab_cols + header)
                fh.flush()
            lab_vals = [(cfg.get("label") or {}).get(c, "") for c in lab_cols]
            thr = int(thr_b or thr_a or (before != after))
            for r in rows:
                writer.writerow([ts, name, rnd, ci, before, after, thr] + lab_vals + r)
            fh.flush()
            if done % 10 == 0 or done == total:
                el = time.time() - t_start
                print(f"[{name}] {done}/{total} elapsed {el:.0f}s", flush=True)
    fh.close()
    print(f"[{name}] wrote {path}")
    return path


def quick():
    return os.environ.get("QUICK", "0") == "1"
