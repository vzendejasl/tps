# Compressible TGV M0=0.5 `t=0` Diagnostic Reference

This note records the continuum `t=0` values implied by
[`input.compressible_tgv_m05.ini`](./input.compressible_tgv_m05.ini) and the
current implementation in [`src/M2ulPhyS.cpp`](../src/M2ulPhyS.cpp).

## Inputs used

- `rho0 = 1`
- `U0 = 1`
- `gamma = 1.4`
- `R = 1`
- `M0 = 0.5`
- `Re = 500`
- `L = 1/pi`
- domain `[-1,1]^3`, so `|Omega| = 8`

The code sets

- `p0 = rho0*U0^2/(gamma*M0^2) = 20/7`
- `T0 = p0/(rho0*R) = 20/7`
- `mu0 = rho0*U0*L/Re = 1/(500*pi)`

When `tgvUsePaperSutherland = True`, the transport model is normalized so that
`mu(T0) = mu0`. Since the initial condition uses `T = T0` everywhere, the code
has `mu(T)/mu0 = 1` at `t=0`.

## Initial condition

With `X = x/L`, `Y = y/L`, and `Z = z/L`, the code projects

- `u = sin(X) cos(Y) cos(Z)`
- `v = -cos(X) sin(Y) cos(Z)`
- `w = 0`
- `p = p0 + (1/16) [cos(2X) + cos(2Y)] [2 + cos(2Z)]`
- `rho = p/T0`

This field is exactly divergence free in the continuum:

- `div u = 0`

The maximum speed is `|u|_max = U0 = 1`, so the maximum Mach number is

- `M_max = U0 / sqrt(gamma*R*T0) = 0.5`

## Exact continuum `t=0` diagnostics

These are the exact values of the quantities written by
`writeTGVDiagnostics()` before any projection or quadrature error:

| Quantity | Exact value |
| --- | ---: |
| `kinetic_energy` | `1/8 = 1.2500000000000000e-01` |
| `solenoidal_dissipation` | `3/(4*Re) = 1.5000000000000000e-03` |
| `dilatational_dissipation` | `0` |
| `enstrophy` | `3*pi^2/8 = 3.7011016504085088e+00` |
| `pressure_work` | `0` |
| `viscous_work` | `-3/(4*Re) = -1.5000000000000000e-03` |
| `viscous_dissipation` | `3/(4*Re) = 1.5000000000000000e-03` |
| `raw_ke_integral` | `2.0000000000000000e+00` |
| `raw_vorticity_integral` | `6*pi^2 = 5.9217626406536141e+01` |
| `raw_weighted_vorticity_integral` | `6*pi^2 = 5.9217626406536141e+01` |
| `raw_divergence_integral` | `0` |
| `raw_weighted_divergence_integral` | `0` |
| `raw_pressure_dilatation_integral` | `0` |
| `raw_viscous_dissipation_integral` | `6*pi/Re = 3.7699111843077518e-02` |
| `min_pressure` | `p0 - 3/8 = 2.4821428571428572e+00` |
| `min_rho` | `(p0 - 3/8)/T0 = 8.6875000000000002e-01` |
| `max_mach` | `5.0000000000000000e-01` |
| `max_abs_divu` | `0` |

## Continuum vs. emitted CSV

The solver does not integrate the analytic field directly. It

1. projects the analytic state into the finite-element space,
2. reconstructs gradients from the projected field,
3. evaluates the diagnostics with numerical quadrature.

Because of that, the emitted `t=0` CSV row is only approximately equal to the
continuum values above. The regression test checks the emitted row against these
reference values with tolerances chosen to cover the current projection and
quadrature error on the provided mesh, and separately checks that serial and MPI
emit the same `t=0` row.

## Files changed for this work

The TGV implementation and diagnostics support added in this branch live in

- [`src/run_configuration.hpp`](../src/run_configuration.hpp)
- [`src/run_configuration.cpp`](../src/run_configuration.cpp)
- [`src/M2ulPhyS.hpp`](../src/M2ulPhyS.hpp)
- [`src/M2ulPhyS.cpp`](../src/M2ulPhyS.cpp)
- [`examples/input.compressible_tgv_m05.ini`](./input.compressible_tgv_m05.ini)

The `t=0` diagnostic reference and regression tests added here live in

- [`examples/COMPRESSIBLE_TGV_M05_T0_REFERENCE.md`](./COMPRESSIBLE_TGV_M05_T0_REFERENCE.md)
- [`test/inputs/input.compressible_tgv_m05.ini`](../test/inputs/input.compressible_tgv_m05.ini)
- [`test/check_tgv_diagnostics.py`](../test/check_tgv_diagnostics.py)
- [`test/compressible_tgv_diag.test`](../test/compressible_tgv_diag.test)
- [`test/Makefile.am`](../test/Makefile.am)
- [`test/Makefile.in`](../test/Makefile.in)

## What to keep for another machine

To reproduce the TGV case and its regression tests on another machine, keep the
source and test files listed above.

Do not keep generated output such as

- `build-macos/`
- `history.hist`
- `partition.4p.h5`
- `restart_tgv_m05_output_*.sol*.h5`
- `tgv_m05_output_*/`

Those files are test/build artifacts and will be regenerated locally.
