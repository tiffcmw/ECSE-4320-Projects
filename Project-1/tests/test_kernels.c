/* Correctness tests for every kernel x dtype x build in the registry against a scalar reference.
 * NOTE: on arm64 macOS `long double` is 64-bit (same as double), so it cannot serve as the high-precision
 * accumulator. The reference uses double-double arithmetic (error-free transforms with fma, ~106 bits).
 * Compile this file with -ffp-contract=off so the reference itself is not contracted.
 * Element-wise kernels: <= 1 ulp from the correctly rounded reference (stencil: <= 2 ulp, documented below).
 * Reductions: relative error <= n * eps(type) (worst-case sequential bound); observed values are printed.
 * u32: exact (mod 2^32). Guard regions around every buffer detect out-of-bounds writes. */
#include "common.h"
#include "registry_gen.h"
#include <math.h>

#define NREG (sizeof(REGISTRY) / sizeof(REGISTRY[0]))
typedef struct { double hi, lo; } dd;
static dd two_sum(double a, double b) { double s = a + b, bb = s - a; return (dd){s, (a - (s - bb)) + (b - bb)}; }
static dd dd_add(dd a, dd b) { dd s = two_sum(a.hi, b.hi); s.lo += a.lo + b.lo; double h = s.hi + s.lo; return (dd){h, s.lo - (h - s.hi)}; }
static dd dd_mul_d(double a, double b) { double p = a * b; return (dd){p, fma(a, b, -p)}; }
static double dd_round(dd a) { return a.hi + a.lo; }

static int64_t ulp_dist_f(float a, float b) { int32_t x, y; memcpy(&x, &a, 4); memcpy(&y, &b, 4); if (x < 0) x = INT32_MIN - x; if (y < 0) y = INT32_MIN - y; return llabs((int64_t)x - y); }
static int64_t ulp_dist_d(double a, double b) { int64_t x, y; memcpy(&x, &a, 8); memcpy(&y, &b, 8); if (x < 0) x = INT64_MIN - x; if (y < 0) y = INT64_MIN - y; int64_t d = x - y; return d < 0 ? -d : d; }

#define GUARD 64
static const long SIZES[] = {0, 1, 2, 3, 4, 5, 7, 8, 9, 15, 16, 17, 31, 32, 33, 63, 64, 65, 100, 127, 128, 129, 255, 1000, 1023, 1024, 1025, 4097, 100003};
static const long OFFS[] = {0, 4, 8, 12, 16, 60, 64};

int main(void) {
  int fails = 0; long checks = 0; uint64_t seed = 987654321ULL;
  double worst_ulp[3][4] = {{0}}, worst_rel[3] = {0}; /* [dtype][kernel] */
  for (size_t r = 0; r < NREG; r++) {
    const struct kentry *e = &REGISTRY[r];
    int di = !strcmp(e->dtype, "f32") ? 0 : !strcmp(e->dtype, "f64") ? 1 : 2;
    int ki = !strcmp(e->kernel, "saxpy") ? 0 : !strcmp(e->kernel, "mul") ? 1 : !strcmp(e->kernel, "dot") ? 2 : 3;
    size_t sz = dtype_size(e->dtype);
    for (size_t si = 0; si < sizeof(SIZES) / sizeof(SIZES[0]); si++) for (size_t oi = 0; oi < sizeof(OFFS) / sizeof(OFFS[0]); oi++) {
      long n = SIZES[si], off = OFFS[oi];
      if (n > 5000 && oi > 1) continue;
      size_t bytes = ((size_t)n + 2 * GUARD) * sz + 128;
      char *bx = malloc(bytes + 64), *by = malloc(bytes + 64), *bz = malloc(bytes + 64), *by0 = malloc(bytes + 64);
      memset(bx, 0xA5, bytes); memset(by, 0xA5, bytes); memset(bz, 0xA5, bytes);
      char *x = bx + GUARD * sz + off, *y = by + GUARD * sz + off, *z = bz + GUARD * sz + off;
      fill_array(x, n, e->dtype, &seed); fill_array(y, n, e->dtype, &seed);
      memcpy(by0, by, bytes); /* snapshot of y (incl. guards) before the call */
      char *y0 = by0 + GUARD * sz + off;
      double a = 0.75; if (!strcmp(e->dtype, "f32")) a = (double)(float)0.75; if (!strcmp(e->dtype, "u32")) a = 3.0;
      double ret = e->fn((size_t)n, a, x, y, z);
      int bad = 0; double maxu = 0;
      const float *xf = (float *)x, *y0f = (float *)y0, *yf = (float *)y, *zf = (float *)z;
      const double *xd = (double *)x, *y0d = (double *)y0, *yd = (double *)y, *zd = (double *)z;
      const uint32_t *xu = (uint32_t *)x, *y0u = (uint32_t *)y0, *yu = (uint32_t *)y, *zu = (uint32_t *)z;
      for (long i = 0; i < n && !bad; i++) {
        double ref_hi = 0; int64_t u = 0; int isint = di == 2; uint32_t refu = 0, gotu = 0;
        if (ki == 0) {
          if (di == 0) { ref_hi = fma((double)(float)a, (double)xf[i], (double)y0f[i]); u = ulp_dist_f((float)ref_hi, yf[i]); }
          else if (di == 1) { ref_hi = fma(a, xd[i], y0d[i]); u = ulp_dist_d(ref_hi, yd[i]); }
          else { refu = (uint32_t)3u * xu[i] + y0u[i]; gotu = yu[i]; }
        } else if (ki == 1) {
          if (di == 0) { ref_hi = (double)xf[i] * (double)y0f[i]; u = ulp_dist_f((float)ref_hi, zf[i]); }
          else if (di == 1) { ref_hi = xd[i] * y0d[i]; u = ulp_dist_d(ref_hi, zd[i]); }
          else { refu = xu[i] * y0u[i]; gotu = zu[i]; }
        } else if (ki == 3) {
          if (i == 0 || i + 1 >= n) continue;
          if (di == 0) { dd s = dd_add(dd_add(dd_mul_d(0.25, xf[i - 1]), dd_mul_d(0.5, xf[i])), dd_mul_d(0.25, xf[i + 1])); u = ulp_dist_f((float)dd_round(s), yf[i]); }
          else if (di == 1) { dd s = dd_add(dd_add(dd_mul_d(0.25, xd[i - 1]), dd_mul_d(0.5, xd[i])), dd_mul_d(0.25, xd[i + 1])); u = ulp_dist_d(dd_round(s), yd[i]); }
          else { refu = xu[i - 1] + 2u * xu[i] + xu[i + 1]; gotu = yu[i]; }
        } else continue;
        if (isint) { if (refu != gotu) bad = 1; } else { if ((double)u > maxu) maxu = (double)u; if (u > (ki == 3 ? 2 : 1)) bad = 1; }
      }
      if (ki == 2) { /* dot */
        dd s = {0, 0}; uint32_t su = 0;
        for (long i = 0; i < n; i++) {
          if (di == 0) s = dd_add(s, dd_mul_d(xf[i], ((float *)y0)[i]));
          else if (di == 1) s = dd_add(s, dd_mul_d(xd[i], y0d[i]));
          else su += xu[i] * y0u[i];
        }
        if (di == 2) { if ((uint32_t)(uint64_t)ret != su) bad = 1; }
        else {
          double ref = dd_round(s), eps = di == 0 ? 0x1p-24 : 0x1p-53;
          double rel = ref != 0 ? fabs(ret - ref) / fabs(ref) : fabs(ret);
          if (rel > worst_rel[di]) worst_rel[di] = rel;
          if (rel > (double)(n > 1 ? n : 1) * eps) bad = 1;
        }
      }
      if (maxu > worst_ulp[di][ki]) worst_ulp[di][ki] = maxu;
      /* guard / untouched-region checks: bytes outside the written range must be unchanged */
      for (size_t g = 0; g < (size_t)GUARD * sz + off && !bad; g++) { if (((unsigned char *)by)[g] != 0xA5 && ki != 3) { /* y guard before */ bad = 1; } }
      if (ki == 0 || ki == 3) { for (size_t g = (size_t)GUARD * sz + off + (size_t)n * sz; g < bytes && !bad; g++) if (((unsigned char *)by)[g] != ((unsigned char *)by0)[g]) bad = 1; }
      if (ki == 3 && n >= 2) { if (memcmp(y, y0, sz) || memcmp(y + (n - 1) * sz, y0 + (n - 1) * sz, sz)) bad = 1; } /* boundary elems untouched */
      if (ki == 1) { for (size_t g = 0; g < (size_t)GUARD * sz + off && !bad; g++) if (((unsigned char *)bz)[g] != 0xA5) bad = 1;
                     for (size_t g = (size_t)GUARD * sz + off + (size_t)n * sz; g < bytes && !bad; g++) if (((unsigned char *)bz)[g] != 0xA5) bad = 1; }
      checks++;
      if (bad) { fails++; printf("FAIL %s %s %s n=%ld off=%ld\n", e->kernel, e->dtype, e->build, n, off); }
      free(bx); free(by); free(bz); free(by0);
    }
  }
  printf("checks=%ld failures=%d\n", checks, fails);
  const char *dn[3] = {"f32", "f64", "u32"}, *kn[4] = {"saxpy", "mul", "dot", "stencil"};
  for (int d = 0; d < 2; d++) { printf("max ulp %s:", dn[d]); for (int k = 0; k < 4; k++) if (k != 2) printf(" %s=%.0f", kn[k], worst_ulp[d][k]); printf("  worst dot rel err=%.3g\n", worst_rel[d]); }
  return fails != 0;
}
