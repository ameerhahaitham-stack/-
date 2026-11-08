#!/bin/bash
cd "$(dirname "$0")/../.."
export PYTHONPATH=src
L=docs/audit/raw/queue4.log
log(){ echo "$(date +%H:%M:%S) $*" >> $L; }
step(){ log "START $*"; "$@" >> docs/audit/raw/queue4_out.log 2>&1; log "END   $*"; }
step python3 scripts/audit/t3_tail.py --mode W --phi 0.95 --n 20000 --nfull 3000 --procs 1
step python3 scripts/audit/t3_tail.py --mode W --phi 0.8 --n 20000 --nfull 3000 --procs 1
step python3 scripts/audit/t2_bc.py --mode W --phi 0.95 --n 10000 --procs 1
step python3 scripts/audit/t2_bc.py --mode W --phi 0.8 --n 10000 --procs 1
log "Q4 DONE"
