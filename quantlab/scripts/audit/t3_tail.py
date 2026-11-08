"""Tasks 2-3 runner. usage: python scripts/audit/t3_tail.py --mode S --phi 0.8 --n 10000 --procs 2"""
import argparse, os, sys, functools, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from quantlab.audit import guard
guard.install()
from quantlab.audit.tail import TailAudit, tail_audit_study
from quantlab.audit.runner import run_resumable

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True); ap.add_argument("--phi", type=float, required=True)
    ap.add_argument("--n", type=int, default=10000); ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--out", default="docs/audit/raw"); ap.add_argument("--budget", type=float, default=None)
    ap.add_argument("--k0", type=int, default=0); ap.add_argument("--nfull", type=int, default=0); ap.add_argument("--tag", default="")
    a = ap.parse_args()
    cfg = TailAudit(phi=a.phi, mode=a.mode, n_full=a.nfull, k_full0=a.k0)
    os.makedirs(a.out, exist_ok=True)
    name = f"t3_{a.mode}_phi{a.phi}{a.tag}"
    with open(os.path.join(a.out, name + ".config.json"), "w") as f:
        json.dump(cfg.__dict__, f, indent=1)
    run_resumable(os.path.join(a.out, name + ".csv"), functools.partial(tail_audit_study, cfg), range(a.k0, a.k0 + a.n), a.procs, block=200, time_budget=a.budget)
