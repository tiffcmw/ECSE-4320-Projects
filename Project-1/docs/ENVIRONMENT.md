# Environment (captured 2026-10-06, Phase 0)

Raw output of the commands requested in the assignment. Re-captured per session by `scripts/capture_env.sh` (Phase 1).

## `uname -a`
```
Darwin tiffsmbp 25.5.0 Darwin Kernel Version 25.5.0: Tue Jun  9 22:28:34 PDT 2026; root:xnu-12377.121.10~1/RELEASE_ARM64_T6050 arm64

```

## `sw_vers`
```
ProductName:		macOS
ProductVersion:		26.5.2
BuildVersion:		25F84

```

## `sysctl -a | grep -E 'hw\.(model|ncpu|physicalcpu|perflevel|l1|l2|cachelinesize|pagesize|memsize)|machdep.cpu'`
```
hw.ncpu: 18
hw.memsize: 38654705664
hw.perflevel0.physicalcpu: 6
hw.perflevel0.physicalcpu_max: 6
hw.perflevel0.logicalcpu: 6
hw.perflevel0.logicalcpu_max: 6
hw.perflevel0.l1icachesize: 196608
hw.perflevel0.l1dcachesize: 131072
hw.perflevel0.l2cachesize: 16777216
hw.perflevel0.cpusperl2: 6
hw.perflevel0.name: Super
hw.perflevel1.physicalcpu: 12
hw.perflevel1.physicalcpu_max: 12
hw.perflevel1.logicalcpu: 12
hw.perflevel1.logicalcpu_max: 12
hw.perflevel1.l1icachesize: 131072
hw.perflevel1.l1dcachesize: 65536
hw.perflevel1.l2cachesize: 8388608
hw.perflevel1.cpusperl2: 6
hw.perflevel1.name: Performance
hw.physicalcpu: 18
hw.physicalcpu_max: 18
hw.pagesize: 16384
hw.pagesize32: 16384
hw.cachelinesize: 128
hw.l1icachesize: 131072
hw.l1dcachesize: 65536
hw.l2cachesize: 8388608
hw.memsize_usable: 37667586048
machdep.cpu.cores_per_package: 18
machdep.cpu.core_count: 18
machdep.cpu.logical_per_package: 18
machdep.cpu.thread_count: 18
machdep.cpu.brand_string: Apple M5 Max

```

## `clang --version`
```
Apple clang version 21.0.0 (clang-2100.1.1.101)
Target: arm64-apple-darwin25.5.0
Thread model: posix
InstalledDir: /Library/Developer/CommandLineTools/usr/bin

```

## `python3 --version`
```
Python 3.13.15

```

## `pmset -g batt`
```
Now drawing from 'AC Power'
 -InternalBattery-0 (id=23724131)	80%; AC attached; not charging present: true

```

## `pmset -g therm`
```
Note: No thermal warning level has been recorded
Note: No performance warning level has been recorded
Note: No CPU power status has been recorded

```

## Derived facts and decisions

- Chip: Apple M5 Max, 18 cores: 6 "Super" cores (perflevel0) and 12 "Performance" cores (perflevel1). The Super cores are the fastest tier. Naming differs from M1-M4 (P and E).
- Caches (sysctl): cache line 128 B. Super core: L1D 128 KiB, L2 16 MiB shared by 6 cores. Performance core: L1D 64 KiB, L2 8 MiB shared by 6 cores. The plain `hw.l1dcachesize` / `hw.l2cachesize` keys report the Performance tier values.
- System Level Cache (SLC) size is not exposed by sysctl. It will be inferred from the locality sweep and labelled as an inference.
- Memory: 36 GiB unified (`hw.memsize`). Page size 16 KiB.
- NEON: 128-bit, 4 x fp32, 2 x fp64, 4 x int32, FMA available. `-mcpu=native` resolves to `apple-m4` in this clang (checked with `-###`). The compiler does not list an apple-m5 CPU.
- SVE/SME: the chip reports FEAT_SME, SME2 (and `sme_max_svl_b = 64`, a 512-bit streaming vector length). SME needs streaming mode (`smstart`), has its own register file, and only runs in the shared SME unit, so it is not a drop-in SIMD path. It is out of scope; no SVE (non-streaming) is reported. No ASK needed because streaming mode is not trivially usable.
- Python 3.13.15 with numpy 2.5.2 and matplotlib 3.11.1. pandas is not installed and will not be installed; analysis uses numpy and the csv module.
- Power: AC attached, battery 80% not charging. Low Power Mode state is checked per session by `scripts/capture_env.sh` (`pmset -g`). `pmset -g therm` reports no warning levels recorded at capture time.
- Counters: no `perf`. `xctrace` exists at `/usr/bin/xctrace`; whether CPU Counters work will be tried with bounded effort in Phase 1 and the outcome reported plainly.
- Timer: `hw.tbfrequency` = 24 MHz; the harness will use `clock_gettime_nsec_np(CLOCK_UPTIME_RAW)` and measure its overhead.
