#!/bin/bash
# E0: timer and noise characterization.
set -euo pipefail
cd "$(dirname "$0")/.."
caffeinate -dimsu python3 scripts/exp_noise.py
