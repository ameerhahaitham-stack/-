"""bootalt.all_p['boot'] equals the production stats.cluster_bootstrap p_raw (equal trade counts per month, incl. tie-heavy discrete R)."""
import numpy as np, pandas as pd
from quantlab.stats import cluster_bootstrap
from quantlab.audit.bootalt import all_p


def test_boot_matches_production():
    rng = np.random.default_rng(5)
    for K, n in ((24, 5), (12, 3), (24, 1), (60, 5)):
        for _ in range(6):
            r = np.where(rng.random(K * n) > 2 / 3, 2.0, -1.0) if _ % 2 == 0 else rng.standard_normal(K * n)   # integer-lattice (tie heavy) and continuous R
            t = pd.Timestamp("2023-01-01") + pd.to_timedelta(np.repeat(np.arange(K), n) * 31, unit="D") + pd.to_timedelta(np.arange(K * n), unit="m")
            prod = cluster_bootstrap(pd.DataFrame({"entry_time": t, "net_R": r}), 5000, 12345, "month")["p_raw"]
            ap = all_p(r.reshape(K, n).sum(1)[None, :], n)["boot"][0]
            assert abs(prod - ap) < 1e-12, (K, n, prod, ap)
