# Shared build configuration. Sourced by build.sh and others.
KERNELS="saxpy mul dot stencil saxpy_s1 saxpy_s2 saxpy_s4 saxpy_s8 saxpy_s16 saxpy_s24 saxpy_s32 saxpy_s48 gather triad"
DTYPES="f32 f64 u32"
BUILDS="scalar scalar_nounroll scalar_unroll8 auto native fastmath auto_norestrict auto_forcevec scalar_norestrict"
CC=${CC:-clang}
COMMON_FLAGS="-std=c11 -Wall -Wextra -Wno-unused-parameter"
build_flags() {
  case "$1" in
    scalar)          echo "-O3 -fno-vectorize -fno-slp-vectorize -ffp-contract=on" ;;
    scalar_nounroll) echo "-O3 -fno-vectorize -fno-slp-vectorize -fno-unroll-loops -ffp-contract=on" ;;
    scalar_unroll8)  echo "-O3 -fno-vectorize -fno-slp-vectorize -DFORCE_UNROLL -ffp-contract=on" ;;
    auto_norestrict) echo "-O3 -DNORESTRICT -ffp-contract=on" ;;
    auto_forcevec)  echo "-O3 -DFORCE_VEC -ffp-contract=on" ;;
    scalar_norestrict) echo "-O3 -fno-vectorize -fno-slp-vectorize -DNORESTRICT -ffp-contract=on" ;;
    auto)            echo "-O3 -ffp-contract=on" ;;
    native)          echo "-O3 -mcpu=native -ffp-contract=on" ;;
    fastmath)        echo "-O3 -ffast-math -ffp-contract=fast" ;;
    *) echo "unknown build $1" >&2; return 1 ;;
  esac
}

# Additional kernels built only for the combinations they are used with (memory-ceiling kernels: f32 only;
# dot-product decomposition: f32 and f64). Prints "kernel dtype build" lines.
EXTRA_MEM_KERNELS="read incr copy scale add saxpy_oop"
EXTRA_MEM_BUILDS="scalar_unroll8 auto"
EXTRA_DOT_KERNELS="dot_a1 dot_a4 dot_a8 dot_a16"
EXTRA_DOT_BUILDS="scalar auto"
extra_combos() {
  for k in $EXTRA_MEM_KERNELS; do for b in $EXTRA_MEM_BUILDS; do echo "$k f32 $b"; done; done
  for k in $EXTRA_DOT_KERNELS; do for d in f32 f64; do for b in $EXTRA_DOT_BUILDS; do echo "$k $d $b"; done; done; done
}
