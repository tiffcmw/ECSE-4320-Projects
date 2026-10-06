"""E0: timer resolution/overhead and fixed-work noise floor."""
import runlib

reps = 30 if runlib.quick() else 100
cfgs = [{"label": {"run": i}, "args": ["--reps", str(reps)]} for i in range(3)]
runlib.run_experiment("noise", "timer_noise", cfgs, rounds=1)
