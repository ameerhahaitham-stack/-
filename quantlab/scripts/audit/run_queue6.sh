#!/bin/bash
# Reduced final queue (machine restarts forced smaller targets; sizes are reported in the report)
cd "$(dirname "$0")/../.."
export PYTHONPATH=src
L=docs/audit/raw/queue6.log
log(){ echo "$(date +%H:%M:%S) $*" >> $L; }
step(){ log "START $*"; "$@" >> docs/audit/raw/queue6_out.log 2>&1; log "END   $*"; }
if [ "$1" = A ]; then
step python3 scripts/audit/t3_tail.py --mode W --phi 0.8 --n 8000 --nfull 3000 --procs 1
step python3 scripts/audit/t2_bc.py --mode W --phi 0.95 --n 5000 --procs 1
step python3 scripts/audit/t3_tail.py --mode C --phi 0.8 --n 6000 --nfull 2000 --procs 1
step python3 scripts/audit/t2_bc.py --mode C --phi 0.8 --n 4000 --procs 1
else
step python3 scripts/audit/t3_tail.py --mode G --phi 0.5 --n 8000 --nfull 3000 --procs 1
step python3 scripts/audit/t2_bc.py --mode G --phi 0.0 --n 5000 --procs 1
step python3 scripts/audit/t2_bc.py --mode G --phi 0.5 --n 5000 --procs 1
step python3 scripts/audit/t3_tail.py --mode R --phi 0.8 --n 6000 --nfull 2000 --procs 1
step python3 scripts/audit/t2_bc.py --mode R --phi 0.8 --n 4000 --procs 1
step python3 scripts/audit/t5_trade.py --setting phi0.8_regular --n 800
fi
log "Q6$1 DONE"
