#!/bin/bash
# Stage: Exp 3 (read/write mix) and Exp 4 (queue-depth sweep).
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
preflight; stage_begin exp34
# Exp 3
for mix in 100 70 50 0; do
  case $mix in 100) rw=randread;; 0) rw=randwrite;; *) rw=randrw;; esac
  geom $rw 16
  for t in $(seq 1 "$TRIALS"); do
    run_fio "$FIO_DIR/03_rwmix.fio" "$RAW/exp3/exp3__mixread=$mix__t$t.json" \
      RW=$rw BS=4k NUMJOBS=16 IODEPTH=1 MIXREAD=$mix JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 20) RAMP=$(ramp 3)
  done
done
# Exp 4: psync numjobs=QD (<=16 per process), then 2/4/8 processes x 16 = QD 32/64/128
geom randread 1
for qd in 1 2 4 8 16; do
  for t in $(seq 1 "$TRIALS"); do
    run_fio "$FIO_DIR/04_qd_sweep.fio" "$RAW/exp4/exp4__eng=psync__qd=$qd__t$t.json" \
      RW=randread BS=4k NUMJOBS=$qd IODEPTH=1 JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 20) RAMP=$(ramp 3)
  done
done
for k in 2 4 8; do
  [ "${SMOKE:-0}" = 1 ] && [ $k != 2 ] && continue
  for t in $(seq 1 "$TRIALS"); do
    run_multi "$FIO_DIR/04_qd_sweep.fio" "$RAW/exp4/exp4__eng=psync__qd=$((16*k))__t$t" $k \
      RW=randread BS=4k NUMJOBS=16 IODEPTH=1 JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 20) RAMP=$(ramp 3)
  done
done
# posixaio cross-check: configured iodepth vs effective depth
for qd in 1 2 4 8 16 32 64; do
  for t in $(seq 1 "$TRIALS"); do
    ENGINE=posixaio run_fio "$FIO_DIR/04_qd_sweep.fio" "$RAW/exp4/exp4__eng=posixaio__qd=$qd__t$t.json" \
      RW=randread BS=4k NUMJOBS=1 IODEPTH=$qd JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 20) RAMP=$(ramp 3)
  done
done
stage_end exp34
