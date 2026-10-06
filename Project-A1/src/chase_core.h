// Pointer-chase construction, validation and traversal. Header-only so that
// tests/ and the benchmarks use identical code.
#pragma once
#include "harness.h"

typedef enum { CHASE_RANDOM = 0, CHASE_SEQ = 1 } ChaseMode;

// Node i lives at buf + i*stride and holds the address of its successor.
// RANDOM: Sattolo shuffle gives a uniformly random single n-cycle.
// SEQ: node i points to node i+1 (wrapping): the "obvious" prefetcher-friendly
//      layout, kept only for the AI-resilience before/after comparison.
// Returns number of nodes, or 0 on failure.
static inline size_t chase_build(char *buf, size_t bytes, size_t stride, ChaseMode mode, uint64_t seed) {
    size_t n = bytes / stride;
    if (n < 2 || stride < sizeof(void *)) return 0;
    if (mode == CHASE_SEQ) {
        for (size_t i = 0; i < n; i++)
            *(void **)(buf + i * stride) = buf + ((i + 1 == n) ? 0 : i + 1) * stride;
        return n;
    }
    uint32_t *perm = malloc(n * sizeof(uint32_t));
    if (!perm || n > UINT32_MAX) return 0;
    for (size_t i = 0; i < n; i++) perm[i] = (uint32_t)i;
    Rng r = { seed ? seed : 0x9E3779B97F4A7C15ULL };
    for (size_t i = n - 1; i > 0; i--) {
        size_t j = rng_below(&r, i);  // j in [0, i-1]: Sattolo (never j == i)
        uint32_t t = perm[i]; perm[i] = perm[j]; perm[j] = t;
    }
    for (size_t i = 0; i < n; i++)
        *(void **)(buf + i * stride) = buf + (size_t)perm[i] * stride;
    free(perm);
    return n;
}

// Returns 1 iff following pointers from node 0 visits all n nodes exactly once
// and returns to node 0 after exactly n steps (a single full cycle).
static inline int chase_verify(char *buf, size_t stride, size_t n) {
    uint8_t *seen = calloc((n + 7) / 8, 1);
    if (!seen) return 0;
    char *p = buf;
    size_t steps = 0;
    int ok = 1;
    do {
        size_t idx = (size_t)(p - buf) / stride;
        if ((size_t)(p - buf) % stride != 0 || idx >= n) { ok = 0; break; }
        if (seen[idx >> 3] & (1u << (idx & 7))) { ok = 0; break; }
        seen[idx >> 3] |= (uint8_t)(1u << (idx & 7));
        p = *(char **)p;
        steps++;
    } while (p != buf && steps <= n);
    if (ok && (steps != n || p != buf)) ok = 0;
    free(seen);
    return ok;
}

// Dependent-load traversal. Each load's address is the previous load's result,
// so latency (not throughput) is measured. Returns final pointer (sunk by caller).
static inline void *chase_run(void *start, uint64_t steps) {
    void **p = (void **)start;
    for (uint64_t i = 0; i < steps; i++) p = (void **)*p;
    return p;
}
