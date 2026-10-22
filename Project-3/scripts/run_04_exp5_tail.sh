#!/bin/bash
# Stage: Exp 5 (tail latency) at mid QD (4) and at the knee QD found from Exp 4.
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
preflight
export RAW_SUBDIR="${RAW#$P3/}"; [ "${SMOKE:-0}" = 1 ] && export PROC_SUBDIR=data/smoke/processed
python3 -I "$P3/scripts/parse_fio.py" >/dev/null
KNEE_CFG=$(python3 -I "$P3/scripts/find_knee.py") || die "knee not found; run Exp 4 first"
read -r K_ENG K_NJ K_QD_ITER K_THREAD KNEE <<<"$KNEE_CFG"
echo "knee (smallest effective QD with >=90% of peak IOPS): QD $KNEE via engine=$K_ENG numjobs=$K_NJ iodepth=$K_QD_ITER thread=$K_THREAD"
echo "$KNEE_CFG" > "$RAW/exp5_knee_cfg.txt"
stage_begin exp5
geom randread 1
for t in $(seq 1 "$TRIALS"); do
  run_fio "$FIO_DIR/05_tail.fio" "$RAW/exp5/exp5__role=mid__qd=4__t${t}.json" THREAD=1 \
    RW=randread BS=4k NUMJOBS=4 IODEPTH=1 JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 60) RAMP=$(ramp 5)
  ENGINE=${K_ENG%%-*} run_fio "$FIO_DIR/05_tail.fio" "$RAW/exp5/exp5__role=knee__qd=${KNEE}__t${t}.json" THREAD=$K_THREAD \
    RW=randread BS=4k NUMJOBS=$K_NJ IODEPTH=$K_QD_ITER JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 60) RAMP=$(ramp 5)
done
stage_end exp5
