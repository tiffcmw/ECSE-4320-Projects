#ifndef COMMON_H
#define COMMON_H
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <pthread.h>
#include <pthread/qos.h>
#include <sys/mman.h>
#include <notify.h>

typedef double (*kfn)(size_t, double, const void *, void *, void *);
struct kentry { const char *kernel, *dtype, *build; kfn fn; };

static inline uint64_t now_ns(void) { return clock_gettime_nsec_np(CLOCK_UPTIME_RAW); }
static inline void barrier(void) { __asm__ volatile("" ::: "memory"); }
static inline void sink_d(double v) { __asm__ volatile("" ::"w"(v) : "memory"); }

static inline size_t dtype_size(const char *d) { return strcmp(d, "f64") == 0 ? 8 : 4; }

/* xorshift64*: fixed-seed generator for reproducible data. */
static inline uint64_t rng_next(uint64_t *s) {
  uint64_t x = *s; x ^= x >> 12; x ^= x << 25; x ^= x >> 27; *s = x;
  return x * 0x2545F4914F6CDD1DULL;
}
static inline double rng_unit(uint64_t *s) { return (double)(rng_next(s) >> 11) * (1.0 / 9007199254740992.0); }

/* Values in [0.5, 1.5): no denormals, no zeros. u32: small odd-ish integers. */
static inline void fill_array(void *p, size_t n, const char *dt, uint64_t *seed) {
  if (strcmp(dt, "f32") == 0) { float *f = p; for (size_t i = 0; i < n; i++) f[i] = (float)(0.5 + rng_unit(seed)); }
  else if (strcmp(dt, "f64") == 0) { double *f = p; for (size_t i = 0; i < n; i++) f[i] = 0.5 + rng_unit(seed); }
  else { uint32_t *u = p; for (size_t i = 0; i < n; i++) u[i] = (uint32_t)(rng_next(seed) >> 40) | 1u; }
}

static inline void set_qos_interactive(void) {
  pthread_set_qos_class_self_np(QOS_CLASS_USER_INTERACTIVE, 0);
}
static inline void set_qos_named(const char *name) {
  qos_class_t c = QOS_CLASS_USER_INTERACTIVE;
  if (!strcmp(name, "user-initiated")) c = QOS_CLASS_USER_INITIATED;
  else if (!strcmp(name, "default")) c = QOS_CLASS_DEFAULT;
  else if (!strcmp(name, "utility")) c = QOS_CLASS_UTILITY;
  else if (!strcmp(name, "background")) c = QOS_CLASS_BACKGROUND;
  pthread_set_qos_class_self_np(c, 0);
}

/* Thermal pressure level from the notify service: 0 nominal, 1 moderate, 2 heavy, 3 trapping, 4 sleeping.
 * Returns -1 if unavailable. */
static inline int thermal_level(void) {
  static int tok = -1, init = 0;
  if (!init) { init = 1; if (notify_register_check("com.apple.system.thermalpressurelevel", &tok) != NOTIFY_STATUS_OK) tok = -1; }
  if (tok < 0) return -1;
  uint64_t st = 0;
  if (notify_get_state(tok, &st) != NOTIFY_STATUS_OK) return -1;
  return (int)st;
}
#endif
