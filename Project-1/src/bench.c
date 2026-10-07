/* Benchmark harness. Modes:
 *   bench run   --out F --session S [--builds a,b] [--kernels a,b] [--dtypes a,b]
 *               (--ws bytes,... | --n elems,...) [--offset bytes,...] [--reps R] [--passes P]
 *               [--seed N] [--min-ms X] [--qos name] [--append]
 *               [--offsets-xy ox:oy,...]  separate start offsets of x and y (bytes); default: every array uses --offset
 *               [--skew B]  extra bytes between consecutive arrays (default 2176)
 *   bench chase --out F --session S --ws bytes,... [--reps R] [--passes P] [--min-ms X] [--qos name]
 *               (pointer chase over a random single-cycle permutation, one 128 B node per cache line; --node-bytes B changes the spacing)
 *   bench freq  --out F --session S [--reps R] [--qos name]   (dependent-chain clock estimate)
 *   bench timer                                                 (timer resolution and overhead)
 *   bench list
 * One CSV row per sample (rep). Configuration order is shuffled per pass with a fixed seed. */
#include "common.h"
#include "registry_gen.h"
#include <math.h>
#include <sys/resource.h>

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

static int arrays_of(const char *k) {
  if (!strcmp(k, "mul") || !strcmp(k, "gather") || !strcmp(k, "triad") || !strcmp(k, "add") || !strcmp(k, "saxpy_oop")) return 3;
  if (!strcmp(k, "read") || !strcmp(k, "incr")) return 1;
  return 2;
}
/* kernels whose second operand y is a pure input that must be filled with data */
static int y_is_input(const char *k) { return !strcmp(k, "mul") || !strncmp(k, "dot", 3) || !strcmp(k, "triad") || !strcmp(k, "add") || !strcmp(k, "saxpy_oop"); }
/* kernels that modify y in place and need y re-initialised before every sample */
static int y_inplace(const char *k) { return !strncmp(k, "saxpy", 5) && strcmp(k, "saxpy_oop") != 0; }
static int stride_of(const char *k) { return strncmp(k, "saxpy_s", 7) == 0 ? atoi(k + 7) : 1; }
/* footprint in bytes per touched element n: x and y span n*stride elements; gather also has a 4 B index per element */
static size_t foot_per_n(const char *k, const char *dt) {
  size_t sz = dtype_size(dt);
  if (!strcmp(k, "gather")) return 2 * sz + 4;
  return (size_t)arrays_of(k) * sz * (size_t)stride_of(k);
}
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

struct cfg { int reg; long n; long off; long offy; };
static long g_alias = 0, g_skew = 2176;

static void run_cfg(FILE *f, const char *session, const struct cfg *c, int pass, int reps, double min_ms, double ovh, const char *qos, uint64_t seed, int *inner_cache) {
  const struct kentry *e = &REGISTRY[c->reg];
  size_t sz = dtype_size(e->dtype), n = (size_t)c->n, na = arrays_of(e->kernel), S = (size_t)stride_of(e->kernel), nal = n * S; /* nal = allocated elements per array */
  long offmax = c->off > c->offy ? c->off : c->offy;
  size_t region = (((nal * sz + (size_t)offmax + 4096) + 16383) / 16384) * 16384;
  size_t total = na * (region + (size_t)g_skew) + 16384;
  char *slab = mmap(NULL, total, PROT_READ | PROT_WRITE, MAP_ANON | MAP_PRIVATE, -1, 0);
  if (slab == MAP_FAILED) { perror("mmap"); exit(1); }
  char *arr[3] = {0};
  for (size_t k = 0; k < (size_t)na; k++) arr[k] = slab + k * (region + (size_t)g_skew) + (size_t)(k == 1 ? c->offy : c->off);
  uint64_t s = seed ^ (uint64_t)c->n;
  fill_array(arr[0], nal, e->dtype, &s);                /* first touch happens here, outside timing */
  if (y_is_input(e->kernel)) fill_array(arr[1], n, e->dtype, &s);
  if (!strcmp(e->kernel, "mul") || !strcmp(e->kernel, "triad") || !strcmp(e->kernel, "add") || !strcmp(e->kernel, "saxpy_oop")) memset(arr[2], 0, n * sz);
  if (!strcmp(e->kernel, "copy") || !strcmp(e->kernel, "scale")) memset(arr[1], 0, n * sz); /* output array: first touch outside timing */
  if (!strcmp(e->kernel, "incr")) arr[1] = arr[0];       /* in-place kernel on a single array (passed as y) */
  if (g_alias) arr[1] = arr[0] + (size_t)g_alias * sz; /* y overlaps x shifted by g_alias elements (only valid for builds without restrict) */
  if (!strcmp(e->kernel, "stencil")) memset(arr[1], 0, n * sz);
  int is_gather = !strcmp(e->kernel, "gather");
  if (is_gather) { uint32_t *ix = (uint32_t *)arr[2]; for (size_t i = 0; i < n; i++) ix[i] = (uint32_t)(rng_next(&s) % n); } /* random indices into x */
  int is_saxpy = y_inplace(e->kernel) || is_gather || !strcmp(e->kernel, "incr");
  const double a = 1e-6; double acc = 0;
  for (int r = 0; r < reps; r++) {
    if (g_alias) init_y_pattern(arr[0], n + (size_t)g_alias, e->dtype); else if (is_saxpy) init_y_pattern(arr[1], is_gather ? n : nal, e->dtype);  /* re-initialise in-place operand every sample */
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
    fprintf(f, "%llu,%s,%s,%s,%s,%zu,%zu,%ld,%zu,%d,%d,%d,%.4f,%.4f,%d,%d,%s,%ld,%ld,%ld\n", (unsigned long long)t0, session, e->build, e->kernel, e->dtype,
            n, n * foot_per_n(e->kernel, e->dtype), c->off, S, pass, r, inner, ns, ovh, th0, th1, qos, g_alias, c->offy, g_skew);
  }
  sink_d(acc); { volatile char sinkc = arr[0][0] + (arr[1] ? arr[1][0] : 0); (void)sinkc; }
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
  g_alias = atol(getarg(argc, argv, "--alias", "0"));
  g_skew = atol(getarg(argc, argv, "--skew", "2176"));
  const char *xyl = getarg(argc, argv, "--offsets-xy", NULL);
  long ox[256], oy[256]; int nxy = 0;
  if (xyl) {  /* "ox:oy,ox:oy,..." */
    char *buf = strdup(xyl), *sv, *t = strtok_r(buf, ",", &sv);
    while (t && nxy < 256) { ox[nxy] = strtol(t, NULL, 0); const char *c = strchr(t, ':'); oy[nxy] = c ? strtol(c + 1, NULL, 0) : ox[nxy]; nxy++; t = strtok_r(NULL, ",", &sv); }
    free(buf);
  }
  set_qos_named(qos);
  int nvar = xyl ? nxy : no;
  struct cfg *cfgs = malloc(sizeof(struct cfg) * NREG * ns_ * nvar); int nc = 0;
  for (size_t r = 0; r < NREG; r++) {
    if (!csv_contains(builds, REGISTRY[r].build) || !csv_contains(kernels, REGISTRY[r].kernel) || !csv_contains(dtypes, REGISTRY[r].dtype)) continue;
    for (int i = 0; i < ns_; i++) for (int j = 0; j < nvar; j++) {
      long n = sizes[i];
      if (use_ws) { n = sizes[i] / (long)foot_per_n(REGISTRY[r].kernel, REGISTRY[r].dtype); n &= ~63L; if (n < 64) n = 64; }
      cfgs[nc++] = xyl ? (struct cfg){(int)r, n, ox[j], oy[j]} : (struct cfg){(int)r, n, offs[j], offs[j]};
    }
  }
  int *inner = calloc(nc, sizeof(int));
  double ovh = measure_call_overhead();
  FILE *f = fopen(out, hasflag(argc, argv, "--append") ? "a" : "w");
  if (!f) { perror(out); return 1; }
  if (!hasflag(argc, argv, "--append") || ftell(f) == 0)
    fprintf(f, "epoch_ns,session,build,kernel,dtype,n,ws_bytes,offset,stride,pass,rep,inner_reps,ns_per_call,ovh_ns,therm_before,therm_after,qos,alias,offset_y,skew\n");
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


#include "fma_gen.h"
/* FMA throughput: N independent accumulators, `fmla` repeated; time per fmla instruction. */
static int cmd_fmapeak(int argc, char **argv) {
  const char *out = getarg(argc, argv, "--out", NULL), *session = getarg(argc, argv, "--session", "s0");
  int reps = atoi(getarg(argc, argv, "--reps", "15"));
  set_qos_interactive();
  FILE *f = out ? fopen(out, "w") : stdout;
  fprintf(f, "epoch_ns,session,arrangement,accumulators,rep,ns_per_fmla,iters,therm\n");
  for (int a = 0; a < 2; a++) for (int n = 1; n <= FMA_MAXACC; n++) {
    fmafn fn = a == 0 ? FMA_4S[n - 1] : FMA_2D[n - 1];
    long iters = 200000 / (n > 4 ? n / 4 : 1); fn(iters / 4);
    for (int r = 0; r < reps; r++) {
      uint64_t t0 = now_ns(); fn(iters); uint64_t t1 = now_ns();
      fprintf(f, "%llu,%s,%s,%d,%d,%.6f,%ld,%d\n", (unsigned long long)t0, session, a == 0 ? "4s" : "2d", n, r, (double)(t1 - t0) / ((double)iters * FMA_REPEAT * n), iters, thermal_level());
    }
  }
  if (out) fclose(f);
  return 0;
}


/* Pointer chase: one node per 128 B cache line (the pointer sits at the start of the line, so no two nodes share a line),
 * linked into one random cycle (Sattolo shuffle). Each load depends on the previous one, so time per step is load-to-use
 * latency at the level that holds the working set. The cycle is verified before timing: every node visited once and the walk
 * returns to node 0 after exactly n steps (the harness aborts otherwise). */
static size_t g_node = 128;  /* node spacing in bytes; 128 = one node per cache line (default), 16512 = one node per 16 KiB page plus one line */
#define NODE_BYTES g_node
static __attribute__((noinline)) void *chase_walk(void *p, uint64_t steps) {
  void **q = (void **)p;
  for (uint64_t i = 0; i < steps; i++) q = (void **)*q;
  return (void *)q;
}
static int build_cycle(char *buf, size_t n, uint64_t seed) {
  uint32_t *perm = malloc(n * sizeof(uint32_t));
  if (!perm || n < 2 || n > UINT32_MAX) return 0;
  for (size_t i = 0; i < n; i++) perm[i] = (uint32_t)i;
  uint64_t st = seed ^ (uint64_t)n;
  for (size_t i = n - 1; i > 0; i--) { size_t j = (size_t)(rng_next(&st) % (uint64_t)i); uint32_t t = perm[i]; perm[i] = perm[j]; perm[j] = t; } /* Sattolo: j < i */
  for (size_t i = 0; i < n; i++) *(void **)(buf + i * NODE_BYTES) = buf + (size_t)perm[i] * NODE_BYTES;
  free(perm);
  uint8_t *seen = calloc((n + 7) / 8, 1);
  if (!seen) return 0;
  char *p = buf; size_t steps = 0; int ok = 1;
  do {
    size_t idx = (size_t)(p - buf) / NODE_BYTES;
    if ((size_t)(p - buf) % NODE_BYTES || idx >= n || (seen[idx >> 3] & (1u << (idx & 7)))) { ok = 0; break; }
    seen[idx >> 3] |= (uint8_t)(1u << (idx & 7));
    p = *(char **)p; steps++;
  } while (p != buf && steps <= n);
  if (ok && (steps != n || p != buf)) ok = 0;
  free(seen);
  return ok;
}
static int cmd_chase(int argc, char **argv) {
  const char *out = getarg(argc, argv, "--out", NULL), *session = getarg(argc, argv, "--session", "s0"), *qos = getarg(argc, argv, "--qos", "user-interactive");
  const char *wsl = getarg(argc, argv, "--ws", NULL);
  if (!out || !wsl) { fprintf(stderr, "--out and --ws required\n"); return 2; }
  int reps = atoi(getarg(argc, argv, "--reps", "5")), passes = atoi(getarg(argc, argv, "--passes", "3"));
  double min_ms = atof(getarg(argc, argv, "--min-ms", "1.0"));
  uint64_t seed = strtoull(getarg(argc, argv, "--seed", "12345"), NULL, 0);
  g_node = (size_t)atol(getarg(argc, argv, "--node-bytes", "128")); if (g_node < 128 || g_node % 128) { fprintf(stderr, "--node-bytes must be a multiple of 128\n"); return 2; }
  long sizes[512]; int nc = parse_list(wsl, sizes, 512);
  set_qos_named(qos);
  FILE *f = fopen(out, "w"); if (!f) { perror(out); return 1; }
  fprintf(f, "epoch_ns,session,ws_bytes,nodes,pass,rep,steps,ns_per_load,therm_before,therm_after,qos,minflt_timed,node_bytes\n");
  int *idx = malloc(sizeof(int) * nc); for (int i = 0; i < nc; i++) idx[i] = i;
  uint64_t order_seed = seed * 7919 + 1; void *sinkp = NULL;
  for (int p = 0; p < passes; p++) {
    for (int i = nc - 1; i > 0; i--) { int j = (int)(rng_next(&order_seed) % (uint64_t)(i + 1)); int t = idx[i]; idx[i] = idx[j]; idx[j] = t; }
    for (int ii = 0; ii < nc; ii++) {
      size_t bytes = ((size_t)sizes[idx[ii]] / NODE_BYTES) * NODE_BYTES, n = bytes / NODE_BYTES;
      char *buf = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_ANON | MAP_PRIVATE, -1, 0);
      if (buf == MAP_FAILED) { perror("mmap"); return 1; }
      if (!build_cycle(buf, n, seed)) { fprintf(stderr, "FATAL: chase permutation is not one full cycle (n=%zu)\n", n); return 3; }
      void *q = buf;
      uint64_t warm = n * 2 < (1u << 22) ? n * 2 : (1u << 22); if (warm < 4096) warm = 4096;
      q = chase_walk(q, warm);                                              /* untimed warm-up, also calibrates step count */
      uint64_t t0 = now_ns(); q = chase_walk(q, warm); double per = (double)(now_ns() - t0) / (double)warm;
      uint64_t steps = (uint64_t)(min_ms * 1e6 / (per > 0.05 ? per : 0.05)); if (steps < 4096) steps = 4096;
      for (int r = 0; r < reps; r++) {
        struct rusage a, b; getrusage(RUSAGE_SELF, &a);
        int th0 = thermal_level(); uint64_t s0 = now_ns();
        q = chase_walk(q, steps);
        uint64_t s1 = now_ns(); int th1 = thermal_level(); getrusage(RUSAGE_SELF, &b);
        fprintf(f, "%llu,%s,%zu,%zu,%d,%d,%llu,%.4f,%d,%d,%s,%ld,%zu\n", (unsigned long long)s0, session, bytes, n, p, r, (unsigned long long)steps, (double)(s1 - s0) / (double)steps, th0, th1, qos, b.ru_minflt - a.ru_minflt, g_node);
      }
      sinkp = q; barrier(); __asm__ volatile("" ::"r"(sinkp) : "memory");
      munmap(buf, bytes);
    }
    fflush(f); fprintf(stderr, "pass %d/%d done (%d sizes), thermal=%d\n", p + 1, passes, nc, thermal_level());
  }
  fclose(f); return 0;
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
  if (argc < 2) { fprintf(stderr, "usage: bench run|chase|freq|fmapeak|timer|list ...\n"); return 2; }
  if (!strcmp(argv[1], "run")) return cmd_run(argc, argv);
  if (!strcmp(argv[1], "freq")) return cmd_freq(argc, argv);
  if (!strcmp(argv[1], "timer")) return cmd_timer();
  if (!strcmp(argv[1], "chase")) return cmd_chase(argc, argv);
  if (!strcmp(argv[1], "fmapeak")) return cmd_fmapeak(argc, argv);
  if (!strcmp(argv[1], "list")) { for (size_t i = 0; i < NREG; i++) printf("%s %s %s\n", REGISTRY[i].kernel, REGISTRY[i].dtype, REGISTRY[i].build); return 0; }
  return 2;
}
