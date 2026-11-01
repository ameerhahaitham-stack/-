"""Command line: python -m quantlab.cli <command>"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from . import registry
from .config import ensure_dirs, load_config, root
from .data import cross_check, ingest, load_manifest, read_mt5_csv, validate

TFS = ["D1", "H4", "H1", "M15"]


def _specs_from_csv(path: Path, symbol: str) -> dict:
    kv = dict(pd.read_csv(path).values.tolist())
    f = lambda k, d=0.0: float(kv.get(k, d))
    tick_val = f("tick_value_profit") or f("tick_value")
    tick_size = f("tick_size") or f("point")
    spec = {"symbol": symbol, "point": f("point"), "digits": int(f("digits")), "value_per_px_per_lot": tick_val / tick_size,
            "contract_size": f("contract_size"), "volume_min": f("volume_min"), "volume_max": f("volume_max"),
            "volume_step": f("volume_step"), "swap_long": f("swap_long"), "swap_short": f("swap_short"),
            "swap_mode_points": int(f("swap_mode")) == 1, "currency_profit": kv.get("currency_profit"),
            "stops_level_points": f("stops_level_points"), "assumed": False}
    spec["swap_modeled"] = bool(spec["swap_mode_points"])
    return spec


def cmd_ingest(a) -> int:
    ensure_dirs()
    folder = Path(a.folder) if a.folder else root() / "data" / "incoming"
    meta_p = folder / "QL_meta.csv"
    meta = dict(pd.read_csv(meta_p).values.tolist()) if meta_p.exists() else {}
    broker = f"{meta.get('broker_company', '?')} / {meta.get('server', '?')}"
    tz = f"server-GMT seconds at export: {meta.get('server_minus_gmt_seconds_now', '?')} (DST behaviour must be confirmed from the week-open check)"
    prefix = "SYNTH_" if a.synthetic else "QL_"
    found = 0
    for sym in load_config()["symbols"]:
        sp = folder / f"{prefix}{sym}_specs.csv"
        if sp.exists():
            (root() / "data" / "specs").mkdir(parents=True, exist_ok=True)
            (root() / "data" / "specs" / f"{sym}.json").write_text(json.dumps(_specs_from_csv(sp, sym), indent=2), encoding="utf-8")
        for tf in TFS:
            p = folder / f"{prefix}{sym}_{tf}.csv"
            if not p.exists():                       # MT5 'Export Bars' names: XAUUSD_Daily_<from>_<to>.csv
                alias = "Daily" if tf == "D1" else tf
                hits = sorted(folder.glob(f"{sym}_{alias}_*.csv"))
                if len(hits) == 1:
                    p = hits[0]
                elif len(hits) > 1:
                    print(f"  ambiguous for {sym} {tf}: {[h.name for h in hits]}")
                    continue
            if not p.exists():
                print(f"  missing: {sym} {tf}")
                continue
            r = ingest(p, sym, tf, source="synthetic test data" if a.synthetic else "MT5 export", broker=broker, tz_note=tz, synthetic=a.synthetic)
            found += 1
            print(f"  {sym} {tf}: raw {r['raw']['status']} -> clean {r['clean']['status']} | {r['cleaning']} | "
                  + ", ".join(f"{k}:{v['rows']}" for k, v in r["splits"].items()))
    print(f"ingested {found} files. Next: python -m quantlab.cli validate")
    return 0


def cmd_validate(a) -> int:
    ensure_dirs()
    m = load_manifest()
    cfg = load_config()
    lines = ["# Data quality report", ""]
    data_by_key = {}
    for key, e in m.items():
        p = Path(e["raw_file"])
        if not p.exists():
            lines.append(f"- {key}: raw file not found ({p})")
            continue
        df = read_mt5_csv(p)
        data_by_key[key] = df
        rep = validate(df, e["symbol"], e["tf"], cfg)
        (root() / "reports" / "data_quality" / f"{key}.json").write_text(json.dumps(rep, indent=2, default=str), encoding="utf-8")
        lines += [f"## {e['symbol']} {e['tf']} - {rep['status']}", f"source: {e['source']} | broker: {e['broker']} | synthetic: {e['synthetic']}",
                  f"cleaning: {e['cleaning']}", ""]
        for c in rep["checks"]:
            lines.append(f"- [{c['status']}] **{c['name']}**: {c['detail']}")
        lines.append("")
    lines += ["## Cross-timeframe consistency", ""]
    for sym in cfg["symbols"]:
        for lo, hi in [("M15", "H1"), ("H1", "H4"), ("H1", "D1")]:
            if f"{sym}_{lo}" in data_by_key and f"{sym}_{hi}" in data_by_key:
                r = cross_check(data_by_key[f"{sym}_{lo}"], data_by_key[f"{sym}_{hi}"], lo, hi, cfg)
                lines.append(f"- [{r['status']}] {sym} {r['pair']}: {r['detail']}")
    out = root() / "reports" / "data_quality_report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nreport saved: {out}")
    return 0


def cmd_calc_check(a) -> int:
    """Import QL_calc_check.csv (OrderCalcProfit result) and mark the specs as verified."""
    df = pd.read_csv(a.file)
    for r in df.itertuples():
        p = root() / "data" / "specs" / f"{r.symbol}.json"
        sp = json.loads(p.read_text(encoding="utf-8"))
        old = sp["value_per_px_per_lot"]
        sp.update(value_per_px_per_lot=float(r.value_per_px_per_lot), verified=True, tick_basis_conflict=False,
                  verified_by="OrderCalcProfit", verified_value_per_px_per_lot=float(r.value_per_px_per_lot), previous_assumed=old)
        p.write_text(json.dumps(sp, indent=2), encoding="utf-8")
        print(f"{r.symbol}: value per 1.00 price move per lot = {r.value_per_px_per_lot} (was assumed {old})")
    return 0


def cmd_audit_hold(a) -> int:
    from .holdguard import audit
    res = audit()
    for r in res:
        print(f"[{r['status']}] {r['check']}: {r['detail']}")
    return 1 if any(r["status"] == "FAIL" for r in res) else 0


def cmd_lock(a) -> int:
    unverified = []
    for sym in load_config()["symbols"]:
        sp = root() / "data" / "specs" / f"{sym}.json"
        spec = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}
        if not spec.get("verified"):
            unverified.append(sym)
    if unverified and not a.allow_unverified_specs:
        print(f"REFUSED: symbol specs not verified with OrderCalcProfit for {unverified}. Run QuantLab_CalcCheck.mq5 and "
              "'python -m quantlab.cli calc-check --file <QL_calc_check.csv>', or lock explicitly with --allow-unverified-specs.")
        return 2
    note = (a.note or "") + (f" | UNVERIFIED SPECS ACCEPTED: {unverified}" if unverified else "")
    info = registry.lock_protocol(note)
    print("protocol locked:", info)
    return 0


def cmd_status(a) -> int:
    print("protocol:", registry.lock_status())
    print("registry chain:", registry.verify_chain())
    print("DEV+VALID trials logged:", registry.trial_count(("dev", "valid")))
    print(registry.hypotheses_df().to_string(index=False) if len(registry.hypotheses_df()) else "no hypotheses yet")
    return 0


def cmd_synth(a) -> int:
    from .synth import make_all
    out = Path(a.out)
    paths = make_all(out, start=a.start, end=a.end)
    print(f"wrote {len(paths)} SYNTHETIC files to {out} (code testing only - never research evidence)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="quantlab")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("ingest"); s.add_argument("--folder"); s.add_argument("--synthetic", action="store_true"); s.set_defaults(fn=cmd_ingest)
    s = sub.add_parser("validate"); s.set_defaults(fn=cmd_validate)
    s = sub.add_parser("lock-protocol"); s.add_argument("--note"); s.add_argument("--allow-unverified-specs", action="store_true"); s.set_defaults(fn=cmd_lock)
    s = sub.add_parser("calc-check"); s.add_argument("--file", required=True); s.set_defaults(fn=cmd_calc_check)
    s = sub.add_parser("audit-hold"); s.set_defaults(fn=cmd_audit_hold)
    s = sub.add_parser("status"); s.set_defaults(fn=cmd_status)
    s = sub.add_parser("synth"); s.add_argument("--out", required=True); s.add_argument("--start", default="2018-01-01"); s.add_argument("--end", default="2025-06-30"); s.set_defaults(fn=cmd_synth)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
