// membench: cache and memory profiling harness for Apple Silicon (ARM64, macOS).
//
// Subcommands (all print long-format CSV rows to stdout, see common.h):
//   header | freq | chase | tlb | bw | pat | mlp | loaded | kern | dce | ramp | hugetest | selftest
// Build: scripts/build.sh (clang -O2 -mcpu=native -ffp-contract=off).
#include <arm_neon.h>
#include <errno.h>
#include <math.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
#include <mach/vm_statistics.h>
#include "common.h"

#define LINE 128u
#define PAGE 16384u
#define LOOP_UNROLL _Pragma("clang loop unroll(full)")

static int g_fail = 0;
#define CHECK(cond, msg) do { if (!(cond)) { fprintf(stderr, "FAIL: %s\n", msg); g_fail++; } else fprintf(stderr, "ok:   %s\n", msg); } while (0)

// ---------------------------------------------------------------- timing helpers
// fn(ctx, n) runs n units of work and returns elapsed ns. Find n so that one call lasts target_ns.
typedef double (*work_fn)(void *, size_t);
static size_t calib(work_fn fn, void *ctx, double target_ns, size_t unit) {
    size_t n = unit * 16; double t;
    for (;;) { t = fn(ctx, n); if (t >= 2e6) break; n *= 4; }
    double per = t / (double)n;
    size_t want = (size_t)(target_ns / per);
    want = (want / unit + 1) * unit;
    return want < unit ? unit : want;
}

// ---------------------------------------------------------------- effective frequency estimate
#define ADD8 "add %0, %0, %1\n add %0, %0, %1\n add %0, %0, %1\n add %0, %0, %1\n" \
             "add %0, %0, %1\n add %0, %0, %1\n add %0, %0, %1\n add %0, %0, %1\n"
static __attribute__((noinline)) uint64_t add_chain(size_t outer) {
    uint64_t x = 1, y = 1;
    for (size_t i = 0; i < outer; i++) { __asm__ volatile(ADD8 ADD8 ADD8 ADD8 : "+r"(x) : "r"(y)); }  // 32 dependent adds
    return x;
}
static double add_chain_time(void *ctx, size_t outer) {
    (void)ctx; uint64_t t0 = now_ns(); sink_u64(add_chain(outer)); return (double)(now_ns() - t0);
}
// GHz estimate assuming a dependent 64-bit register add retires at 1 cycle latency. Label as an estimate.
// Busy-spin to bring the core out of its idle clock state (a fresh process starts at a low clock and ramps
// over roughly 100 ms; see the ramp experiment). Used at process start and inside freq_ghz().
static void warm_spin(double ms) {
    uint64_t t0 = now_ns(); while ((double)(now_ns() - t0) < ms * 1e6) sink_u64(add_chain(20000));
}
static int cmp_dbl(const void *a, const void *b) { double x = *(const double *)a, y = *(const double *)b; return (x > y) - (x < y); }
static double freq_ghz(void) {
    warm_spin(250);
    size_t outer = calib(add_chain_time, NULL, 20e6, 1);
    double f[5]; for (int i = 0; i < 5; i++) f[i] = 32.0 * (double)outer / add_chain_time(NULL, outer);
    qsort(f, 5, sizeof f[0], cmp_dbl); return f[2];
}

// ---------------------------------------------------------------- pointer chase
typedef struct { void *cur; size_t n; } chase_t;

static void shuffle_ptrs(void **a, size_t n, uint64_t seed) {
    uint64_t s = seed * 0x9E3779B97F4A7C15ull + 1;
    for (size_t i = n - 1; i > 0; i--) { size_t j = mulhi(xs64(&s), i + 1); void *t = a[i]; a[i] = a[j]; a[j] = t; }
}
// Link the addresses into one cycle in the given order (random order => single random cycle).
static void chase_link(chase_t *c, void **addrs, size_t n, int do_shuffle, uint64_t seed) {
    if (do_shuffle) shuffle_ptrs(addrs, n, seed);
    for (size_t i = 0; i < n; i++) *(void **)addrs[i] = addrs[i + 1 == n ? 0 : i + 1];
    c->cur = addrs[0]; c->n = n;
}
// Node j of a strided layout. For strides above one line the pointer slot moves by whole lines inside the
// stride block so that nodes spread over all cache sets (stride 16 KB would otherwise alias to a few sets).
static inline uint8_t *stride_addr(uint8_t *base, size_t j, size_t stride) {
    size_t off = stride > LINE ? ((j * LINE) % stride) : 0;
    return base + j * stride + off;
}
static __attribute__((noinline)) void *chase_loop(void *p, size_t n) {
    for (size_t i = 0; i < n; i += 8) {
        p = *(void **)p; p = *(void **)p; p = *(void **)p; p = *(void **)p;
        p = *(void **)p; p = *(void **)p; p = *(void **)p; p = *(void **)p;
    }
    return p;
}
static double run_chase(void *v, size_t n) {
    chase_t *c = v; uint64_t t0 = now_ns(); c->cur = chase_loop(c->cur, n); uint64_t t1 = now_ns();
    return (double)(t1 - t0);
}
// Warm, calibrate, then time `reps` repetitions. Emits ns_per_load.
static void chase_measure(chase_t *c, const char *exp, const char *variant, size_t ws, size_t stride,
                          int threads, double param, int reps, double target_ms) {
    size_t warm = c->n < (1u << 20) ? c->n : (1u << 20);
    warm = (warm / 8 + 1) * 8;
    run_chase(c, warm);
    size_t n = calib(run_chase, c, target_ms * 1e6, 8);
    for (int r = 0; r < reps; r++) {
        long f0 = minor_faults(); double t = run_chase(c, n); g_faults = minor_faults() - f0;
        emit(exp, variant, ws, stride, 8, threads, param, r, "ns_per_load", t / (double)n);
    }
}

static void cmd_chase(void) {
    size_t sizes[256]; int ns = arg_list("--sizes", "64K,1M,64M,1G", sizes, 256);
    size_t stride = arg_size("--stride", LINE);
    const char *mode = arg_str("--mode", "rand");
    int seq = !strcmp(mode, "seq");
    int reps = arg_int("--reps", 3); double tms = arg_dbl("--target-ms", 25);
    const char *exp = arg_str("--exp", "chase"), *variant = arg_str("--variant", mode);
    uint64_t seed = (uint64_t)arg_int("--seed", 1);
    for (int i = 0; i < ns; i++) {
        size_t ws = sizes[i], n = ws / stride;
        if (n < 8) continue;
        uint8_t *base = alloc_touch(ws, 1);
        void **addrs = (void **)alloc_touch(n * sizeof(void *), 0);
        for (size_t j = 0; j < n; j++) addrs[j] = stride_addr(base, j, stride);
        chase_t c; chase_link(&c, addrs, n, !seq, seed + (uint64_t)i * 7919);
        free_map(addrs, n * sizeof(void *));
        chase_measure(&c, exp, variant, ws, stride, 1, 0, reps, tms);
        fflush(stdout); free_map(base, ws);
    }
}

// TLB: fixed line count L = pages*lpp. "paged": lpp lines in each of `pages` distinct 16 KB pages.
// "packed": the same L lines contiguous (same cache footprint, fewer pages).
static void cmd_tlb(void) {
    size_t pgs[64]; int np = arg_list("--pages", "1,16,256,4096", pgs, 64);
    size_t lpp = arg_size("--lpp", 1);
    const char *layout = arg_str("--layout", "paged");
    int packed = !strcmp(layout, "packed");
    size_t fixedL = arg_size("--lines", 0);   // if set: L fixed and pages = L / lpp (pages sweep at fixed footprint)
    int reps = arg_int("--reps", 3); double tms = arg_dbl("--target-ms", 25);
    uint64_t seed = (uint64_t)arg_int("--seed", 1);
    const char *exp = arg_str("--exp", "tlb");
    for (int i = 0; i < np; i++) {
        size_t P = fixedL ? fixedL / pgs[i] : pgs[i];
        size_t l = fixedL ? pgs[i] : lpp;  // in fixed-L mode the list holds lines-per-page values
        if (fixedL) { P = fixedL / l; }
        size_t L = P * l;
        if (L < 8) continue;
        size_t bytes = packed ? L * LINE : P * PAGE;
        uint8_t *base = alloc_touch(bytes, 1);
        void **addrs = (void **)alloc_touch(L * sizeof(void *), 0);
        if (packed) { for (size_t j = 0; j < L; j++) addrs[j] = base + j * LINE; }
        else {
            for (size_t p = 0; p < P; p++) for (size_t j = 0; j < l; j++)
                addrs[p * l + j] = base + p * PAGE + (((p * l + j) * LINE) % PAGE);
        }
        chase_t c; chase_link(&c, addrs, L, 1, seed + (uint64_t)i * 104729);
        free_map(addrs, L * sizeof(void *));
        chase_measure(&c, exp, layout, L * LINE, PAGE, 1, (double)(packed ? (L * LINE + PAGE - 1) / PAGE : P),
                      reps, tms);
        fflush(stdout); free_map(base, bytes);
    }
}

// ---------------------------------------------------------------- streaming kernels
static inline uint32x4_t rd_line(const uint8_t *p) {
    const uint32_t *q = (const uint32_t *)p;
    uint32x4_t a = veorq_u32(vld1q_u32(q), vld1q_u32(q + 4));
    uint32x4_t b = veorq_u32(vld1q_u32(q + 8), vld1q_u32(q + 12));
    uint32x4_t c = veorq_u32(vld1q_u32(q + 16), vld1q_u32(q + 20));
    uint32x4_t d = veorq_u32(vld1q_u32(q + 24), vld1q_u32(q + 28));
    return veorq_u32(veorq_u32(a, b), veorq_u32(c, d));
}
static inline void wr_st(uint8_t *p, uint32x4_t v) {
    uint32_t *q = (uint32_t *)p;
    for (int k = 0; k < 8; k++) vst1q_u32(q + 4 * k, v);
}
// Non-temporal store pair hint (stnp). Content identical to wr_st.
static inline void wr_nt(uint8_t *p, uint32x4_t v) {
    __asm__ volatile("stnp %q1, %q1, [%0]\n stnp %q1, %q1, [%0, #32]\n stnp %q1, %q1, [%0, #64]\n"
                     "stnp %q1, %q1, [%0, #96]\n" : : "r"(p), "w"(v) : "memory");
}
// dc zva zeroes a block without reading it (no write-allocate fetch). Block size from DCZID_EL0.
static size_t g_zva_bs = 0;   // 0 = not permitted
static void zva_init(void) {
    uint64_t z; __asm__ volatile("mrs %0, dczid_el0" : "=r"(z));
    g_zva_bs = (z & 16) ? 0 : (size_t)4 << (z & 15);
}
static inline void wr_zva(uint8_t *p, uint32x4_t v) {
    (void)v;
    for (size_t b = 0; b < LINE; b += g_zva_bs) __asm__ volatile("dc zva, %0" : : "r"(p + b) : "memory");
}

typedef uint64_t (*mixfn)(uint8_t *A, uint8_t *B, size_t groups);
// One group = 10 lines: RL read lines from stream A, WL written lines to stream B.
#define DEF_MIX(NAME, RL, WL, WR)                                                                       \
    static __attribute__((noinline)) uint64_t NAME(uint8_t *A, uint8_t *B, size_t groups) {             \
        uint32x4_t acc = vdupq_n_u32(0);                                                                \
        for (size_t g = 0; g < groups; g++) {                                                           \
            LOOP_UNROLL for (int k = 0; k < RL; k++) acc = veorq_u32(acc, rd_line(A + ((g * RL + k) << 7))); \
            LOOP_UNROLL for (int k = 0; k < WL; k++)                                                    \
                WR(B + ((g * WL + k) << 7), vdupq_n_u32((uint32_t)(g * 16 + k)));                       \
        }                                                                                               \
        return vgetq_lane_u32(acc, 0) ^ vgetq_lane_u32(acc, 1) ^ vgetq_lane_u32(acc, 2) ^ vgetq_lane_u32(acc, 3); \
    }
DEF_MIX(mix_r10w0, 10, 0, wr_st)
DEF_MIX(mix_r7w3_st, 7, 3, wr_st)
DEF_MIX(mix_r7w3_nt, 7, 3, wr_nt)
DEF_MIX(mix_r5w5_st, 5, 5, wr_st)
DEF_MIX(mix_r5w5_nt, 5, 5, wr_nt)
DEF_MIX(mix_r0w10_st, 0, 10, wr_st)
DEF_MIX(mix_r0w10_nt, 0, 10, wr_nt)
DEF_MIX(mix_r0w10_zva, 0, 10, wr_zva)
// Read-modify-write of the same line (50/50 at the bus, no separate allocate fetch for the store).
static __attribute__((noinline)) uint64_t mix_rmw(uint8_t *A, uint8_t *B, size_t groups) {
    (void)B; uint32x4_t one = vdupq_n_u32(1); uint32x4_t acc = vdupq_n_u32(0);
    for (size_t g = 0; g < groups; g++)
        LOOP_UNROLL for (int k = 0; k < 10; k++) {
            uint32_t *q = (uint32_t *)(A + ((g * 10 + k) << 7));
            for (int j = 0; j < 8; j++) { uint32x4_t v = vaddq_u32(vld1q_u32(q + 4 * j), one); vst1q_u32(q + 4 * j, v); acc = veorq_u32(acc, v); }
        }
    return vgetq_lane_u32(acc, 0) ^ vgetq_lane_u32(acc, 3);
}
typedef struct { const char *name; mixfn fn; int rl, wl; int a_lines, b_lines; } mix_t;
// rl/wl are lines read / written per group (for accounting); a_lines/b_lines are lines consumed from each region.
static const mix_t MIXES[] = {
    {"r10w0", mix_r10w0, 10, 0, 10, 0},       {"r7w3_st", mix_r7w3_st, 7, 3, 7, 3},
    {"r7w3_nt", mix_r7w3_nt, 7, 3, 7, 3},     {"r5w5_st", mix_r5w5_st, 5, 5, 5, 5},
    {"r5w5_nt", mix_r5w5_nt, 5, 5, 5, 5},     {"r0w10_st", mix_r0w10_st, 0, 10, 0, 10},
    {"r0w10_nt", mix_r0w10_nt, 0, 10, 0, 10}, {"r0w10_zva", mix_r0w10_zva, 0, 10, 0, 10},
    {"rmw", mix_rmw, 10, 10, 10, 0},
};
#define NMIX ((int)(sizeof MIXES / sizeof MIXES[0]))
static const mix_t *find_mix(const char *n) {
    for (int i = 0; i < NMIX; i++) if (!strcmp(MIXES[i].name, n)) return &MIXES[i];
    fprintf(stderr, "unknown kernel %s\n", n); exit(2);
}

typedef struct { const mix_t *m; uint8_t *A, *B; size_t groups; } bwctx;
static void bw_alloc(bwctx *c, const mix_t *m, size_t ws) {
    c->m = m; c->groups = ws / (10 * LINE);
    c->A = m->a_lines ? alloc_touch(c->groups * m->a_lines * LINE, 0x55) : NULL;
    c->B = m->b_lines ? alloc_touch(c->groups * m->b_lines * LINE, 0x55) : NULL;
}
static void bw_free(bwctx *c) {
    if (c->A) free_map(c->A, c->groups * c->m->a_lines * LINE);
    if (c->B) free_map(c->B, c->groups * c->m->b_lines * LINE);
}
static double run_bw(void *v, size_t passes) {
    bwctx *c = v; uint64_t s = 0; uint64_t t0 = now_ns();
    for (size_t i = 0; i < passes; i++) s += c->m->fn(c->A, c->B, c->groups);
    uint64_t t1 = now_ns(); sink_u64(s); return (double)(t1 - t0);
}
static void cmd_bw(void) {
    size_t sizes[128]; int ns = arg_list("--sizes", "8M,1G", sizes, 128);
    int reps = arg_int("--reps", 3); double tms = arg_dbl("--target-ms", 25);
    const char *exp = arg_str("--exp", "bw");
    for (int i = 0; i < ns; i++) {
        char *save, *tok;
        char kcopy[512]; strncpy(kcopy, arg_str("--kernels", "r10w0"), sizeof kcopy - 1); kcopy[sizeof kcopy - 1] = 0;
        for (tok = strtok_r(kcopy, ",", &save); tok; tok = strtok_r(NULL, ",", &save)) {
            const mix_t *m = find_mix(tok);
            if (strstr(m->name, "zva") && !g_zva_bs) continue;
            bwctx c; bw_alloc(&c, m, sizes[i]);
            if (!c.groups) { bw_free(&c); continue; }
            run_bw(&c, 2);                                   // warm / fault in
            size_t passes = calib(run_bw, &c, tms * 1e6, 1);
            double bytes_per_pass = (double)c.groups * (m->rl + m->wl) * LINE;
            for (int r = 0; r < reps; r++) {
                long f0 = minor_faults(); double t = run_bw(&c, passes); g_faults = minor_faults() - f0;
                emit(exp, m->name, sizes[i], 0, LINE, 1, 0, r, "gbps_app", bytes_per_pass * (double)passes / t);
            }
            fflush(stdout); bw_free(&c);
        }
    }
}

// Pattern bandwidth: independent loads of `size` bytes at stride S, sequential or random slots.
static inline uint32x4_t ld_size(const uint8_t *p, const int sz) {
    const uint32_t *q = (const uint32_t *)p; uint32x4_t a = vld1q_u32(q);
    if (sz >= 32) a = veorq_u32(a, vld1q_u32(q + 4));
    if (sz >= 64) { a = veorq_u32(a, vld1q_u32(q + 8)); a = veorq_u32(a, vld1q_u32(q + 12)); }
    if (sz >= 128) { for (int k = 4; k < 8; k++) a = veorq_u32(a, vld1q_u32(q + 4 * k)); }
    return a;
}
typedef struct { uint8_t *base; size_t ws, stride; size_t nslots; uint64_t st[8]; size_t off; int size, rand; uint64_t sum; } patctx;
#define DEF_PAT(SZ)                                                                                       \
    static __attribute__((noinline)) uint64_t pat_seq_##SZ(patctx *c, size_t n) {                         \
        uint32x4_t acc = vdupq_n_u32(0); size_t off = c->off; const size_t S = c->stride;                 \
        for (size_t i = 0; i < n; i += 8) {                                                               \
            LOOP_UNROLL for (int k = 0; k < 8; k++) acc = veorq_u32(acc, ld_size(c->base + off + k * S, SZ)); \
            off += 8 * S; if (off >= c->ws) off = 0;                                                      \
        }                                                                                                 \
        c->off = off; return vgetq_lane_u32(acc, 0) ^ vgetq_lane_u32(acc, 1) ^ vgetq_lane_u32(acc, 2) ^ vgetq_lane_u32(acc, 3); \
    }                                                                                                     \
    static __attribute__((noinline)) uint64_t pat_rnd_##SZ(patctx *c, size_t n) {                         \
        uint32x4_t acc = vdupq_n_u32(0); uint64_t s0 = c->st[0], s1 = c->st[1], s2 = c->st[2], s3 = c->st[3]; \
        uint64_t s4 = c->st[4], s5 = c->st[5], s6 = c->st[6], s7 = c->st[7];                              \
        const uint64_t ns = c->nslots, S = c->stride; const uint8_t *b = c->base;                         \
        const uint64_t M = 6364136223846793005ull, C = 1442695040888963407ull;                            \
        for (size_t i = 0; i < n; i += 8) {                                                               \
            s0 = s0 * M + C; s1 = s1 * M + C; s2 = s2 * M + C; s3 = s3 * M + C;                           \
            s4 = s4 * M + C; s5 = s5 * M + C; s6 = s6 * M + C; s7 = s7 * M + C;                           \
            acc = veorq_u32(acc, ld_size(b + (((s0 >> 32) * ns) >> 32) * S, SZ));                         \
            acc = veorq_u32(acc, ld_size(b + (((s1 >> 32) * ns) >> 32) * S, SZ));                         \
            acc = veorq_u32(acc, ld_size(b + (((s2 >> 32) * ns) >> 32) * S, SZ));                         \
            acc = veorq_u32(acc, ld_size(b + (((s3 >> 32) * ns) >> 32) * S, SZ));                         \
            acc = veorq_u32(acc, ld_size(b + (((s4 >> 32) * ns) >> 32) * S, SZ));                         \
            acc = veorq_u32(acc, ld_size(b + (((s5 >> 32) * ns) >> 32) * S, SZ));                         \
            acc = veorq_u32(acc, ld_size(b + (((s6 >> 32) * ns) >> 32) * S, SZ));                         \
            acc = veorq_u32(acc, ld_size(b + (((s7 >> 32) * ns) >> 32) * S, SZ));                         \
        }                                                                                                 \
        c->st[0] = s0; c->st[1] = s1; c->st[2] = s2; c->st[3] = s3; c->st[4] = s4; c->st[5] = s5; c->st[6] = s6; c->st[7] = s7; \
        return vgetq_lane_u32(acc, 0) ^ vgetq_lane_u32(acc, 1) ^ vgetq_lane_u32(acc, 2) ^ vgetq_lane_u32(acc, 3); \
    }
DEF_PAT(16) DEF_PAT(32) DEF_PAT(64) DEF_PAT(128)
static uint64_t pat_dispatch(patctx *c, size_t n) {
    switch (c->size) {
    case 16: return c->rand ? pat_rnd_16(c, n) : pat_seq_16(c, n);
    case 32: return c->rand ? pat_rnd_32(c, n) : pat_seq_32(c, n);
    case 64: return c->rand ? pat_rnd_64(c, n) : pat_seq_64(c, n);
    default: return c->rand ? pat_rnd_128(c, n) : pat_seq_128(c, n);
    }
}
static double run_pat(void *v, size_t n) {
    patctx *c = v; uint64_t t0 = now_ns(); uint64_t s = pat_dispatch(c, n); uint64_t t1 = now_ns();
    sink_u64(s); return (double)(t1 - t0);
}
static void pat_init(patctx *c, uint8_t *base, size_t ws, size_t stride, int size, int rnd, uint64_t seed) {
    c->base = base; c->ws = ws; c->stride = stride; c->nslots = ws / stride; c->off = 0; c->size = size; c->rand = rnd;
    uint64_t s = seed * 0x9E3779B97F4A7C15ull + 7; for (int i = 0; i < 8; i++) c->st[i] = xs64(&s);
}
static void cmd_pat(void) {
    size_t ws = arg_size("--ws", 1ull << 30);
    size_t strides[64]; int nst = arg_list("--strides", "64,128,256,1024", strides, 64);
    size_t sizes[8]; int nsz = arg_list("--sizes", "16,64,128", sizes, 8);
    const char *pats = arg_str("--patterns", "seq,rand");
    int reps = arg_int("--reps", 3); double tms = arg_dbl("--target-ms", 25);
    uint64_t seed = (uint64_t)arg_int("--seed", 1);
    const char *exp = arg_str("--exp", "pat");
    uint8_t *base = alloc_touch(ws, 3);
    // configuration list, visited in a seeded random order so slow drift cannot alias with the stride axis
    typedef struct { int a, i, j; } cfg_t; cfg_t *cf = malloc(sizeof(cfg_t) * 2 * 64 * 8); int ncf = 0;
    for (int a = 0; a < 2; a++) { if (!strstr(pats, a ? "rand" : "seq")) continue;
        for (int i = 0; i < nst; i++) for (int j = 0; j < nsz; j++) if (sizes[j] <= strides[i]) cf[ncf++] = (cfg_t){a, i, j}; }
    uint64_t rs = seed * 0x9E3779B97F4A7C15ull + 11;
    for (int k = ncf - 1; k > 0; k--) { int m = (int)mulhi(xs64(&rs), (uint64_t)k + 1); cfg_t t = cf[k]; cf[k] = cf[m]; cf[m] = t; }
    for (int q = 0; q < ncf; q++) {
        const char *pn = cf[q].a ? "rand" : "seq"; size_t S = strides[cf[q].i]; int sz = (int)sizes[cf[q].j];
        patctx c; pat_init(&c, base, ws, S, sz, cf[q].a, seed);
        pat_dispatch(&c, 1u << 16);
        size_t n = calib(run_pat, &c, tms * 1e6, 8);
        for (int r = 0; r < reps; r++) {
            long f0 = minor_faults(); double t = run_pat(&c, n); g_faults = minor_faults() - f0;
            emit(exp, pn, ws, S, (size_t)sz, 1, 0, r, "gbps_useful", (double)n * sz / t);
            emit(exp, pn, ws, S, (size_t)sz, 1, 0, r, "ns_per_access", t / (double)n);
        }
        fflush(stdout);
    }
    free(cf); free_map(base, ws);
}

// ---------------------------------------------------------------- MLP sweep (K independent chains in one thread)
#define DEF_MLP(K)                                                                                      \
    static __attribute__((noinline)) void mlp_##K(void **st, size_t steps) {                            \
        void *p[K]; for (int k = 0; k < K; k++) p[k] = st[k];                                           \
        for (size_t i = 0; i < steps; i++) { LOOP_UNROLL for (int k = 0; k < K; k++) p[k] = *(void **)p[k]; } \
        for (int k = 0; k < K; k++) st[k] = p[k];                                                       \
    }
DEF_MLP(1) DEF_MLP(2) DEF_MLP(3) DEF_MLP(4) DEF_MLP(6) DEF_MLP(8) DEF_MLP(12) DEF_MLP(16) DEF_MLP(20)
DEF_MLP(24) DEF_MLP(32) DEF_MLP(40) DEF_MLP(48) DEF_MLP(64)
typedef void (*mlpfn)(void **, size_t);
static mlpfn mlp_lookup(int K) {
    switch (K) {
    case 1: return mlp_1; case 2: return mlp_2; case 3: return mlp_3; case 4: return mlp_4; case 6: return mlp_6;
    case 8: return mlp_8; case 12: return mlp_12; case 16: return mlp_16; case 20: return mlp_20;
    case 24: return mlp_24; case 32: return mlp_32; case 40: return mlp_40; case 48: return mlp_48; case 64: return mlp_64;
    }
    return NULL;
}
typedef struct { mlpfn fn; void **st; } mlpctx;
static double run_mlp(void *v, size_t steps) {
    mlpctx *c = v; uint64_t t0 = now_ns(); c->fn(c->st, steps); uint64_t t1 = now_ns(); return (double)(t1 - t0);
}
static void cmd_mlp(void) {
    size_t ws = arg_size("--ws", 1ull << 30);
    size_t ks[32]; int nk = arg_list("--chains", "1,2,4,8,16,32,64", ks, 32);
    int reps = arg_int("--reps", 3); double tms = arg_dbl("--target-ms", 25);
    uint64_t seed = (uint64_t)arg_int("--seed", 1);
    const char *exp = arg_str("--exp", "mlp");
    size_t n = ws / LINE;
    uint8_t *base = alloc_touch(ws, 1);
    void **addrs = (void **)alloc_touch(n * sizeof(void *), 0);
    for (size_t j = 0; j < n; j++) addrs[j] = base + j * LINE;
    chase_t c; chase_link(&c, addrs, n, 1, seed);   // addrs[] now holds the cycle order
    for (int i = 0; i < nk; i++) {
        int K = (int)ks[i]; mlpfn fn = mlp_lookup(K); if (!fn) continue;
        void *st[64]; for (int k = 0; k < K; k++) st[k] = addrs[(size_t)k * (n / (size_t)K)];
        mlpctx m = {fn, st};
        fn(st, 1u << 14);
        size_t steps = calib(run_mlp, &m, tms * 1e6, 1);
        for (int r = 0; r < reps; r++) {
            long f0 = minor_faults(); double t = run_mlp(&m, steps); g_faults = minor_faults() - f0;
            emit(exp, "mlp", ws, LINE, 8, 1, K, r, "ns_per_step", t / (double)steps);
            emit(exp, "mlp", ws, LINE, 8, 1, K, r, "gbps", (double)K * LINE * (double)steps / t);
        }
        fflush(stdout);
    }
    free_map(addrs, n * sizeof(void *)); free_map(base, ws);
}

// ---------------------------------------------------------------- loaded latency (probe chase + N bandwidth threads)
typedef struct {
    const mix_t *m; uint8_t *A, *B; size_t groups; size_t delay;
    volatile uint64_t bytes; volatile int qos_seen; int qos;
    volatile int *go, *stop; volatile int *ready;
} bwthr;
static void *bw_thread(void *arg) {
    bwthr *t = arg; set_thread_qos(t->qos); t->qos_seen = get_thread_qos();
    __atomic_add_fetch(t->ready, 1, __ATOMIC_SEQ_CST);
    while (!__atomic_load_n(t->go, __ATOMIC_ACQUIRE)) __asm__ volatile("yield");
    const size_t slice = (1u << 20) / (10 * LINE); size_t g = 0; uint64_t s = 0;
    const size_t per_group = (size_t)(t->m->rl + t->m->wl) * LINE;
    while (!__atomic_load_n(t->stop, __ATOMIC_RELAXED)) {
        size_t sl = t->groups - g < slice ? t->groups - g : slice;
        s += t->m->fn(t->A ? t->A + g * t->m->a_lines * LINE : NULL, t->B ? t->B + g * t->m->b_lines * LINE : NULL, sl);
        __atomic_store_n(&t->bytes, t->bytes + sl * per_group, __ATOMIC_RELAXED);
        g += sl; if (g >= t->groups) g = 0;
        if (t->delay) { uint64_t x = 0; for (size_t i = 0; i < t->delay; i++) __asm__ volatile("add %0, %0, #1" : "+r"(x)); }
    }
    sink_u64(s); return NULL;
}
static void cmd_loaded(void) {
    size_t thr[32]; int nt = arg_list("--threads", "0,1,2,4,8,16", thr, 32);
    size_t dly[32]; int nd = arg_list("--delays", "0", dly, 32);
    const mix_t *m = find_mix(arg_str("--mix", "r10w0"));
    size_t bufsz = arg_size("--bufsize", 256ull << 20), cws = arg_size("--chase-ws", 1ull << 30);
    int probe = arg_int("--probe", 1); double win = arg_dbl("--window-ms", 400) * 1e6;
    int qos = qos_from_name(arg_str("--qos", "interactive"));
    int reps = arg_int("--reps", 1); uint64_t seed = (uint64_t)arg_int("--seed", 1);
    const char *exp = arg_str("--exp", "loaded");
    int maxt = 0; for (int i = 0; i < nt; i++) if ((int)thr[i] > maxt) maxt = (int)thr[i];
    // probe chain
    chase_t c = {0}; uint8_t *cbase = NULL;
    if (probe) {
        size_t n = cws / LINE; cbase = alloc_touch(cws, 1); void **addrs = (void **)alloc_touch(n * sizeof(void *), 0);
        for (size_t j = 0; j < n; j++) addrs[j] = cbase + j * LINE;
        chase_link(&c, addrs, n, 1, seed); free_map(addrs, n * sizeof(void *));
    }
    // per-thread buffers (allocated once, reused)
    bwthr *T = calloc((size_t)(maxt ? maxt : 1), sizeof *T);
    for (int i = 0; i < maxt; i++) { bwctx b; bw_alloc(&b, m, bufsz); T[i].A = b.A; T[i].B = b.B; T[i].groups = b.groups; T[i].m = m; }
    for (int di = 0; di < nd; di++) for (int ti = 0; ti < nt; ti++) for (int r = 0; r < reps; r++) {
        int N = (int)thr[ti]; volatile int go = 0, stop = 0, ready = 0; pthread_t th[32];
        for (int i = 0; i < N; i++) { T[i].delay = dly[di]; T[i].bytes = 0; T[i].qos = qos; T[i].go = &go; T[i].stop = &stop; T[i].ready = &ready; pthread_create(&th[i], NULL, bw_thread, &T[i]); }
        while (ready < N) usleep(1000);
        set_thread_qos(qos); g_qos_seen = get_thread_qos();
        __atomic_store_n(&go, 1, __ATOMIC_RELEASE);
        usleep(200000);                                          // let threads ramp (frequency, queues)
        uint64_t b0[32]; for (int i = 0; i < N; i++) b0[i] = T[i].bytes;
        uint64_t t0 = now_ns(); size_t loads = 0; long f0 = minor_faults();
        if (probe) { while ((double)(now_ns() - t0) < win) { c.cur = chase_loop(c.cur, 4096); loads += 4096; } }
        else usleep((useconds_t)(win / 1000));
        uint64_t t1 = now_ns(); g_faults = minor_faults() - f0;
        uint64_t b1[32]; for (int i = 0; i < N; i++) b1[i] = T[i].bytes;
        __atomic_store_n(&stop, 1, __ATOMIC_RELEASE);
        for (int i = 0; i < N; i++) pthread_join(th[i], NULL);
        sink_ptr(c.cur);
        double el = (double)(t1 - t0), tot = 0, mn = 1e18, mx = 0;
        for (int i = 0; i < N; i++) { double g = (double)(b1[i] - b0[i]) / el; tot += g; if (g < mn) mn = g; if (g > mx) mx = g; }
        double dl = (double)dly[di];
        emit(exp, m->name, bufsz, 0, LINE, N, dl, r, "bw_gbps", tot);
        if (N) { emit(exp, m->name, bufsz, 0, LINE, N, dl, r, "bw_thread_min", mn); emit(exp, m->name, bufsz, 0, LINE, N, dl, r, "bw_thread_max", mx); }
        if (probe) emit(exp, m->name, cws, LINE, 8, N, dl, r, "lat_ns", el / (double)loads);
        fflush(stdout);
    }
    for (int i = 0; i < maxt; i++) { bwctx b = {m, T[i].A, T[i].B, T[i].groups}; bw_free(&b); }
    free(T); if (cbase) free_map(cbase, cws);
}

// ---------------------------------------------------------------- simple kernels: z=x*y, y=a*x+y with three index patterns
typedef struct { float *x, *y, *z; size_t n; float a; int kernel; size_t mult; uint64_t pos; } kctx;
#define KMUL_UNIT 1
static __attribute__((noinline)) void k_unit(kctx *c, size_t count) {
    size_t n = c->n; float *restrict x = c->x, *restrict y = c->y, *restrict z = c->z; const float a = c->a;
    size_t pos = (size_t)(c->pos & (n - 1));
    while (count) {
        size_t seg = n - pos < count ? n - pos : count;
        if (c->kernel == 0) { for (size_t i = pos; i < pos + seg; i++) z[i] = x[i] * y[i]; }
        else { for (size_t i = pos; i < pos + seg; i++) y[i] = a * x[i] + y[i]; }
        pos += seg; count -= seg; if (pos == n) pos = 0;
    }
    c->pos = pos;
}
static __attribute__((noinline)) void k_idx(kctx *c, size_t count) {
    size_t mask = c->n - 1, m = c->mult; float *x = c->x, *y = c->y, *z = c->z; const float a = c->a; uint64_t i = c->pos;
    if (c->kernel == 0) for (size_t k = 0; k < count; k++, i++) { size_t j = (size_t)(i * m) & mask; z[j] = x[j] * y[j]; }
    else for (size_t k = 0; k < count; k++, i++) { size_t j = (size_t)(i * m) & mask; y[j] = a * x[j] + y[j]; }
    c->pos = i;
}
static void k_run(kctx *c, size_t count) { if (c->mult == 1) k_unit(c, count); else k_idx(c, count); }
static double run_kern(void *v, size_t count) {
    kctx *c = v; uint64_t t0 = now_ns(); k_run(c, count); uint64_t t1 = now_ns(); return (double)(t1 - t0);
}
static void kern_init(kctx *c, size_t n, int kernel, size_t mult) {
    c->n = n; c->kernel = kernel; c->mult = mult; c->pos = 0; c->a = 0.5f;
    c->x = (float *)alloc_touch(n * 4, 0); c->y = (float *)alloc_touch(n * 4, 0); c->z = (float *)alloc_touch(n * 4, 0);
    for (size_t i = 0; i < n; i++) { c->x[i] = 1.0f + (float)(i % 97) * 0.01f; c->y[i] = 0.5f + (float)(i % 31) * 0.02f; }
}
static void kern_free(kctx *c) { free_map(c->x, c->n * 4); free_map(c->y, c->n * 4); free_map(c->z, c->n * 4); }
static void cmd_kern(void) {
    size_t ns_[64]; int nn = arg_list("--elems", "4096,1048576", ns_, 64);   // elements per array, power of two
    size_t mults[16]; int nm = arg_list("--mults", "1,16,40503", mults, 16); // 1 unit; 2^k stride; odd = scattered
    int reps = arg_int("--reps", 3); double tms = arg_dbl("--target-ms", 25);
    const char *exp = arg_str("--exp", "kern");
    for (int kernel = 0; kernel < 2; kernel++) for (int i = 0; i < nn; i++) {
        size_t n = ns_[i]; kctx c; kern_init(&c, n, kernel, 1);
        size_t foot = (kernel == 0 ? 3 : 2) * n * 4;
        for (int j = 0; j < nm; j++) {
            c.mult = mults[j]; c.pos = 0;
            k_run(&c, n < (1u << 20) ? n : (1u << 20));
            size_t count = calib(run_kern, &c, tms * 1e6, 1);
            for (int r = 0; r < reps; r++) {
                long f0 = minor_faults(); double t = run_kern(&c, count); g_faults = minor_faults() - f0;
                emit(exp, kernel ? "saxpy" : "mul", foot, mults[j] * 4, 4, 1, (double)n, r, "ns_per_elem", t / (double)count);
                emit(exp, kernel ? "saxpy" : "mul", foot, mults[j] * 4, 4, 1, (double)n, r, "gbps_useful", 12.0 * (double)count / t);
            }
            fflush(stdout);
        }
        sink_ptr(c.z); kern_free(&c);
    }
}

// ---------------------------------------------------------------- pitfalls
// (1) The result of this loop is unused: the optimizer removes it. (2) The same loop with a sink is real work.
static __attribute__((noinline)) void read_nosink(const uint8_t *p, size_t bytes) {
    uint32x4_t acc = vdupq_n_u32(0);
    for (size_t o = 0; o < bytes; o += LINE) acc = veorq_u32(acc, rd_line(p + o));
    (void)acc;
}
static __attribute__((noinline)) uint64_t read_sink(const uint8_t *p, size_t bytes) {
    uint32x4_t acc = vdupq_n_u32(0);
    for (size_t o = 0; o < bytes; o += LINE) acc = veorq_u32(acc, rd_line(p + o));
    return vgetq_lane_u32(acc, 0) ^ vgetq_lane_u32(acc, 1);
}
typedef struct { uint8_t *p; size_t bytes; int sink; } dcectx;
static double run_dce(void *v, size_t passes) {
    dcectx *c = v; uint64_t s = 0; uint64_t t0 = now_ns();
    for (size_t i = 0; i < passes; i++) { if (c->sink) s += read_sink(c->p, c->bytes); else read_nosink(c->p, c->bytes); }
    uint64_t t1 = now_ns(); sink_u64(s); return (double)(t1 - t0);
}
static void cmd_dce(void) {
    size_t ws = arg_size("--ws", 1ull << 30); int reps = arg_int("--reps", 3);
    uint8_t *p = alloc_touch(ws, 1);
    for (int sink = 0; sink < 2; sink++) {
        dcectx c = {p, ws, sink}; run_dce(&c, 2);
        size_t passes = calib(run_dce, &c, 25e6, 1);
        for (int r = 0; r < reps; r++) {
            double t = run_dce(&c, passes);
            emit("pitfall_dce", sink ? "with_sink" : "no_sink", ws, 0, LINE, 1, 0, r, "gbps_claimed", (double)ws * (double)passes / t);
        }
    }
    free_map(p, ws);
}
// Frequency ramp: fixed work chunks right after an idle period.
static void cmd_ramp(void) {
    int idle_ms = arg_int("--idle-ms", 3000), chunks = arg_int("--chunks", 120); double chunk_us = arg_dbl("--chunk-us", 500);
    int reps = arg_int("--reps", 3);
    freq_ghz();                                            // steady-state warm up
    size_t outer = calib(add_chain_time, NULL, chunk_us * 1e3, 1);
    for (int r = 0; r < reps; r++) {
        usleep((useconds_t)idle_ms * 1000);
        for (int k = 0; k < chunks; k++) {
            double t = add_chain_time(NULL, outer);
            emit("pitfall_ramp", "after_idle", 0, 0, 0, 1, k, r, "chunk_ns", t);
            emit("pitfall_ramp", "after_idle", 0, 0, 0, 1, k, r, "ghz_est", 32.0 * (double)outer / t);
        }
        for (int k = 0; k < chunks; k++) {                  // steady reference immediately after
            double t = add_chain_time(NULL, outer);
            emit("pitfall_ramp", "steady", 0, 0, 0, 1, k, r, "ghz_est", 32.0 * (double)outer / t);
        }
    }
}

// ---------------------------------------------------------------- huge page probe
static void cmd_hugetest(void) {
    size_t sz = 4ull << 20; mach_vm_address_t a = 0;
    kern_return_t kr = mach_vm_allocate(mach_task_self(), &a, sz, VM_FLAGS_ANYWHERE | VM_FLAGS_SUPERPAGE_SIZE_2MB);
    printf("mach_vm_allocate SUPERPAGE_SIZE_2MB: kern_return=%d (%s)\n", kr, mach_error_string(kr));
    if (kr == KERN_SUCCESS) mach_vm_deallocate(mach_task_self(), a, sz);
    a = 0; kr = mach_vm_allocate(mach_task_self(), &a, sz, VM_FLAGS_ANYWHERE | VM_FLAGS_SUPERPAGE_SIZE_ANY);
    printf("mach_vm_allocate SUPERPAGE_SIZE_ANY: kern_return=%d (%s)\n", kr, mach_error_string(kr));
    if (kr == KERN_SUCCESS) mach_vm_deallocate(mach_task_self(), a, sz);
    void *p = mmap(NULL, sz, PROT_READ | PROT_WRITE, MAP_ANON | MAP_PRIVATE, VM_FLAGS_SUPERPAGE_SIZE_2MB, 0);
    printf("mmap fd=SUPERPAGE_SIZE_2MB: %s (errno %d)\n", p == MAP_FAILED ? "failed" : "succeeded", p == MAP_FAILED ? errno : 0);
}

// ---------------------------------------------------------------- self tests
static int walk_cycle(void *start, size_t n, uint8_t *seen, uint8_t *lo, uint8_t *hi) {
    void *p = start; size_t distinct = 0;
    for (size_t i = 0; i < n; i++) {
        uint8_t *q = p; if (q < lo || q >= hi) return -1;
        size_t k = (size_t)(q - lo) / LINE; if (!seen[k]) { seen[k] = 1; distinct++; }
        p = *(void **)p;
    }
    return (p == start && distinct == n) ? 1 : 0;
}
static void selftest(void) {
    // single-cycle chases
    for (int mode = 0; mode < 2; mode++) {
        size_t n = 5000, stride = 128, ws = n * stride;
        uint8_t *b = alloc_touch(ws, 1); void **a = (void **)alloc_touch(n * 8, 0);
        for (size_t j = 0; j < n; j++) a[j] = stride_addr(b, j, stride);
        chase_t c; chase_link(&c, a, n, mode, 5);
        uint8_t *seen = calloc(n, 1);
        CHECK(walk_cycle(c.cur, n, seen, b, b + ws) == 1, mode ? "random chase is one full cycle (128 B)" : "sequential chase is one full cycle");
        free(seen); free_map(a, n * 8); free_map(b, ws);
    }
    {   // strided layout with line-offsets inside stride blocks stays inside its block
        size_t n = 1000, stride = 4096; uint8_t *b = alloc_touch(n * stride, 1); int ok = 1;
        for (size_t j = 0; j < n; j++) { uint8_t *q = stride_addr(b, j, stride); if (q < b + j * stride || q + 8 > b + (j + 1) * stride) ok = 0; }
        CHECK(ok, "strided layout offsets stay within their stride block");
        free_map(b, n * stride);
    }
    {   // TLB layout: P pages x lpp lines is one cycle over exactly P*lpp distinct lines in P distinct pages
        size_t P = 300, l = 5, L = P * l, bytes = P * PAGE;
        uint8_t *b = alloc_touch(bytes, 1); void **a = (void **)alloc_touch(L * 8, 0);
        for (size_t p = 0; p < P; p++) for (size_t j = 0; j < l; j++) a[p * l + j] = b + p * PAGE + (((p * l + j) * LINE) % PAGE);
        chase_t c; chase_link(&c, a, L, 1, 3);
        uint8_t *seen = calloc(bytes / LINE, 1); uint8_t *pg = calloc(P, 1);
        void *q = c.cur; size_t distinct = 0, pages = 0; int ok = 1;
        for (size_t i = 0; i < L; i++) { size_t k = ((uint8_t *)q - b) / LINE, pp = ((uint8_t *)q - b) / PAGE; if (!seen[k]) { seen[k] = 1; distinct++; } if (!pg[pp]) { pg[pp] = 1; pages++; } q = *(void **)q; }
        if (q != c.cur) ok = 0;
        CHECK(ok && distinct == L && pages == P, "TLB layout visits P pages, P*lpp lines, one cycle");
        free(seen); free(pg); free_map(a, L * 8); free_map(b, bytes);
    }
    {   // read kernel xor against scalar reference
        size_t bytes = 64 * LINE; uint8_t *b = alloc_touch(bytes, 0); uint32_t *w = (uint32_t *)b;
        for (size_t i = 0; i < bytes / 4; i++) w[i] = (uint32_t)(i * 2654435761u);
        uint32_t ref = 0; for (size_t i = 0; i < bytes / 4; i++) ref ^= w[i];
        uint32x4_t acc = vdupq_n_u32(0); for (size_t o = 0; o < bytes; o += LINE) acc = veorq_u32(acc, rd_line(b + o));
        uint32_t got = vgetq_lane_u32(acc, 0) ^ vgetq_lane_u32(acc, 1) ^ vgetq_lane_u32(acc, 2) ^ vgetq_lane_u32(acc, 3);
        CHECK(got == ref, "NEON read kernel matches scalar xor reference");
        free_map(b, bytes);
    }
    {   // write variants produce identical content; zva zeroes
        uint8_t *a = alloc_touch(LINE, 0x77), *b2 = alloc_touch(LINE, 0x66); uint32x4_t v = vdupq_n_u32(0xA5A5u);
        wr_st(a, v); wr_nt(b2, v);
        CHECK(!memcmp(a, b2, LINE), "stnp store writes the same bytes as regular store");
        if (g_zva_bs) { wr_zva(a, v); int z = 1; for (size_t i = 0; i < LINE; i++) if (a[i]) z = 0; CHECK(z, "dc zva zeroes a full 128 B line"); }
        else fprintf(stderr, "skip: dc zva not permitted\n");
        free_map(a, LINE); free_map(b2, LINE);
    }
    {   // mix kernels: coverage and accounting
        for (int mi = 0; mi < NMIX; mi++) {
            const mix_t *m = &MIXES[mi]; if (strstr(m->name, "zva") && !g_zva_bs) continue;
            bwctx c; bw_alloc(&c, m, 20 * 10 * LINE);
            uint64_t s = m->fn(c.A, c.B, c.groups); sink_u64(s);
            int ok = 1;
            if (m->b_lines && c.B) for (size_t l = 0; l < c.groups * m->b_lines; l++) { uint8_t *q = c.B + l * LINE; int same = 1; for (size_t k = 0; k < LINE; k++) if (q[k] != 0x55) same = 0; if (same && strcmp(m->name, "r0w10_zva")) { ok = 0; } }
            if (!strcmp(m->name, "rmw")) { for (size_t k = 0; k < c.groups * 10 * LINE; k++) if (c.A[k] != ((k & 3) ? 0x55 : 0x56)) ok = 0; }
            char msg[96]; snprintf(msg, sizeof msg, "mix kernel %s touches every line it should", m->name);
            CHECK(ok, msg); bw_free(&c);
        }
    }
    {   // pattern kernels vs scalar reference of the same address sequence
        size_t ws = 1u << 20, S = 256; uint8_t *b = alloc_touch(ws, 0); for (size_t i = 0; i < ws / 4; i++) ((uint32_t *)b)[i] = (uint32_t)(i * 40503u + 7);
        patctx c; pat_init(&c, b, ws, S, 64, 0, 9); uint64_t got = pat_dispatch(&c, 4096);
        uint32_t ref = 0; size_t off = 0;
        for (size_t i = 0; i < 4096; i += 8) { for (int k = 0; k < 8; k++) for (int w = 0; w < 16; w++) ref ^= ((uint32_t *)(b + off + k * S))[w]; off += 8 * S; if (off >= ws) off = 0; }
        uint32_t g32 = (uint32_t)got; CHECK(g32 == ref, "sequential pattern kernel matches scalar reference");
        patctx r; pat_init(&r, b, ws, S, 64, 1, 9); uint64_t gr = pat_dispatch(&r, 1024);
        uint64_t st[8]; memcpy(st, r.st, 0); patctx r2; pat_init(&r2, b, ws, S, 64, 1, 9); memcpy(st, r2.st, sizeof st);
        uint32_t refr = 0; const uint64_t M = 6364136223846793005ull, C = 1442695040888963407ull;
        for (size_t i = 0; i < 1024; i += 8) { for (int k = 0; k < 8; k++) st[k] = st[k] * M + C; for (int k = 0; k < 8; k++) { size_t slot = (size_t)(((st[k] >> 32) * (ws / S)) >> 32); for (int w = 0; w < 16; w++) refr ^= ((uint32_t *)(b + slot * S))[w]; } }
        CHECK((uint32_t)gr == refr, "random pattern kernel matches scalar reference");
        free_map(b, ws);
    }
    {   // z=x*y and y=a*x+y against a scalar reference, all index patterns
        size_t mults[3] = {1, 16, 40503}; int ok = 1;
        for (int kernel = 0; kernel < 2; kernel++) for (int mi = 0; mi < 3; mi++) {
            size_t n = 4096; kctx c; kern_init(&c, n, kernel, mults[mi]);
            float *rx = malloc(n * 4), *ry = malloc(n * 4), *rz = malloc(n * 4);
            memcpy(rx, c.x, n * 4); memcpy(ry, c.y, n * 4); memset(rz, 0, n * 4);
            size_t total = 3 * n + 123;
            k_run(&c, 1000); k_run(&c, total - 1000);
            for (uint64_t i = 0; i < total; i++) { size_t j = (size_t)(i * mults[mi]) & (n - 1); volatile float t;
                if (kernel == 0) { t = rx[j] * ry[j]; rz[j] = t; } else { t = 0.5f * rx[j]; ry[j] = t + ry[j]; } }
            if (memcmp(ry, c.y, n * 4) || (kernel == 0 && memcmp(rz, c.z, n * 4))) ok = 0;
            free(rx); free(ry); free(rz); kern_free(&c);
        }
        CHECK(ok, "kernels z=x*y and y=a*x+y match scalar reference (unit, stride, scattered)");
    }
    {   // timer and frequency estimate
        uint64_t t0 = now_ns(), t1 = t0; while (t1 == t0) t1 = now_ns();
        CHECK(t1 - t0 < 100000, "clock advances in under 100 us steps (tick about 41.7 ns)");
        double f = freq_ghz(); char msg[96]; snprintf(msg, sizeof msg, "effective frequency estimate %.2f GHz in [2.0, 6.0]", f);
        CHECK(f > 2.0 && f < 6.0, msg);
    }
    CHECK(get_thread_qos() != 0, "thread QoS readable");
    fprintf(stderr, g_fail ? "SELFTEST FAILED (%d)\n" : "SELFTEST PASSED\n", g_fail);
}

// ---------------------------------------------------------------- main
int main(int argc, char **argv) {
    g_argc = argc; g_argv = argv;
    if (argc < 2) { fprintf(stderr, "usage: membench <cmd> [--key value]...\n"); return 1; }
    const char *cmd = argv[1];
    zva_init();
    g_round = arg_int("--round", 0);
    int q = qos_from_name(arg_str("--qos", "interactive"));
    set_thread_qos(q); g_qos_seen = get_thread_qos();
    if (!strcmp(cmd, "header")) { emit_header(); return 0; }
    if (strcmp(cmd, "ramp") && strcmp(cmd, "freq") && !arg_int("--no-warm", 0)) warm_spin(300);
    if (!strcmp(cmd, "freq")) { printf("%.4f\n", freq_ghz()); return 0; }
    if (!strcmp(cmd, "zva")) { printf("%zu\n", g_zva_bs); return 0; }
    if (!strcmp(cmd, "chase")) cmd_chase();
    else if (!strcmp(cmd, "tlb")) cmd_tlb();
    else if (!strcmp(cmd, "bw")) cmd_bw();
    else if (!strcmp(cmd, "pat")) cmd_pat();
    else if (!strcmp(cmd, "mlp")) cmd_mlp();
    else if (!strcmp(cmd, "loaded")) cmd_loaded();
    else if (!strcmp(cmd, "kern")) cmd_kern();
    else if (!strcmp(cmd, "dce")) cmd_dce();
    else if (!strcmp(cmd, "ramp")) cmd_ramp();
    else if (!strcmp(cmd, "hugetest")) cmd_hugetest();
    else if (!strcmp(cmd, "selftest")) { selftest(); return g_fail ? 1 : 0; }
    else { fprintf(stderr, "unknown command %s\n", cmd); return 1; }
    return 0;
}
