#!/bin/bash
# Shared helpers, sourced by every driver. Provides the safety guards:
#   - the only file ever benchmarked is $TESTFILE (or other files) inside $SCRATCH
#   - refuse to run if free space after the file would drop below 20%
#   - refuse to run on battery / Low Power Mode unless ALLOW_BATTERY=1
set -euo pipefail

P3="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SCRATCH="$P3/scratch.noindex"   # *.noindex: Spotlight skips this directory
TESTFILE="$SCRATCH/testfile.bin"
SIZE_GIB="${SIZE_GIB:-32}"
SIZE_BYTES=$((SIZE_GIB * 1024 * 1024 * 1024))
RAW="${RAW:-$P3/data/raw}"          # smoke tests override this to data/smoke
HEALTH="$RAW/health"
FIO_DIR="$P3/fio"
ENGINE="${ENGINE:-psync}"

die() { echo "ABORT: $*" >&2; exit 1; }

# guard_path PATH: abort unless PATH resolves to a location inside $SCRATCH
guard_path() {
  local p="$1" d f
  case "$p" in /dev/*|/dev) die "refusing device path: $p";; esac
  [ -L "$SCRATCH" ] && die "$SCRATCH is a symlink"
  [ -d "$SCRATCH" ] || die "$SCRATCH does not exist (mkdir it first)"
  d="$(cd "$(dirname "$p")" 2>/dev/null && pwd -P)" || die "cannot resolve directory of $p"
  f="$d/$(basename "$p")"
  case "$f" in
    "$SCRATCH"/*) ;;
    *) die "target $f is outside $SCRATCH" ;;
  esac
  [ -L "$f" ] && die "target $f is a symlink"
  return 0
}

# check_free NEEDED_BYTES: free space left after writing NEEDED_BYTES must be >= 20% of the volume
check_free() {
  local need="$1" total avail
  read -r total avail < <(df -k "$SCRATCH" | awk 'NR==2{print $2, $4}')
  local after=$(( avail - need / 1024 ))
  [ $(( after * 100 )) -ge $(( total * 20 )) ] || die "free space after test file would be <20% (avail ${avail}KiB of ${total}KiB, need $((need/1024))KiB)"
}

check_power() {
  local src; src="$(pmset -g batt | head -1)"
  if ! echo "$src" | grep -q "AC Power"; then
    [ "${ALLOW_BATTERY:-0}" = "1" ] || die "not on AC power ($src). Plug in, or set ALLOW_BATTERY=1 (recorded in metadata)."
    echo "WARNING: running on battery (ALLOW_BATTERY=1)" >&2
  fi
  if [ "$(pmset -g | awk '/lowpowermode/{print $2}')" = "1" ]; then die "Low Power Mode is on"; fi
}

# SMART "Data Units Written" (1 unit = 512000 bytes) -> bytes written by host since manufacture
smart_bytes_written() {
  smartctl -a disk0 2>/dev/null | awk -F: '/Data Units Written/{gsub(/[ ,]/,"",$2); sub(/\[.*/,"",$2); print $2*512000}'
}

# health_log TAG PHASE: snapshot of drive/power/thermal state to data/raw/health/TAG_PHASE.txt
health_log() {
  mkdir -p "$HEALTH"
  local out="$HEALTH/${1}_${2}.txt"
  {
    echo "== time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "== host: $(sw_vers -productName) $(sw_vers -productVersion) ($(sw_vers -buildVersion)); $(sysctl -n machdep.cpu.brand_string); $(( $(sysctl -n hw.memsize) / 1073741824 )) GiB RAM"
    echo "== fio: $(fio --version)"
    echo "== power:"; pmset -g batt; pmset -g | grep -i -E "lowpowermode|powermode" || true
    echo "== thermal:"; pmset -g therm 2>&1 | grep -v '^$' || true
    echo "== free space:"; df -h "$SCRATCH" | tail -1
    echo "== smartctl:"; smartctl -a disk0 2>&1 | grep -E "Model Number|Firmware|Temperature|Percentage Used|Data Units|Host (Read|Write)|Available Spare:|Critical Warning|self-assessment" || echo "smartctl unreadable"
    echo "== smart_bytes_written: $(smart_bytes_written)"
    echo "== top CPU consumers:"; ps -Aro pcpu,comm | head -6
  } > "$out" 2>&1
}

# run_fio JOBFILE OUTPUT_JSON [VAR=value ...]  (variables are exported to the job file as ${VAR})
# Never overwrites an existing raw file.
run_fio() {
  local job="$1" out="$2"; shift 2
  guard_path "$TESTFILE"
  mkdir -p "$(dirname "$out")"
  if [ -f "$out" ]; then echo "  exists, skip: $(basename "$out")"; return 0; fi
  echo "  fio $(basename "$job") -> $(basename "$out")"
  env TESTFILE="$TESTFILE" ENGINE="$ENGINE" "$@" fio --output-format=json --output="$out.tmp" "$job" \
    || { rm -f "$out.tmp"; die "fio failed for $out"; }
  mv "$out.tmp" "$out"
  sleep "${SETTLE:-3}"
}

# Common preflight for a stage driver. Needs the test file to exist unless $1 = nofile.
preflight() {
  mkdir -p "$SCRATCH" "$RAW"
  guard_path "$TESTFILE"
  check_power
  if [ "${1:-}" = "nofile" ]; then check_free "$SIZE_BYTES"; else
    [ -f "$TESTFILE" ] || die "test file missing; run scripts/run_00_precondition.sh first"
    [ "$(stat -f %z "$TESTFILE")" = "$SIZE_BYTES" ] || die "test file size != ${SIZE_GIB} GiB"
    [ -f "$SCRATCH/.precondition_done" ] || die "preconditioning not completed"
  fi
  command -v fio >/dev/null || die "fio not installed"
}

# Smoke mode: SMOKE=1 -> short runs, one trial, output to data/smoke (never mixed with raw data)
if [ "${SMOKE:-0}" = "1" ]; then RAW="$P3/data/smoke"; HEALTH="$RAW/health"; RT_SCALE=smoke; fi
TRIALS="${TRIALS:-3}"
[ "${SMOKE:-0}" = "1" ] && TRIALS=1
# rt FULL_RUNTIME: runtime in seconds, 3 in smoke mode
rt() { if [ "${SMOKE:-0}" = "1" ]; then echo 3; else echo "$1"; fi; }
ramp() { if [ "${SMOKE:-0}" = "1" ]; then echo 1; else echo "$1"; fi; }

# is_random RW
is_random() { case "$1" in rand*) return 0;; *) return 1;; esac; }
# geom RW NUMJOBS -> sets JOBSIZE / OFFINC.  Random jobs share the whole range; sequential jobs get
# disjoint 1/NUMJOBS slices so that each job stays sequential.
geom() {
  if is_random "$1"; then JOBSIZE="${SIZE_GIB}g"; OFFINC=0
  else JOBSIZE="$(( SIZE_GIB / $2 ))g"; OFFINC="$JOBSIZE"; fi
}

# run_multi JOBFILE OUTPUT_PREFIX K [VAR=value ...]: K concurrent fio processes -> PREFIX__p0.json .. PREFIX__p{K-1}.json
# (fio allows <= 16 jobs per process on macOS because of the 4 MB System V shm limit)
run_multi() {
  local job="$1" pre="$2" k="$3"; shift 3
  guard_path "$TESTFILE"; mkdir -p "$(dirname "$pre")"
  [ -f "${pre}__p0.json" ] && { echo "  exists, skip: $(basename "$pre")"; return 0; }
  echo "  fio x$k $(basename "$job") -> $(basename "$pre")__p*.json"
  local pids=() i
  for ((i=0;i<k;i++)); do
    env TESTFILE="$TESTFILE" ENGINE="$ENGINE" "$@" fio --output-format=json --output="${pre}__p$i.json.tmp" "$job" &
    pids+=($!)
  done
  local fail=0; for p in "${pids[@]}"; do wait "$p" || fail=1; done
  [ $fail = 0 ] || { rm -f "${pre}"__p*.json.tmp; die "a fio process failed for $pre"; }
  for ((i=0;i<k;i++)); do mv "${pre}__p$i.json.tmp" "${pre}__p$i.json"; done
  sleep "${SETTLE:-3}"
}

# stage_begin NAME / stage_end NAME: health snapshots + SMART bytes written for the whole stage
stage_begin() { STAGE_B0=$(smart_bytes_written); health_log "$1" before; echo "stage $1 start $(date '+%H:%M:%S')"; }
stage_end() {
  health_log "$1" after
  local b1; b1=$(smart_bytes_written)
  echo "stage $1 end $(date '+%H:%M:%S'); SMART host bytes written this stage: $(( b1 - STAGE_B0 ))" | tee -a "$RAW/health/${1}_bytes_written.txt"
}
