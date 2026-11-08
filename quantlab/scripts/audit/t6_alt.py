"""Supplementary audit T6: size (mu=0, many reps) and power (mu>0) of the production monthly bootstrap and diagnostic alternatives, all computed on the SAME
datasets, with K (months) changed ALONE (n trades per month fixed = 5, same generator, same return law).
Raw output: docs/audit/raw/t6/{scenario}_K{K}_mu{mu}.npz (float32 p arrays + variance estimates). Resumable; seeds default_rng([SEED0, scen, K, mu_i, chunk]).
usage: python scripts/audit/t6_alt.py [--reps0 100000] [--reps1 20000] [--K 24 60]"""
import argparse, os, sys, json, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from quantlab.audit import guard
guard.install()
from quantlab.audit.bootalt import SCEN, gen_month_sums, all_p, kv_ref

SEED0 = 20261120
N_PER_MONTH = 5
MUS = (0.0, 0.1, 0.2, 0.3, 0.5)


def cell(scen, K, mu, reps, mi, sd_true=None, chunk=5000):
    names = list(SCEN)
    rng_base = [SEED0, names.index(scen), K, mi]
    P, V = {}, {}
    for ci, a in enumerate(range(0, reps, chunk)):
        rng = np.random.default_rng(rng_base + [ci])
        S = gen_month_sums(scen, K, N_PER_MONTH, min(chunk, reps - a), rng, mu)
        out = all_p(S, N_PER_MONTH, sd_true)
        for k, v in out.items():
            (V if k.startswith("_") else P).setdefault(k, []).append(v)
    return {k: np.concatenate(v) for k, v in P.items()}, {k: np.concatenate(v) for k, v in V.items()}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps0", type=int, default=100000); ap.add_argument("--reps1", type=int, default=20000)
    ap.add_argument("--K", type=int, nargs="+", default=[24, 60]); ap.add_argument("--out", default="docs/audit/raw/t6")
    ap.add_argument("--scen", nargs="*", default=None); ap.add_argument("--procs", type=int, default=1)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    json.dump({"seed0": SEED0, "n_per_month": N_PER_MONTH, "mus": MUS, "reps0": a.reps0, "reps1": a.reps1, "K": a.K, "scenarios": SCEN, "nb": 5000,
               "kv_reference": "1e6 iid N(0,1) draws per K, seed 424242"}, open(f"{a.out}/t6_config.json", "w"), indent=1, default=str)
    for K in a.K:
        kv_ref(K)
        for scen in (a.scen or list(SCEN)):
            sd_true = None
            for mi, mu in enumerate(MUS):
                f = f"{a.out}/{scen}_K{K}_mu{mu}.npz"
                reps = a.reps0 if mu == 0 else a.reps1
                if os.path.exists(f):
                    if mu == 0:
                        sd_true = float(np.std(np.load(f)["_m"]))
                    continue
                t0 = time.time()
                if mu == 0:
                    P0, V0 = cell(scen, K, 0.0, reps, mi)                 # pass 1: sd_true of the mean of month totals (needs a first pass)
                    sd_true = float(np.std(V0["_m"]))
                    P, V = cell(scen, K, 0.0, reps, mi, sd_true)
                else:
                    P, V = cell(scen, K, mu, reps, mi, sd_true)
                np.savez_compressed(f, sd_true=sd_true, **{k: v.astype(np.float32) if not k.startswith("_") else v.astype(np.float64) for k, v in {**P, **V}.items()})
                print(scen, K, mu, reps, f"{time.time()-t0:.0f}s", flush=True)
