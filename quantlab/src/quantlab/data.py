"""Data reading, quality validation, cleaning, split-sealing and guarded loading.

Principles
- Nothing is silently repaired. Duplicates are dropped (logged), invalid OHLC rows are
  quarantined (logged), gaps are never forward-filled.
- At ingest the data is physically split into dev / valid (data/clean) and hold (data/sealed).
  The HOLD file can only be read through registry.request_hold() (one-shot, audited).
  NOTE: this is a procedural lock, not cryptographic - everything is on one machine - but
  accidental use is blocked, every access is logged, and the SHA-256 proves the file is unchanged.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .config import ensure_dirs, load_config, protocol_params, root

TF_MIN = {"M15": 15, "H1": 60, "H4": 240, "D1": 1440}
RANK = {"PASS": 0, "WARN": 1, "FAIL": 2}
COLS = ["time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"]


class HoldLockedError(RuntimeError):
    pass


class DataIntegrityError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- reading
def read_mt5_csv(path) -> pd.DataFrame:
    """Reads both formats: QuantLab_Export.mq5 (comma, 'time') and MT5 'Export Bars'
    (tab, <DATE> [<TIME>] <OPEN> ... <TICKVOL> <VOL> <SPREAD>; D1 files have no <TIME>)."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        first = f.readline()
    df = pd.read_csv(path, sep="\t" if "\t" in first else ",")
    df.columns = [c.strip().strip("<>").lower() for c in df.columns]
    df = df.rename(columns={"tickvol": "tick_volume", "vol": "real_volume"})
    if "time" not in df.columns and "date" in df.columns:
        stamp = df["date"].astype(str).str.strip()
        if "time" in df.columns:
            stamp = stamp + " " + df["time"].astype(str).str.strip()
        df["time"] = stamp
    elif "date" in df.columns:                       # <DATE> and <TIME> both present
        df["time"] = df["date"].astype(str).str.strip() + " " + df["time"].astype(str).str.strip()
    missing = [c for c in ["time", "open", "high", "low", "close"] if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    raw = df["time"].astype(str)
    t = pd.to_datetime(raw, format="%Y.%m.%d %H:%M:%S", errors="coerce")
    for fmt in ("%Y.%m.%d %H:%M", "%Y.%m.%d"):
        t = t.fillna(pd.to_datetime(raw, format=fmt, errors="coerce"))
    t = t.fillna(pd.to_datetime(raw, errors="coerce"))
    if t.isna().any():
        raise ValueError(f"{path}: {int(t.isna().sum())} unparseable time values")
    df["time"] = t
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["tick_volume", "spread", "real_volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce") if c in df.columns else np.nan
    return df[COLS]


# --------------------------------------------------------------------------- validation
def _chk(name, status, detail, **extra):
    return {"name": name, "status": status, "detail": detail, **extra}


def _ohlc_bad_mask(df: pd.DataFrame) -> pd.Series:
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    nan = o.isna() | h.isna() | l.isna() | c.isna()
    nonpos = (o <= 0) | (h <= 0) | (l <= 0) | (c <= 0)
    incons = (h < l) | (h < o) | (h < c) | (l > o) | (l > c)
    return nan | nonpos | incons


def _holiday_dates(y0: int, y1: int) -> set:
    """Weekday market closures that are expected for metals/FX CFDs: Good Friday, Dec 24-26, Dec 31, Jan 1-2.
    Used only to avoid calling a real holiday closure a data defect; every such gap is still counted and reported."""
    from dateutil.easter import easter
    out = set()
    for y in range(y0, y1 + 1):
        gf = pd.Timestamp(easter(y)) - pd.Timedelta(days=2)
        out.add(gf.normalize())
        for m, d in [(12, 24), (12, 25), (12, 26), (12, 31), (1, 1), (1, 2)]:
            out.add(pd.Timestamp(year=y, month=m, day=d))
    return out


def _gap_analysis(t: pd.Series, tf: str) -> dict:
    """Classify gaps between consecutive bars. Returns counts and the largest unexpected gaps."""
    t = t.reset_index(drop=True)
    n = len(t)
    if n < 3:
        return {"unexpected_missing_bars": 0, "unexpected_gaps": [], "expected_bars": n, "notes": []}
    if tf == "D1":
        dates = t.dt.normalize()
        a = dates.shift(1).iloc[1:].values.astype("datetime64[D]")
        b = dates.iloc[1:].values.astype("datetime64[D]")
        gaps = []
        total_missing = 0
        holiday_missing = 0
        HOL = _holiday_dates(int(t.dt.year.min()), int(t.dt.year.max()))
        for prev, cur in zip(a, b):
            m = int(np.busday_count(prev + np.timedelta64(1, "D"), cur))
            if m > 0:
                days = pd.date_range(pd.Timestamp(prev) + pd.Timedelta(days=1), pd.Timestamp(cur) - pd.Timedelta(days=1))
                days = [d for d in days if d.weekday() < 5]
                hol_days = [d for d in days if d.normalize() in HOL]
                holiday_missing += len(hol_days)
                days = [d for d in days if d.normalize() not in HOL]
                if days:
                    total_missing += len(days)
                    gaps.append({"start": str(pd.Timestamp(prev).date()), "end": str(pd.Timestamp(cur).date()), "missing": len(days)})
        wk = int((t.dt.weekday >= 5).sum())
        notes = [f"{wk} D1 bars fall on Sat/Sun (broker Sunday session?)"] if wk else []
        notes.append(f"{holiday_missing} weekday closures match holidays (Good Friday / Christmas / New Year) and are not counted as defects")
        expected = n + total_missing
        return {"unexpected_missing_bars": total_missing, "unexpected_gaps": sorted(gaps, key=lambda g: -g["missing"])[:10],
                "expected_bars": expected, "notes": notes}

    per = pd.Timedelta(minutes=TF_MIN[tf])
    d = t.diff()
    prev_t = t.shift(1)
    small = (d > per) & (d <= per + pd.Timedelta(minutes=150))
    ndays = max(int(t.dt.normalize().nunique()), 1)
    slots = (prev_t[small].dt.hour * 60 + prev_t[small].dt.minute).value_counts()
    break_slots = set(slots[slots >= 0.05 * ndays].index.tolist())   # daily break; shifts by 1h in DST-mismatch weeks
    unexpected = 0
    gaps = []
    holiday_like = 0
    HOL = _holiday_dates(int(t.dt.year.min()), int(t.dt.year.max()))
    from pandas.tseries.holiday import USFederalHolidayCalendar
    US_HOL = set(USFederalHolidayCalendar().holidays(start=t.min().normalize(), end=t.max().normalize()))
    us_early = 0
    for i in np.where(d.values > per.to_timedelta64())[0]:
        gap = d.iloc[i]
        p = prev_t.iloc[i]
        slot = p.hour * 60 + p.minute
        missing_bars = int(round(gap / per)) - 1
        if gap <= per + pd.Timedelta(minutes=150) and slot in break_slots:
            continue  # normal daily break (1h, or 2h in the weeks when US and EU daylight-saving dates differ)
        if p.weekday() == 4 and gap <= pd.Timedelta(hours=72):
            continue  # normal weekend
        if p.normalize() in US_HOL and missing_bars * per <= pd.Timedelta(hours=8):
            us_early += 1          # shortened US-holiday session (metals/FX CFD early close)
            continue
        if gap >= pd.Timedelta(hours=20):
            full_days = [x for x in pd.date_range(p.normalize() + pd.Timedelta(days=1), t.iloc[i].normalize() - pd.Timedelta(days=1)) if x.weekday() < 5]
            if full_days and all(x in HOL for x in full_days):
                holiday_like += 1
                continue
        if gap >= pd.Timedelta(hours=24):
            nxt = t.iloc[i]
            near_hol = (p.month == 12 and p.day >= 23) or (p.month == 1 and p.day <= 3)
            if near_hol or (p.weekday() == 4 and gap <= pd.Timedelta(hours=100)):
                holiday_like += 1
                continue
        unexpected += missing_bars
        gaps.append({"start": str(p), "end": str(t.iloc[i]), "missing": missing_bars})
    notes = [f"{holiday_like} long gaps look like holidays", f"{us_early} shortened US-holiday sessions", f"daily-break slots (minute-of-day): {sorted(break_slots)}"]
    return {"unexpected_missing_bars": unexpected, "unexpected_gaps": sorted(gaps, key=lambda g: -g["missing"])[:10],
            "expected_bars": n + unexpected, "notes": notes}


def _week_open_patterns(df: pd.DataFrame) -> pd.DataFrame:
    t = df["time"]
    iso = t.dt.isocalendar()
    key = iso["year"].astype(str) + "-" + iso["week"].astype(str)
    first = df.groupby(key.values)["time"].min()
    pat = first.dt.day_name().str[:3] + " " + first.dt.strftime("%H:%M")
    year = first.dt.year
    return pd.crosstab(year, pat)


def validate(df: pd.DataFrame, symbol: str, tf: str, cfg: dict | None = None) -> dict:
    """Quality checks. Never modifies the data. Overall status = worst check."""
    cfg = cfg or load_config()
    q = cfg["data_quality"]
    checks: list[dict] = []
    n = len(df)
    if n == 0:
        return {"symbol": symbol, "tf": tf, "rows": 0, "status": "FAIL", "checks": [_chk("rows", "FAIL", "file is empty")]}
    t = df["time"]
    checks.append(_chk("coverage", "PASS" if t.min() <= pd.Timestamp(q["min_start"]) else "WARN",
                       f"{t.min()} -> {t.max()} ({n} bars)"))
    dups = int(t.duplicated().sum())
    checks.append(_chk("duplicates", "PASS" if dups == 0 else "FAIL", f"{dups} duplicated timestamps"))
    nonmono = int((t.diff().dropna() < pd.Timedelta(0)).sum())
    checks.append(_chk("sorted", "PASS" if nonmono == 0 else "FAIL", f"{nonmono} out-of-order timestamps"))
    bad = _ohlc_bad_mask(df)
    checks.append(_chk("ohlc_valid", "PASS" if not bad.any() else "FAIL", f"{int(bad.sum())} invalid OHLC rows"))
    ok = df[~bad]
    zr = float((ok["high"] == ok["low"]).mean()) if len(ok) else 0.0
    checks.append(_chk("zero_range_bars", "PASS" if zr <= q["zero_range_warn_share"] else "WARN", f"{zr:.2%} bars have high == low"))

    # price jumps
    if len(ok) > 10:
        ret = np.log(ok["close"] / ok["close"].shift(1)).dropna()
        sig = 1.4826 * float((ret - ret.median()).abs().median())
        lim = q["max_bar_move_pct"].get(symbol, 5.0)
        mv = (np.exp(ret.abs()) - 1) * 100
        worst = mv.sort_values(ascending=False).head(5)
        st = "FAIL" if (mv > 2 * lim).any() else ("WARN" if (mv > lim).any() else "PASS")
        checks.append(_chk("price_jumps", st, f"largest close-to-close moves %: " + ", ".join(f"{v:.2f}@{ok['time'].loc[i]}" for i, v in worst.items()) + f" (robust sigma {sig:.5f}, warn>{lim}%)"))

    # gaps
    g = _gap_analysis(t.drop_duplicates().sort_values(), tf)
    frac = g["unexpected_missing_bars"] / max(g["expected_bars"], 1)
    st = "FAIL" if frac > q["unexpected_missing_fail"] else ("WARN" if frac > q["unexpected_missing_warn"] else "PASS")
    checks.append(_chk("gaps", st, f"{g['unexpected_missing_bars']} unexpected missing bars ({frac:.3%}); " + "; ".join(g["notes"]), largest=g["unexpected_gaps"]))

    # session / timezone pattern
    if tf != "D1":
        ct = _week_open_patterns(df.drop_duplicates("time").sort_values("time"))
        shifting = []
        for yr, row in ct.iterrows():
            tot = row.sum()
            if tot and (row / tot > 0.10).sum() > 1:
                shifting.append(int(yr))
        top = ct.sum().sort_values(ascending=False).head(4)
        checks.append(_chk("week_open_pattern", "WARN" if shifting else "PASS",
                           "first bar of week: " + ", ".join(f"{k} x{int(v)}" for k, v in top.items()) +
                           (f"; mixed patterns in years {shifting} (possible DST/timezone shift in server time)" if shifting else "")))

    # spread
    sp = df["spread"].dropna()
    if len(sp) == 0:
        checks.append(_chk("spread", "WARN", "no spread column - costs will use fallback assumptions"))
    else:
        zs = float((sp == 0).mean())
        by_year = df.dropna(subset=["spread"]).groupby(df["time"].dt.year)["spread"].median().to_dict()
        checks.append(_chk("spread", "PASS" if zs <= q["zero_spread_warn_share"] else "WARN",
                           f"points: median {sp.median():.1f}, p95 {sp.quantile(.95):.1f}, max {sp.max():.0f}, zero-share {zs:.1%}; median by year {by_year}. "
                           "Note: MT5 bar spread is the spread at bar open, not an average."))
    tv = df["tick_volume"].dropna()
    if len(tv):
        checks.append(_chk("tick_volume", "PASS" if (tv == 0).mean() < 0.01 else "WARN",
                           f"{(tv == 0).mean():.2%} zero tick-volume bars (tick volume is NOT global FX volume)"))
    status = max((c["status"] for c in checks), key=lambda s: RANK[s])
    return {"symbol": symbol, "tf": tf, "rows": n, "start": str(t.min()), "end": str(t.max()), "status": status, "checks": checks}


def cross_check(df_low: pd.DataFrame, df_high: pd.DataFrame, tf_low: str, tf_high: str, cfg: dict | None = None) -> dict:
    """Aggregate the lower timeframe into the higher one and compare OHLC bar by bar."""
    cfg = cfg or load_config()
    q = cfg["data_quality"]
    lo = df_low.drop_duplicates("time").sort_values("time")
    hi = df_high.drop_duplicates("time").sort_values("time").set_index("time")
    minutes = TF_MIN[tf_high]
    if tf_high == "D1":
        bucket = lo["time"].dt.normalize()
    else:
        anchor = int(hi.index.hour.to_series().mode().iloc[0]) % (minutes // 60)
        shift = pd.Timedelta(hours=anchor)
        bucket = (lo["time"] - shift).dt.floor(f"{minutes}min") + shift
    g = lo.assign(bucket=bucket.values).groupby("bucket")
    agg = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                        "close": g["close"].last(), "cnt": g["open"].count()})
    full = agg["cnt"].mode().iloc[0]
    agg = agg[agg["cnt"] >= max(int(0.8 * full), 1)]
    j = agg.join(hi[["open", "high", "low", "close"]], how="inner", lsuffix="_agg", rsuffix="_hi")
    if len(j) == 0:
        return {"pair": f"{tf_low}->{tf_high}", "status": "WARN", "detail": "no overlapping complete buckets"}
    med_rng = float((hi["high"] - hi["low"]).median())
    tol = max(1e-9, 0.02 * med_rng)
    mism = {f: float(((j[f + "_agg"] - j[f + "_hi"]).abs() > tol).mean()) for f in ["open", "high", "low", "close"]}
    worst = max(mism.values())
    st = "FAIL" if worst > q["crosstf_mismatch_fail"] else ("WARN" if worst > q["crosstf_mismatch_warn"] else "PASS")
    return {"pair": f"{tf_low}->{tf_high}", "status": st, "compared_bars": int(len(j)), "tolerance": tol,
            "mismatch_share": mism, "detail": f"mismatch share o/h/l/c: " + "/".join(f"{mism[f]:.2%}" for f in ["open", "high", "low", "close"])}


# --------------------------------------------------------------------------- cleaning / sealing
def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    log = {"rows_in": int(len(df))}
    df = df.sort_values("time", kind="mergesort")
    dup = df["time"].duplicated(keep="first")
    log["duplicates_dropped"] = int(dup.sum())
    df = df[~dup]
    bad = _ohlc_bad_mask(df)
    quarantine = df[bad]
    log["quarantined_invalid_ohlc"] = int(bad.sum())
    df = df[~bad].reset_index(drop=True)
    log["rows_out"] = int(len(df))
    return df, quarantine, log


def _manifest_path() -> Path:
    return root() / "data" / "manifest.json"


def load_manifest() -> dict:
    p = _manifest_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def manifest_summary() -> dict:
    """What the UI may show: names, status and row counts only - never file paths, hashes or sealed content."""
    out = {}
    for k, v in load_manifest().items():
        out[k] = {"symbol": v["symbol"], "tf": v["tf"], "source": v["source"], "synthetic": v["synthetic"],
                  "raw_status": v["raw_status"], "clean_status": v["clean_status"],
                  "rows": {n: v["splits"][n]["rows"] for n in ("dev", "valid", "hold")}}
    return out


def _split_bounds(params: dict) -> dict:
    s = params["splits"]
    return {
        "dev": (pd.Timestamp(s["dev"]["start"]), pd.Timestamp(s["dev"]["end"]) + pd.Timedelta(days=1)),
        "valid": (pd.Timestamp(s["valid"]["start"]), pd.Timestamp(s["valid"]["end"]) + pd.Timedelta(days=1)),
        "hold": (pd.Timestamp(s["hold"]["start"]), pd.Timestamp.max if s["hold"]["end"] is None else pd.Timestamp(s["hold"]["end"]) + pd.Timedelta(days=1)),
    }


def ingest(path, symbol: str, tf: str, source: str, broker: str = "", tz_note: str = "", synthetic: bool = False) -> dict:
    """Validate raw file, clean it, split into dev/valid (clean) and hold (sealed), update manifest."""
    ensure_dirs()
    params = protocol_params()
    df = read_mt5_csv(path)
    raw_report = validate(df, symbol, tf)
    cdf, quarantine, log = clean(df)
    clean_report = validate(cdf, symbol, tf)
    b = _split_bounds(params)
    out = {}
    for name, (lo, hi) in b.items():
        part = cdf[(cdf["time"] >= lo) & (cdf["time"] < hi)]
        folder = "sealed" if name == "hold" else "clean"
        p = root() / "data" / folder / f"{symbol}_{tf}_{name}.csv.gz"
        if p.exists():
            os.chmod(p, 0o644)                       # re-ingest (before the protocol is locked) may replace the file
        part.to_csv(p, index=False, compression="gzip", date_format="%Y-%m-%d %H:%M:%S")
        if name == "hold":
            os.chmod(p, 0o444)                       # sealed: write bits cleared
        out[name] = {"file": str(p.relative_to(root())), "rows": int(len(part)), "sha256": sha256_file(p),
                     "start": str(part["time"].min()) if len(part) else None, "end": str(part["time"].max()) if len(part) else None}
    if len(quarantine):
        quarantine.to_csv(root() / "data" / "clean" / f"{symbol}_{tf}_QUARANTINE.csv", index=False)
    m = load_manifest()
    m[f"{symbol}_{tf}"] = {"symbol": symbol, "tf": tf, "source": source, "broker": broker, "timezone_note": tz_note,
                           "synthetic": bool(synthetic), "raw_file": str(path), "raw_sha256": sha256_file(Path(path)),
                           "ingested_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                           "splits_used": params["splits"], "cleaning": log, "splits": out,
                           "raw_status": raw_report["status"], "clean_status": clean_report["status"]}
    _manifest_path().write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"raw": raw_report, "clean": clean_report, "cleaning": log, "splits": out}


# --------------------------------------------------------------------------- guarded loading
def _read_split(entry: dict, name: str) -> pd.DataFrame:
    p = root() / entry["splits"][name]["file"]
    if sha256_file(p) != entry["splits"][name]["sha256"]:
        raise DataIntegrityError(f"{p.name}: SHA-256 differs from the manifest - the file was modified after ingest")
    df = pd.read_csv(p, parse_dates=["time"])
    return df


def load_with_context(symbol: str, tf: str, split: str, hid: str | None = None):
    """Return (df, eval_start, eval_end, manifest_entry).

    df contains all data visible for that stage (for warm-up of indicators); trades must only be
    counted when entered inside [eval_start, eval_end).
      dev   -> dev data
      valid -> dev + valid data, evaluated on the valid window
      hold  -> requires registry.request_hold(hid); dev + valid + hold, evaluated on the hold window
    """
    m = load_manifest()
    key = f"{symbol}_{tf}"
    if key not in m:
        raise FileNotFoundError(f"{key} has not been ingested")
    entry = m[key]
    params = protocol_params()
    if entry["splits_used"] != params["splits"]:
        raise DataIntegrityError("protocol splits changed after ingest - re-ingest the data")
    b = _split_bounds(params)
    if split == "dev":
        df = _read_split(entry, "dev")
        return df, b["dev"][0], b["dev"][1], entry
    if split == "valid":
        df = pd.concat([_read_split(entry, "dev"), _read_split(entry, "valid")], ignore_index=True)
        return df, b["valid"][0], b["valid"][1], entry
    if split == "hold":
        if hid is None:
            raise HoldLockedError("HOLD is sealed. It can only be opened through registry.request_hold(hypothesis_id).")
        from . import registry
        registry.assert_hold_open(hid, symbol, tf)
        df = pd.concat([_read_split(entry, s) for s in ["dev", "valid", "hold"]], ignore_index=True)
        return df, b["hold"][0], b["hold"][1], entry
    raise ValueError(split)


def load_specs(symbol: str) -> dict:
    """Symbol specs from the MT5 export (data/specs/<symbol>.json) or flagged fallbacks."""
    p = root() / "data" / "specs" / f"{symbol}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    fb = {"XAUUSD": dict(point=0.01, digits=2, value_per_px_per_lot=100.0, contract_size=100.0, volume_min=0.01, volume_step=0.01, volume_max=100.0),
          "EURUSD": dict(point=0.00001, digits=5, value_per_px_per_lot=100000.0, contract_size=100000.0, volume_min=0.01, volume_step=0.01, volume_max=100.0)}
    return {**fb.get(symbol, {}), "assumed": True, "swap_modeled": False}
