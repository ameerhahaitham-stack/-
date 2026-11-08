#!/bin/bash
# Supplementary-audit queue 7 (event-calibration gaps). Resumable.
cd "$(dirname "$0")/../.."
export PYTHONPATH=src
L=docs/audit/raw/queue7.log
log(){ echo "$(date +%H:%M:%S) $*" >> $L; }
step(){ log "START $*"; "$@" >> docs/audit/raw/queue7_out.log 2>&1; log "END   $*"; }
if [ "$1" = A ]; then
step python3 scripts/audit/t1_ablation.py --setting phi0 --n 1500 --procs 1
step python3 scripts/audit/t1_ablation.py --setting phi0.5 --n 1500 --procs 1
else
step python3 scripts/audit/t3_tail.py --mode S --phi 0.0 --n 8000 --nfull 3000 --procs 1
step python3 scripts/audit/t3_tail.py --mode S --phi 0.5 --n 8000 --nfull 3000 --procs 1
step python3 scripts/audit/t3_tail.py --mode S --phi 0.95 --n 8000 --nfull 3000 --procs 1
fi
log "Q7$1 DONE"
