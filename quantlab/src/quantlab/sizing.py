"""Position sizing from real symbol specs: lot rounding, min/max lot, optional leverage cap, loss limits.

Memory lesson built in: when a leverage cap or the minimum lot forces the real risk away from the planned risk,
the trade is flagged and the REAL risk % is reported - never silently assumed to be the planned 0.5%.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def apply_sizing(trades: pd.DataFrame, specs_by_symbol: dict, risk_pct: float = 0.5, start_equity: float = 10000.0,
                 max_leverage: float | None = None, daily_loss_limit_pct: float | None = None,
                 weekly_loss_limit_pct: float | None = None) -> tuple[pd.DataFrame, dict]:
    """trades needs: symbol, entry_time, exit_time, side, entry_fill, risk_px, pnl_px_net."""
    if len(trades) == 0:
        return trades.copy(), {"rejected": {}, "final_equity": start_equity, "max_dd_pct": 0.0}
    tr = trades.sort_values("entry_time").reset_index(drop=True)
    acc_exit, acc_pnl = [], []
    rows, rej = [], {"below_min_lot": 0, "daily_loss_limit": 0, "weekly_loss_limit": 0}
    for r in tr.itertuples():
        sp = specs_by_symbol[r.symbol]
        val = sp["value_per_px_per_lot"]
        step, vmin, vmax = sp["volume_step"], sp["volume_min"], sp["volume_max"]
        ex = np.array(acc_exit, dtype="datetime64[ns]")
        pn = np.array(acc_pnl, float)
        realized = pn[ex <= np.datetime64(r.entry_time)].sum() if len(pn) else 0.0
        eq = start_equity + realized
        day = pd.Timestamp(r.entry_time).normalize()
        week = day - pd.Timedelta(days=day.weekday())
        if len(pn):
            ex_ts = pd.to_datetime(ex)
            m_day = (ex_ts.normalize() == day) & (ex <= np.datetime64(r.entry_time))
            m_week = (ex_ts >= week) & (ex <= np.datetime64(r.entry_time))
            if daily_loss_limit_pct and pn[m_day].sum() <= -daily_loss_limit_pct / 100 * eq:
                rej["daily_loss_limit"] += 1
                continue
            if weekly_loss_limit_pct and pn[m_week].sum() <= -weekly_loss_limit_pct / 100 * eq:
                rej["weekly_loss_limit"] += 1
                continue
        risk_usd = eq * risk_pct / 100
        lots = risk_usd / (r.risk_px * val)
        capped = False
        if max_leverage:
            cap = max_leverage * eq / (sp["contract_size"] * r.entry_fill)
            if lots > cap:
                lots, capped = cap, True
        lots = min(np.floor(lots / step + 1e-9) * step, vmax)
        if lots < vmin - 1e-12:
            rej["below_min_lot"] += 1
            continue
        pnl_usd = lots * val * r.pnl_px_net
        acc_exit.append(np.datetime64(r.exit_time))
        acc_pnl.append(pnl_usd)
        rows.append({**r._asdict(), "lots": lots, "risk_usd_planned": risk_usd, "risk_usd_real": lots * val * r.risk_px,
                     "risk_pct_real": lots * val * r.risk_px / eq * 100, "leverage_capped": capped, "pnl_usd": pnl_usd})
    out = pd.DataFrame(rows).drop(columns=["Index"], errors="ignore")
    if len(out):
        o = out.sort_values("exit_time").reset_index(drop=True)
        o["equity"] = start_equity + o["pnl_usd"].cumsum()
        peak = np.maximum.accumulate(np.r_[start_equity, o["equity"].to_numpy()])[1:]
        o["drawdown_pct"] = (peak - o["equity"]) / peak * 100
        summary = {"rejected": rej, "final_equity": float(o["equity"].iloc[-1]), "max_dd_pct": float(o["drawdown_pct"].max()),
                   "leverage_capped_trades": int(o["leverage_capped"].sum()),
                   "risk_pct_real_p50": float(o["risk_pct_real"].median()), "risk_pct_real_max": float(o["risk_pct_real"].max())}
        return o, summary
    return out, {"rejected": rej, "final_equity": start_equity, "max_dd_pct": 0.0}


def real_risk_under_truth(equity: float, risk_pct: float, stop_px: float, assumed_vpp: float, true_vpp: float,
                          vmin: float = 0.01, step: float = 0.01) -> dict:
    """If lots are sized with an ASSUMED value per price unit but the terminal uses the TRUE one, what is the real risk?
    Used to audit the XAUUSD tick-value contradiction (assumed 100 vs possible 10)."""
    import math
    lots = math.floor((equity * risk_pct / 100) / (stop_px * assumed_vpp) / step + 1e-9) * step
    if lots < vmin - 1e-12:
        return {"lots": 0.0, "real_risk_usd": 0.0, "real_risk_pct": 0.0, "rejected_below_min_lot": True}
    usd = lots * true_vpp * stop_px
    return {"lots": round(lots, 4), "real_risk_usd": usd, "real_risk_pct": usd / equity * 100, "rejected_below_min_lot": False}
