"""E1c: bandwidth kernels vs working-set size (single thread, default QoS)."""
import runlib
from sizes import bw_sizes

q = runlib.quick()
reps = "3" if q else "5"
cfgs = []
for b in bw_sizes(q):
    for k in ("read_seq", "read_rand", "triad"):
        cfgs.append({"label": {"kernel_cfg": k}, "args": ["--kernel", k, "--bytes", str(b), "--reps", reps]})
    if b >= 1 << 20:
        for sl in (4, 16, 128):
            cfgs.append({"label": {"kernel_cfg": f"stride{sl}"},
                         "args": ["--kernel", "read_stride", "--stride_lines", str(sl), "--bytes", str(b), "--reps", reps]})
runlib.run_experiment("bw", "bw", cfgs, rounds=1 if q else 3)
