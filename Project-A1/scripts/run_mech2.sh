#!/bin/bash
# Mechanism 2: QoS and process-policy experiments (includes placement probe).
set -euo pipefail
cd "$(dirname "$0")"
caffeinate -dimsu bash -c 'python3 exp_qos.py && python3 probe_core_type.py --reps 15 interactive initiated default utility background && python3 probe_core_type.py --reps 15 --wrap "/usr/sbin/taskpolicy -c utility" none && python3 probe_core_type.py --reps 15 --wrap "/usr/sbin/taskpolicy -c background" none && python3 probe_core_type.py --reps 15 --wrap "/usr/sbin/taskpolicy -b" none'
