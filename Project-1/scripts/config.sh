# Shared build configuration. Sourced by build.sh and others.
KERNELS="saxpy mul dot stencil"
DTYPES="f32 f64 u32"
BUILDS="scalar scalar_nounroll scalar_unroll8 auto native fastmath"
CC=${CC:-clang}
COMMON_FLAGS="-std=c11 -Wall -Wextra -Wno-unused-parameter"
build_flags() {
  case "$1" in
    scalar)          echo "-O3 -fno-vectorize -fno-slp-vectorize -ffp-contract=on" ;;
    scalar_nounroll) echo "-O3 -fno-vectorize -fno-slp-vectorize -fno-unroll-loops -ffp-contract=on" ;;
    scalar_unroll8)  echo "-O3 -fno-vectorize -fno-slp-vectorize -DFORCE_UNROLL -ffp-contract=on" ;;
    auto)            echo "-O3 -ffp-contract=on" ;;
    native)          echo "-O3 -mcpu=native -ffp-contract=on" ;;
    fastmath)        echo "-O3 -ffast-math -ffp-contract=fast" ;;
    *) echo "unknown build $1" >&2; return 1 ;;
  esac
}
