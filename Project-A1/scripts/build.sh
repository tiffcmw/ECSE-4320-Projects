#!/bin/bash
# Build all benchmarks. Flags are documented in docs/METHODOLOGY.md.
# -O2 as required; -mcpu=native targets the host (Apple M-series); no -ffast-math
# so floating-point semantics (and the compute loop's dependency chain) are preserved.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build
CFLAGS="-O2 -std=c17 -Wall -Wextra -mcpu=native -pthread"
for src in src/*.c; do
    name=$(basename "$src" .c)
    clang $CFLAGS "$src" -o "build/$name" -lm
    echo "built build/$name"
done
clang $CFLAGS tests/test_harness.c -o build/test_harness -lm
echo "built build/test_harness"
