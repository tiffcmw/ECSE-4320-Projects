#!/usr/bin/env bash
# Appends a dated environment snapshot (assignment Step 0 commands plus session power state) to docs/ENVIRONMENT_sessions.log.
cd "$(dirname "$0")/.."
{
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  pmset -g batt | head -2
  pmset -g | grep -iE "lowpowermode|powermode"
  pmset -g therm
  echo "thermalpressurelevel: $(notifyutil -g com.apple.system.thermalpressurelevel | awk '{print $NF}')"
  uptime
} >> docs/ENVIRONMENT_sessions.log
tail -12 docs/ENVIRONMENT_sessions.log
