# Upstreaming plan — checkpoint 2026-09-06

The tested local stack stays in build order across its three folders.
Upstream submissions should be small and grouped by subsystem and dependency.
See [project status](project-status.md) for the current baseline and scope.
Submission status and applicability to current upstream must be checked before
posting; the local patch inventory alone does not establish either.

## First batch: independent correctness fixes

| Patch | Problem addressed | Preparation needed |
|-------|-------------------|--------------------|
| `test-coverage/0023` | Flavored selftest objects miss their own generated skeleton dependencies | Validate incremental rebuilds across flavors, including native builds |
| `test-coverage/0024` | Signed light skeletons retain signatures after a signing-key change | Validate key/certificate rotation regenerates skeletons and consumers |
| `bpf-selftests-uml/0026` | Two cpumask subtests assume CPU 1 exists | Confirm two skips on a one-CPU system and execution on a multi-CPU system |
| `uml-veristat/0025` | UML kernel-nofault reads accept guest-user addresses | Check valid kernel reads, rejected user/NULL pointers, and unmapped kernel faults |
| `uml-veristat/0027` | UML static CPU feature macro calls itself instead of the inline helper | Check current upstream applicability and UML build coverage |
| `test-coverage/0028` | Libarena BPF objects remain stale after header changes | Validate regular and ASAN dependency rebuilds on native builds |

The separate `pahole/0001` workaround is retired: unpatched upstream
master fixes the wide-scalar tracing case, so it does not need submission.
See the [comparison](../reports/pahole-update/2026-09-07.md). Patch `0024`
retains only the private-key prerequisite because the advanced kernel pin
already tracks the verification certificate.

Start with `0023/0024` as a related selftests build-fix series. Prepare `0026`
as a separate selftest fix and `0025` for UML review. For each, check a fresh
upstream tree, establish any dependencies, run checkpatch and relevant tests,
and generate maintainer lists from that tree. Local patch numbers are
identifiers, not final mailing-list series numbers.

## Following candidates

- Standalone UML/selftest build fixes: stub alignment (`0003`), test-module
  compilation (`0004`), and compiler CET defaults (`0013b`).
- Generic libbpf changes: duplicate base-BTF candidates (`0005`) and duplicate
  target-type IDs (`0005b`). They need focused native tests and explicit
  justification of ambiguity handling before submission.
- Veristat/selftest correctness: benchmark map defaults (`0007`) and zero
  `max_entries` for per-CPU cgroup storage (`0007b`).
- Program-iterator selftest (`test-coverage/0021`): validate on native BPF
  selftests and refresh its coverage evidence. The gcov instrumentation patch
  is separate harness infrastructure, not a prerequisite to submitting the test.
- UML capabilities: host CPU feature probing (`0017`), software perf (`0018`),
  BPF_EVENTS dependencies (`0019`), irq_work self-IPIs (`uml-veristat/0021`),
  and pt_regs access macros (`bpf-selftests-uml/0020`). Route by affected
  subsystem and confirm dependencies independently.

## Larger JIT and tracing work

The native x86 JIT wiring (`0003b`), per-CPU feature restrictions (`0003c`),
probe-memory guards (`0009b`), exception fixups (`0016`), text pokes (`0013`),
syscall wrappers (`0001`), and dynamic ftrace (`uml-veristat/0020`) need a
coherent dependency story. Split supporting changes into buildable units,
minimize native x86 conditionals, and validate both native and UML behavior.
This remains a larger review task after the first batch.

The former verification-stub RFC is obsolete: real software perf and
BPF_EVENTS replaced the stubs. Arena allocation workarounds (`0006/0006b`)
and the veristat log-size patch (`0008`) were also removed. Do not resurrect
those submissions from historical planning notes.
