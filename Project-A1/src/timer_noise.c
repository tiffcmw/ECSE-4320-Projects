// E0: timer resolution and overhead, and run-to-run noise floor of a fixed
// compute loop. Output: one CSV line per measurement.
//   kind,value,unit
#include "harness.h"

static uint64_t fixed_work(uint64_t iters) {
    // Dependent integer chain: cannot be vectorized or eliminated (result is sunk).
    uint64_t x = 88172645463325252ULL;
    for (uint64_t i = 0; i < iters; i++) x = x * 6364136223846793005ULL + 1442695040888963407ULL;
    return x;
}

int main(int argc, char **argv) {
    int reps = (int)arg_long(argc, argv, "--reps", 100);
    uint64_t iters = (uint64_t)arg_long(argc, argv, "--iters", 20000000);
    printf("kind,value,unit\n");

    // 1. Timer granularity: smallest nonzero delta between consecutive reads.
    uint64_t min_delta = UINT64_MAX;
    for (int i = 0; i < 100000; i++) {
        uint64_t a = now_ns(), b = now_ns();
        while (b == a) b = now_ns();
        if (b - a < min_delta) min_delta = b - a;
    }
    printf("timer_granularity,%llu,ns\n", (unsigned long long)min_delta);

    // 2. Timer overhead: average cost of one now_ns() call over a long loop.
    uint64_t t0 = now_ns(), acc = 0;
    const int N = 5000000;
    for (int i = 0; i < N; i++) acc += now_ns();
    uint64_t t1 = now_ns();
    sink_u64(acc);
    printf("timer_overhead,%.2f,ns_per_call\n", (double)(t1 - t0) / N);

    // 3. Noise floor: fixed work repeated; spread of wall time.
    double *w = malloc(reps * sizeof(double));
    for (int i = 0; i < 3; i++) sink_u64(fixed_work(iters));  // warmup
    for (int i = 0; i < reps; i++) {
        uint64_t a = now_ns();
        sink_u64(fixed_work(iters));
        w[i] = (double)(now_ns() - a);
    }
    for (int i = 0; i < reps; i++) printf("fixed_work_wall,%.0f,ns\n", w[i]);
    Stats s = compute_stats(w, reps);
    printf("fixed_work_summary_median,%.0f,ns\n", s.median);
    printf("fixed_work_summary_min,%.0f,ns\n", s.min);
    printf("fixed_work_summary_iqr_over_median,%.5f,ratio\n", (s.q3 - s.q1) / s.median);
    printf("fixed_work_ns_per_iter_median,%.4f,ns\n", s.median / iters);
    free(w);
    return 0;
}
