#!/bin/bash
# Mechanism 1: cache/TLB experiments. The naive chase runs first (AI-resilience 'before' data).
set -euo pipefail
cd "$(dirname "$0")/.."
cd scripts
caffeinate -dimsu bash -c 'python3 exp_chase_naive.py && python3 exp_chase.py && python3 exp_bw.py'
