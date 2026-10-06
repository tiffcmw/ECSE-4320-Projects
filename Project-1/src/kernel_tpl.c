/* One kernel x dtype x build per translation unit. Instantiated by scripts/build.sh with
 *   -DKERN=<saxpy|mul|dot|stencil> -DDT=<f32|f64|u32> -DBUILD=<build name>
 * Uniform ABI so the harness never needs the element type:
 *   double fn(size_t n, double a, const void *x, void *y, void *z)
 *   saxpy:   y[i] = a*x[i] + y[i]
 *   mul:     z[i] = x[i]*y[i]
 *   dot:     return sum x[i]*y[i]  (accumulated in the element type)
 *   stencil: y[i] = .25*x[i-1] + .5*x[i] + .25*x[i+1], i = 1..n-2 (x != y)
 * u32 uses wrap-around integer arithmetic (stencil weights are shifts: x>>2 etc. are not
 * used; the integer stencil uses weights 1,2,1 without normalization). */
#include <stddef.h>
#include <stdint.h>

#define CAT_(a, b) a##b
#define CAT(a, b) CAT_(a, b)
#define K_saxpy 0
#define K_mul 1
#define K_dot 2
#define K_stencil 3
#define T_f32 float
#define T_f64 double
#define T_u32 uint32_t
#define TY CAT(T_, DT)
#define KID CAT(K_, KERN)
#define FNAME CAT(CAT(CAT(CAT(CAT(kern_, KERN), _), DT), _), BUILD)

#ifdef NORESTRICT
#define RS
#else
#define RS restrict
#endif

#ifdef FORCE_UNROLL
#define LP _Pragma("clang loop unroll_count(8)")
#else
#define LP
#endif

#define IS_U32 (CAT(U_, DT) == 1)
#define U_f32 0
#define U_f64 0
#define U_u32 1

/* The loop lives in a function whose parameters carry `restrict`: LLVM only derives noalias from restrict on
 * parameters (not on locals), so the main variants need it here. always_inline keeps the noalias scopes. */
static inline __attribute__((always_inline)) double body(size_t n, TY a, const TY *RS x, TY *RS y, TY *RS z) {
#if KID == 0
  LP for (size_t i = 0; i < n; i++) y[i] = a * x[i] + y[i];
  return 0.0;
#elif KID == 1
  LP for (size_t i = 0; i < n; i++) z[i] = x[i] * y[i];
  return 0.0;
#elif KID == 2
  TY s = 0;
  LP for (size_t i = 0; i < n; i++) s += x[i] * y[i];
  return (double)s;
#else
#if IS_U32
  LP for (size_t i = 1; i + 1 < n; i++) y[i] = x[i - 1] + 2u * x[i] + x[i + 1];
#else
  LP for (size_t i = 1; i + 1 < n; i++) y[i] = (TY)0.25 * x[i - 1] + (TY)0.5 * x[i] + (TY)0.25 * x[i + 1];
#endif
  return 0.0;
#endif
}

__attribute__((noinline)) double FNAME(size_t n, double a, const void *xv, void *yv, void *zv) {
  return body(n, (TY)a, (const TY *)xv, (TY *)yv, (TY *)zv);
}
