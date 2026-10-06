# Environment

Captured in Phase 0 (2026-10-06) by running the commands listed below. Raw values are copied verbatim; interpretation is marked as such.

## Hardware

| Item | Value | Source |
|---|---|---|
| Machine | MacBook Pro, `Mac17,6` | `sysctl hw.model`, `system_profiler` |
| Chip | Apple M5 Max | `machdep.cpu.brand_string` |
| Cores | 18 total: 6 "Super" + 12 "Performance". No efficiency cores, no SMT. | `hw.perflevel*`, `system_profiler` |
| Memory | 36 GB unified (`hw.memsize` = 38654705664) | `sysctl` |
| Page size | 16 KB (`hw.pagesize` = 16384) | `sysctl` |
| Cache line | 128 B (`hw.cachelinesize`) | `sysctl` |
| Timebase | 24 MHz (`hw.tbfrequency`) so `mach_absolute_time` tick is about 41.7 ns | `sysctl` |

### Per-tier cache sizes (from `sysctl hw.perflevel*`)

| Tier | Name | Cores | L1I | L1D | L2 | Cores per L2 |
|---|---|---|---|---|---|---|
| perflevel0 | Super | 6 | 192 KB | 128 KB | 16 MB | 6 |
| perflevel1 | Performance | 12 | 128 KB | 64 KB | 8 MB | 6 |

Notes (interpretation):
- The assignment text assumed performance + efficiency cores. This chip has two high-performance tiers instead. The user confirmed (Phase 0) that the core-type interaction is reframed as **Super vs Performance**.
- The system-level-cache (SLC / L3) size is not exposed by sysctl. `hw.cachesize` index 0 (3307847680) is not a cache size. SLC capacity will be inferred from the latency-vs-working-set curve and labeled as inferred.
- The default `hw.l1dcachesize` (65536) and `hw.l2cachesize` (8388608) describe perflevel1 (Performance), not Super.

## Software

| Item | Value |
|---|---|
| OS | macOS 26.5.2 (build 25F84) |
| Kernel | `Darwin tiffsmbp 25.5.0 ... xnu-12377.121.10~1/RELEASE_ARM64_T6050 arm64` |
| Compiler | Apple clang 21.0.0 (clang-2100.1.1.101), target arm64-apple-darwin25.5.0 |
| Python | 3.13.15, numpy 2.5.2, matplotlib 3.11.1 (pandas is not installed and is not used) |
| Tools present | `/usr/bin/powermetrics` (needs sudo), `/usr/bin/xctrace` shim (`xcrun --find xctrace` fails, so Instruments counters are unverified), `taskpolicy`, `caffeinate` |

## Power and thermal at start

- `pmset -g batt`: "Now drawing from 'AC Power'", battery 80%, AC attached, not charging.
- `pmset -g | grep powermode`: `powermode 0` (Low Power Mode off).
- `pmset -g therm`: "No thermal warning level has been recorded", "No performance warning level has been recorded", "No CPU power status has been recorded".

## Run protocol

Every benchmark run script will: run under `caffeinate -dimsu`, record `pmset -g therm` and `pmset -g batt` before and after, store the thermal text in the raw CSV, flag runs whose thermal state changed or reported a warning, randomize the order of configurations, and exclude warmup repetitions. See `docs/METHODOLOGY.md` (written in Phase 1).

## Capabilities and limits on this platform

| Feature | Status |
|---|---|
| Thread-to-core pinning | Not supported. Affinity tags are hints only. Placement is steered with QoS classes and verified empirically; where it is only inferred, the report says so. |
| `taskset`, `numactl`, cgroups, `perf`, hugetlbfs, THP | Not available on macOS. Not emulated. |
| NUMA | None (unified memory). |
| PMU counters | Not directly available. Candidates: `powermetrics` (sudo, to be approved by the user), Instruments via `xctrace` (to be tested in Phase 1). Fallback: latency-vs-working-set curves, `getrusage` page faults, `vm_stat`, timing signatures. |

## Commands run

```
uname -a; sw_vers
sysctl -a | grep -E "hw\.(model|ncpu|physicalcpu|perflevel|l1|l2|cachelinesize|pagesize|memsize)"
sysctl -n hw.model machdep.cpu.brand_string; sysctl hw.cacheconfig hw.cachesize hw.l3cachesize hw.tbfrequency
clang --version; python3 --version
pmset -g therm; pmset -g batt; pmset -g
system_profiler SPHardwareDataType
```
