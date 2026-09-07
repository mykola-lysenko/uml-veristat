# Upstreaming preparation — checkpoint 2026-09-06

Current priorities live in [project status](project-status.md), and the
submission groups are in [upstreaming-series.md](upstreaming-series.md).

## Completed locally

- Kernel patch metadata was normalized and several dependent patches were
  consolidated into tested local units.
- Real software perf and BPF_EVENTS replaced the verification stubs.
- Host CPU feature probing replaced the arena allocation workarounds.
- Guest-sized verbose log policy moved into the wrapper.
- Runtime regression CI, package/distro checks, optional gcov/kmemleak modes,
  and selftests build-dependency fixes are implemented.
- Cpumask PR #30 is merged. The checkpoint baseline records its new pass
  using the existing timer flake policy.

## Preparation still required

1. Check each first-batch patch (`0023/0024`, `0026`, `0025`) against current
   upstream and verify whether equivalent fixes or submissions already exist.
2. Produce focused before/after evidence and native validation where relevant.
   Keep each patch independently buildable, or state its real dependencies.
3. Run the full pinned runtime gate and corpus checks for code changes that
   affect the tested stack. Record the kernel and toolchain inputs used.
4. Generate final patch metadata and maintainer lists from the target tree.
   Include a concrete failure, resulting behavior, and validation in each
   commit message. Prepare drafts before arranging submission.
5. Add focused native ambiguity tests before proposing the generic libbpf
   changes; UML success alone does not settle their semantics.
6. Later, split the larger UML/x86 JIT and tracing work into reviewable,
   buildable units and validate native x86 behavior alongside UML.

The old cleanup priority of preparing a verification-stub RFC no longer
applies. Historical patch-impact and coverage reports must be regenerated
before being used as evidence for the current stack.
