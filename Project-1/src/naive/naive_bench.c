/* EXPERIMENT 8: a deliberately naive benchmark, kept on purpose together with its corrected twin.
 * Each experiment runs as variant "naive" (written first, contains a classic flaw) and "fixed".
 *   N1 hoist : elementwise multiply repeated on identical inputs, result never consumed. The compiler is free to
 *              execute the loop once or not at all (loop invariant, idempotent, dead stores to a local buffer).
 *   N2 zeropg: a "1 GiB" array allocated with calloc and never written. Reads of untouched anonymous memory are
 *              served from shared zero-fill pages, so the data is not 1 GiB of distinct DRAM-resident memory.
 *   N3 touch : first-touch page faults (fill) inside the timed region, one repetition.
 * Output CSV: experiment,variant,n,reps,ns_total,ns_per_element,GiB_per_s_useful,checksum
 * Compile: clang -O3 -ffast-math (N2 needs a vectorized reduction to be fast either way). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
static uint64_t now(void) { return clock_gettime_nsec_np(CLOCK_UPTIME_RAW); }
#define P(exp, var, n, reps, t, bytes, chk) printf("%s,%s,%zu,%d,%llu,%.6f,%.3f,%.6g\n", exp, var, (size_t)(n), reps, (unsigned long long)(t), (double)(t) / ((double)(n) * (reps)), (double)(bytes) * (reps) * (n) / (double)(t) * 1e9 / (1ULL << 30), (double)(chk))

/* ---- N1: hoisting. naive: all in one translation unit, nothing consumed */
static void mul_inl(float *z, const float *x, const float *y, size_t n) { for (size_t i = 0; i < n; i++) z[i] = x[i] * y[i]; }
__attribute__((noinline)) static void n1_naive(size_t n, int reps) {
  static float x[1 << 14], y[1 << 14], z[1 << 14];
  for (size_t i = 0; i < n; i++) { x[i] = 1.0f + (float)(i & 7) * 0.125f; y[i] = 0.5f; }
  uint64_t t0 = now();
  for (int r = 0; r < reps; r++) mul_inl(z, x, y, n);
  uint64_t t1 = now();
  P("N1_hoist", "naive", n, reps, t1 - t0, 12, 0);   /* z never read: nothing forces the work */
}
/* fixed: kernel in another TU would be best; here noinline + compiler barrier + result consumed + inputs perturbed */
__attribute__((noinline)) static void mul_noinl(float *z, const float *x, const float *y, size_t n) { for (size_t i = 0; i < n; i++) z[i] = x[i] * y[i]; }
__attribute__((noinline)) static void n1_fixed(size_t n, int reps) {
  static float x[1 << 14], y[1 << 14], z[1 << 14];
  for (size_t i = 0; i < n; i++) { x[i] = 1.0f + (float)(i & 7) * 0.125f; y[i] = 0.5f; }
  uint64_t t0 = now();
  for (int r = 0; r < reps; r++) { mul_noinl(z, x, y, n); __asm__ volatile("" ::: "memory"); }
  uint64_t t1 = now();
  double chk = 0; for (size_t i = 0; i < n; i++) chk += z[i];
  P("N1_hoist", "fixed", n, reps, t1 - t0, 12, chk);
}

/* ---- N2: zero pages. sum over a large array */
__attribute__((noinline)) static float sum(const float *x, size_t n) { float s = 0; for (size_t i = 0; i < n; i++) s += x[i]; return s; }
static void n2(const char *variant, size_t n, int reps, int touch) {
  float *x = calloc(n, sizeof(float));           /* demand-zero memory */
  if (touch) for (size_t i = 0; i < n; i++) x[i] = 1.0f + (float)(i & 7) * 0.125f;  /* fixed: really back every page */
  volatile float sink = sum(x, n);                 /* warm-up pass */
  uint64_t t0 = now(); float s = 0;
  /* run 1 used: __asm__ volatile("" ::: "memory"). That does not help for memory that never escaped: x came from calloc and is
   only passed to a read-only function, so the compiler may still hoist sum(x,n) out of the loop (data/raw/naive_phase5_run1_*.csv).
   Passing the pointer into the asm makes the memory reachable from it. */
  for (int r = 0; r < reps; r++) { s += sum(x, n); __asm__ volatile("" :: "r"(x) : "memory"); }
  uint64_t t1 = now(); sink = s; (void)sink;
  P("N2_zeropage", variant, n, reps, t1 - t0, 4, s);
  free(x);
}

/* ---- N3: first touch in the timed region. SAXPY over fresh malloc memory */
__attribute__((noinline)) static void saxpy(size_t n, float a, const float *x, float *y) { for (size_t i = 0; i < n; i++) y[i] = a * x[i] + y[i]; }
static void n3(const char *variant, size_t n, int fixed) {
  float *x = malloc(n * 4), *y = malloc(n * 4);
  uint64_t t0, t1;
  if (!fixed) { t0 = now(); for (size_t i = 0; i < n; i++) { x[i] = 1.0f; y[i] = 2.0f; } saxpy(n, 0.5f, x, y); t1 = now(); }       /* page faults + init + compute */
  else { for (size_t i = 0; i < n; i++) { x[i] = 1.0f; y[i] = 2.0f; } saxpy(n, 0.5f, x, y); t0 = now(); saxpy(n, 0.5f, x, y); t1 = now(); } /* init and a warm pass outside the timed region */
  P("N3_firsttouch", variant, n, 1, t1 - t0, 12, y[n / 2]);
  free(x); free(y);
}

int main(void) {
  printf("experiment,variant,n,reps,ns_total,ns_per_element,GiB_per_s_useful,checksum\n");
  for (int rep = 0; rep < 5; rep++) {
    n1_naive(4096, 100000); n1_fixed(4096, 100000);
    n2("naive", (size_t)1 << 28, 5, 0); n2("fixed", (size_t)1 << 28, 5, 1);       /* 1 GiB of floats */
    n3("naive", (size_t)1 << 28, 0); n3("fixed", (size_t)1 << 28, 1);              /* 2 GiB for SAXPY */
  }
  return 0;
}
