#!/usr/bin/env python3

import csv
import math
import os
import sys


def load_first_row(path):
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        row = next(reader)
    out = {}
    for key, value in row.items():
        clean_key = key.strip()
        clean_value = value.strip()
        if clean_key == "iter":
            out[clean_key] = int(clean_value)
        else:
            out[clean_key] = float(clean_value)
    return out


def sidecar_path(summary_path, suffix):
    root, ext = os.path.splitext(summary_path)
    if ext:
        return root + suffix + ext
    return summary_path + suffix


def load_grouped_first_row(summary_path):
    paths = [
        summary_path,
        sidecar_path(summary_path, "_budget"),
        sidecar_path(summary_path, "_integrals"),
        sidecar_path(summary_path, "_extrema"),
    ]
    merged = {}
    for path in paths:
        row = load_first_row(path)
        for key, value in row.items():
            if key in ("time", "iter") and key in merged:
                if merged[key] != value:
                    fail(f"inconsistent {key} between grouped diagnostics in {path}")
                continue
            merged[key] = value
    return merged


def exact_reference():
    pi = math.pi
    re = 500.0
    gamma = 1.4
    mach = 0.5
    p0 = 1.0 / (gamma * mach * mach)
    t0 = p0
    return {
        "time": 0.0,
        "iter": 0,
        "kinetic_energy": 1.0 / 8.0,
        "internal_energy": 50.0 / 7.0,
        "total_energy": 407.0 / 56.0,
        "turbulent_mach": math.sqrt(1.0 / 48.0),
        "solenoidal_dissipation": 3.0 / (4.0 * re),
        "dilatational_dissipation": 0.0,
        "enstrophy": 3.0 * pi * pi / 8.0,
        "pressure_work": 0.0,
        "viscous_work": -3.0 / (4.0 * re),
        "viscous_dissipation": 3.0 / (4.0 * re),
        "ke_integral": 2.0,
        "internal_energy_integral": 400.0 / 7.0,
        "total_energy_integral": 407.0 / 7.0,
        "vorticity_integral": 6.0 * pi * pi,
        "weighted_vorticity_integral": 6.0 * pi * pi,
        "divergence_integral": 0.0,
        "weighted_divergence_integral": 0.0,
        "pressure_dilatation_integral": 0.0,
        "viscous_dissipation_integral": 6.0 * pi / re,
        "min_rho": (p0 - 3.0 / 8.0) / t0,
        "min_pressure": p0 - 3.0 / 8.0,
        "max_mach": 0.5,
        "max_abs_divu": 0.0,
    }


EXACT_TOLERANCES = {
    "time": 1.0e-14,
    "iter": 0,
    "kinetic_energy": 1.0e-4,
    "internal_energy": 2.0e-3,
    "total_energy": 2.0e-3,
    "turbulent_mach": 1.0e-3,
    "solenoidal_dissipation": 1.0e-6,
    "dilatational_dissipation": 1.0e-7,
    "enstrophy": 3.0e-4,
    "pressure_work": 1.0e-12,
    "viscous_work": 1.0e-6,
    "viscous_dissipation": 1.0e-6,
    "ke_integral": 2.0e-4,
    "internal_energy_integral": 2.0e-2,
    "total_energy_integral": 2.0e-2,
    "vorticity_integral": 3.0e-3,
    "weighted_vorticity_integral": 3.0e-3,
    "divergence_integral": 5.0e-4,
    "weighted_divergence_integral": 5.0e-4,
    "pressure_dilatation_integral": 1.0e-12,
    "viscous_dissipation_integral": 2.0e-4,
    "min_rho": 5.0e-3,
    "min_pressure": 1.0e-2,
    "max_mach": 1.0e-3,
    "max_abs_divu": 5.0e-2,
}


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def check_exact(path):
    got = load_grouped_first_row(path)
    ref = exact_reference()
    errors = []

    for key, expected in ref.items():
        actual = got[key]
        tol = EXACT_TOLERANCES[key]
        if key == "iter":
            if actual != expected:
                errors.append(f"{key}: got {actual}, expected {expected}")
            continue
        if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=tol):
            errors.append(f"{key}: got {actual:.16e}, expected {expected:.16e}, abs diff {abs(actual - expected):.3e}, tol {tol:.3e}")

    if errors:
        fail("\n".join(errors))


def check_compare(path_a, path_b):
    a = load_grouped_first_row(path_a)
    b = load_grouped_first_row(path_b)
    errors = []

    for key in a:
        va = a[key]
        vb = b[key]
        if key == "iter":
            if va != vb:
                errors.append(f"{key}: serial {va}, parallel {vb}")
            continue
        tol = 1.0e-10 * max(1.0, abs(va), abs(vb))
        if not math.isclose(va, vb, rel_tol=0.0, abs_tol=tol):
            errors.append(f"{key}: serial {va:.16e}, parallel {vb:.16e}, abs diff {abs(va - vb):.3e}, tol {tol:.3e}")

    if errors:
        fail("\n".join(errors))


def main(argv):
    if len(argv) < 3:
        fail("usage: check_tgv_diagnostics.py exact <csv> | compare <csv1> <csv2>")

    mode = argv[1]
    if mode == "exact" and len(argv) == 3:
        check_exact(argv[2])
        return
    if mode == "compare" and len(argv) == 4:
        check_compare(argv[2], argv[3])
        return

    fail("invalid arguments")


if __name__ == "__main__":
    main(sys.argv)
