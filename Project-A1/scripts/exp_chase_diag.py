"""AI-resilience diagnosis: if the prefetcher is why the naive chase is fast, then
making the sequential stride larger (beyond what the prefetcher tracks) must raise
its latency toward the random-chase value. Fixed 1 GB footprint, same node count rule."""
import runlib

q = runlib.quick()
B = str(1 << 30)
cfgs = []
for stride in (128, 256, 512, 1024, 2048, 4096, 16384, 65536):
    cfgs.append({"label": {"design": "seq", "stride": stride},
                 "args": ["--bytes", B, "--stride", str(stride), "--mode", "seq", "--reps", "5", "--warmups", "2"]})
cfgs.append({"label": {"design": "random", "stride": 128},
             "args": ["--bytes", B, "--stride", "128", "--mode", "random", "--reps", "5", "--warmups", "2"]})
runlib.run_experiment("chase_diag", "chase", cfgs, rounds=1 if q else 3)
