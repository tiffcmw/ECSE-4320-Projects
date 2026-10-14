#!/bin/bash
# Build the benchmark harness. Flags are recorded in data/raw/meta_*.json by scripts/meta.py.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p bin
CFLAGS="-O2 -std=gnu17 -mcpu=native -ffp-contract=off -Wall -Wextra -Wno-unused-function -pthread"
echo "$CFLAGS" > bin/CFLAGS.txt
clang $CFLAGS src/membench.c -o bin/membench -lm
echo "built bin/membench with: clang $CFLAGS"
