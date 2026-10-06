// Sanity and correctness checks. Exit code 0 = all pass.
#include "../src/chase_core.h"
#include <assert.h>

static int fails = 0;
#define CHECK(c, msg) do { if (!(c)) { printf("FAIL: %s\n", msg); fails++; } else printf("ok:   %s\n", msg); } while (0)

int main(void) {
    // 1. Random chase is a single full cycle for several sizes/strides/seeds.
    size_t sizes[] = { 4096, 65536, 1 << 20, 16 << 20 };
    size_t strides[] = { 128, 16384 };
    for (int si = 0; si < 4; si++)
        for (int st = 0; st < 2; st++) {
            if (sizes[si] / strides[st] < 2) continue;
            char *b = map_bytes(sizes[si]);
            size_t n = chase_build(b, sizes[si], strides[st], CHASE_RANDOM, 1 + si * 7 + st);
            char m[96]; snprintf(m, sizeof m, "random single cycle bytes=%zu stride=%zu n=%zu", sizes[si], strides[st], n);
            CHECK(n > 0 && chase_verify(b, strides[st], n), m);
            munmap(b, sizes[si]);
        }

    // 2. Sequential chase is also a single cycle.
    {
        char *b = map_bytes(1 << 20);
        size_t n = chase_build(b, 1 << 20, 128, CHASE_SEQ, 0);
        CHECK(chase_verify(b, 128, n), "seq single cycle");
        munmap(b, 1 << 20);
    }

    // 3. The verifier rejects a broken permutation (two disjoint cycles).
    {
        char *b = map_bytes(65536);
        size_t n = chase_build(b, 65536, 128, CHASE_SEQ, 0);
        *(void **)(b + (n / 2 - 1) * 128) = b;  // short-circuits back to node 0
        CHECK(!chase_verify(b, 128, n), "verifier rejects short cycle");
        munmap(b, 65536);
    }

    // 4. Traversal returns to start after exactly n steps (checksum known-answer).
    {
        char *b = map_bytes(1 << 20);
        size_t n = chase_build(b, 1 << 20, 128, CHASE_RANDOM, 99);
        CHECK(chase_run(b, n) == b, "n steps returns to start");
        CHECK(n < 2 || chase_run(b, n - 1) != b, "n-1 steps does not return to start");
        munmap(b, 1 << 20);
    }

    // 5. Stats: known answers.
    {
        double v[5] = { 5, 1, 3, 2, 4 };
        Stats s = compute_stats(v, 5);
        CHECK(s.min == 1 && s.max == 5 && s.median == 3 && s.q1 == 2 && s.q3 == 4, "stats median/IQR known answer");
    }

    // 6. Clock monotonic and non-trivially advancing.
    {
        uint64_t a = now_ns(), b = now_ns();
        CHECK(b >= a, "clock monotonic");
        volatile uint64_t x = 0; uint64_t t0 = now_ns();
        for (int i = 0; i < 2000000; i++) x += i;
        CHECK(now_ns() > t0, "clock advances over work");
    }

    // 7. QoS round trip inside the calling thread.
    {
        CHECK(set_thread_qos(QOS_CLASS_UTILITY) == 0 && get_thread_qos() == QOS_CLASS_UTILITY, "qos set/get utility");
        CHECK(set_thread_qos(QOS_CLASS_USER_INTERACTIVE) == 0 && get_thread_qos() == QOS_CLASS_USER_INTERACTIVE, "qos set/get interactive");
    }

    printf(fails ? "%d FAILED\n" : "all tests passed\n", fails);
    return fails != 0;
}
