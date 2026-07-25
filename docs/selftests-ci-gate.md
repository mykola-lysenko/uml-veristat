# Selftests CI regression gate — design

Goal: every PR proves it did not regress test_progs coverage against the
committed baseline (509 OK / 150 FAIL / 77 SKIP / 0 NORESULT at pin
520d7d794). New passes ratchet the baseline upward; lost passes fail CI.

## Decision: full run per PR, no subset

The subset-vs-nightly question dissolved on measurement:

- Full 736-test sweep (30 chunks, serial): **18.7 min** wall locally, with
  0 timeouts and 0 panics since the percpu fix + triage landed.
- CI `Build package` job (full `build.sh --package`, including test_progs
  and the corpus check): **15–16 min** measured on ubuntu-24.04 runners.
- After a plain `./build.sh`, `uml-test-progs` and `run_test_chunks.py`
  auto-discover `.build/bpf-next/linux` and
  `.build/selftests-output/test_progs` — no packaging or artifact plumbing
  needed.

Budget on a GitHub runner: ~16 min build + 25–40 min sweep (assume up to
2× local, single-core UML guests, serial chunks) + compare ≈ 60–75 min
worst case. Job timeout 120 min. That fits per-PR comfortably; a curated
subset would add a second source of truth for zero benefit.

## Architecture

One orchestrator script, `scripts/selftests_gate.py`, so CI and a
developer's pre-PR check are the same command:

1. **Run** the full sweep via `run_test_chunks.py` (default chunking,
   default denylist).
2. **Compare** `summary.json` against the committed baseline.
3. **Retry** each regressed test once, standalone (one extra chunk via
   `--only`); a pass on retry demotes the regression to a flake report.
4. **Verdict**: nonzero exit on any surviving regression; Markdown summary
   to stdout (CI redirects it to `$GITHUB_STEP_SUMMARY`).

The compare logic lives in the same script (baseline JSON and
`summary.json` share the `{counts, tests, chunks}` shape; the diff is a
dict comparison, not worth a separate module until something else needs it).

## Gate semantics

Per-test transitions, baseline → run:

| transition            | verdict                                   |
|-----------------------|-------------------------------------------|
| OK → FAIL/NORESULT    | regression (retry once; fail if it holds) |
| OK → SKIP             | regression (coverage loss = config drift) |
| FAIL/SKIP → OK        | new pass — report as ratchet candidate    |
| FAIL ↔ SKIP           | neutral, report only                      |
| test missing from run | regression (denylist/list drift)          |
| new test in run       | report only (bpf-next pin unchanged ⇒ rare)|

Whole-run tripwires, independent of per-test state: any chunk
`timed_out`, or any `NORESULT` in the final statuses, fails the gate
immediately — those signals meant guest hangs/panics historically and
must never become background noise again.

## Flake policy

- Retry-once-standalone is the primary mechanism. A retried pass is a
  **soft pass**: the job stays green but the summary calls it out. (Note
  the known inversion: `wq` fails standalone but passes in-suite — which
  is exactly why the retry is only applied to tests that just regressed
  in-suite, never to the whole set.)
- Repeat offenders get an explicit `reports/selftests-baseline/FLAKY`
  list (one test per line, comment = evidence link). Flaky-listed tests
  never fail the gate in either direction, and the summary nags while the
  list is non-empty. Start empty; only populate with observed CI flakes.

## Baseline management

- Dated result files stay as history
  (`reports/selftests-baseline/<date>-<pin7>[-tag].{json,md}`).
- A one-line pointer file `reports/selftests-baseline/CURRENT` names the
  JSON the gate compares against (no symlink — survives all checkouts).
- **Pin check**: the gate fails fast with a clear message if the pin
  prefix embedded in the CURRENT filename ≠ `bpf-next-commit`. Bumping the
  pin therefore *requires* committing a fresh baseline in the same PR.
- **Ratchet**: `selftests_gate.py --write-baseline` copies the fresh
  summary to a new dated file and updates CURRENT. New passes never
  auto-ratchet in CI; the PR author runs `--write-baseline` locally so the
  diff is reviewed like any other change.

## CI wiring

New job in a separate workflow `selftests-gate.yml` (keeps the existing
build workflow's every-push behavior untouched):

- Triggers: `pull_request` on kernel-affecting paths (same list as the
  distros workflow: `build.sh`, `patches/**`, `scripts/**`,
  `bpf-next-commit`, `uml-test-progs`, `corpus_manifest.json`, the
  workflow file, plus `reports/selftests-baseline/**`), `push` to
  `master`, and `workflow_dispatch`.
- Steps: checkout → `./build.sh` (no `--package`) →
  `python3 scripts/selftests_gate.py` → upload `.build/test-logs/**`
  (chunk logs + summary.json) as an artifact, 14-day retention, uploaded
  `if: always()`.
- `timeout-minutes: 120`, concurrency group per ref with
  cancel-in-progress.

## Later (explicitly out of scope for v1)

- Parallel chunks (N concurrent UML guests) if runner wall time becomes
  annoying; the harness change is small but memory per guest (`UML_MEM`
  default 1792M) needs checking against runner RAM first.
- Subtest-level gating (`test:OK` today hides subtest churn).
- Gating the JIT-expansion corpus metrics the same way.
