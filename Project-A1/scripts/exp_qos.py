"""Mechanism 2: QoS classes and process policy (E2a idle, E2b threads, E2c contention, E2x control)."""
import runlib

q = runlib.quick()
reps = "3" if q else "5"
rounds = 1 if q else 3
TP = "/usr/sbin/taskpolicy"
QOS = ["interactive", "initiated", "default", "utility", "background"]
POLICIES = {"plain": [], "clamp_utility": [TP, "-c", "utility"], "clamp_background": [TP, "-c", "background"],
            "bg_b": [TP, "-b"]}
HOG = ["--kind", "compute", "--threads", "36", "--qos", "interactive", "--reps", "100000", "--warmups", "0"]
MEM_BYTES = str(256 << 20)


def cfg(exp, kind, qos, threads=1, policy="plain", hog=False, where="inside", chunks=200):
    args = ["--kind", kind, "--threads", str(threads), "--qos", qos, "--qos_where", where, "--chunks", str(chunks),
            "--reps", reps, "--warmups", "1", "--bytes", MEM_BYTES]
    c = {"label": {"exp": exp, "policy": policy, "hog": int(hog)}, "args": args, "wrap": POLICIES[policy]}
    if hog:
        c["hog"] = HOG
    return c


cfgs = []
for kind in ("compute", "mem"):
    # E2a: idle, 1 thread, five thread QoS classes, plus process policies
    for qs in QOS:
        cfgs.append(cfg("E2a", kind, qs))
    for pol in ("clamp_utility", "clamp_background", "bg_b"):
        cfgs.append(cfg("E2a", kind, "none", policy=pol))
    # E2b: N threads (same QoS on all), plain policy
    for n in ((4, 18) if q else (4, 6, 12, 18, 36)):
        for qs in (("default", "background") if q else QOS):
            cfgs.append(cfg("E2b", kind, qs, threads=n))
    # E2c: contention with a 36-thread interactive hog in another process
    for qs in (("default", "background") if q else QOS):
        cfgs.append(cfg("E2c", kind, qs, hog=True))
    cfgs.append(cfg("E2c", kind, "none", policy="clamp_background", hog=True, chunks=20))
    cfgs.append(cfg("E2c", kind, "none", policy="bg_b", hog=True, chunks=10))
    # E2x control: QoS applied to the main thread after workers started (does not reach workers)
    for qs in ("interactive", "background"):
        cfgs.append(cfg("E2x", kind, qs, hog=True, where="main_after"))
runlib.run_experiment("qos", "qos_loop", cfgs, rounds=rounds)
