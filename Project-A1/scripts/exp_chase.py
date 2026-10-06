"""E1a (latency vs working set) and E1b (TLB reach: packed vs one node per page)."""
import runlib
from sizes import chase_sizes

q = runlib.quick()
reps = "3" if q else "5"
rounds = 1 if q else 3

cfgs = [{"label": {"design": "random_a", "n_nodes": b // 128},
         "args": ["--bytes", str(b), "--stride", "128", "--mode", "random", "--reps", reps, "--warmups", "2"]}
        for b in chase_sizes(q)]
runlib.run_experiment("chase_random", "chase", cfgs, rounds=rounds)

# E1b: fixed node count n, vary placement. 128 = packed lines, 4224 = 4 per 16 KB page
# (+1 line to spread cache sets), 16512 = one per page (+1 line).
cfgs = []
for stride in (128, 4224, 16512):
    for lg in range(4, 17, 2 if q else 1):
        n = 2 ** lg
        cfgs.append({"label": {"design": "tlb", "n_nodes": n},
                     "args": ["--bytes", str(n * stride), "--stride", str(stride), "--mode", "random",
                              "--reps", reps, "--warmups", "2"]})
runlib.run_experiment("chase_tlb", "chase", cfgs, rounds=rounds)
