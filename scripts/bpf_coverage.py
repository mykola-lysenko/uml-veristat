#!/usr/bin/env python3
"""BPF-subsystem code coverage for the UML guest (task #9).

The kernel is built with CONFIG_GCOV_KERNEL and GCOV_PROFILE limited to the
BPF-relevant directories (see the gcov Makefile patch). Each guest exposes
counters under /sys/kernel/debug/gcov/<abs-build-path>/...gcda; since the
guest sees the host filesystem through hostfs, copying them to matching
paths lands them next to their .gcno files in the build tree, where host
gcov can process them.

Modes:
  run     — run tests in a single guest, collect its counters into a
            snapshot dir (repeat for more workloads; snapshots accumulate)
  sweep   — full chunked sweep, one snapshot per chunk
  report  — merge all snapshots (gcov-tool), run gcov --json, and write a
            markdown report: per-file coverage plus every never-executed
            function (the missing-tests list)

Typical flow:
  scripts/bpf_coverage.py sweep --jobs 6
  scripts/bpf_coverage.py report
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD = ROOT / ".build" / "bpf-next"
SNAP_ROOT = ROOT / ".build" / "coverage"
GCOV_DIRS = [
    "kernel/bpf",
    "net/bpf",
    "arch/x86/net",
    "kernel/trace",
    "net/core",
    "net/xdp",
]


def guest_collect_cmd(snap: pathlib.Path) -> str:
    """Shell run inside the guest after the workload: mirror the debugfs
    gcov tree for our build into the snapshot dir (relative .gcda paths)."""
    return (
        f'base=/sys/kernel/debug/gcov{BUILD}; '
        f'if [ -d "$base" ]; then '
        f'cd "$base" && find . -name "*.gcda" | while read -r f; do '
        f'mkdir -p "{snap}/$(dirname "$f")" && cp "$f" "{snap}/$f"; done; '
        f'else echo "bpf_coverage: no gcov debugfs tree (kernel built '
        f'without GCOV?)" >&2; fi'
    )


def run_guest(tests: str, snap: pathlib.Path, watchdog: int = 120) -> int:
    snap.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["UML_TEST_PROGS_PREFIX"] = (
        'sh -c \'"$0" "$@"; rc=$?; ' + guest_collect_cmd(snap) + '; exit $rc\''
    )
    return subprocess.call(
        [str(ROOT / "uml-test-progs"), "-j1",
         f"--watchdog-timeout={watchdog}", "-t", tests],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def cmd_run(args) -> int:
    snap = SNAP_ROOT / f"snap-{args.name or 'run'}"
    rc = run_guest(args.tests, snap)
    n = len(list(snap.rglob("*.gcda")))
    print(f"collected {n} gcda files into {snap} (guest rc {rc})")
    return 0 if n else 1


def cmd_sweep(args) -> int:
    # One snapshot per chunk: run_test_chunks spawns one guest per chunk,
    # and counters reset with every boot, so each chunk needs its own copy
    # before merging.
    import run_test_chunks as rtc  # noqa: F401  (same dir)
    rtc.join_session_keyring()
    tests = rtc.list_tests(BUILD.parent / "selftests-output" / "test_progs")
    denied = set(rtc.DEFAULT_DENY.split(","))
    tests = [t for t in tests if t not in denied]
    chunks = [tests[i:i + 25] for i in range(0, len(tests), 25)]

    import concurrent.futures
    def one(i):
        snap = SNAP_ROOT / f"snap-chunk-{i:03d}"
        rc = run_guest(",".join(chunks[i]), snap)
        print(f"chunk {i:03d}: guest rc {rc}, "
              f"{len(list(snap.rglob('*.gcda')))} gcda", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        list(ex.map(one, range(len(chunks))))
    return 0


def merge_snapshots(dest: pathlib.Path) -> int:
    snaps = sorted(p for p in SNAP_ROOT.glob("snap-*")
                   if any(p.rglob("*.gcda")))
    if not snaps:
        sys.exit("no snapshots with gcda files under " + str(SNAP_ROOT))
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(snaps[0], dest)
    for snap in snaps[1:]:
        # gcov-tool merge writes the union of dest+snap into dest
        subprocess.run(["gcov-tool", "merge", "-o", str(dest),
                        str(dest), str(snap)], check=True,
                       stdout=subprocess.DEVNULL)
    print(f"merged {len(snaps)} snapshot(s)")
    return len(snaps)


def cmd_report(args) -> int:
    merged = SNAP_ROOT / "merged"
    merge_snapshots(merged)

    # Drop the merged .gcda files next to their .gcno in the build tree.
    for gcda in merged.rglob("*.gcda"):
        rel = gcda.relative_to(merged)
        target = BUILD / rel
        if (BUILD / rel).with_suffix(".gcno").exists():
            shutil.copyfile(gcda, target)

    files = {}       # source -> {covered, total, functions:[(name, count)]}
    workdir = SNAP_ROOT / "gcov-json"
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    for d in GCOV_DIRS:
        for gcda in sorted((BUILD / d).glob("*.gcda")):
            subprocess.run(["gcov", "--json-format", str(gcda)],
                           cwd=workdir, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for jz in workdir.glob("*.gcov.json.gz"):
        data = json.loads(gzip.decompress(jz.read_bytes()))
        for f in data.get("files", []):
            src = f["file"]
            if src.startswith("/") or src.startswith(".."):
                continue  # headers outside the tree / generated
            if not any(src.startswith(d) for d in GCOV_DIRS):
                continue
            entry = files.setdefault(src, {"covered": 0, "total": 0,
                                           "functions": []})
            for line in f.get("lines", []):
                entry["total"] += 1
                if line["count"]:
                    entry["covered"] += 1
            for fn in f.get("functions", []):
                entry["functions"].append(
                    (fn["name"], fn["execution_count"], fn["start_line"]))

    out = pathlib.Path(args.output)
    with out.open("w") as md:
        md.write("# BPF subsystem coverage under the UML selftests\n\n")
        md.write(
            "Read the gaps with three filters in mind before calling "
            "something an upstream test gap:\n\n"
            "1. **Harness scope** — this sweep runs `test_progs` only; "
            "suites living in standalone binaries (`test_maps`, "
            "`test_verifier`) do not contribute, so e.g. classic map-op "
            "paths may be covered upstream but not here.\n"
            "2. **Environment** — tests that FAIL or SKIP on UML leave "
            "their kernel paths unexercised (e.g. stackmap ↔ the failing "
            "stacktrace family, priv-stack ↔ JIT features disabled on "
            "UML).\n"
            "3. **Dead-by-design** — some never-executed functions are "
            "unreachable error stubs (e.g. map ops that return "
            "-EOPNOTSUPP by contract).\n\n"
            "What survives all three filters is upstream-test material.\n\n")
        tot_c = sum(e["covered"] for e in files.values())
        tot_l = sum(e["total"] for e in files.values())
        md.write(f"Overall line coverage: **{tot_c}/{tot_l} "
                 f"({100*tot_c/max(tot_l,1):.1f}%)** across "
                 f"{len(files)} instrumented sources.\n\n")
        md.write("| file | line coverage | uncovered functions |\n")
        md.write("|---|---|---|\n")
        for src in sorted(files, key=lambda s: files[s]["covered"] /
                          max(files[s]["total"], 1)):
            e = files[src]
            dead = [n for n, c, _ in e["functions"] if c == 0]
            md.write(f"| {src} | {e['covered']}/{e['total']} "
                     f"({100*e['covered']/max(e['total'],1):.1f}%) "
                     f"| {len(dead)}/{len(e['functions'])} |\n")
        md.write("\n## Never-executed functions (missing-test candidates)"
                 "\n\n")
        for src in sorted(files):
            dead = sorted((ln, n) for n, c, ln in files[src]["functions"]
                          if c == 0)
            if not dead:
                continue
            md.write(f"### {src}\n\n")
            for ln, n in dead:
                md.write(f"- `{n}` (line {ln})\n")
            md.write("\n")
    print(f"wrote {out}")
    return 0


def main() -> int:
    sys.path.insert(0, str(ROOT / "scripts"))
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="mode", required=True)
    r = sub.add_parser("run", help="single-guest workload + collect")
    r.add_argument("tests", help="comma list for test_progs -t")
    r.add_argument("--name", help="snapshot name")
    s = sub.add_parser("sweep", help="full sweep, one snapshot per chunk")
    s.add_argument("--jobs", type=int, default=6)
    p = sub.add_parser("report", help="merge snapshots and write report")
    p.add_argument("--output", default=str(ROOT / "reports" /
                                           "bpf-coverage.md"))
    args = ap.parse_args()
    return {"run": cmd_run, "sweep": cmd_sweep, "report": cmd_report}[
        args.mode](args)


if __name__ == "__main__":
    sys.exit(main())
