#!/bin/bash
# Stage: Exp 6 (working set, sustained write) and Exp 7 (misleading setups).
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
preflight; stage_begin exp67
# Exp 7 first (reads only), then Exp 6a, then idle, then 6b last (heaviest write)
geom randread 1
for cfg in "A:psync:1:1:1" "B:psync:0:1:1" "C:psync:1:16:1" "D:psync:1:1:64"; do
  IFS=: read -r tag eng direct nj qd <<<"$cfg"
  for t in $(seq 1 "$TRIALS"); do
    run_fio "$FIO_DIR/07_misleading.fio" "$RAW/exp7/exp7__cfg=${tag}__eng=${eng}__direct=${direct}__nj=${nj}__qd=${qd}__t$t.json" \
      ENGINE=$eng DIRECT=$direct NUMJOBS=$nj IODEPTH=$qd RUNTIME=$(rt 20) RAMP=$(ramp 5)
  done
done
for rw in randread randwrite; do for sz in 1 32; do
  for t in $(seq 1 "$TRIALS"); do
    run_fio "$FIO_DIR/06_workingset.fio" "$RAW/exp6a/exp6a__rw=${rw}__range=${sz}g__t$t.json" \
      RW=$rw BS=4k NUMJOBS=16 IODEPTH=1 JOBSIZE=${sz}g OFFINC=0 RUNTIME=$(rt 20) RAMP=$(ramp 3)
  done
done; done
# Exp 6b: rested drive (idle 120 s) -> 300 s sustained 1 MiB sequential write, 1 s time series + SMART temperature
echo "idle before sustained write"; [ "${SMOKE:-0}" = 1 ] || sleep 120
OUT="$RAW/exp6b"; mkdir -p "$OUT"
if [ ! -f "$OUT/exp6b__sustained.json" ]; then
  B0=$(smart_bytes_written)
  ( while true; do echo "$(date +%s) $(smartctl -a disk0 2>/dev/null | awk '/^Temperature:/{print $2}')" >> "$OUT/temperature.log"; sleep 10; done ) &
  TPID=$!
  if [ "${SMOKE:-0}" = 1 ]; then RTS=5; else RTS=300; fi
  sed "s/^runtime=300/runtime=$RTS/" "$FIO_DIR/06_sustained_write.fio" > "$SCRATCH/06_sustained_write.run.fio"
  ( cd "$OUT" && env TESTFILE="$TESTFILE" LOGPREFIX="$OUT/exp6b" fio --output-format=json --output="$OUT/exp6b__sustained.json.tmp" "$SCRATCH/06_sustained_write.run.fio" ) \
     || { kill $TPID; die "sustained fio failed"; }
  kill $TPID; wait $TPID 2>/dev/null || true
  pmset -g batt | head -1 | grep -q "AC Power" || { mkdir -p "$RAW/invalid"; mv "$OUT/exp6b__sustained.json.tmp" "$RAW/invalid/"; die "sustained run invalid: left AC power"; }
  mv "$OUT/exp6b__sustained.json.tmp" "$OUT/exp6b__sustained.json"
  echo "SMART host bytes written during sustained write: $(( $(smart_bytes_written) - B0 ))" | tee "$OUT/bytes_written.txt"
fi
stage_end exp67

# Drift check: repeat the Exp 4 psync QD16 point (and the Exp 3 100% read point) at the very end of the campaign.
# Exp 2/4 gave ~190 k IOPS for this workload and Exp 3 gave ~220 k; this tells whether the machine drifts over time.
geom randread 1
for t in $(seq 1 "$TRIALS"); do
  run_fio "$FIO_DIR/04_qd_sweep.fio" "$RAW/drift/drift__src=exp4style__qd=16__t${t}.json" THREAD=1 \
    RW=randread BS=4k NUMJOBS=16 IODEPTH=1 JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 20) RAMP=$(ramp 3)
  run_fio "$FIO_DIR/03_rwmix.fio" "$RAW/drift/drift__src=exp3style__qd=16__t${t}.json" \
    RW=randread BS=4k NUMJOBS=16 IODEPTH=1 MIXREAD=100 JOBSIZE=$JOBSIZE OFFINC=$OFFINC RUNTIME=$(rt 20) RAMP=$(ramp 3)
done
