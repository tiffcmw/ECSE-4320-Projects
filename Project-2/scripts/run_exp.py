#!/usr/bin/env python3
"""Experiment driver. One group = one raw CSV. Within a group each round runs every job once, in shuffled
order, with a per-round seed (new random permutations each round). Metadata JSON written per session.

  scripts/run_exp.py --profile quick|full --sid ID [--only g1,g2]
"""
import argparse, json, os, random, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meta  # noqa: E402

EXE = os.path.join(ROOT, "bin", "membench")
RAW = os.environ.get("P2_RAW", os.path.join(ROOT, "data", "raw"))
K, M, G = 1 << 10, 1 << 20, 1 << 30


def fmt(n):
    for u, s in ((G, "G"), (M, "M"), (K, "K")):
        if n % u == 0:
            return f"{n // u}{s}"
    return str(n)


def sweep_sizes(profile, hi=2 * G):
    if profile == "quick":
        base = [4 * K * 2 ** k for k in range(0, 20, 1)]
        extra = [96 * K, 192 * K, 12 * M, 24 * M, 48 * M, 96 * M]
    else:
        base = [int(4 * K * 2 ** (k / 4)) // 1024 * 1024 for k in range(0, 77)]
        extra = [80 * K, 96 * K, 112 * K, 144 * K, 160 * K, 192 * K, 6 * M, 7 * M, 9 * M, 10 * M, 12 * M, 14 * M, 18 * M, 20 * M,
                 24 * M, 32 * M, 48 * M, 96 * M, 128 * M, 192 * M, 384 * M, 768 * M]
    s = sorted({x for x in base + extra if 4 * K <= x <= hi})
    return s


def groups(profile):
    q = profile == "quick"
    sz = sweep_sizes(profile)
    sz_bw = [x for x in sz if x <= G]
    half = [x for i, x in enumerate(sz) if i % 2 == 0 or x in (128 * K, 16 * M)] if not q else sz
    L = lambda l: ",".join(fmt(x) for x in l)
    strides = "64,128,256,512,1024,4096,16384"
    ws2 = "256M" if q else "1G"
    mixes_all = ["r10w0", "r7w3_st", "r5w5_st", "r0w10_st", "r0w10_nt", "r0w10_zva", "rmw"]
    nt_thr = "0,4,16" if q else "0,2,4,8,16"
    G_ = {}

    def rnd(n_quick, n_full):
        return n_quick if q else n_full

    # e0 placement: cache-signature check for core tier (L1D 128K vs 64K, L2 16M vs 8M)
    G_["e0_placement"] = (rnd(2, 5), lambda r: [["chase", "--sizes", "48K,96K,6M,12M", "--qos", qn, "--reps", "2", "--exp", "e0_placement",
                                                  "--variant", qn] for qn in ("interactive", "default", "background")])
    # e1/e5: random chase vs working set (zero-queue latency table + working-set sweep)
    G_["e1_chase"] = (rnd(3, 9), lambda r: [["chase", "--sizes", L(sz), "--reps", "1", "--exp", "e1_chase", "--variant", "rand"]])
    G_["e5_bw"] = (rnd(3, 9), lambda r: [["bw", "--sizes", L(sz_bw), "--kernels", "r10w0", "--reps", "1", "--exp", "e5_bw"]])
    # e2: pattern and granularity
    G_["e2_chase_stride"] = (rnd(2, 5), lambda r: [["chase", "--sizes", ws2, "--stride", str(s), "--mode", md, "--reps", "1",
                                                     "--exp", "e2_chase_stride", "--variant", md] for s in map(int, strides.split(",")) for md in ("seq", "rand")])
    G_["e2_pat"] = (rnd(3, 9), lambda r: [["pat", "--ws", ws2, "--strides", strides, "--sizes", "16,32,64,128", "--reps", "1", "--exp", "e2_pat"]])
    # e3: read/write mix
    G_["e3_mix_bw"] = (rnd(2, 5), lambda r: [["bw", "--sizes", "256K,8M,1G" if not q else "8M,256M", "--kernels", "r10w0,r7w3_st,r7w3_nt,r5w5_st,r5w5_nt,r0w10_st,r0w10_nt,r0w10_zva,rmw",
                                               "--reps", "1", "--exp", "e3_mix_bw"]])
    G_["e3_mix_loaded"] = (rnd(2, 4), lambda r: [["loaded", "--mix", mx, "--threads", nt_thr, "--exp", "e3_mix_loaded", "--window-ms", "300" if q else "400"]
                                                   for mx in mixes_all])
    # e4: intensity (MLP in one thread; threads and injection delay)
    G_["e4_mlp"] = (rnd(3, 9), lambda r: [["mlp", "--ws", "1G" if not q else "256M", "--chains", "1,2,3,4,6,8,12,16,20,24,32,40,48,64", "--reps", "1", "--exp", "e4_mlp"]])
    G_["e4_loaded"] = (rnd(2, 7), lambda r: [
        ["loaded", "--mix", "r10w0", "--threads", "0,2,4,8,16" if q else "0,1,2,3,4,5,6,8,10,12,14,16", "--exp", "e4_loaded_threads"],
        ["loaded", "--mix", "r10w0", "--threads", "16", "--delays", "0,100000,800000" if q else "0,20000,60000,100000,200000,400000,800000,1600000,3200000", "--exp", "e4_loaded_delay"],
        ["loaded", "--mix", "r10w0", "--threads", "6", "--delays", "0,100000,800000" if q else "0,20000,60000,100000,200000,400000,800000,1600000,3200000", "--exp", "e4_loaded_delay6"]])
    # e6: kernels
    el = "4096,65536,1048576,16777216" if q else ",".join(str(2 ** k) for k in range(10, 28))
    mu = "1,16,40503" if q else "1,2,4,8,16,32,64,40503"
    G_["e6_kern"] = (rnd(2, 5), lambda r: [["kern", "--elems", el, "--mults", mu, "--reps", "1", "--exp", "e6_kern"]])
    # e7: TLB
    pages = ",".join(str(2 ** k) for k in (range(0, 17, 2) if q else range(0, 17)))
    G_["e7_tlb"] = (rnd(3, 9), lambda r: [["tlb", "--pages", pages, "--lpp", "1", "--layout", lay, "--reps", "1", "--exp", "e7_tlb_pages"] for lay in ("paged", "packed")]
                    + [["tlb", "--lines", "32768", "--pages", "128,64,32,16,8,4,2,1" if not q else "128,16,1", "--layout", "paged", "--reps", "1", "--exp", "e7_tlb_fixedL"]])
    # e8: pitfalls
    G_["e8_pitfalls"] = (rnd(2, 5), lambda r: [["dce", "--ws", "256M", "--reps", "2"],
                                                ["ramp", "--idle-ms", "3000", "--chunks", "400", "--chunk-us", "500", "--reps", "2" if q else "3"],
                                                ["chase", "--sizes", L(half), "--mode", "seq", "--stride", "128", "--reps", "1", "--exp", "pitfall_seqchase", "--variant", "seq"]]
                         + [["loaded", "--probe", "0", "--mix", "r10w0", "--threads", "16", "--bufsize", b, "--exp", "pitfall_resident_bw", "--window-ms", "300"]
                            for b in ("256K", "1M", "4M", "16M", "64M", "256M")])
    return G_


def run_group(name, rounds, mk, sid, meta_acc):
    path = os.path.join(RAW, f"{name}_{sid}.csv")
    hdr = subprocess.run([EXE, "header"], capture_output=True, text=True).stdout
    out = open(path, "w")
    out.write(hdr)
    out_log = open(os.path.join(RAW, f"{name}_{sid}.log"), "w")
    rec = {"group": name, "rounds": rounds, "thermal_by_round": [], "start": time.time()}
    for r in range(rounds):
        jobs = mk(r)
        random.Random(1000 * r + len(name)).shuffle(jobs)
        th = meta.thermal(); rec["thermal_by_round"].append({"round": r, "no_warning": th["no_warning"], "text": th["text"]})
        for j in jobs:
            t0 = time.time()
            cmd = [EXE] + j + ["--round", str(r), "--seed", str(r + 1)]
            p = subprocess.run(cmd, capture_output=True, text=True)
            if p.returncode != 0:
                out_log.write(f"FAILED {' '.join(cmd)}\n{p.stderr}\n"); out_log.flush()
                print(f"  job failed: {' '.join(cmd)}\n{p.stderr}", file=sys.stderr)
                continue
            out.write(p.stdout if not p.stdout.startswith("exp,") else p.stdout.split("\n", 1)[1])
            out.flush()
            if j[0] in ("dce", "ramp"):   # these commands set exp themselves
                pass
            out_log.write(f"r{r} {' '.join(j)} {time.time() - t0:.1f}s\n"); out_log.flush()
        print(f"  {name}: round {r + 1}/{rounds} done", flush=True)
    th = meta.thermal(); rec["thermal_end"] = th; rec["elapsed_s"] = time.time() - rec["start"]
    rec["raw_file"] = os.path.basename(path)
    meta_acc.append(rec)
    out.close(); out_log.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="quick", choices=["quick", "full"])
    ap.add_argument("--sid", default=time.strftime("%Y%m%d-%H%M%S"))
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    os.makedirs(RAW, exist_ok=True)
    G_ = groups(a.profile)
    names = [n for n in G_ if not a.only or n in a.only.split(",")]
    base = meta.collect({"session": a.sid, "profile": a.profile, "groups_planned": names})
    acc = []
    for n in names:
        rounds, mk = G_[n]
        print(f"[{a.profile}] {n}: {rounds} rounds", flush=True)
        run_group(n, rounds, mk, a.sid, acc)
        base["groups_done"] = acc
        base["thermal_end"] = meta.thermal()
        base["effective_freq_ghz_estimate_end"] = subprocess.run([EXE, "freq"], capture_output=True, text=True).stdout.strip()
        json.dump(base, open(os.path.join(RAW, f"meta_{a.sid}_{a.profile}.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
