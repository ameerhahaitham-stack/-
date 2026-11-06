"""Run the control calibration (synthetic null series) and write docs/CONTROL_CALIBRATION.md.  python scripts/control_calibration.py [n_series]"""
import json, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quantlab import calibration as C, events as E

n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
res = {}
t0 = time.time()
for label, phi in (("gap-constrained control, phi=0.8", 0.8), ("gap-constrained control, phi=0.5", 0.5), ("gap-constrained control, phi=0.0", 0.0)):
    cfg = C.CalibConfig(n_series=n, phi=phi)
    res[label] = {"config": C.config_dict(cfg), "result": C.summarize(C.run_calibration(cfg, procs=2))}
    print(label, json.dumps(res[label]["result"]), f"{time.time()-t0:.0f}s", flush=True)
# old behaviour for comparison: independent draws (duplicates and adjacent bars allowed)
orig = E._place_chunk
def independent(pools, n_draws, n_bars, min_gap, rng, max_tries=40):
    return np.stack([p[rng.integers(0, len(p), size=n_draws)] for p in pools], axis=1), np.ones(n_draws, bool)
E._place_chunk = independent
cfg = C.CalibConfig(n_series=n, phi=0.8)
res["OLD independent draws, phi=0.8"] = {"config": C.config_dict(cfg), "result": C.summarize(C.run_calibration(cfg, procs=1))}
E._place_chunk = orig
print("old", json.dumps(res["OLD independent draws, phi=0.8"]["result"]), f"{time.time()-t0:.0f}s")
out = Path(__file__).resolve().parents[1] / "docs" / "control_calibration.json"
out.write_text(json.dumps(res, indent=1), encoding="utf-8")
print("saved", out)
