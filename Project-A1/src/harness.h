// Common stats, RNG and CLI helpers shared by all benchmarks.
#pragma once
#include <stdio.h>
#include <math.h>
#include "platform.h"

typedef struct { double min, q1, median, q3, max, mean; } Stats;

static int cmp_d(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

// Linear-interpolated quantile on a sorted array.
static inline double quantile_sorted(const double *s, int n, double q) {
    double pos = q * (n - 1);
    int lo = (int)pos;
    double f = pos - lo;
    return lo + 1 < n ? s[lo] * (1 - f) + s[lo + 1] * f : s[lo];
}

// Sorts v in place.
static inline Stats compute_stats(double *v, int n) {
    qsort(v, n, sizeof(double), cmp_d);
    Stats s; double sum = 0;
    for (int i = 0; i < n; i++) sum += v[i];
    s.min = v[0]; s.max = v[n - 1]; s.mean = sum / n;
    s.q1 = quantile_sorted(v, n, 0.25);
    s.median = quantile_sorted(v, n, 0.5);
    s.q3 = quantile_sorted(v, n, 0.75);
    return s;
}

// xorshift64* RNG (deterministic, seedable).
typedef struct { uint64_t s; } Rng;
static inline uint64_t rng_next(Rng *r) {
    uint64_t x = r->s;
    x ^= x >> 12; x ^= x << 25; x ^= x >> 27;
    r->s = x;
    return x * 0x2545F4914F6CDD1DULL;
}
// Unbiased-enough index in [0, n) via multiply-high.
static inline uint64_t rng_below(Rng *r, uint64_t n) {
    return (uint64_t)(((__uint128_t)rng_next(r) * n) >> 64);
}

// Tiny CLI: --key value pairs.
static inline const char *arg_get(int argc, char **argv, const char *key, const char *def) {
    for (int i = 1; i + 1 < argc; i++)
        if (!strcmp(argv[i], key)) return argv[i + 1];
    return def;
}
static inline long arg_long(int argc, char **argv, const char *key, long def) {
    const char *s = arg_get(argc, argv, key, NULL);
    return s ? atol(s) : def;
}
static inline int arg_flag(int argc, char **argv, const char *key) {
    for (int i = 1; i < argc; i++) if (!strcmp(argv[i], key)) return 1;
    return 0;
}
