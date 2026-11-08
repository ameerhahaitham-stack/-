#!/bin/bash
cd "$(dirname "$0")/../.."
export PYTHONPATH=src
for s in D1 D2 D0; do
  echo "$(date +%H:%M:%S) START $s" >> docs/audit/raw/queue8.log
  python3 scripts/audit/t10_drift.py --setting $s --n 300 --procs 1 >> docs/audit/raw/queue8_out.log 2>&1
  echo "$(date +%H:%M:%S) END $s" >> docs/audit/raw/queue8.log
done
