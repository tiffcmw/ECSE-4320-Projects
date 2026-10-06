// Platform layer: clock, QoS, page-fault counter. A Linux port only has to
// reimplement this file (clock_gettime, sched/affinity, getrusage).
#pragma once
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <sys/mman.h>
#include <sys/resource.h>
#ifdef __APPLE__
#include <mach/mach_time.h>
#include <pthread/qos.h>
#endif

// Single monotonic clock for every benchmark: mach_absolute_time converted to ns.
// On Apple Silicon the tick is 1/24 MHz (about 41.7 ns), so timed regions must
// last milliseconds; every benchmark enforces this.
static inline uint64_t now_ns(void) {
    static mach_timebase_info_data_t tb;
    if (tb.denom == 0) mach_timebase_info(&tb);
    return mach_absolute_time() * tb.numer / tb.denom;
}

// Minor page faults of the calling process (RUSAGE_SELF).
static inline long minor_faults(void) {
    struct rusage ru;
    getrusage(RUSAGE_SELF, &ru);
    return ru.ru_minflt;
}

// Prevent dead-code elimination of a computed value.
static inline void sink_u64(uint64_t v) { __asm__ volatile("" : : "r"(v) : "memory"); }
static inline void sink_ptr(const void *p) { __asm__ volatile("" : : "r"(p) : "memory"); }

// QoS names accepted on command lines: interactive, initiated, default, utility, background.
// Returns the qos_class_t value, or -1 for "none" (leave thread at process default).
static inline int qos_from_name(const char *s) {
    if (!strcmp(s, "interactive")) return QOS_CLASS_USER_INTERACTIVE;
    if (!strcmp(s, "initiated"))   return QOS_CLASS_USER_INITIATED;
    if (!strcmp(s, "default"))     return QOS_CLASS_DEFAULT;
    if (!strcmp(s, "utility"))     return QOS_CLASS_UTILITY;
    if (!strcmp(s, "background"))  return QOS_CLASS_BACKGROUND;
    return -1;
}

// Set QoS on the CALLING thread. Must run inside the thread that does the work
// (setting it on a different thread, or after the work starts, is the flawed
// design documented in docs/AI_USE.md). Returns 0 on success.
static inline int set_thread_qos(int qos) {
    if (qos < 0) return 0;
    return pthread_set_qos_class_self_np((qos_class_t)qos, 0);
}

// Report the QoS class the calling thread actually has.
static inline int get_thread_qos(void) {
    qos_class_t c; int rp;
    pthread_get_qos_class_np(pthread_self(), &c, &rp);
    return (int)c;
}

// Page-aligned anonymous mapping (16 KB aligned on this system). Zero-filled.
static inline void *map_bytes(size_t n) {
    void *p = mmap(NULL, n, PROT_READ | PROT_WRITE, MAP_ANON | MAP_PRIVATE, -1, 0);
    return p == MAP_FAILED ? NULL : p;
}
