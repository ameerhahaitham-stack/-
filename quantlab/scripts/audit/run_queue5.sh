#!/bin/bash
cd "$(dirname "$0")/../.."
export PYTHONPATH=src
L=docs/audit/raw/queue.log
log(){ echo "$(date +%H:%M:%S) $*" >> $L; }
step(){ log "START $*"; "$@" >> docs/audit/raw/queue_out.log 2>&1; log "END   $*"; }
while pgrep -f "t3_tail.py --mode G --phi 0.0" > /dev/null; do sleep 10; done
step python3 scripts/audit/t3_tail.py --mode G --phi 0.5 --n 20000 --nfull 3000
step python3 scripts/audit/t2_bc.py --mode G --phi 0.0 --n 10000
step python3 scripts/audit/t2_bc.py --mode G --phi 0.5 --n 10000
step python3 scripts/audit/t3_tail.py --mode C --phi 0.8 --n 20000 --nfull 3000
step python3 scripts/audit/t3_tail.py --mode R --phi 0.8 --n 20000 --nfull 3000
step python3 scripts/audit/t2_bc.py --mode C --phi 0.8 --n 10000
step python3 scripts/audit/t2_bc.py --mode R --phi 0.8 --n 10000
step python3 scripts/audit/t3_tail.py --mode G --phi 0.8 --k0 20000 --n 10000 --tag _ext
step python3 scripts/audit/t3_tail.py --mode G --phi 0.95 --k0 6000 --n 14000 --tag _ext
log "QUEUE5 DONE"
