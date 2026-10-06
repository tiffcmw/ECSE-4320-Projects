"""E1x (AI-resilience, 'before'): the obvious sequentially linked chase.
Node i points to node i+1, so the hardware prefetcher can predict every load.
Kept as a deliberately flawed design; see docs/AI_USE.md."""
import runlib
from sizes import chase_sizes

q = runlib.quick()
cfgs = [{"label": {"design": "naive_seq"},
         "args": ["--bytes", str(b), "--stride", "128", "--mode", "seq", "--reps", "5", "--warmups", "2"]}
        for b in chase_sizes(q)]
runlib.run_experiment("chase_naive", "chase", cfgs, rounds=1 if q else 2)
