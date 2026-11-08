import numpy as np, pandas as pd
from quantlab.audit.tradecal import TradeCfg, null_signals, matched_control_audit
from quantlab.calibration import ar_series, H4
from quantlab.costs import ZERO
from quantlab.engine import atr, matched_control


def test_audit_matched_control_equals_production():
    for phi, k in ((0.0, 1), (0.8, 2)):
        cfg = TradeCfg(phi=phi)
        df = ar_series(cfg.n_bars, phi, 5 + k)
        t = pd.to_datetime(df["time"]); a, o = atr(df, 14), df["open"].to_numpy(float)
        sg = null_signals(df, a, o, cfg, np.random.default_rng(k))
        es, ee = t.iloc[0], t.iloc[-1] + H4
        prod = matched_control(df, sg, ZERO, es, ee, 60, 777)
        mine = matched_control_audit(df, sg, ZERO, es, ee, 60, 777)
        p = (1 + int((mine["means"] >= prod["signal_mean"]).sum())) / (1 + len(mine["means"]))
        assert abs(p - prod["p_vs_control"]) < 1e-15 and abs(mine["means"].mean() - prod["control_mean"]) < 1e-12
