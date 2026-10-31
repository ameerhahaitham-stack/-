"""Trading-cost model. Costs are charged per trade and reported relative to the actual stop distance (R)."""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import pandas as pd


@dataclass
class CostModel:
    name: str = "zero"
    spread_mode: str = "measured"        # measured | fixed | none
    spread_mult: float = 1.0
    spread_fixed_px: float = 0.0
    spread_floor_px: float = 0.0         # minimum spread when measured spread is 0 / missing
    commission_usd_per_lot_rt: float = 0.0
    slippage_in_px: float = 0.0          # adverse, applied to market entries
    slippage_out_px: float = 0.0         # adverse, applied to stop / time exits (not to TP limits)
    swap_long_pts: float = 0.0           # MT5 'points' mode only; negative = cost
    swap_short_pts: float = 0.0
    point: float = 0.01
    value_per_px_per_lot: float = 100.0  # account-currency value of 1.0 price move per 1 lot

    @property
    def commission_px(self) -> float:
        return self.commission_usd_per_lot_rt / self.value_per_px_per_lot

    def spread_array(self, df: pd.DataFrame, fallback_px: float = 0.0) -> np.ndarray:
        n = len(df)
        if self.spread_mode == "none":
            return np.zeros(n)
        if self.spread_mode == "fixed":
            return np.full(n, self.spread_fixed_px * self.spread_mult)
        s = df["spread"].to_numpy(float) * self.point if "spread" in df else np.full(n, np.nan)
        s = np.where(np.isnan(s), fallback_px, s)
        return np.maximum(s * self.spread_mult, self.spread_floor_px * self.spread_mult)


ZERO = CostModel(name="zero", spread_mode="none")

WEEKDAY_NIGHTS = {0: 1, 1: 1, 2: 3, 3: 1, 4: 1, 5: 0, 6: 0}  # nights charged when rolling out of this weekday (Wed = triple)


def swap_nights(t_in: pd.Timestamp, t_out: pd.Timestamp) -> int:
    """Weighted number of rollovers (server midnight) between entry and exit."""
    d0, d1 = t_in.normalize(), t_out.normalize()
    n = 0
    d = d0
    while d < d1:
        n += WEEKDAY_NIGHTS[d.weekday()]
        d += pd.Timedelta(days=1)
    return n


def build_scenarios(symbol: str, specs: dict, params: dict) -> dict[str, CostModel]:
    """Four scenarios from protocol_params (optimistic/base/pessimistic/stress)."""
    base = params["costs"]["symbols"][symbol]
    out = {}
    for name, m in params["costs"]["scenarios"].items():
        out[name] = CostModel(
            name=name, spread_mode="measured", spread_mult=m["spread_mult"],
            spread_floor_px=base["spread_floor_px"],
            commission_usd_per_lot_rt=base["commission_usd_per_lot_rt"] * m["commission_mult"],
            slippage_in_px=base["slippage_in_px"] * m["slip_mult"], slippage_out_px=base["slippage_out_px"] * m["slip_mult"],
            swap_long_pts=specs.get("swap_long", 0.0) if specs.get("swap_mode_points") else 0.0,
            swap_short_pts=specs.get("swap_short", 0.0) if specs.get("swap_mode_points") else 0.0,
            point=specs["point"], value_per_px_per_lot=specs["value_per_px_per_lot"])
    return out


def fallback_spread_px(symbol: str, params: dict) -> float:
    return params["costs"]["symbols"][symbol].get("fallback_spread_px", 0.0)
