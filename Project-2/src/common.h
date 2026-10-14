// Shared helpers: clock, RNG, allocation, QoS, CSV output, argument parsing.
#pragma once
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <mach/mach_time.h>
#include <pthread/qos.h>

// Monotonic clock in ns. Tick is 1/24 MHz (41.7 ns), so every timed region is >= 10 ms.
static inline uint64_t now_ns(void) {
    static mach_timebase_info_data_t tb;
    if (tb.denom == 0) mach_timebase_info(&tb);
    return mach_absolute_time() * tb.numer / tb.denom;
}
static inline long minor_faults(void) {
    struct rusage ru; getrusage(RUSAGE_SELF, &ru); return ru.ru_minflt;
}
static inline void sink_u64(uint64_t v) { __asm__ volatile("" : : "r"(v) : "memory"); }
static inline void sink_ptr(const void *p) { __asm__ volatile("" : : "r"(p) : "memory"); }

static inline uint64_t xs64(uint64_t *s) {
    uint64_t x = *s; x ^= x << 13; x ^= x >> 7; x ^= x << 17; return *s = x;
}
static inline uint64_t mulhi(uint64_t a, uint64_t b) { return (uint64_t)(((unsigned __int128)a * b) >> 64); }

// Page-aligned anonymous mapping, every page written (so physical pages exist before timing).
static inline uint8_t *alloc_touch(size_t bytes, int fill) {
    uint8_t *p = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_ANON | MAP_PRIVATE, -1, 0);
    if (p == MAP_FAILED) { fprintf(stderr, "mmap %zu failed\n", bytes); exit(2); }
    memset(p, fill, bytes);
    return p;
}
static inline void free_map(void *p, size_t bytes) { munmap(p, bytes); }

// QoS
static inline int qos_from_name(const char *s) {
    if (!strcmp(s, "interactive")) return QOS_CLASS_USER_INTERACTIVE;
    if (!strcmp(s, "initiated"))   return QOS_CLASS_USER_INITIATED;
    if (!strcmp(s, "default"))     return QOS_CLASS_DEFAULT;
    if (!strcmp(s, "utility"))     return QOS_CLASS_UTILITY;
    if (!strcmp(s, "background"))  return QOS_CLASS_BACKGROUND;
    return -1;
}
static inline int set_thread_qos(int q) { return q < 0 ? 0 : pthread_set_qos_class_self_np((qos_class_t)q, 0); }
static inline int get_thread_qos(void) { qos_class_t c; int rp; pthread_get_qos_class_np(pthread_self(), &c, &rp); return (int)c; }

// Command line: membench <cmd> --key value ...
static int g_argc; static char **g_argv;
static inline const char *arg_str(const char *key, const char *def) {
    for (int i = 2; i + 1 < g_argc; i++) if (!strcmp(g_argv[i], key)) return g_argv[i + 1];
    return def;
}
static inline size_t parse_size(const char *s) {
    char *e; double v = strtod(s, &e); size_t m = 1;
    switch (*e) { case 'k': case 'K': m = 1ull << 10; break; case 'm': case 'M': m = 1ull << 20; break;
                  case 'g': case 'G': m = 1ull << 30; break; default: break; }
    return (size_t)(v * (double)m);
}
static inline size_t arg_size(const char *key, size_t def) { const char *s = arg_str(key, NULL); return s ? parse_size(s) : def; }
static inline double arg_dbl(const char *key, double def) { const char *s = arg_str(key, NULL); return s ? atof(s) : def; }
static inline int arg_int(const char *key, int def) { const char *s = arg_str(key, NULL); return s ? atoi(s) : def; }
// Comma separated list of sizes (suffixes K, M, G) into out; returns count.
static inline int arg_list(const char *key, const char *def, size_t *out, int max) {
    const char *s = arg_str(key, def); char buf[4096]; strncpy(buf, s, sizeof buf - 1); buf[sizeof buf - 1] = 0;
    int n = 0; for (char *t = strtok(buf, ","); t && n < max; t = strtok(NULL, ",")) out[n++] = parse_size(t);
    return n;
}

// CSV output (long format): one row per measured metric.
static int g_round = 0, g_qos_seen = 0; static long g_faults = 0;
static inline void emit_header(void) {
    puts("exp,variant,ws_bytes,stride,size,threads,param,round,rep,metric,value,qos_seen,faults");
}
static inline void emit(const char *exp, const char *variant, size_t ws, size_t stride, size_t size,
                        int thr, double param, int rep, const char *metric, double v) {
    printf("%s,%s,%zu,%zu,%zu,%d,%.6g,%d,%d,%s,%.9g,%d,%ld\n", exp, variant, ws, stride, size, thr, param,
           g_round, rep, metric, v, g_qos_seen, g_faults);
}
