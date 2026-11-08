import numpy as np
from quantlab.audit.bootcal import Scenario, simulate_trades, month_sums, fast_p, production_p


def test_fast_p_equals_production():
    rng = np.random.default_rng(5)
    for sc in (Scenario("a", K=24, r_dist="rr2"), Scenario("b", K=12, month_dist="sparse", n_per_month=3, r_dist="t3"),
               Scenario("c", K=60, month_dist="negbin", phi_trade=0.5, r_dist="normal")):
        for _ in range(25):
            r, mid = simulate_trades(sc, rng)
            s, c = month_sums(r, mid)
            if len(s) < 2:
                continue
            assert abs(fast_p(s, c) - production_p(r, mid)) < 1e-12
