#!/bin/bash
# Stage: Exp 3 (read/write mix) and Exp 4 (queue-depth sweep).
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
preflight; stage_begin exp34
# Exp 3
for mix in 100 70 50 0; do
  case $mix in 100) rw=randread;; 0) rw=randwrite;; *) rw=randrw;; esac
  geom $rw 16
  for t in $(seq 1 "$TRIALS"); do
    run_fio "$FIO_DIR/03_rwmix.fio" "$RAW/exp3/exp3__mixread=${mix}__t$t.json" \
      RW=$rw BS=4k NUMJOBS=16 IODEPTH=1 MIXREAD=$mix JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 20) RAMP=$(ramp 3)
  done
done
# Exp 4: psync numjobs=QD (<=16, fio shm limit), then single-process posixaio iodepth up to 256
geom randread 1
for qd in 1 2 4 8 16; do
  for t in $(seq 1 "$TRIALS"); do
    run_fio "$FIO_DIR/04_qd_sweep.fio" "$RAW/exp4/exp4__eng=psync__qd=${qd}__t$t.json" \
      THREAD=1 RW=randread BS=4k NUMJOBS=$qd IODEPTH=1 JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 20) RAMP=$(ramp 3)
  done
done
# posixaio, one process, iodepth up to 256 (macOS 27 limits: aioprocmax=256); Little's law checks the effective depth
for qd in 1 2 4 8 16 32 64 128 256; do
  for t in $(seq 1 "$TRIALS"); do
    ENGINE=posixaio run_fio "$FIO_DIR/04_qd_sweep.fio" "$RAW/exp4/exp4__eng=posixaio__qd=${qd}__t$t.json" \
      THREAD=1 RW=randread BS=4k NUMJOBS=1 IODEPTH=$qd JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 20) RAMP=$(ramp 3)
  done
done
stage_end exp34
