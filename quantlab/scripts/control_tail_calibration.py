"""Tail calibration runner (synthetic null series only; no market data, no registry).  Resumable, writes one CSV row per study.
python scripts/control_tail_calibration.py --phi 0.8 --n 20000 --out docs/calibration_raw/tail_phi0.8.csv [--procs 2] [--block 500]"""
import argparse, csv, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quantlab.calibration import TailConfig, run_tail_block

ap = argparse.ArgumentParser()
ap.add_argument("--phi", type=float, default=0.8); ap.add_argument("--n", type=int, default=20000)
ap.add_argument("--out", required=True); ap.add_argument("--procs", type=int, default=2); ap.add_argument("--block", type=int, default=500)
ap.add_argument("--series-seed0", type=int, default=100_000)
a = ap.parse_args()
cfg = TailConfig(phi=a.phi, n_series=a.n, series_seed0=a.series_seed0)
out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
done = set()
if out.exists():
    with out.open(encoding="utf-8") as f:
        done = {int(r["k"]) for r in csv.DictReader(f)}
fields = ["k", "n_events", "obs", "p_prod", "p_ref", "coverage", "n_ctrl_used", "refined"]
new = not out.exists()
t0 = time.time()
with out.open("a", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    if new:
        w.writeheader()
    todo = [k for k in range(cfg.n_series) if k not in done]
    for i in range(0, len(todo), a.block):
        rows = run_tail_block(cfg, todo[i:i + a.block], a.procs)
        w.writerows(rows); f.flush()
        print(f"{len(done) + i + len(rows)}/{cfg.n_series} studies  {time.time() - t0:.0f}s", flush=True)
print("DONE", out)
