"""Resumable multiprocess CSV runner for the audit simulations (append-only raw results; a re-run skips finished studies)."""
from __future__ import annotations

import csv
import os
from multiprocessing import Pool


def _call(args):
    fn, k = args
    return fn(k)


def done_ks(path: str) -> set:
    if not os.path.exists(path):
        return set()
    with open(path, newline="") as f:
        return {int(r["k"]) for r in csv.DictReader(f)}


def run_resumable(path: str, fn, ks, procs: int = 2, block: int = 200, log=print, time_budget: float | None = None):
    """fn(k) -> list[dict] (rows for study k). Appends rows to `path`. Stops after time_budget seconds (finishing the block)."""
    import time
    t0 = time.time()
    finished = done_ks(path)
    todo = [k for k in ks if k not in finished]
    log(f"{path}: {len(finished)} done, {len(todo)} to do")
    header_needed = not os.path.exists(path)
    with Pool(procs) as pool:
        for b in range(0, len(todo), block):
            blk = todo[b:b + block]
            rows = [r for part in pool.map(_call, [(fn, k) for k in blk], chunksize=max(1, len(blk) // (procs * 4))) for r in part]
            with open(path, "a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                if header_needed:
                    w.writeheader()
                    header_needed = False
                w.writerows(rows)
            log(f"  block {b // block}: +{len(blk)} studies ({time.time() - t0:.0f}s)")
            if time_budget and time.time() - t0 > time_budget:
                log("  time budget reached; resume later")
                break
