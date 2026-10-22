#!/bin/bash
# Block until the Mac is on AC power (polls every 15 s, gives up after MAXWAIT seconds, default 3600).
MAXWAIT="${MAXWAIT:-3600}"; t=0
until pmset -g batt | head -1 | grep -q "AC Power"; do
  [ $t -ge "$MAXWAIT" ] && { echo "gave up waiting for AC power"; exit 1; }
  [ $((t % 300)) -eq 0 ] && echo "waiting for AC power ($(date '+%H:%M:%S'))"
  sleep 15; t=$((t+15))
done
echo "AC power detected $(date '+%H:%M:%S')"
