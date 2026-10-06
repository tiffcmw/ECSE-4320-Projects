// Pointer-chase latency benchmark (Mechanism 1, interaction E3a).
// One invocation = one configuration; prints one CSV row per repetition.
// Args: --bytes N --stride S --mode random|seq --reps R --warmups W --steps K
//       --qos interactive|initiated|default|utility|background|none --header
#include "chase_core.h"

int main(int argc, char **argv) {
    size_t bytes = (size_t)arg_long(argc, argv, "--bytes", 1 << 20);
    size_t stride = (size_t)arg_long(argc, argv, "--stride", 128);
    const char *mode_s = arg_get(argc, argv, "--mode", "random");
    ChaseMode mode = strcmp(mode_s, "seq") == 0 ? CHASE_SEQ : CHASE_RANDOM;
    int reps = (int)arg_long(argc, argv, "--reps", 5);
    int warmups = (int)arg_long(argc, argv, "--warmups", 2);
    uint64_t steps = (uint64_t)arg_long(argc, argv, "--steps", 1 << 23);
    const char *qos_s = arg_get(argc, argv, "--qos", "none");
    int qos = qos_from_name(qos_s);

    if (arg_flag(argc, argv, "--header"))
        printf("bench,mode,bytes,stride,nodes,qos_req,qos_actual,rep,steps,ns_per_load,minflt_timed,checksum\n");

    // QoS is set inside the thread that does the work, before any measurement.
    if (set_thread_qos(qos) != 0) { fprintf(stderr, "set qos failed\n"); return 2; }

    char *buf = map_bytes(bytes);
    if (!buf) { fprintf(stderr, "mmap failed\n"); return 2; }
    size_t n = chase_build(buf, bytes, stride, mode, 12345);
    if (!n) { fprintf(stderr, "build failed\n"); return 2; }
    if (!chase_verify(buf, stride, n)) { fprintf(stderr, "FATAL: chase is not a single full cycle\n"); return 3; }

    uint64_t cs = 0;
    // Warmups (excluded). The first also sizes `steps` so each timed region is >= 20 ms,
    // which is >> the 41.7 ns timer tick.
    void *p = buf;
    for (int w = 0; w < warmups; w++) {
        uint64_t a = now_ns();
        p = chase_run(p, steps);
        uint64_t el = now_ns() - a;
        if (w == 0 && el < 20000000ULL && steps < (1ULL << 28)) {
            double scale = 20000000.0 / (double)(el ? el : 1);
            steps = (uint64_t)(steps * (scale > 64 ? 64 : scale)) + 1;
            if (steps > (1ULL << 28)) steps = 1ULL << 28;
        }
    }
    for (int r = 0; r < reps; r++) {
        long f0 = minor_faults();
        uint64_t a = now_ns();
        p = chase_run(p, steps);
        uint64_t el = now_ns() - a;
        long f1 = minor_faults();
        sink_ptr(p);
        cs += (uint64_t)((char *)p - buf);
        printf("chase,%s,%zu,%zu,%zu,%s,%d,%d,%llu,%.4f,%ld,%llu\n", mode_s, bytes, stride, n, qos_s,
               get_thread_qos(), r, (unsigned long long)steps, (double)el / steps, f1 - f0,
               (unsigned long long)cs);
    }
    return 0;
}
