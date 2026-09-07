# Project checkpoint — 2026-09-07

`uml-veristat` runs BPF verification in a rootless UML guest;
`uml-test-progs` runs the runtime selftests against the same kernel.
The kernel, pahole, and LLVM advances are separate validated changes.

## Validated dependency advancements

The kernel pin is `1b7415bf70be95b9a1e7e87d544867881065613f`
(bpf-next, September 6, 2026; Linux 7.3-rc2). All 29 patches apply cleanly.
Upstream pahole `416753b4` fixes the wide-scalar BTF issue without the
retired local workaround. Its isolated LLVM 22 comparison preserved every
recorded test status: 623 OK / 58 FAIL / 86 SKIP.

LLVM **23.1.0** is now selected by `llvm-release` for local builds and CI.
Its full sweep records **629 OK / 58 FAIL / 80 SKIP / 0 NORESULT**, with
31 chunks and zero host timeouts. Six previously skipped stack-argument
and aggregate-return tests pass; no pass is lost. The standalone corpus
and exact arena checks pass, including one newly enabled arena program.

Compiler identity changes rebuild compiler-dependent outputs while
preserving the previous compiler and artifacts. Pahole identity changes
regenerate kernel/module BTF. A parallel signing-key generation race found
in CI is fixed in patch 0024, with a reproducer and full Makefile check.

See the [baseline](../reports/selftests-baseline/2026-09-07-1b7415bf7-llvm23-gate.md),
[kernel report](../reports/bpf-next-2026-09-06.md),
[pahole comparison](../reports/pahole-update/2026-09-07.md), and
[LLVM comparison](../reports/llvm-update/2026-09-07.md).

## Baseline and provenance

The previous kernel pin, `520d7d7942025a58a0c79a61b905a556cf3cb524`,
used the [604 OK / 56 FAIL / 76 SKIP checkpoint](../reports/selftests-baseline/2026-09-06-520d7d794-gate.md).
That baseline adopted an unchanged August 1 measurement on September 6.
It included the cpumask fix from [PR #30](https://github.com/mykola-lysenko/uml-veristat/pull/30);
its two CPU-1-dependent subtests skip on the single-CPU guest, and the other
34 pass. No other cpumask subtests were disabled.

[`CURRENT`](../reports/selftests-baseline/CURRENT) selects the LLVM 23
measurement completed September 7 at 10:50: 766 selected names and 767
recorded names (substring matching can report additional tests).
The preceding kernel advancement corrected four unsupported dummy tests'
status to SKIP; LLVM 23 now enables their real programs and they pass.
Upstream also replaced one raw-tracepoint test with a passing successor,
and `verif_scale_pyperf600` gained a pass. `timer_mim` retains its existing
flake treatment. The [cross-pin comparison](../reports/pin-update/2026-09-06-1b7415bf7-final-comparison.json)
and [compiler comparison](../reports/llvm-update/2026-09-07-comparison.json)
preserve these separate transitions.

New coverage gaps include `ksock_lsm`, `ksock_lsm_verifier`, and
`sock_xattr` (network-LSM hooks are disabled), and `verifier_percpu_addr`
(map-FD validation failure, still requiring triage).

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

The normal gate deliberately rejects a baseline from a different kernel
pin. For future pin updates, use `scripts/run_test_chunks.py --jobs 2` to
collect candidate results for explicit cross-pin review; do not rename
the old baseline as if it were measured on the new kernel.

`--jobs 2` matches the current CI sweep. `build.sh --update` deliberately
changes the kernel pin and is a separate task requiring a new baseline.
Kernel, pahole, and LLVM inputs are pinned. Installed and packaged version
records include the actual compiler commit, archive hash, and tool identity.
Explicit compiler comparisons can override `LLVM_RELEASE_TAG` and
`LLVM_INSTALL`; see the LLVM report for preserved reference artifacts.

## Next work, in order

The kernel advancement is committed and pushed in [PR #32](https://github.com/mykola-lysenko/uml-veristat/pull/32).
All eight checks pass at `49cab17`: [full runtime gate](https://github.com/mykola-lysenko/uml-veristat/actions/runs/34144378371),
[package build](https://github.com/mykola-lysenko/uml-veristat/actions/runs/34144376025),
and [all five distro builds](https://github.com/mykola-lysenko/uml-veristat/actions/runs/34144378379).
The pahole advancement and signing-key race fix are pushed in
[PR #33](https://github.com/mykola-lysenko/uml-veristat/pull/33), stacked on
#32. All eight checks pass at `9e2e050`, including the full runtime gate
and five distro builds. LLVM follows on `advance-llvm-20260907`, preserving the LLVM 22
reference results. Each branch has independent validation; the LLVM
report records the distinction between the local measured source tree
and the subsequent Makefile-only signing-key fix.

After those dependency updates, continue this upstream preparation queue:

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
