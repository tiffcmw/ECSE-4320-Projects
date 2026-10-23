#!/bin/bash
# Read-only follow-up to the drift check: 30 back-to-back 10 s runs of the Exp 4 psync QD16 4 KiB random read point,
# starting right after heavy writes, to see whether the 190 k vs 220 k IOPS levels depend on time since the last writes.
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
preflight; stage_begin driftseries
geom randread 1
for i in $(seq -w 1 30); do
  SETTLE=0 run_fio "$FIO_DIR/04_qd_sweep.fio" "$RAW/driftseries/driftseries__i=${i}__t1.json" THREAD=1 \
    RW=randread BS=4k NUMJOBS=16 IODEPTH=1 JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 10) RAMP=2
  echo "$i $(date +%H:%M:%S)" >> "$RAW/driftseries/clock.txt"
done
stage_end driftseries
