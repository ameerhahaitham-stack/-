#!/bin/bash
# Queue part 2 (re-prioritised after the first results). Resumable.
cd "$(dirname "$0")/../.."
export PYTHONPATH=src
L=docs/audit/raw/queue.log
log(){ echo "$(date +%H:%M:%S) $*" >> $L; }
while pgrep -f "t3_tail.py --mode S --phi 0.8" > /dev/null; do sleep 10; done
step(){ log "START $*"; "$@" >> docs/audit/raw/queue_out.log 2>&1; log "END   $*"; }
step python3 scripts/audit/t2_bc.py --mode G --phi 0.8 --n 20000
step python3 scripts/audit/t2_bc.py --mode G --phi 0.95 --n 20000
step python3 scripts/audit/t4b_extra.py --part b --fams 2500
step python3 scripts/audit/t4b_extra.py --part a --reps 20000
for s in phi0.8_mid phi0.8_crowded phi0.0_mid phi0.95_mid phi0.8_sparse; do
  step python3 scripts/audit/t5_trade.py --setting $s --n 800
done
step python3 scripts/audit/t1_ablation.py --setting phi0.95 --n 1500 --which extra
step python3 scripts/audit/t1_ablation.py --setting sv_phi0.8_2y --n 1500 --which extra
step python3 scripts/audit/t3_tail.py --mode G --phi 0.0 --n 20000 --nfull 3000
step python3 scripts/audit/t3_tail.py --mode G --phi 0.5 --n 20000 --nfull 3000
step python3 scripts/audit/t3_tail.py --mode G --phi 0.8 --k0 20000 --n 10000 --tag _ext
step python3 scripts/audit/t3_tail.py --mode G --phi 0.95 --k0 6000 --n 14000 --tag _ext
for phi in 0.95 0.0 0.5; do
  step python3 scripts/audit/t3_tail.py --mode S --phi $phi --n 20000 --nfull 3000
done
step python3 scripts/audit/t2_bc.py --mode G --phi 0.0 --n 10000
step python3 scripts/audit/t2_bc.py --mode G --phi 0.5 --n 10000
step python3 scripts/audit/t2_bc.py --mode S --phi 0.8 --n 10000
step python3 scripts/audit/t3_tail.py --mode C --phi 0.8 --n 20000 --nfull 3000
step python3 scripts/audit/t3_tail.py --mode R --phi 0.8 --n 20000 --nfull 3000
step python3 scripts/audit/t2_bc.py --mode C --phi 0.8 --n 10000
step python3 scripts/audit/t2_bc.py --mode R --phi 0.8 --n 10000
step python3 scripts/audit/t1_ablation.py --setting phi0.5 --n 1500
step python3 scripts/audit/t1_ablation.py --setting phi0 --n 1500
log "QUEUE DONE"
