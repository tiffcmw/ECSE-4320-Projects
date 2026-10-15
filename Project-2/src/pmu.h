// Optional PMU access through Apple's private kperf/kperfdata frameworks (needs root: run via sudo).
// Enabled only with --pmu EVENT1,EVENT2,... ; without it nothing here is called and membench behaves as before.
// Event names come from the system database /usr/share/kpep (see data/raw/counters/kpep_events.txt).
// Per-thread counting: counters are read for the calling thread around the timed region, then reported per operation.
#pragma once
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct kpep_db kpep_db_t;
typedef struct kpep_config kpep_config_t;
typedef struct kpep_event kpep_event_t;

static struct {
    int on, nev; char names[16][64]; size_t map[32]; uint32_t classes; uint64_t reg[64];
    int (*kpc_force_all_ctrs_set)(int); int (*kpc_set_counting)(uint32_t); int (*kpc_set_thread_counting)(uint32_t);
    int (*kpc_set_config)(uint32_t, void *); int (*kpc_get_thread_counters)(uint32_t, uint32_t, uint64_t *);
    int (*kpep_db_create)(const char *, kpep_db_t **); int (*kpep_config_create)(kpep_db_t *, kpep_config_t **);
    int (*kpep_config_force_counters)(kpep_config_t *); int (*kpep_db_event)(kpep_db_t *, const char *, kpep_event_t **);
    int (*kpep_config_add_event)(kpep_config_t *, kpep_event_t **, uint32_t, uint32_t *);
    int (*kpep_config_kpc)(kpep_config_t *, uint64_t *, size_t); int (*kpep_config_kpc_classes)(kpep_config_t *, uint32_t *);
    int (*kpep_config_kpc_map)(kpep_config_t *, size_t *, size_t);
} P;

#define PMU_SYM(h, f) do { *(void **)&P.f = dlsym(h, #f); if (!P.f) { fprintf(stderr, "pmu: missing symbol %s\n", #f); return -1; } } while (0)

// Returns 0 on success. On failure prints the reason to stderr (the caller reports that no counters are available).
static int pmu_init(const char *csv) {
    void *kp = dlopen("/System/Library/PrivateFrameworks/kperf.framework/kperf", RTLD_LAZY);
    void *kd = dlopen("/System/Library/PrivateFrameworks/kperfdata.framework/kperfdata", RTLD_LAZY);
    if (!kp || !kd) { fprintf(stderr, "pmu: cannot load kperf/kperfdata\n"); return -1; }
    PMU_SYM(kp, kpc_force_all_ctrs_set); PMU_SYM(kp, kpc_set_counting); PMU_SYM(kp, kpc_set_thread_counting);
    PMU_SYM(kp, kpc_set_config); PMU_SYM(kp, kpc_get_thread_counters);
    PMU_SYM(kd, kpep_db_create); PMU_SYM(kd, kpep_config_create); PMU_SYM(kd, kpep_config_force_counters);
    PMU_SYM(kd, kpep_db_event); PMU_SYM(kd, kpep_config_add_event); PMU_SYM(kd, kpep_config_kpc);
    PMU_SYM(kd, kpep_config_kpc_classes); PMU_SYM(kd, kpep_config_kpc_map);
    kpep_db_t *db = NULL; kpep_config_t *cfg = NULL; int r;
    if ((r = P.kpep_db_create(NULL, &db))) { fprintf(stderr, "pmu: kpep_db_create failed (%d)\n", r); return -1; }
    if ((r = P.kpep_config_create(db, &cfg))) { fprintf(stderr, "pmu: kpep_config_create failed (%d)\n", r); return -1; }
    if ((r = P.kpep_config_force_counters(cfg))) { fprintf(stderr, "pmu: force_counters failed (%d)\n", r); return -1; }
    char buf[1024]; strncpy(buf, csv, sizeof buf - 1); buf[sizeof buf - 1] = 0;
    for (char *t = strtok(buf, ","); t && P.nev < 16; t = strtok(NULL, ",")) {
        kpep_event_t *ev = NULL;
        if (P.kpep_db_event(db, t, &ev)) { fprintf(stderr, "pmu: unknown event %s\n", t); return -1; }
        uint32_t err = 0;
        if ((r = P.kpep_config_add_event(cfg, &ev, 0, &err))) { fprintf(stderr, "pmu: cannot add %s (%d, err %u)\n", t, r, err); return -1; }
        strncpy(P.names[P.nev++], t, 63);
    }
    if (P.kpep_config_kpc(cfg, P.reg, sizeof P.reg) || P.kpep_config_kpc_classes(cfg, &P.classes) || P.kpep_config_kpc_map(cfg, P.map, sizeof P.map)) {
        fprintf(stderr, "pmu: kpep_config_kpc* failed\n"); return -1; }
    if (P.kpc_force_all_ctrs_set(1)) { fprintf(stderr, "pmu: kpc_force_all_ctrs_set failed (not root?)\n"); return -1; }
    if ((P.classes & 2) && P.kpc_set_config(P.classes, P.reg)) { fprintf(stderr, "pmu: kpc_set_config failed\n"); return -1; }
    if (P.kpc_set_counting(P.classes) || P.kpc_set_thread_counting(P.classes)) { fprintf(stderr, "pmu: set_counting failed\n"); return -1; }
    P.on = 1; return 0;
}
// Snapshot of this thread's counters for the configured events (in the order requested).
static void pmu_snap(uint64_t *out) {
    uint64_t c[64] = {0};
    P.kpc_get_thread_counters(0, 64, c);
    for (int i = 0; i < P.nev; i++) out[i] = c[P.map[i]];
}
