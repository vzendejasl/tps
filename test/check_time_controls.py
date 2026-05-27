#!/usr/bin/env python3

import csv
import math
import os
import re
import sys


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def sidecar_path(summary_path, suffix):
    root, ext = os.path.splitext(summary_path)
    if ext:
        return root + suffix + ext
    return summary_path + suffix


def load_grouped_rows(summary_path):
    paths = [
        summary_path,
        sidecar_path(summary_path, "_budget"),
        sidecar_path(summary_path, "_integrals"),
        sidecar_path(summary_path, "_extrema"),
    ]

    rows = None
    for path in paths:
        with open(path, newline="") as handle:
            reader = csv.DictReader(handle)
            file_rows = []
            for row in reader:
                clean = {}
                for key, value in row.items():
                    key = key.strip()
                    value = value.strip()
                    if key == "iter":
                        clean[key] = int(value)
                    else:
                        clean[key] = float(value)
                file_rows.append(clean)

        if rows is None:
            rows = file_rows
            continue

        if len(rows) != len(file_rows):
            fail(f"row count mismatch between grouped diagnostics in {path}")

        for i, row in enumerate(file_rows):
            if rows[i]["time"] != row["time"] or rows[i]["iter"] != row["iter"]:
                fail(f"time/iter mismatch in grouped diagnostics row {i} from {path}")
            rows[i].update({k: v for k, v in row.items() if k not in ("time", "iter")})

    return rows


def check_final(summary_path, expected_time, expected_iter, tol):
    rows = load_grouped_rows(summary_path)
    final = rows[-1]
    if final["iter"] != expected_iter:
        fail(f"final iter mismatch: got {final['iter']}, expected {expected_iter}")
    if not math.isclose(final["time"], expected_time, rel_tol=0.0, abs_tol=tol):
        fail(
            f"final time mismatch: got {final['time']:.16e}, expected {expected_time:.16e}, "
            f"abs diff {abs(final['time'] - expected_time):.3e}, tol {tol:.3e}"
        )


def check_roots(outdir, expected_cycles):
    actual = []
    pattern = re.compile(r"visit_(\d+)\.mfem_root$")
    for name in sorted(os.listdir(outdir)):
        match = pattern.match(name)
        if match:
            actual.append(int(match.group(1)))

    if actual != expected_cycles:
        fail(f"visit root cycles mismatch: got {actual}, expected {expected_cycles}")


def check_compare_last(summary_a, summary_b):
    a = load_grouped_rows(summary_a)[-1]
    b = load_grouped_rows(summary_b)[-1]

    errors = []
    for key in a:
        va = a[key]
        vb = b[key]
        if key == "iter":
            if va != vb:
                errors.append(f"{key}: {va} != {vb}")
            continue
        tol = 1.0e-10 * max(1.0, abs(va), abs(vb))
        if not math.isclose(va, vb, rel_tol=0.0, abs_tol=tol):
            errors.append(f"{key}: {va:.16e} != {vb:.16e} (tol {tol:.3e})")

    if errors:
        fail("\n".join(errors))


def main(argv):
    if len(argv) < 2:
        fail("usage: check_time_controls.py <final|roots|compare-last> ...")

    mode = argv[1]
    if mode == "final" and len(argv) == 6:
        check_final(argv[2], float(argv[3]), int(argv[4]), float(argv[5]))
        return
    if mode == "roots" and len(argv) == 4:
        expected = [int(x) for x in argv[3].split(",") if x]
        check_roots(argv[2], expected)
        return
    if mode == "compare-last" and len(argv) == 4:
        check_compare_last(argv[2], argv[3])
        return

    fail("invalid arguments")


if __name__ == "__main__":
    main(sys.argv)
