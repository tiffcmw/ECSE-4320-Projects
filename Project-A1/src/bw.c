// Bandwidth kernels (Mechanism 1, cross-check, interaction E3b).
// One invocation = one configuration; prints one CSV row per repetition.
// Args: --kernel read_seq|read_stride|read_rand|triad --bytes N --stride_lines L
//       --reps R --warmups W --qos NAME --header
// GB/s = decimal GB per second. read_stride/read_rand touch one 8 B word per
// 128 B line and are reported as line traffic (128 B per access).
#include "harness.h"

static uint64_t read_seq(const uint64_t *a, size_t n) {
    uint64_t s0 = 0, s1 = 0, s2 = 0, s3 = 0, s4 = 0, s5 = 0, s6 = 0, s7 = 0;
    for (size_t i = 0; i + 8 <= n; i += 8) {
        s0 += a[i]; s1 += a[i + 1]; s2 += a[i + 2]; s3 += a[i + 3];
        s4 += a[i + 4]; s5 += a[i + 5]; s6 += a[i + 6]; s7 += a[i + 7];
    }
    return s0 + s1 + s2 + s3 + s4 + s5 + s6 + s7;
}

// One load per (stride_lines * 16) words (16 words = one 128 B line).
static uint64_t read_stride(const uint64_t *a, size_t n, size_t step_words) {
    uint64_t s0 = 0, s1 = 0, s2 = 0, s3 = 0;
    size_t i = 0;
    for (; i + 4 * step_words <= n; i += 4 * step_words) {
        s0 += a[i]; s1 += a[i + step_words]; s2 += a[i + 2 * step_words]; s3 += a[i + 3 * step_words];
    }
    return s0 + s1 + s2 + s3;
}

// Independent loads at pseudo-random lines. Addresses do not depend on loaded
// data, so the core can overlap misses (bandwidth, not latency).
static uint64_t read_rand(const uint64_t *a, size_t nlines, uint64_t accesses, Rng *r) {
    uint64_t s = 0;
    for (uint64_t i = 0; i < accesses; i++) s += a[rng_below(r, nlines) * 16];
    return s;
}

static void triad(double *restrict a, const double *restrict b, const double *restrict c, size_t n, double k) {
    for (size_t i = 0; i < n; i++) a[i] = b[i] + k * c[i];
}

int main(int argc, char **argv) {
    const char *kernel = arg_get(argc, argv, "--kernel", "read_seq");
    size_t bytes = (size_t)arg_long(argc, argv, "--bytes", 1 << 24);
    size_t stride_lines = (size_t)arg_long(argc, argv, "--stride_lines", 2);
    int reps = (int)arg_long(argc, argv, "--reps", 5);
    int warmups = (int)arg_long(argc, argv, "--warmups", 2);
    const char *qos_s = arg_get(argc, argv, "--qos", "none");
    if (arg_flag(argc, argv, "--header"))
        printf("bench,kernel,bytes,stride_lines,qos_req,qos_actual,rep,passes,gbps,minflt_timed,checksum\n");
    if (set_thread_qos(qos_from_name(qos_s)) != 0) { fprintf(stderr, "set qos failed\n"); return 2; }

    int is_triad = !strcmp(kernel, "triad");
    uint8_t *buf = map_bytes(bytes);
    if (!buf) { fprintf(stderr, "mmap failed\n"); return 2; }
    memset(buf, 1, bytes);  // first touch every page (and nonzero data)
    size_t words = bytes / 8, nlines = bytes / 128;
    size_t tn = bytes / 3 / 8;  // triad: three arrays of tn doubles
    double *ta = (double *)buf, *tb = ta + tn, *tc = tb + tn;
    if (is_triad) for (size_t i = 0; i < tn; i++) { ta[i] = 0; tb[i] = 1.0; tc[i] = 2.0; }
    Rng rng = { 88172645463325252ULL };

    // Bytes of traffic per pass.
    double bytes_per_pass;
    if (!strcmp(kernel, "read_seq")) bytes_per_pass = (double)words * 8;
    else if (!strcmp(kernel, "read_stride")) bytes_per_pass = (double)(words / (stride_lines * 16)) * 128;
    else if (!strcmp(kernel, "read_rand")) bytes_per_pass = (double)nlines * 128;
    else if (is_triad) bytes_per_pass = (double)tn * 24;  // STREAM convention: 2 reads + 1 write
    else { fprintf(stderr, "unknown kernel\n"); return 2; }

    uint64_t cs = 0, passes = 1;
#define ONE_PASS() do { \
        if (!strcmp(kernel, "read_seq")) cs += read_seq((const uint64_t *)buf, words); \
        else if (!strcmp(kernel, "read_stride")) cs += read_stride((const uint64_t *)buf, words, stride_lines * 16); \
        else if (!strcmp(kernel, "read_rand")) cs += read_rand((const uint64_t *)buf, nlines, nlines, &rng); \
        else { triad(ta, tb, tc, tn, 3.0); cs += (uint64_t)ta[tn / 2]; } } while (0)

    for (int w = 0; w < warmups; w++) {
        uint64_t a = now_ns();
        for (uint64_t k = 0; k < passes; k++) ONE_PASS();
        uint64_t el = now_ns() - a;
        if (w == 0 && el < 25000000ULL) passes = (uint64_t)(25000000.0 / (el ? el : 1)) + 1;  // timed region >= 25 ms
    }
    for (int r = 0; r < reps; r++) {
        long f0 = minor_faults();
        uint64_t a = now_ns();
        for (uint64_t k = 0; k < passes; k++) ONE_PASS();
        uint64_t el = now_ns() - a;
        long f1 = minor_faults();
        sink_u64(cs);
        printf("bw,%s,%zu,%zu,%s,%d,%d,%llu,%.3f,%ld,%llu\n", kernel, bytes, stride_lines, qos_s, get_thread_qos(),
               r, (unsigned long long)passes, bytes_per_pass * passes / (double)el, f1 - f0, (unsigned long long)cs);
    }
    return 0;
}
