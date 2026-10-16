#!/bin/bash
# Deletes only the named benchmark files inside Project-3/scratch. No recursive deletes.
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
for f in "$TESTFILE" "$SCRATCH/engine_check.bin" "$SCRATCH/.precondition_done"; do
  guard_path "$f"
  if [ -f "$f" ]; then rm -f -- "$f" && echo "removed $f"; fi
done
rmdir "$SCRATCH" 2>/dev/null && echo "removed empty $SCRATCH" || true
