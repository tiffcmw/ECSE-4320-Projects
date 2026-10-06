/* Benchmark harness. Modes:
 *   bench run   --out F --session S [--builds a,b] [--kernels a,b] [--dtypes a,b]
 *               (--ws bytes,... | --n elems,...) [--offset bytes,...] [--reps R] [--passes P]
 *               [--seed N] [--min-ms X] [--qos name] [--append]
 *   bench freq  --out F --session S [--reps R] [--qos name]   (dependent-chain clock estimate)
 *   bench timer                                                 (timer resolution and overhead)
 *   bench list
 * One CSV row per sample (rep). Configuration order is shuffled per pass with a fixed seed. */
#include "common.h"
#include "registry_gen.h"
#include <math.h>

#define NREG (sizeof(REGISTRY) / sizeof(REGISTRY[0]))

static int cmp_d(const void *a, const void *b) { double x = *(const double *)a, y = *(const double *)b; return (x > y) - (x < y); }
static double median(double *v, int n) { qsort(v, n, sizeof(double), cmp_d); return n % 2 ? v[n / 2] : 0.5 * (v[n / 2 - 1] + v[n / 2]); }

static const char *getarg(int argc, char **argv, const char *k, const char *def) {
  for (int i = 2; i + 1 < argc; i++) if (!strcmp(argv[i], k)) return argv[i + 1];
  return def;
}
static int hasflag(int argc, char **argv, const char *k) { for (int i = 2; i < argc; i++) if (!strcmp(argv[i], k)) return 1; return 0; }

static int csv_contains(const char *csv, const char *tok) {
  size_t L = strlen(tok); const char *p = csv;
  while (*p) { const char *e = strchr(p, ','); size_t l = e ? (size_t)(e - p) : strlen(p); if (l == L && !strncmp(p, tok, L)) return 1; if (!e) break; p = e + 1; }
  return 0;
}
static int parse_list(const char *s, long *out, int max) {
  int c = 0; char *buf = strdup(s), *sv, *t = strtok_r(buf, ",", &sv);
  while (t && c < max) { out[c++] = strtol(t, NULL, 0); t = strtok_r(NULL, ",", &sv); }
  free(buf); return c;
}

static int arrays_of(const char *k) { return !strcmp(k, "mul") ? 3 : 2; }
static __attribute__((noinline)) double empty_kernel(size_t n, double a, const void *x, void *y, void *z) { (void)n; (void)a; (void)x; (void)y; (void)z; return 0.0; }

static double measure_call_overhead(void) {
  kfn volatile fp = empty_kernel; double s[15];
  for (int r = 0; r < 15; r++) {
    const long N = 2000000; double acc = 0; uint64_t t0 = now_ns();
    for (long i = 0; i < N; i++) { acc += fp(512, 1e-6, NULL, NULL, NULL); barrier(); }
    uint64_t t1 = now_ns(); sink_d(acc); s[r] = (double)(t1 - t0) / N;
  }
  return median(s, 15);
}

static void init_y_pattern(void *y, size_t n, const char *dt) {
  if (!strcmp(dt, "f32")) { float *f = y; for (size_t i = 0; i < n; i++) f[i] = 0.5f + (float)(i & 1023) * (1.0f / 1024.0f); }
  else if (!strcmp(dt, "f64")) { double *f = y; for (size_t i = 0; i < n; i++) f[i] = 0.5 + (double)(i & 1023) * (1.0 / 1024.0); }
  else { uint32_t *u = y; for (size_t i = 0; i < n; i++) u[i] = (uint32_t)((i & 1023) | 1); }
}

struct cfg { int reg; long n; long off; };

static void run_cfg(FILE *f, const char *session, const struct cfg *c, int pass, int reps, double min_ms, double ovh, const char *qos, uint64_t seed, int *inner_cache) {
  const struct kentry *e = &REGISTRY[c->reg];
  size_t sz = dtype_size(e->dtype), n = (size_t)c->n, na = arrays_of(e->kernel);
  size_t region = (((n * sz + (size_t)c->off + 4096) + 16383) / 16384) * 16384;
  size_t total = na * (region + 2176) + 16384;
  char *slab = mmap(NULL, total, PROT_READ | PROT_WRITE, MAP_ANON | MAP_PRIVATE, -1, 0);
  if (slab == MAP_FAILED) { perror("mmap"); exit(1); }
  char *arr[3] = {0};
  for (int k = 0; k < na; k++) arr[k] = slab + (size_t)k * (region + 2176) + (size_t)c->off;
  uint64_t s = seed ^ (uint64_t)c->n;
  fill_array(arr[0], n, e->dtype, &s);                 /* first touch happens here, outside timing */
  if (!strcmp(e->kernel, "mul") || !strcmp(e->kernel, "dot")) fill_array(arr[1], n, e->dtype, &s);
  if (!strcmp(e->kernel, "mul")) memset(arr[2], 0, n * sz);
  if (!strcmp(e->kernel, "stencil")) memset(arr[1], 0, n * sz);
  int is_saxpy = !strcmp(e->kernel, "saxpy");
  const double a = 1e-6; double acc = 0;
  for (int r = 0; r < reps; r++) {
    if (is_saxpy) init_y_pattern(arr[1], n, e->dtype);  /* re-initialise in-place operand every sample */
    acc += e->fn(n, a, arr[0], arr[1], arr[2]); barrier(); /* untimed steady-state warm-up call */
    int inner = *inner_cache;
    if (inner == 0) {
      double t[5];
      for (int i = 0; i < 5; i++) { uint64_t t0 = now_ns(); acc += e->fn(n, a, arr[0], arr[1], arr[2]); barrier(); t[i] = (double)(now_ns() - t0); }
      double tm = median(t, 5) - ovh; if (tm < 1) tm = 1;
      double want = min_ms * 1e6 / tm; inner = want < 1 ? 1 : (want > 5e7 ? 50000000 : (int)ceil(want));
      *inner_cache = inner;
    }
    int th0 = thermal_level();
    uint64_t t0 = now_ns();
    for (int i = 0; i < inner; i++) { acc += e->fn(n, a, arr[0], arr[1], arr[2]); barrier(); }
    uint64_t t1 = now_ns();
    int th1 = thermal_level();
    double ns = (double)(t1 - t0) / inner - ovh;
    fprintf(f, "%llu,%s,%s,%s,%s,%zu,%zu,%ld,1,%d,%d,%d,%.4f,%.4f,%d,%d,%s\n", (unsigned long long)t0, session, e->build, e->kernel, e->dtype,
            n, n * sz * na, c->off, pass, r, inner, ns, ovh, th0, th1, qos);
  }
  sink_d(acc); if (is_saxpy || 1) { volatile char sinkc = arr[0][0] + arr[1][0]; (void)sinkc; }
  munmap(slab, total);
}

static int cmd_run(int argc, char **argv) {
  const char *out = getarg(argc, argv, "--out", NULL), *session = getarg(argc, argv, "--session", "s0");
  if (!out) { fprintf(stderr, "--out required\n"); return 2; }
  const char *builds = getarg(argc, argv, "--builds", "scalar,auto"), *kernels = getarg(argc, argv, "--kernels", "saxpy");
  const char *dtypes = getarg(argc, argv, "--dtypes", "f32"), *qos = getarg(argc, argv, "--qos", "user-interactive");
  const char *wsl = getarg(argc, argv, "--ws", NULL), *nl = getarg(argc, argv, "--n", NULL), *offl = getarg(argc, argv, "--offset", "0");
  int reps = atoi(getarg(argc, argv, "--reps", "5")), passes = atoi(getarg(argc, argv, "--passes", "3"));
  uint64_t seed = strtoull(getarg(argc, argv, "--seed", "12345"), NULL, 0);
  double min_ms = atof(getarg(argc, argv, "--min-ms", "1.0"));
  long sizes[512], offs[64]; int ns_ = 0, no = parse_list(offl, offs, 64);
  int use_ws = wsl != NULL;
  if (!wsl && !nl) { fprintf(stderr, "--ws or --n required\n"); return 2; }
  ns_ = parse_list(use_ws ? wsl : nl, sizes, 512);
  set_qos_named(qos);
  struct cfg *cfgs = malloc(sizeof(struct cfg) * NREG * ns_ * no); int nc = 0;
  for (size_t r = 0; r < NREG; r++) {
    if (!csv_contains(builds, REGISTRY[r].build) || !csv_contains(kernels, REGISTRY[r].kernel) || !csv_contains(dtypes, REGISTRY[r].dtype)) continue;
    for (int i = 0; i < ns_; i++) for (int j = 0; j < no; j++) {
      long n = sizes[i];
      if (use_ws) { n = sizes[i] / (long)(arrays_of(REGISTRY[r].kernel) * dtype_size(REGISTRY[r].dtype)); n &= ~63L; if (n < 64) n = 64; }
      cfgs[nc++] = (struct cfg){(int)r, n, offs[j]};
    }
  }
  int *inner = calloc(nc, sizeof(int));
  double ovh = measure_call_overhead();
  FILE *f = fopen(out, hasflag(argc, argv, "--append") ? "a" : "w");
  if (!f) { perror(out); return 1; }
  if (!hasflag(argc, argv, "--append") || ftell(f) == 0)
    fprintf(f, "epoch_ns,session,build,kernel,dtype,n,ws_bytes,offset,stride,pass,rep,inner_reps,ns_per_call,ovh_ns,therm_before,therm_after,qos\n");
  uint64_t order_seed = seed * 7919 + 1;
  int *idx = malloc(sizeof(int) * nc);
  for (int i = 0; i < nc; i++) idx[i] = i;
  for (int p = 0; p < passes; p++) {
    for (int i = nc - 1; i > 0; i--) { int j = (int)(rng_next(&order_seed) % (uint64_t)(i + 1)); int t = idx[i]; idx[i] = idx[j]; idx[j] = t; }
    for (int i = 0; i < nc; i++) { run_cfg(f, session, &cfgs[idx[i]], p, reps, min_ms, ovh, qos, seed, &inner[idx[i]]); }
    fflush(f);
    fprintf(stderr, "pass %d/%d done (%d configs), thermal=%d\n", p + 1, passes, nc, thermal_level());
  }
  fclose(f); return 0;
}

/* Dependent chains. Each outer iteration holds 64 dependent ops; loop control is off the critical path. */
#define REP64(s) ".rept 64\n" s "\n.endr\n"
static double chain_add(long iters) {
  uint64_t acc = 1, one = 1; uint64_t t0 = now_ns();
  __asm__ volatile("mov x9, %1\n1:\n" REP64("add %0, %0, %2") "subs x9, x9, #1\nb.ne 1b\n" : "+r"(acc) : "r"(iters), "r"(one) : "x9", "cc");
  uint64_t t1 = now_ns(); sink_d((double)acc); return (double)(t1 - t0) / ((double)iters * 64.0);
}
static double chain_mul(long iters) {
  uint64_t acc = 3, m = 1; uint64_t t0 = now_ns();
  __asm__ volatile("mov x9, %1\n1:\n" REP64("mul %0, %0, %2") "subs x9, x9, #1\nb.ne 1b\n" : "+r"(acc) : "r"(iters), "r"(m) : "x9", "cc");
  uint64_t t1 = now_ns(); sink_d((double)acc); return (double)(t1 - t0) / ((double)iters * 64.0);
}
static double chain_fma(long iters) {
  double acc = 1.0, m = 1.0, c = 0.0; uint64_t t0 = now_ns();
  __asm__ volatile("mov x9, %3\n1:\n" REP64("fmadd %d0, %d0, %d1, %d2") "subs x9, x9, #1\nb.ne 1b\n" : "+w"(acc) : "w"(m), "w"(c), "r"(iters) : "x9", "cc");
  uint64_t t1 = now_ns(); sink_d(acc); return (double)(t1 - t0) / ((double)iters * 64.0);
}

static int cmd_freq(int argc, char **argv) {
  const char *out = getarg(argc, argv, "--out", NULL), *session = getarg(argc, argv, "--session", "s0"), *qos = getarg(argc, argv, "--qos", "user-interactive");
  int reps = atoi(getarg(argc, argv, "--reps", "50"));
  long iters = atol(getarg(argc, argv, "--iters", "400000")); /* 400000*64 ops ~ 6 ms at 4 GHz */
  set_qos_named(qos);
  FILE *f = out ? fopen(out, hasflag(argc, argv, "--append") ? "a" : "w") : stdout;
  if (!f) { perror(out); return 1; }
  if (!hasflag(argc, argv, "--append") || ftell(f) == 0) fprintf(f, "epoch_ns,session,test,rep,ns_per_op,iters,therm,qos\n");
  chain_add(iters / 4); /* warm-up */
  for (int r = 0; r < reps; r++) {
    double v[3] = {chain_add(iters), chain_mul(iters), chain_fma(iters)}; const char *nm[3] = {"add", "mul", "fmadd"};
    for (int k = 0; k < 3; k++) fprintf(f, "%llu,%s,%s,%d,%.6f,%ld,%d,%s\n", (unsigned long long)now_ns(), session, nm[k], r, v[k], iters, thermal_level(), qos);
  }
  if (out) fclose(f); return 0;
}

static int cmd_timer(void) {
  enum { N = 1000000 }; static uint64_t d[N]; uint64_t prev = now_ns(); int nz = 0; uint64_t mn = ~0ULL;
  for (int i = 0; i < N; i++) { uint64_t t = now_ns(); d[i] = t - prev; prev = t; }
  for (int i = 0; i < N; i++) { if (d[i]) { nz++; if (d[i] < mn) mn = d[i]; } }
  static double dd[N]; for (int i = 0; i < N; i++) dd[i] = (double)d[i];
  printf("timer: back-to-back delta median %.1f ns, min nonzero %llu ns, fraction of nonzero deltas %.4f (tick granularity)\n", median(dd, N), (unsigned long long)mn, (double)nz / N);
  printf("call overhead (empty kernel via fn pointer + barrier): %.3f ns\n", measure_call_overhead());
  return 0;
}

int main(int argc, char **argv) {
  if (argc < 2) { fprintf(stderr, "usage: bench run|freq|timer|list ...\n"); return 2; }
  if (!strcmp(argv[1], "run")) return cmd_run(argc, argv);
  if (!strcmp(argv[1], "freq")) return cmd_freq(argc, argv);
  if (!strcmp(argv[1], "timer")) return cmd_timer();
  if (!strcmp(argv[1], "list")) { for (size_t i = 0; i < NREG; i++) printf("%s %s %s\n", REGISTRY[i].kernel, REGISTRY[i].dtype, REGISTRY[i].build); return 0; }
  return 2;
}
