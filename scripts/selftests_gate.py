#!/usr/bin/env python3
"""Selftests regression gate: run the full test_progs sweep and compare it
against the committed baseline (docs/selftests-ci-gate.md).

Exit 0 = no coverage regression. Exit 1 = regression or run tripwire (chunk
timeout / NORESULT — the historical guest-hang signals, always fatal).
Markdown verdict goes to stdout; sweep progress goes to stderr so stdout can
be redirected into $GITHUB_STEP_SUMMARY.

Typical use:
  scripts/selftests_gate.py                     # build tree present: run + compare
  scripts/selftests_gate.py --summary S.json    # compare an existing run (no retry)
  scripts/selftests_gate.py --write-baseline    # run, then ratchet the baseline
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_test_chunks as rtc  # noqa: E402

BASELINE_DIR = ROOT / "reports" / "selftests-baseline"
CURRENT_PTR = BASELINE_DIR / "CURRENT"
FLAKY_DEFAULT = BASELINE_DIR / "FLAKY"
PIN_PATH = ROOT / "bpf-next-commit"
PIN_IN_NAME_RE = re.compile(r"(?<![0-9a-f])[0-9a-f]{7,40}(?![0-9a-f])")

REGRESSED = ("FAIL", "SKIP", "NORESULT")


def read_flaky(path: pathlib.Path) -> set[str]:
    if not path.exists():
        return set()
    names = set()
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            names.add(line)
    return names


def resolve_baseline(arg: str | None) -> pathlib.Path:
    if arg:
        return pathlib.Path(arg)
    if not CURRENT_PTR.exists():
        sys.exit(f"error: {CURRENT_PTR} not found and no --baseline given")
    name = CURRENT_PTR.read_text().strip()
    return BASELINE_DIR / name


def check_pin(baseline: pathlib.Path) -> str:
    """The baseline must belong to the pinned bpf-next commit: a pin bump
    without a fresh baseline in the same change must fail loudly."""
    pin = PIN_PATH.read_text().strip()
    m = PIN_IN_NAME_RE.search(baseline.name)
    if not m:
        sys.exit(
            f"error: cannot find a commit prefix in baseline name "
            f"'{baseline.name}' (expected <date>-<pin-prefix>[-tag].json)"
        )
    prefix = m.group(0)
    if not pin.startswith(prefix):
        sys.exit(
            f"error: baseline {baseline.name} is for pin {prefix}, but "
            f"bpf-next-commit is {pin[:12]}…\n"
            f"Bumping the pin requires committing a fresh baseline "
            f"(scripts/selftests_gate.py --write-baseline) in the same PR."
        )
    return prefix


def run_sweep(out_dir: pathlib.Path, jobs: int) -> dict:
    cmd = [sys.executable, str(ROOT / "scripts" / "run_test_chunks.py"),
           "--out-dir", str(out_dir), "--jobs", str(jobs)]
    print(f"gate: running full sweep: {' '.join(cmd)}", file=sys.stderr, flush=True)
    proc = subprocess.run(cmd, stdout=sys.stderr, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        sys.exit(f"error: run_test_chunks.py exited {proc.returncode}")
    return json.loads((out_dir / "summary.json").read_text())


def retry_standalone(tests: list[str], out_dir: pathlib.Path) -> dict[str, str]:
    """One extra chunk with only the regressed tests. A pass here demotes the
    regression to a reported flake."""
    log_path = out_dir / "retry.log"
    print(f"gate: retrying {len(tests)} regressed test(s) standalone: "
          f"{','.join(tests)}", file=sys.stderr, flush=True)
    rtc.run_chunk(ROOT / "uml-test-progs", tests, log_path,
                  watchdog=120, timeout=900)
    results, _, _ = rtc.parse_log(log_path)
    return {t: results.get(t, "NORESULT") for t in tests}


def compare(base: dict[str, str], run: dict[str, str], flaky: set[str]) -> dict:
    buckets: dict[str, list] = {
        "regressions": [],   # (name, base_status, run_status)
        "missing": [],       # in baseline, absent from run entirely
        "new_passes": [],    # (name, base_status)
        "neutral": [],       # FAIL <-> SKIP drift, (name, base, run)
        "new_tests": [],     # (name, run_status)
        "flaky_activity": [],  # (name, base, run) — flaky-listed, never fatal
    }
    for name, b in sorted(base.items()):
        r = run.get(name)
        if name in flaky:
            if r != b:
                buckets["flaky_activity"].append((name, b, r or "missing"))
            continue
        if r is None:
            buckets["missing"].append((name, b))
        elif b == "OK" and r in REGRESSED:
            buckets["regressions"].append((name, b, r))
        elif b in REGRESSED and r == "OK":
            buckets["new_passes"].append((name, b))
        elif b != r:
            buckets["neutral"].append((name, b, r))
    for name, r in sorted(run.items()):
        if name not in base:
            buckets["new_tests"].append((name, r))
    return buckets


def fmt_counts(counts: dict) -> str:
    order = ("OK", "FAIL", "SKIP", "NORESULT")
    parts = [f"{k} {counts[k]}" for k in order if counts.get(k)]
    return " / ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", help="baseline JSON (default: CURRENT pointer)")
    ap.add_argument("--summary", help="compare this existing summary.json "
                    "instead of running the sweep (implies --no-retry)")
    ap.add_argument("--out-dir", help="sweep output dir (default: timestamped "
                    "under .build/test-logs/)")
    ap.add_argument("--jobs", type=int, default=1,
                    help="concurrent sweep chunks (passed to run_test_chunks)")
    ap.add_argument("--no-retry", action="store_true",
                    help="fail regressions immediately, no standalone retry")
    ap.add_argument("--flaky", default=str(FLAKY_DEFAULT),
                    help="flaky-list file (default: %(default)s)")
    ap.add_argument("--write-baseline", action="store_true",
                    help="on a clean run, save it as the new baseline and "
                    "update CURRENT (review the diff before committing)")
    args = ap.parse_args()

    rtc.join_session_keyring()

    baseline_path = resolve_baseline(args.baseline)
    if not baseline_path.exists():
        sys.exit(f"error: baseline {baseline_path} not found")
    pin_prefix = check_pin(baseline_path)
    baseline = json.loads(baseline_path.read_text())
    flaky = read_flaky(pathlib.Path(args.flaky))

    out_dir = pathlib.Path(
        args.out_dir or ROOT / ".build" / "test-logs"
        / f"gate-{time.strftime('%Y%m%d-%H%M%S')}"
    )
    if args.summary:
        summary = json.loads(pathlib.Path(args.summary).read_text())
    else:
        out_dir.mkdir(parents=True, exist_ok=True)
        summary = run_sweep(out_dir, args.jobs)

    timeouts = [c["index"] for c in summary.get("chunks", []) if c.get("timed_out")]
    noresult = sorted(n for n, s in summary["tests"].items() if s == "NORESULT")
    tripwire = bool(timeouts or noresult)

    buckets = compare(baseline["tests"], summary["tests"], flaky)

    retried: dict[str, str] = {}
    hard = list(buckets["regressions"])
    if hard and not tripwire and not args.no_retry and not args.summary:
        retried = retry_standalone([n for n, _, _ in hard], out_dir)
        hard = [(n, b, r) for n, b, r in hard if retried.get(n) != "OK"]
    soft = [(n, b, r) for n, b, r in buckets["regressions"]
            if (n, b, r) not in hard]

    failed = tripwire or bool(hard) or bool(buckets["missing"])

    # ---- markdown verdict on stdout ----
    print(f"# Selftests gate — {'FAIL' if failed else 'PASS'}\n")
    print(f"- baseline: `{baseline_path.name}` ({fmt_counts(baseline['counts'])})")
    print(f"- run: {fmt_counts(summary['counts'])}, "
          f"{len(summary.get('chunks', []))} chunks, {len(timeouts)} timeout(s)")
    print(f"- pin: `{pin_prefix}` matches `bpf-next-commit`\n")

    if tripwire:
        print("## Tripwire — guest hang signals (always fatal)\n")
        for i in timeouts:
            print(f"- chunk {i} timed out")
        for n in noresult:
            print(f"- `{n}`: NORESULT")
        print()
    if hard:
        print(f"## Regressions ({len(hard)})\n")
        print("| test | baseline | run | retry |")
        print("|---|---|---|---|")
        for n, b, r in hard:
            print(f"| `{n}` | {b} | {r} | {retried.get(n, '—')} |")
        print()
    if buckets["missing"]:
        print(f"## Missing from run ({len(buckets['missing'])}) — "
              "test-list/denylist drift\n")
        for n, b in buckets["missing"]:
            print(f"- `{n}` (baseline {b})")
        print()
    if soft:
        print(f"## Soft passes ({len(soft)}) — regressed in-suite, "
              "passed standalone retry\n")
        for n, b, r in soft:
            print(f"- `{n}`: {b} → {r}, retry OK — flaky? consider the FLAKY list")
        print()
    if buckets["new_passes"]:
        print(f"## New passes ({len(buckets['new_passes'])}) — ratchet with "
              "`--write-baseline`\n")
        for n, b in buckets["new_passes"]:
            print(f"- `{n}`: {b} → OK")
        print()
    if buckets["neutral"]:
        print(f"## Neutral drift ({len(buckets['neutral'])})\n")
        for n, b, r in buckets["neutral"]:
            print(f"- `{n}`: {b} → {r}")
        print()
    if buckets["new_tests"]:
        print(f"## New tests ({len(buckets['new_tests'])})\n")
        for n, r in buckets["new_tests"]:
            print(f"- `{n}`: {r}")
        print()
    if buckets["flaky_activity"]:
        print(f"## Flaky-listed activity ({len(buckets['flaky_activity'])})\n")
        for n, b, r in buckets["flaky_activity"]:
            print(f"- `{n}`: {b} → {r}")
        print()
    if flaky:
        print(f"_FLAKY list has {len(flaky)} entrie(s) — work to burn it down._\n")

    if args.write_baseline:
        if tripwire:
            sys.exit("error: refusing --write-baseline: run has hang signals")
        if args.summary:
            src = pathlib.Path(args.summary)
        else:
            src = out_dir / "summary.json"
        name = f"{time.strftime('%Y-%m-%d')}-{pin_prefix[:9]}-gate"
        dst = BASELINE_DIR / f"{name}.json"
        shutil.copyfile(src, dst)
        md = src.with_suffix(".md")
        if md.exists():
            shutil.copyfile(md, BASELINE_DIR / f"{name}.md")
        CURRENT_PTR.write_text(dst.name + "\n")
        print(f"wrote baseline `{dst.name}` and updated CURRENT — "
              "review and commit the diff\n")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
