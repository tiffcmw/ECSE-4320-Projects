// Mechanism 2: fixed-work loops under QoS classes, with optional background load.
// One invocation = one configuration; prints one CSV row per (rep, worker thread).
// Args: --kind compute|mem  --threads N  --qos NAME  --qos_where inside|main_after
//       --bg_threads M --bg_qos NAME --bg_kind compute|mem
//       --chunks C --chunk_iters I --chunk_steps S --bytes B --reps R --warmups W --header
// Work per rep is fixed (C chunks); per-chunk times give the latency distribution.
// qos_where=main_after is the FLAWED design kept for the AI-resilience study:
// workers are created first and QoS is then applied to the *main* thread, so it
// does not reach the workers.
#include "chase_core.h"
#include <stdatomic.h>
#include <time.h>

typedef struct {
    int id, nthreads, reps, warmups, chunks;
    int qos;            // -1 = leave default
    int is_mem;
    uint64_t chunk_iters, chunk_steps;
    size_t bytes;
    char *buf;
    // results, per rep
    double *wall_ns, *cpu_ns, *p50_us, *p99_us, *max_us;
    int qos_seen;
} Worker;

static atomic_int bar_count, bar_gen;
static atomic_int stop_bg;

static void barrier(int n) {
    int gen = atomic_load(&bar_gen);
    if (atomic_fetch_add(&bar_count, 1) + 1 == n) {
        atomic_store(&bar_count, 0);
        atomic_fetch_add(&bar_gen, 1);
    } else {
        while (atomic_load(&bar_gen) == gen) { }
    }
}

static uint64_t cpu_now_ns(void) { return clock_gettime_nsec_np(CLOCK_THREAD_CPUTIME_ID); }

static uint64_t compute_chunk(uint64_t x, uint64_t iters) {
    for (uint64_t i = 0; i < iters; i++) x = x * 6364136223846793005ULL + 1442695040888963407ULL;
    return x;
}

static void *worker_main(void *arg) {
    Worker *w = arg;
    if (w->qos >= 0 && set_thread_qos(w->qos) != 0) fprintf(stderr, "qos set failed\n");
    w->qos_seen = get_thread_qos();
    void *p = w->buf;
    uint64_t x = 88172645463325252ULL + w->id;
    double *chunk_us = malloc(w->chunks * sizeof(double));
    for (int rep = -w->warmups; rep < w->reps; rep++) {
        barrier(w->nthreads);
        uint64_t t0 = now_ns(), c0 = cpu_now_ns(), prev = t0;
        for (int c = 0; c < w->chunks; c++) {
            if (w->is_mem) p = chase_run(p, w->chunk_steps);
            else x = compute_chunk(x, w->chunk_iters);
            uint64_t t = now_ns();
            chunk_us[c] = (double)(t - prev) / 1000.0;
            prev = t;
        }
        uint64_t t1 = now_ns(), c1 = cpu_now_ns();
        sink_u64(x); sink_ptr(p);
        if (rep >= 0) {
            w->wall_ns[rep] = (double)(t1 - t0);
            w->cpu_ns[rep] = (double)(c1 - c0);
            Stats s = compute_stats(chunk_us, w->chunks);
            w->p50_us[rep] = s.median;
            w->p99_us[rep] = quantile_sorted(chunk_us, w->chunks, 0.99);
            w->max_us[rep] = s.max;
        }
    }
    free(chunk_us);
    return NULL;
}

typedef struct { int qos, is_mem; size_t bytes; char *buf; } Spinner;
static void *spinner_main(void *arg) {
    Spinner *s = arg;
    set_thread_qos(s->qos);
    uint64_t x = 1;
    void *p = s->buf;
    while (!atomic_load_explicit(&stop_bg, memory_order_relaxed)) {
        if (s->is_mem) p = chase_run(p, 4096); else x = compute_chunk(x, 100000);
    }
    sink_u64(x); sink_ptr(p);
    return NULL;
}

static char *make_chase(size_t bytes, uint64_t seed) {
    char *b = map_bytes(bytes);
    if (!b || !chase_build(b, bytes, 128, CHASE_RANDOM, seed)) { fprintf(stderr, "chase alloc failed\n"); exit(2); }
    return b;
}

int main(int argc, char **argv) {
    const char *kind = arg_get(argc, argv, "--kind", "compute");
    int is_mem = !strcmp(kind, "mem");
    int nthreads = (int)arg_long(argc, argv, "--threads", 1);
    const char *qos_s = arg_get(argc, argv, "--qos", "none");
    const char *where = arg_get(argc, argv, "--qos_where", "inside");
    int bg_threads = (int)arg_long(argc, argv, "--bg_threads", 0);
    const char *bg_qos_s = arg_get(argc, argv, "--bg_qos", "background");
    int bg_mem = !strcmp(arg_get(argc, argv, "--bg_kind", "compute"), "mem");
    int chunks = (int)arg_long(argc, argv, "--chunks", 200);
    uint64_t chunk_iters = (uint64_t)arg_long(argc, argv, "--chunk_iters", 1000000);
    uint64_t chunk_steps = (uint64_t)arg_long(argc, argv, "--chunk_steps", 8000);
    size_t bytes = (size_t)arg_long(argc, argv, "--bytes", 256L << 20);
    int reps = (int)arg_long(argc, argv, "--reps", 5);
    int warmups = (int)arg_long(argc, argv, "--warmups", 1);
    int qos = qos_from_name(qos_s), bg_qos = qos_from_name(bg_qos_s);
    int inside = strcmp(where, "main_after") != 0;

    if (arg_flag(argc, argv, "--header"))
        printf("bench,kind,threads,qos_req,qos_where,bg_threads,bg_qos,bg_kind,rep,thread,qos_seen,chunks,"
               "work_units,wall_ms,cpu_ms,cpu_over_wall,throughput_munits_s,p50_chunk_us,p99_chunk_us,max_chunk_us\n");

    // Background spinners first (they run until the workers finish).
    pthread_t *bgt = calloc(bg_threads ? bg_threads : 1, sizeof(pthread_t));
    Spinner *sp = calloc(bg_threads ? bg_threads : 1, sizeof(Spinner));
    for (int i = 0; i < bg_threads; i++) {
        sp[i] = (Spinner){ bg_qos, bg_mem, 128L << 20, bg_mem ? make_chase(128L << 20, 777 + i) : NULL };
        pthread_create(&bgt[i], NULL, spinner_main, &sp[i]);
    }

    pthread_t *th = calloc(nthreads, sizeof(pthread_t));
    Worker *ws = calloc(nthreads, sizeof(Worker));
    for (int i = 0; i < nthreads; i++) {
        Worker *w = &ws[i];
        *w = (Worker){ .id = i, .nthreads = nthreads, .reps = reps, .warmups = warmups, .chunks = chunks,
                       .qos = inside ? qos : -1, .is_mem = is_mem, .chunk_iters = chunk_iters,
                       .chunk_steps = chunk_steps, .bytes = bytes };
        w->buf = is_mem ? make_chase(bytes, 42 + i) : NULL;
        w->wall_ns = calloc(reps, 8); w->cpu_ns = calloc(reps, 8);
        w->p50_us = calloc(reps, 8); w->p99_us = calloc(reps, 8); w->max_us = calloc(reps, 8);
        pthread_create(&th[i], NULL, worker_main, w);
    }
    if (!inside) set_thread_qos(qos);  // flawed: applied to main, which only waits
    for (int i = 0; i < nthreads; i++) pthread_join(th[i], NULL);
    atomic_store(&stop_bg, 1);
    for (int i = 0; i < bg_threads; i++) pthread_join(bgt[i], NULL);

    double units = is_mem ? (double)chunks * chunk_steps : (double)chunks * chunk_iters;
    for (int r = 0; r < reps; r++)
        for (int i = 0; i < nthreads; i++) {
            Worker *w = &ws[i];
            printf("qos,%s,%d,%s,%s,%d,%s,%s,%d,%d,%d,%d,%.0f,%.3f,%.3f,%.4f,%.3f,%.1f,%.1f,%.1f\n", kind, nthreads, qos_s,
                   where, bg_threads, bg_threads ? bg_qos_s : "none", bg_threads ? (bg_mem ? "mem" : "compute") : "none", r, i,
                   w->qos_seen, chunks, units, w->wall_ns[r] / 1e6, w->cpu_ns[r] / 1e6, w->cpu_ns[r] / w->wall_ns[r],
                   units / w->wall_ns[r] * 1e3, w->p50_us[r], w->p99_us[r], w->max_us[r]);
        }
    return 0;
}
