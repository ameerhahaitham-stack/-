"""Real candlestick charts from the stored price data (never screenshots), with trade overlays and example galleries."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd

_STYLE = mpf.make_mpf_style(base_mpf_style="charles", gridstyle=":", facecolor="white")


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    d = df.set_index(pd.DatetimeIndex(df["time"]))[["open", "high", "low", "close"]].astype(float)
    d.columns = ["Open", "High", "Low", "Close"]
    return d


def candlestick(df: pd.DataFrame, path=None, title: str = "", markers=None, hlines=None, zones=None, figsize=(13, 6.5)):
    """df: time/open/high/low/close. markers: dicts(time, price, kind, label). hlines: dicts(price, label, color, style).
    zones: dicts(low, high, color). Returns the matplotlib Figure (and saves it when path is given)."""
    d = _prep(df)
    fig, axes = mpf.plot(d, type="candle", style=_STYLE, title=title, returnfig=True, figsize=figsize, warn_too_much_data=10**9)
    ax = axes[0]
    pos = {ts: k for k, ts in enumerate(d.index)}
    for z in zones or []:
        ax.axhspan(z["low"], z["high"], color=z.get("color", "#cccccc"), alpha=0.25)
    for h in hlines or []:
        ax.axhline(h["price"], color=h.get("color", "#555"), linestyle=h.get("style", "--"), linewidth=1)
        ax.text(0.01, h["price"], h.get("label", ""), transform=ax.get_yaxis_transform(), fontsize=8, va="bottom")
    sty = {"entry_long": ("^", "#0a7"), "entry_short": ("v", "#c22"), "exit": ("x", "#222"), "signal": ("o", "#e90")}
    for m in markers or []:
        ts = pd.Timestamp(m["time"])
        if ts not in pos:
            continue
        mk, col = sty.get(m["kind"], ("o", "#333"))
        ax.scatter(pos[ts], m["price"], marker=mk, s=90, color=col, zorder=5)
        if m.get("label"):
            ax.annotate(m["label"], (pos[ts], m["price"]), textcoords="offset points", xytext=(4, 8), fontsize=8)
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=110, bbox_inches="tight")
        plt.close(fig)
    return fig


def _pos(df, ts):
    return int(df["time"].searchsorted(pd.Timestamp(ts)))


def trade_charts(df: pd.DataFrame, trade: dict, outdir, name: str, pre: int = 80, post: int = 40) -> dict:
    """Two charts per trade. BEFORE shows only bars up to the signal bar (nothing from the future); AFTER shows the outcome."""
    df = df.reset_index(drop=True)
    e, x = _pos(df, trade["entry_time"]), _pos(df, trade["exit_time"])
    sig = max(e - 1, 0)
    side = int(trade["side"])
    lines = [{"price": trade["stop"], "label": "stop", "color": "#c22"}]
    if trade.get("tp") is not None and not pd.isna(trade.get("tp")):
        lines.append({"price": trade["tp"], "label": "target", "color": "#0a7"})
    before = df.iloc[max(sig - pre, 0): sig + 1]
    p1 = Path(outdir) / f"{name}_before.png"
    candlestick(before, p1, f"{name} - BEFORE entry (data up to signal bar only)", hlines=lines,
                markers=[{"time": df['time'].iloc[sig], "price": df['close'].iloc[sig], "kind": "signal", "label": "signal"}])
    after = df.iloc[max(sig - pre, 0): min(x + post, len(df) - 1) + 1]
    p2 = Path(outdir) / f"{name}_after.png"
    candlestick(after, p2, f"{name} - AFTER ({trade['exit_reason']}, {trade['net_R']:+.2f}R net)", hlines=lines,
                markers=[{"time": trade["entry_time"], "price": trade["entry_fill"], "kind": "entry_long" if side == 1 else "entry_short", "label": "entry"},
                         {"time": trade["exit_time"], "price": trade["exit_fill"], "kind": "exit", "label": f"{trade['net_R']:+.2f}R"}])
    return {"before": str(p1), "after": str(p2)}


def example_gallery(df: pd.DataFrame, trades: pd.DataFrame, pattern: str, outdir, n_each: int = 5, seed: int = 1) -> dict:
    """Random (not hand-picked) winners and losers, so the gallery cannot hide the losing trades. Seed is recorded."""
    outdir = Path(outdir)
    rng = np.random.default_rng(seed)
    out = {"pattern": pattern, "seed": seed, "wins": [], "losses": []}
    for label, mask in [("wins", trades["net_R"] > 0), ("losses", trades["net_R"] <= 0)]:
        sub = trades[mask]
        pick = rng.choice(len(sub), size=min(n_each, len(sub)), replace=False) if len(sub) else []
        for k, ix in enumerate(sorted(pick)):
            tr = sub.iloc[int(ix)].to_dict()
            out[label].append({**trade_charts(df, tr, outdir, f"{pattern}_{label[:-1]}{k + 1}"), "entry_time": str(tr["entry_time"]),
                               "net_R": float(tr["net_R"])})
    out["n_wins_total"] = int((trades["net_R"] > 0).sum())
    out["n_losses_total"] = int((trades["net_R"] <= 0).sum())
    (outdir / f"{pattern}_gallery.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out
