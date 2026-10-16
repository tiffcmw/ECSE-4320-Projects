#!/bin/bash
# Stage: Exp 1 (zero-queue baselines) and Exp 2 (block-size sweep).
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
preflight; stage_begin exp12
# Exp 1: QD1, 1 job
for combo in randread:4k randwrite:4k read:128k write:128k; do
  rw=${combo%%:*}; bs=${combo##*:}; geom $rw 1
  for t in $(seq 1 "$TRIALS"); do
    run_fio "$FIO_DIR/01_baseline.fio" "$RAW/exp1/exp1__rw=$rw__bs=$bs__t$t.json" \
      RW=$rw BS=$bs NUMJOBS=1 IODEPTH=1 JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 30) RAMP=$(ramp 5)
  done
done
# Exp 2: effective QD16
for rw in randread read randwrite write; do
  sizes="4k 16k 32k 64k 128k 256k"; [ "$rw" = read ] || [ "$rw" = write ] && sizes="$sizes 512k 1m"
  case $rw in *write) RT=10;; *) RT=15;; esac
  for bs in $sizes; do
    geom $rw 16
    for t in $(seq 1 "$TRIALS"); do
      run_fio "$FIO_DIR/02_blocksize.fio" "$RAW/exp2/exp2__rw=$rw__bs=$bs__t$t.json" \
        RW=$rw BS=$bs NUMJOBS=16 IODEPTH=1 JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt $RT) RAMP=$(ramp 2)
    done
  done
done
stage_end exp12
