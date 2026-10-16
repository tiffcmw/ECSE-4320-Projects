#!/bin/bash
# Stage: Exp 5 (tail latency) at mid QD (4) and at the knee QD found from Exp 4.
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
preflight
python3 -I "$P3/scripts/parse_fio.py" >/dev/null
KNEE=$(python3 -I "$P3/scripts/find_knee.py") || die "knee not found; run Exp 4 first"
echo "knee QD (smallest QD with >=90% of peak IOPS, psync): $KNEE"
echo "$KNEE" > "$RAW/exp5_knee_qd.txt"
stage_begin exp5
geom randread 1
for qd in 4 "$KNEE"; do
  for t in $(seq 1 "$TRIALS"); do
    run_fio "$FIO_DIR/05_tail.fio" "$RAW/exp5/exp5__qd=$qd__t$t.json" \
      RW=randread BS=4k NUMJOBS=$qd IODEPTH=1 JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 60) RAMP=$(ramp 5)
  done
done
stage_end exp5
