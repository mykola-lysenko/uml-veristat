#!/usr/bin/env python3
"""Fit a per-opcode-class expansion model over a jit_expansion report.

Model:  jited_insns - guard_insns - nop_insns  ≈  intercept + Σ cost_c · count_c

Guard and nop instructions are measured directly by the harness, so they are
subtracted out and the remaining native instructions are attributed to xlated
opcode classes by ordinary least squares over all measured programs (pure
python normal equations — the system is only ~12x12). The intercept absorbs
fixed prologue/epilogue overhead not already counted as nops.

Output: per-class fitted native-insns-per-BPF-insn, each class's share of
total native instructions, and model fit quality (R^2, mean abs error).

Usage:  scripts/jit_expansion_model.py .build/jit-expansion/<run>/report.json
"""

from __future__ import annotations

import json
import sys


def solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting."""
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            m[piv][col] = 1e-12  # degenerate class (all-zero counts)
        m[col], m[piv] = m[piv], m[col]
        for r in range(n):
            if r != col:
                f = m[r][col] / m[col][col]
                for c in range(col, n + 1):
                    m[r][c] -= f * m[col][c]
    return [m[i][n] / m[i][i] for i in range(n)]


def main() -> int:
    report = json.load(open(sys.argv[1]))
    progs = [p for p in report["programs"] if "ratio" in p and p.get("hist")]

    classes = sorted({c for p in progs for c in p["hist"]})
    cols = classes + ["intercept"]

    rows = []
    targets = []
    for p in progs:
        rows.append([p["hist"].get(c, 0) for c in classes] + [1.0])
        targets.append(p["jited_insns"] - p["guard_insns"] - p["nop_insns"]
                       - p.get("uml_overhead_insns", 0))

    n = len(cols)
    ata = [[sum(r[i] * r[j] for r in rows) for j in range(n)] for i in range(n)]
    atb = [sum(r[i] * t for r, t in zip(rows, targets)) for i in range(n)]
    coef = solve(ata, atb)

    fitted = [sum(r[i] * coef[i] for i in range(n)) for r in rows]
    resid = [t - f for t, f in zip(targets, fitted)]
    mean_t = sum(targets) / len(targets)
    ss_res = sum(e * e for e in resid)
    ss_tot = sum((t - mean_t) ** 2 for t in targets) or 1.0
    r2 = 1 - ss_res / ss_tot
    mae = sum(abs(e) for e in resid) / len(resid)

    total_jited = sum(p["jited_insns"] for p in progs)
    total_counts = {c: sum(p["hist"].get(c, 0) for p in progs) for c in classes}
    guard_total = sum(p["guard_insns"] for p in progs)
    nop_total = sum(p["nop_insns"] for p in progs)
    uml_total = sum(p.get("uml_overhead_insns", 0) for p in progs)

    print(f"programs: {len(progs)}   R^2: {r2:.4f}   MAE: {mae:.1f} insns/prog\n")
    print(f"{'class':<12}{'BPF insns':>12}{'native/BPF':>12}{'native insns':>14}{'share':>8}")
    attributed = []
    for i, c in enumerate(classes):
        native = coef[i] * total_counts[c]
        attributed.append((native, c, coef[i], total_counts[c]))
    for native, c, k, cnt in sorted(attributed, reverse=True):
        print(f"{c:<12}{cnt:>12}{k:>12.2f}{native:>14.0f}{native / total_jited:>8.1%}")
    print(f"{'(guards)':<12}{'':>12}{'':>12}{guard_total:>14}{guard_total / total_jited:>8.1%}")
    print(f"{'(nops)':<12}{'':>12}{'':>12}{nop_total:>14}{nop_total / total_jited:>8.1%}")
    print(f"{'(uml-only)':<12}{'':>12}{'':>12}{uml_total:>14}{uml_total / total_jited:>8.1%}")
    per_prog = coef[-1]
    print(f"{'(intercept)':<12}{'':>12}{per_prog:>12.2f}"
          f"{per_prog * len(progs):>14.0f}{per_prog * len(progs) / total_jited:>8.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
