# Project checkpoint — 2026-09-06

`uml-veristat` runs BPF verification in a rootless UML guest;
`uml-test-progs` runs the runtime selftests against the same kernel.
The next milestone is preparing small, independent upstream fixes.

## Baseline and provenance

- Kernel base: `520d7d7942025a58a0c79a61b905a556cf3cb524`, recorded in
  [`bpf-next-commit`](../bpf-next-commit). This checkpoint keeps that pin.
- Integrated cpumask fix: [PR #30](https://github.com/mykola-lysenko/uml-veristat/pull/30),
  merge commit `c7ae305d243f03a8e0291cdd6955692e0cbb129a`.
- [`CURRENT`](../reports/selftests-baseline/CURRENT) selects the
  [checkpoint baseline](../reports/selftests-baseline/2026-09-06-520d7d794-gate.md):
  **604 OK / 56 FAIL / 76 SKIP / 0 NORESULT**, across 736 recorded names.
  The sweep selected 735 names; substring matching by `test_progs -t` can
  produce additional reported names. These are recorded result counts,
  not a claim that every upstream test was selected or passed.
- Measurement: the existing local sweep completed on **2026-08-01 at 20:45**,
  from `.build/test-logs/gate-20260801-203645/summary.json`. It contains
  30 chunks and zero timeouts. The September filename records when this
  baseline was adopted, not a new runtime measurement.
- Against the previous baseline, the only result changes are
  `cpumask: FAIL → OK` and `timer_mim: OK → FAIL`. The existing
  [`FLAKY`](../reports/selftests-baseline/FLAKY) policy excludes `timer_mim`
  from gate verdicts and new-pass decisions. Raw results are preserved:
  this is one newly enforced pass, not a measured total of 605 passes.

The cpumask run reports `OK (SKIP: 2/36)`: `test_and_or_xor` and
`test_intersects_subset` require CPU 1 and skip on the single-CPU guest;
the remaining 34 subtests pass. No other cpumask subtests were disabled.

The cpumask branch also passed the
[selftests gate](https://github.com/mykola-lysenko/uml-veristat/actions/runs/30731183542),
[package build](https://github.com/mykola-lysenko/uml-veristat/actions/runs/30731182431),
and [distro builds](https://github.com/mykola-lysenko/uml-veristat/actions/runs/30731183556).
Those results validate the cpumask code revision `e4625a1`; this checkpoint
adopts its local baseline and updates documentation.

## Current capabilities and limits

- The stack uses the native x86 BPF JIT, with UML fault fixups and arena
  support. Host CPU feature probing replaced the old arena allocation
  workarounds.
- Software perf events, real BPF tracing/LSM implementations, and dynamic
  ftrace with direct calls are present. The verification-stub layer was
  removed; historical notes about adding it are obsolete.
- The full runtime regression gate, standalone verifier corpus checks,
  package/distro workflows, and optional gcov and kmemleak modes exist.
- Kprobes, uprobes, hardware perf, stack unwinding, and some JIT features
  remain incomplete or unavailable. Native `%gs`-relative per-CPU JIT
  lowering and private stacks are disabled on UML; supported per-CPU
  operations use the generic helper paths.
- `uprobe_multi_test` is excluded by the runner's existing hang denylist.
  `timer_mim` is the sole flaky-listed test. Passing the gate means no
  regression against the supported baseline, not that the suite is all green.
- Runtime gating is at top-level test granularity. A passing parent can
  contain skipped subtests, as cpumask does here.
- The [gcov report](../reports/bpf-coverage.md) is an older `test_progs`-only
  measurement. Refresh it, including the new program-iterator test and
  standalone suites, before choosing another coverage target.

## Reproduce and compare

From the repository root, build the pinned kernel and all three patch folders:

```bash
./build.sh
python3 scripts/selftests_gate.py --jobs 2
python3 scripts/check_expectations.py
python3 scripts/check_arena_expectations.py
```

`--jobs 2` matches the current CI sweep. `build.sh --update` deliberately
changes the kernel pin and is a separate task requiring a new baseline.
The kernel is pinned; exact toolchain reproduction also requires recording
the LLVM/compiler inputs (the build supports `LLVM_RELEASE_TAG` or an
existing LLVM installation).

To verify the archived checkpoint without booting a guest:

```bash
python3 scripts/selftests_gate.py \
  --baseline reports/selftests-baseline/2026-08-01-520d7d794-gate.json \
  --summary reports/selftests-baseline/2026-09-06-520d7d794-gate.json
```

## Next work, in order

1. Prepare selftests dependency/signing-key fixes `0023/0024`, cpumask
   single-CPU handling `0026`, and UML nofault checking `0025` for upstream
   review. Check current upstream applicability and native validation first;
   preparation does not imply these patches have been submitted.
2. Classify the remaining failures by failing subtest and observed cause.
   Prioritize correctness bugs and small environment fixes; track larger
   architecture capabilities separately.
3. Refresh code coverage with the current test set and standalone suites,
   then choose the next demonstrated test gap.
4. Revisit JIT patch splitting after the small fixes are ready. Broad
   Makefile simplification and JIT guard optimization are deferred.

This file is the current roadmap. The dated findings in
[`uml-selftests-followups.txt`](uml-selftests-followups.txt) and older
comparison reports are historical evidence, not the current task list.
