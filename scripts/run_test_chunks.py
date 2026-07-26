#!/usr/bin/env python3
"""Chunked test_progs runner for the UML guest.

Partitions the full test_progs test list into fixed-size chunks, runs each
chunk through uml-test-progs with a host-side timeout, saves the raw log per
chunk, and emits a parsed machine-readable summary plus a human-readable
report. A hung chunk is killed and recorded; the sweep continues, so one bad
test cannot sink the baseline.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import ctypes
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]


def join_session_keyring() -> None:
    """test_progs registers a session key at startup and exits 255 if the
    session keyring is revoked (common in daemonized/background shells).
    Join a fresh one; harmless if it fails or already works."""
    KEYCTL_JOIN_SESSION_KEYRING = 1
    SYS_keyctl = 250  # x86-64
    try:
        ctypes.CDLL(None, use_errno=True).syscall(
            SYS_keyctl, KEYCTL_JOIN_SESSION_KEYRING, None)
    except OSError:
        pass

def kill_session(sid: int) -> None:
    """SIGKILL every process in session `sid` (start_new_session=True makes
    the chunk runner a session leader, and UML guest processes stay in it
    even when they escape the immediate process group)."""
    for p in pathlib.Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        try:
            # /proc/<pid>/stat, fields after the ')': state ppid pgrp session
            fields = (p / "stat").read_text().rsplit(")", 1)[1].split()
            if int(fields[3]) == sid:
                os.kill(int(p.name), signal.SIGKILL)
        except (OSError, ValueError, IndexError):
            pass


RESULT_RE = re.compile(r"^#(\d+)\s+(\S+):(OK|FAIL|SKIP)\b")

# Known guest-hangers: excluded from chunks by default (see --deny).
# uprobe_multi_test hangs the guest hard enough that even the test_progs
# watchdog cannot recover it (uprobes are unimplemented on UML, task #29).
DEFAULT_DENY = "uprobe_multi_test"
SUMMARY_RE = re.compile(
    r"^Summary: (\d+)/(\d+) PASSED, (\d+) SKIPPED, (\d+) FAILED"
)


def list_tests(test_progs: pathlib.Path) -> list[str]:
    out = subprocess.run(
        [str(test_progs), "--list"], text=True, capture_output=True, check=True
    )
    return sorted({line.strip() for line in out.stdout.splitlines() if line.strip()})


def run_chunk(
    runner: pathlib.Path,
    tests: list[str],
    log_path: pathlib.Path,
    watchdog: int,
    timeout: int,
) -> dict:
    cmd = [
        str(runner),
        "-j1",
        f"--watchdog-timeout={watchdog}",
        "-t",
        ",".join(tests),
    ]
    started = time.time()
    timed_out = False
    with open(log_path, "w") as log:
        proc = subprocess.Popen(
            cmd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
        )
        try:
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGKILL)
            rc = proc.wait()
            # A killed runner can leave the UML guest behind. Kill by session
            # id, not by name — with --jobs > 1 other chunks' guests are
            # running and a global pkill would murder the innocent.
            kill_session(proc.pid)
    return {
        "rc": rc,
        "timed_out": timed_out,
        "seconds": round(time.time() - started, 1),
    }


def parse_log(log_path: pathlib.Path) -> tuple[dict[str, str], dict | None, str | None]:
    """Returns (results, summary, last_reported).

    last_reported is the highest-#id test seen in the log — test_progs runs
    by internal id order, so after a hang/crash the culprit is the next
    matched test AFTER this one in id order (NOT the first alphabetically
    missing one; that heuristic misattributed find_vma for a day).
    """
    results: dict[str, str] = {}
    summary = None
    last_id = -1
    last_reported = None
    for line in log_path.read_text(errors="replace").splitlines():
        m = RESULT_RE.match(line)
        if m and "/" not in m.group(2):
            results[m.group(2)] = m.group(3)
            if int(m.group(1)) > last_id:
                last_id = int(m.group(1))
                last_reported = f"#{m.group(1)} {m.group(2)}"
        m = SUMMARY_RE.match(line)
        if m:
            summary = {
                "passed": int(m.group(1)),
                "subtests": int(m.group(2)),
                "skipped": int(m.group(3)),
                "failed": int(m.group(4)),
            }
    return results, summary, last_reported


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test-progs", default=str(ROOT / ".build/selftests-output/test_progs"))
    ap.add_argument("--runner", default=str(ROOT / "uml-test-progs"))
    ap.add_argument("--chunk-size", type=int, default=25)
    ap.add_argument("--jobs", type=int, default=1,
                    help="chunks to run concurrently, one UML guest each "
                         "(budget UML_MEM≈1.8G of host RAM per job)")
    ap.add_argument("--chunk-timeout", type=int, default=900)
    ap.add_argument("--watchdog", type=int, default=120)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--only", help="comma list: run only chunks containing these tests")
    ap.add_argument("--deny", default=DEFAULT_DENY,
                    help="comma list of tests to exclude (known guest-hangers); "
                         "pass '' to run everything")
    args = ap.parse_args()

    join_session_keyring()

    out_dir = pathlib.Path(
        args.out_dir
        or ROOT / ".build" / "test-logs" / f"baseline-{time.strftime('%Y%m%d-%H%M%S')}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    tests = list_tests(pathlib.Path(args.test_progs))
    denied = {t for t in args.deny.split(",") if t}
    tests = [t for t in tests if t not in denied]
    chunks = [
        tests[i : i + args.chunk_size] for i in range(0, len(tests), args.chunk_size)
    ]
    if args.only:
        wanted = set(args.only.split(","))
        chunks = [c for c in chunks if wanted & set(c)]

    def run_one(idx: int, chunk: list[str]) -> dict:
        log_path = out_dir / f"chunk-{idx:03d}.log"
        meta = run_chunk(
            pathlib.Path(args.runner), chunk, log_path, args.watchdog, args.chunk_timeout
        )
        results, summary, last_reported = parse_log(log_path)
        meta.update({"index": idx, "tests": len(chunk), "summary": summary,
                     "results": results, "last_reported": last_reported})
        state = "TIMEOUT" if meta["timed_out"] else f"rc={meta['rc']}"
        print(f"chunk {idx:03d}/{len(chunks) - 1}: {state} "
              f"{meta['seconds']}s {summary or ''}", flush=True)
        return meta

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as ex:
        chunk_meta = list(ex.map(run_one, range(len(chunks)), chunks))

    # Merge in chunk-index order so results are deterministic regardless of
    # completion order (identical to the old serial behavior).
    statuses: dict[str, str] = {}
    for meta, chunk in zip(chunk_meta, chunks):
        # test_progs -t matches substrings, so a chunk can report tests that
        # belong to other chunks; keep every result, first writer wins.
        for name, status in meta.pop("results").items():
            statuses.setdefault(name, status)
        missing = [t for t in chunk if t not in statuses]
        if meta["timed_out"]:
            for t in missing:
                statuses.setdefault(t, "NORESULT")
        meta["missing"] = missing if meta["timed_out"] else []

    # Anything never reported (e.g. denylisted upstream) is marked absent.
    for t in tests:
        statuses.setdefault(t, "NORESULT")

    counts: dict[str, int] = {}
    for status in statuses.values():
        counts[status] = counts.get(status, 0) + 1

    (out_dir / "summary.json").write_text(
        json.dumps(
            {"counts": counts, "tests": statuses, "chunks": chunk_meta}, indent=1
        )
    )
    with open(out_dir / "summary.md", "w") as f:
        f.write(f"# test_progs UML baseline — {time.strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"Total top-level tests: {len(tests)}\n\n")
        for status in ("OK", "FAIL", "SKIP", "NORESULT"):
            f.write(f"- {status}: {counts.get(status, 0)}\n")
        for status in ("FAIL", "NORESULT"):
            names = sorted(n for n, s in statuses.items() if s == status)
            if names:
                f.write(f"\n## {status} ({len(names)})\n\n")
                f.writelines(f"- {n}\n" for n in names)
    print(f"\nwrote {out_dir}/summary.json and summary.md")
    print("counts:", json.dumps(counts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
