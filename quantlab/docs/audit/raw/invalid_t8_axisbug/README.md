INVALID first run of scripts/audit/t8_holm.py (kept for transparency, NOT used in the report): bootalt._ar_cols looped over axis 1, which is correct for the
2-D (reps x time) arrays of T6/T7 but for the 3-D family arrays (families x strategies x time) applied the AR recursion ACROSS STRATEGIES instead of across time.
Within-strategy temporal dependence was therefore not generated in that run. Fixed by looping over the last axis; the run was repeated (docs/audit/raw/t8).
