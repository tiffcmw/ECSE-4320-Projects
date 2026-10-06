#!/bin/bash
# Phase 4 interaction: core tier x working set.
set -euo pipefail
cd "$(dirname "$0")"
caffeinate -dimsu python3 exp_interaction.py
