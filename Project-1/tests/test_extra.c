/* Correctness tests for the kernels added for the memory-traffic and dot-product decomposition experiments:
 *   read (integer word sum), incr, copy, scale, add, saxpy_oop (f32), dot_a1/a4/a8/a16 (f32, f64).
 * Same method as test_kernels.c: sizes with all remainders, start offsets, 64-element guard regions,
 * double-double reference for the reductions. Compile with -ffp-contract=off. */
#include "common.h"
#include "registry_gen.h"
#include <math.h>

#define NREG (sizeof(REGISTRY) / sizeof(REGISTRY[0]))
typedef struct { double hi, lo; } dd;
static dd two_sum(double a, double b) { double s = a + b, bb = s - a; return (dd){s, (a - (s - bb)) + (b - bb)}; }
static dd dd_add(dd a, dd b) { dd s = two_sum(a.hi, b.hi); s.lo += a.lo + b.lo; double h = s.hi + s.lo; return (dd){h, s.lo - (h - s.hi)}; }
static dd dd_mul_d(double a, double b) { double p = a * b; return (dd){p, fma(a, b, -p)}; }
static int64_t ulp_dist_f(float a, float b) { int32_t x, y; memcpy(&x, &a, 4); memcpy(&y, &b, 4); if (x < 0) x = INT32_MIN - x; if (y < 0) y = INT32_MIN - y; return llabs((int64_t)x - y); }

#define GUARD 64
static const long SIZES[] = {0, 1, 2, 3, 4, 5, 7, 8, 9, 15, 16, 17, 31, 32, 33, 63, 64, 65, 100, 127, 128, 129, 255, 1000, 1023, 1024, 1025, 4097, 100003};
static const long OFFS[] = {0, 4, 8, 12, 16, 60, 64};
enum { READ, INCR, COPY, SCALE, ADD, OOP, DOT, NONE };
static int kind(const char *k) {
  return !strcmp(k, "read") ? READ : !strcmp(k, "incr") ? INCR : !strcmp(k, "copy") ? COPY : !strcmp(k, "scale") ? SCALE :
         !strcmp(k, "add") ? ADD : !strcmp(k, "saxpy_oop") ? OOP : !strncmp(k, "dot_a", 5) ? DOT : NONE;
}

int main(void) {
  int fails = 0; long checks = 0; uint64_t seed = 424242ULL; double worst_rel[2] = {0, 0};
  for (size_t r = 0; r < NREG; r++) {
    const struct kentry *e = &REGISTRY[r];
    int k = kind(e->kernel); if (k == NONE) continue;
    int is64 = !strcmp(e->dtype, "f64"); size_t sz = dtype_size(e->dtype);
    for (size_t si = 0; si < sizeof(SIZES) / sizeof(SIZES[0]); si++) for (size_t oi = 0; oi < sizeof(OFFS) / sizeof(OFFS[0]); oi++) {
      long n = SIZES[si], off = OFFS[oi]; if (n > 5000 && oi > 1) continue;
      size_t bytes = ((size_t)n + 2 * GUARD) * sz + 128;
      char *bx = malloc(bytes + 64), *by = malloc(bytes + 64), *bz = malloc(bytes + 64), *by0 = malloc(bytes + 64);
      memset(bx, 0xA5, bytes); memset(by, 0xA5, bytes); memset(bz, 0xA5, bytes);
      char *x = bx + GUARD * sz + off, *y = by + GUARD * sz + off, *z = bz + GUARD * sz + off;
      fill_array(x, n, e->dtype, &seed); fill_array(y, n, e->dtype, &seed);
      memcpy(by0, by, bytes); char *y0 = by0 + GUARD * sz + off;
      double a = is64 ? 0.75 : (double)(float)0.75; int bad = 0;
      double ret = e->fn((size_t)n, a, x, y, z);
      const float *xf = (float *)x, *y0f = (float *)y0, *yf = (float *)y, *zf = (float *)z; const uint32_t *xu = (uint32_t *)x;
      if (k == READ) { uint32_t s = 0; for (long i = 0; i < n; i++) s += xu[i]; if ((uint32_t)(uint64_t)ret != s) bad = 1; }
      for (long i = 0; i < n && !bad && k != READ && k != DOT; i++) {
        int64_t u = 0;
        if (k == INCR) u = ulp_dist_f((float)((double)y0f[i] + (double)(float)a), yf[i]);
        else if (k == COPY) { if (memcmp(y + i * sz, x + i * sz, sz)) bad = 1; }
        else if (k == SCALE) u = ulp_dist_f((float)((double)(float)a * (double)xf[i]), yf[i]);
        else if (k == ADD) u = ulp_dist_f((float)((double)xf[i] + (double)y0f[i]), zf[i]);
        else if (k == OOP) u = ulp_dist_f((float)fma((double)(float)a, (double)xf[i], (double)y0f[i]), zf[i]);
        if (u > 1) bad = 1;
      }
      if (k == DOT) {
        dd s = {0, 0};
        for (long i = 0; i < n; i++) s = is64 ? dd_add(s, dd_mul_d(((double *)x)[i], ((double *)y0)[i])) : dd_add(s, dd_mul_d(xf[i], y0f[i]));
        double ref = s.hi + s.lo, eps = is64 ? 0x1p-53 : 0x1p-24;
        double rel = ref != 0 ? fabs(ret - ref) / fabs(ref) : fabs(ret);
        if (rel > worst_rel[is64]) worst_rel[is64] = rel;
        if (rel > (double)(n > 1 ? n : 1) * eps) bad = 1;
      }
      /* y is an input (or, for incr, the output) and must stay inside its range; z is written only by add and saxpy_oop */
      for (size_t g = 0; g < (size_t)GUARD * sz + off && !bad; g++) if (((unsigned char *)by)[g] != 0xA5) bad = 1;
      for (size_t g = (size_t)GUARD * sz + off + (size_t)n * sz; g < bytes && !bad; g++) if (((unsigned char *)by)[g] != ((unsigned char *)by0)[g]) bad = 1;
      if (k == ADD || k == OOP) {
        for (size_t g = 0; g < (size_t)GUARD * sz + off && !bad; g++) if (((unsigned char *)bz)[g] != 0xA5) bad = 1;
        for (size_t g = (size_t)GUARD * sz + off + (size_t)n * sz; g < bytes && !bad; g++) if (((unsigned char *)bz)[g] != 0xA5) bad = 1;
        if (!bad && memcmp(y, y0, (size_t)n * sz)) bad = 1; /* inputs untouched */
      }
      if (k == COPY || k == SCALE) { /* x is the input and must be untouched; the output is y */
        for (size_t g = 0; g < (size_t)GUARD * sz + off && !bad; g++) if (((unsigned char *)bx)[g] != 0xA5) bad = 1;
      }
      checks++;
      if (bad) { fails++; printf("FAIL %s %s %s n=%ld off=%ld\n", e->kernel, e->dtype, e->build, n, off); }
      free(bx); free(by); free(bz); free(by0);
    }
  }
  printf("extra checks=%ld failures=%d (worst dot rel err f32=%.3g f64=%.3g)\n", checks, fails, worst_rel[0], worst_rel[1]);
  return fails != 0;
}
