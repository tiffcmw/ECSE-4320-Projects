/* Negative case A, numerics: error of the dot product in each build against a double-double reference.
 * (On arm64 macOS long double is 64-bit, so the reference is double-double with fma-based error-free transforms.)
 * accuracy [csv_out]: rows build,dtype,N,seed,rel_err,rel_err_over_eps */
#include "common.h"
#include "registry_gen.h"
#include <math.h>
#define NREG (sizeof(REGISTRY) / sizeof(REGISTRY[0]))
typedef struct { double hi, lo; } dd;
static dd two_sum(double a, double b) { double s = a + b, bb = s - a; return (dd){s, (a - (s - bb)) + (b - bb)}; }
static dd dd_add(dd a, dd b) { dd s = two_sum(a.hi, b.hi); s.lo += a.lo + b.lo; double h = s.hi + s.lo; return (dd){h, s.lo - (h - s.hi)}; }
static dd dd_mul_d(double a, double b) { double p = a * b; return (dd){p, fma(a, b, -p)}; }
int main(int argc, char **argv) {
  FILE *f = argc > 1 ? fopen(argv[1], "w") : stdout;
  fprintf(f, "build,dtype,N,seed,rel_err,rel_err_over_eps\n");
  const long Ns[] = {1000, 10000, 100000, 1000000, 10000000, 100000000};
  const char *builds[] = {"scalar", "scalar_unroll8", "auto", "native", "fastmath"};
  for (int di = 0; di < 2; di++) {
    const char *dt = di == 0 ? "f32" : "f64"; size_t sz = dtype_size(dt); double eps = di == 0 ? 0x1p-24 : 0x1p-53;
    for (size_t ni = 0; ni < sizeof(Ns) / sizeof(Ns[0]); ni++) {
      long n = Ns[ni]; if (di == 1 && n > 10000000) continue;
      int nseeds = n >= 100000000 ? 1 : 5;
      for (int sd = 1; sd <= nseeds; sd++) {
        char *x = malloc(n * sz), *y = malloc(n * sz); uint64_t seed = 1000 + sd * 7919 + n;
        fill_array(x, n, dt, &seed); fill_array(y, n, dt, &seed);
        dd ref = {0, 0};
        for (long i = 0; i < n; i++) ref = dd_add(ref, di == 0 ? dd_mul_d(((float *)x)[i], ((float *)y)[i]) : dd_mul_d(((double *)x)[i], ((double *)y)[i]));
        double r = ref.hi + ref.lo;
        for (size_t b = 0; b < sizeof(builds) / sizeof(builds[0]); b++) for (size_t k = 0; k < NREG; k++) {
          if (strcmp(REGISTRY[k].kernel, "dot") || strcmp(REGISTRY[k].dtype, dt) || strcmp(REGISTRY[k].build, builds[b])) continue;
          double got = REGISTRY[k].fn(n, 0, x, y, NULL), rel = fabs(got - r) / fabs(r);
          fprintf(f, "%s,%s,%ld,%d,%.6e,%.4f\n", builds[b], dt, n, sd, rel, rel / eps);
        }
        free(x); free(y);
      }
    }
  }
  if (argc > 1) fclose(f);
  return 0;
}
