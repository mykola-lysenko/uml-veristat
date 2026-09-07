# LLVM investigation — 2026-09-06

The proposed next compiler is **LLVM 23.1.0**, with an explicit shared pin
for local builds and CI. This is an investigation and validation plan;
the local compiler has not been upgraded.

## Current state

| Environment | Observed LLVM | Evidence |
| --- | --- | --- |
| Local `.build/llvm-install` | 22.1.8, `ca7933e47d3a3451d81e72ac174dcb5aa28b59d1` | Installed tool version output |
| Latest completed checkpoint CI | 23.1.0, `ea7d852a70e8bdfaf601d6626a760f9771b2c4b4` | [Selftests gate run 34078265043](https://github.com/mykola-lysenko/uml-veristat/actions/runs/34078265043) |

Local clang, llc, lld, llvm-config, llvm-strip, and llvm-objcopy all run
successfully. LLVM 22.1.8 supports the current arena ASAN build and BPF
CPU v4 feature probes. It is a working comparison toolchain.

[LLVM 23.1.0](https://github.com/llvm/llvm-project/releases/tag/llvmorg-23.1.0)
is the latest stable release checked during this investigation, released
August 25, 2026. The completed CI run downloaded its Linux-X64 archive.
On the previous kernel pin, that CI run recorded 606 OK / 55 FAIL /
75 SKIP, including `stack_arg: SKIP → OK` and the known `timer_mim` flake
passing. That is encouraging evidence, but does not isolate compiler
effects from other environment differences.

The new kernel pin `1b7415bf70be95b9a1e7e87d544867881065613f` includes
`progs/verifier_aggregate_ret.c`, which explicitly requires clang 23.
Its parent test skips with LLVM 22.1.8. The focused runtime checks for
the other aggregate-return cases, kfunc calls, cpumask, and arena pass
with the local compiler.

Correction after source and archived-log review: the four stack-argument
tests already required `__BPF_FEATURE_STACK_ARGUMENT` at the old pin.
Their unsupported dummy programs previously reported OK; upstream added
`__skip` so they now report SKIP. No working coverage was lost, and upgrading
LLVM is not required to repair these status changes. A newer compiler may
enable the real test bodies, adding coverage the old dummy passes did not
provide. See the [evidence](../reports/pin-update/2026-09-06-regression-investigation.md).

There is also a separate `tracing_struct/int128_args` regression: pahole
1.31 omits `bpf_testmod_test_int128_arg` from module BTF under the kernel's
`consistent_func` filtering. The ELF symbol exists, and encoding a separate
diagnostic BTF file without that filter includes it. The cause is pahole's
one-register-per-scalar heuristic incorrectly rejecting parameters following
a two-register `__int128`. A separate pahole build with a narrow correction
restores all four `tracing_struct` subtests while keeping `consistent_func`
enabled. The fix is now integrated into the normal build and the focused
runtime checks pass there too, with LLVM unchanged. See the
[integration validation](../reports/pin-update/2026-09-06-pahole-integration.md).

The subsequent [upstream pahole comparison](../reports/pahole-update/2026-09-07.md)
confirms current master fixes this case without our patch. Normal-build
validation of that pinned upstream revision precedes the LLVM update.

## Why local and CI differ

`build.sh` retains a usable installed compiler unless asked to rebuild
or update it. A fresh prebuilt install instead queries GitHub's latest
LLVM release. The internal `LLVM_NIGHTLY=1` name is misleading: this path
downloads release archives. Source mode defaults to the moving `main`
branch.

`LLVM_RELEASE_TAG` already selects a release, but no compiler pin is
committed. Its API-error fallback can query the newest release even when
a tag was requested. A reproducible pin needs to fail clearly instead
of silently selecting another version, and must detect a mismatched
existing installation.

## September 7 archive probe

The current stable release remains 23.1.0. The downloaded official archive
matches its published SHA-256:
`18da30f77f475688a18f7704d23f9f155ae007ed9922dbed6850a9419d9fec8c`.
A separate staging extraction runs clang, llc, llvm-config, llvm-strip and
llvm-objcopy successfully. Its bundled `ld.lld` cannot load
`libicui18n.so.70` on this host; the validated host-linker fallback covers
both the `LD` and `LLD` selftest build paths. Both affected host helpers
also build successfully with the staged LLVM 23 and `/usr/bin/ld`. The active build compiler
remains LLVM 22.1.8 while pahole validation runs.

Clang 23.1.0 defines `__BPF_FEATURE_STACK_ARGUMENT` for `-target bpf -mcpu=v4`;
22.1.8 does not. This confirms the new compiler can compile the real test
bodies behind those four existing guards. Runtime results remain to be
measured after the compiler update.

## Proposed next task

The initial LLVM 22 reference sweep recorded 621 OK / 60 FAIL / 86 SKIP,
with no missing results or host timeouts. Its [validation report](../reports/bpf-next-2026-09-06.md)
preserves the measured results. Follow-up investigation classifies four
apparent lost passes as dummy-test reporting corrections and resolves the
remaining new tracing subtest. The subsequent complete normal-build sweep
records 623 OK / 58 FAIL / 86 SKIP and is the adopted
[baseline](../reports/selftests-baseline/2026-09-06-1b7415bf7-gate.md).

1. With the pahole correction integrated and validated, refresh the kernel
   baseline with the documented upstream dummy-test reporting changes.
   Commit and push the bpf-next advancement first. Preserve the LLVM 22
   reference toolchain and results.
2. Check newer upstream pahole before changing LLVM: determine whether it
   already fixes the wide-scalar problem, update its pin, and validate BTF
   and runtime behavior. Carry the local correction only if still needed.
   Upstream submission of our correction remains a separate user decision.
3. Add a shared LLVM release pin for local builds and all CI workflows,
   initially `llvmorg-23.1.0`. Enforce explicit-tag selection on download
   errors and existing-install reuse. Record the resolved version, commit,
   archive URL, and checksum in build provenance.
4. Install 23.1.0 separately and rebuild compiler-dependent artifacts in
   clean output directories against the same kernel and patch stack.
   Avoid `--update`, which would also advance the kernel. Compare the full
   runtime sweep, standalone corpus, and exact arena checks against the
   LLVM 22 results; inspect newly enabled tests and every lost pass.
5. Adopt 23.1.0 after those checks and the package/distro matrix pass.
   Keep a moving LLVM-main experiment separate from the default build if
   a specific unreleased BPF feature later requires it.

No LLVM implementation or configuration changes are part of this
investigation.
