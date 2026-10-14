#!/usr/bin/env python3
"""Collect machine-readable run metadata (hardware, OS, compiler, flags, thermal, load, frequency)."""
import datetime, json, os, platform, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(cmd, timeout=20):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout).stdout.strip()
    except Exception as e:  # metadata must never abort a run
        return f"error: {e}"


def sysctl(key):
    return sh(f"sysctl -n {key} 2>/dev/null")


def thermal():
    t = sh("pmset -g therm")
    clean = "No thermal warning level has been recorded" in t and "No performance warning level has been recorded" in t \
        and "CPU_Speed_Limit" not in t
    return {"text": t, "no_warning": clean}


def collect(extra=None):
    exe = os.path.join(ROOT, "bin", "membench")
    flags = open(os.path.join(ROOT, "bin", "CFLAGS.txt")).read().strip() if os.path.exists(os.path.join(ROOT, "bin", "CFLAGS.txt")) else ""
    try:
        import numpy, matplotlib
        pyv = {"python": platform.python_version(), "numpy": numpy.__version__, "matplotlib": matplotlib.__version__}
    except Exception:
        pyv = {"python": platform.python_version()}
    m = {
        "timestamp": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "hardware": {
            "model": sysctl("hw.model"), "chip": sysctl("machdep.cpu.brand_string"), "ncpu": int(sysctl("hw.ncpu") or 0),
            "perflevel0": {"name": sysctl("hw.perflevel0.name"), "cores": sysctl("hw.perflevel0.physicalcpu"),
                           "l1d": sysctl("hw.perflevel0.l1dcachesize"), "l2": sysctl("hw.perflevel0.l2cachesize")},
            "perflevel1": {"name": sysctl("hw.perflevel1.name"), "cores": sysctl("hw.perflevel1.physicalcpu"),
                           "l1d": sysctl("hw.perflevel1.l1dcachesize"), "l2": sysctl("hw.perflevel1.l2cachesize")},
            "pagesize": sysctl("hw.pagesize"), "cacheline": sysctl("hw.cachelinesize"), "memsize": sysctl("hw.memsize"),
            "tbfrequency": sysctl("hw.tbfrequency"), "smt": "none (no SMT on Apple M-series)",
        },
        "os": {"product_version": sh("sw_vers -productVersion"), "build": sh("sw_vers -buildVersion"),
               "kernel": " ".join(platform.uname()[0:1] + platform.uname()[2:3] + platform.uname()[4:5])},
        "compiler": {"version": sh("clang --version | head -1"), "flags": flags},
        "python": pyv,
        "power": {"batt": sh("pmset -g batt | head -2"), "powermode": sh("pmset -g | grep -i powermode")},
        "thermal": thermal(),
        "load_avg": list(os.getloadavg()),
        "top_processes": sh("ps -Ao pcpu,comm -r | head -6"),
        "policy": {
            "frequency": "DVFS automatic, no governor control; 300 ms spin warmup at every process start; estimate below is a dependent-add calibration, labeled as an estimate",
            "pinning": "not available on macOS; QoS class set inside each worker thread (default USER_INTERACTIVE); placement verified by L1D-capacity signature",
            "huge_pages": "not available (mach_vm_allocate SUPERPAGE flags return invalid argument, see data/raw/hugetest.txt)",
            "counters": "no PMU access; timing inference only",
            "warmup": "per-config warm pass before calibration; calibration discards first runs; timed regions >= 25 ms; first process action is a 300 ms spin",
        },
        "git": {"commit": sh(f"git -C {ROOT} rev-parse --short HEAD"), "dirty": bool(sh(f"git -C {ROOT} status --porcelain src scripts")),},
    }
    if os.path.exists(exe):
        m["effective_freq_ghz_estimate"] = sh(f"{exe} freq")
    if extra:
        m.update(extra)
    return m


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else None
    j = json.dumps(collect(), indent=2)
    if out:
        open(out, "w").write(j)
    else:
        print(j)
