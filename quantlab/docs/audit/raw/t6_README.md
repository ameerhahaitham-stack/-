# t6 raw p-value arrays (not committed)

`docs/audit/raw/t6/{scenario}_K{K}_mu{mu}.npz` (131 files, ≈361 MB; one float64 p-value array per method, 100 000 reps at μ=0 and 20 000 at μ>0) are **not** in the repository (size).
They are bit-reproducible from the seeds: `python scripts/audit/t6_alt.py --K 24 60` (SEED0=20261120, config in `t6_config.json`), then `python scripts/audit/t6_analyze.py`.
`t6_MANIFEST_sha256.txt` lists the SHA-256 of every file produced in the reported run (to verify a re-run). All rejection counts, rates and exact CIs derived from them are in
`docs/audit/t6_size.csv`, `t6_power.csv`, `t6_lrv.csv`, `t6_mde80.csv`. The raw arrays are available from the author of this audit on request.
