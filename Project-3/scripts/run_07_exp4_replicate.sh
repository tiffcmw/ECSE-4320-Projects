#!/bin/bash
# Replicate of the Exp 4 queue-depth sweep (files exp4b__*), run later in the campaign when the host was in its
# "high-IOPS" state (~222 k at QD16 vs ~189 k earlier; see REPORT anomalies). Read-only.
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
preflight; stage_begin exp4b
geom randread 1
for qd in 1 2 4 8 16; do
  for t in $(seq 1 "$TRIALS"); do
    run_fio "$FIO_DIR/04_qd_sweep.fio" "$RAW/exp4b/exp4b__eng=psync__qd=${qd}__t$t.json" \
      THREAD=1 RW=randread BS=4k NUMJOBS=$qd IODEPTH=1 JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 20) RAMP=$(ramp 3)
  done
done
for qd in 1 2 4 8 16 32 64 128 256; do
  for t in $(seq 1 "$TRIALS"); do
    ENGINE=posixaio run_fio "$FIO_DIR/04_qd_sweep.fio" "$RAW/exp4b/exp4b__eng=posixaio__qd=${qd}__t$t.json" \
      THREAD=1 RW=randread BS=4k NUMJOBS=1 IODEPTH=$qd JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 20) RAMP=$(ramp 3)
  done
done
stage_end exp4b
