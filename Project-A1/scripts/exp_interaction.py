"""Phase 4 interaction: core tier (steered by process policy / thread count) x working-set size.
Conditions: S plain (Super), U clamp utility (control, Super), P clamp background (Performance,
low-power policy), 18T eighteen plain threads (both tiers, analyzed per thread)."""
import runlib
from sizes import bw_sizes, chase_sizes

q = runlib.quick()
TP = "/usr/sbin/taskpolicy"
COND = {"S": [], "U": [TP, "-c", "utility"], "P": [TP, "-c", "background"]}
reps, rounds = ("3", 1) if q else ("5", 3)

# E3a: latency vs working set, matched steps across conditions
cfgs = []
for b in chase_sizes(q):
    for c, wrap in COND.items():
        cfgs.append({"label": {"cond": c}, "wrap": wrap,
                     "args": ["--bytes", str(b), "--stride", "128", "--mode", "random", "--steps", str(1 << 21),
                              "--reps", reps, "--warmups", "2"]})
runlib.run_experiment("inter_latency", "chase", cfgs, rounds=rounds)

# E3b: bandwidth vs working set
cfgs = []
for b in bw_sizes(q):
    for c, wrap in COND.items():
        for k in ("read_seq", "read_rand"):
            cfgs.append({"label": {"cond": c, "kernel_cfg": k}, "wrap": wrap,
                         "args": ["--kernel", k, "--bytes", str(b), "--reps", reps]})
runlib.run_experiment("inter_bw", "bw", cfgs, rounds=rounds)

# E3c: 18 plain threads, per-thread latency (own buffer each), up to 256 MB per thread
cfgs = []
for b in [s for s in chase_sizes(q) if s <= 256 << 20]:
    cfgs.append({"label": {"cond": "18T", "bytes": b},
                 "args": ["--kind", "mem", "--threads", "18", "--qos", "none", "--bytes", str(b), "--chunks", "100",
                          "--chunk_steps", "20000", "--reps", reps, "--warmups", "1"]})
runlib.run_experiment("inter_18t", "qos_loop", cfgs, rounds=rounds)
