#!/bin/bash
cd "$(dirname "$0")/../.."
for s in phi0.8 phi0.95 phi0 phi0.5 sv_phi0.8_2y; do
  PYTHONPATH=src python3 scripts/audit/t1_ablation.py --setting $s --n 1500 --procs 2 >> docs/audit/raw/t1_run.log 2>&1
done
