#pragma once

#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <node.h>

namespace genetic {
namespace detail {

static constexpr float MIN_VAL = 0.001f;

inline bool is_terminal(node::type t) {
  return t == node::type::variable || t == node::type::constant;
}

inline bool is_nonterminal(node::type t) { return !is_terminal(t); }

inline int arity(node::type t) {
  if (node::type::unary_begin <= t && t <= node::type::unary_end) {
    return 1;
  }
  if (node::type::binary_begin <= t && t <= node::type::binary_end) {
    return 2;
  }
  return 0;
}

inline float evaluate_function(node::type t, float in0, float in1) {
  auto abs_inval = fabsf(in0), abs_inval1 = fabsf(in1);
  // note: keep the case statements in alphabetical order under each category
  // of operators.
  switch (t) {
    // binary operators
    case node::type::add:
      return in0 + in1;
    case node::type::atan2:
      return atan2f(in0, in1);
    case node::type::div:
      return abs_inval1 < MIN_VAL ? 1.0f : (in0/in1);//fdividef(in0, in1);
    case node::type::fdim:
      return fdimf(in0, in1);
    case node::type::gt:
      return in0 > in1 ? 1.0f : 0.0f;
    case node::type::max:
      return fmaxf(in0, in1);
    case node::type::min:
      return fminf(in0, in1);
    case node::type::mul:
      return in0 * in1;
    case node::type::pow:
      return powf(in0, in1);
    case node::type::sub:
      return in0 - in1;
    // unary operators
    case node::type::abs:
      return abs_inval;
    case node::type::acos:
      return acosf(in0);
    case node::type::acosh:
      return acoshf(in0);
    case node::type::asin:
      return asinf(in0);
    case node::type::asinh:
      return asinhf(in0);
    case node::type::atan:
      return atanf(in0);
    case node::type::atanh:
      return atanhf(in0);
    case node::type::cbrt:
      return cbrtf(in0);
    case node::type::cos:
      return cosf(in0);
    case node::type::cosh:
      return coshf(in0);
    case node::type::cube:
      return in0 * in0 * in0;
    case node::type::exp:
      return expf(in0);
    case node::type::inv:
      return abs_inval < MIN_VAL ? 0.f : 1.f / in0;
    case node::type::log:
      return abs_inval < MIN_VAL ? 0.f : logf(abs_inval);
    case node::type::neg:
      return -in0;
    case node::type::rcbrt:
      return static_cast<float>(1.0) / cbrtf(in0);
    case node::type::rsqrt:
      return static_cast<float>(1.0) / sqrtf(abs_inval);
    case node::type::sin:
      return sinf(in0);
    case node::type::sinh:
      return sinhf(in0);
    case node::type::sq:
      return in0 * in0;
    case node::type::sqrt:
      return sqrtf(abs_inval);
    case node::type::tan:
      return tanf(in0);
    case node::type::tanh:
      return tanhf(in0);
    // shouldn't reach here!
    default:
      return 0.f;
  };
}

} // namespace detail
} // namespace genetic
