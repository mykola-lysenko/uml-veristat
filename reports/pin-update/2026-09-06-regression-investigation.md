# Pin-update regression investigation

This records the initial isolated experiment. The fix has since been
[integrated and validated in the normal build](2026-09-06-pahole-integration.md).

The initial interpretation of the four stack-argument status changes was
incorrect. Their compiler guards are unchanged for x86; the previous
baseline counted fallback dummy programs as passes. Upstream now marks
those dummy programs as skipped. No working coverage was lost.

## 1. `tracing_struct/int128_args`

The new pin adds this subtest; the three pre-existing subtests still pass.
The module's machine code contains `bpf_testmod_test_int128_arg(__int128 a,
int b, long c)`, but pahole 1.31 omits the function from BTF.

On x86-64, `a` occupies RDI/RSI, `b` is in RDX, and `c` is in RCX.
The module's DWARF records `b` in RDX and `c` in RCX, agreeing with its
disassembly. Pahole's positional parameter check instead expects the
second parameter in RSI and the third in RDX. It sets `unexpected_reg`,
and `consistent_func` then excludes the function. Pahole already exempts
struct parameters from this one-register-per-parameter heuristic, but
does not exempt wide integer parameters.

A [candidate pahole patch](pahole-wide-scalar-parameters.patch) extends
that exception to base types wider than `cu->addr_size`, preserving the
existing struct and typedef/const handling. It leaves `consistent_func`
enabled. The patch is against pahole v1.31
(`1f2805b6eef104df3125143c949b391f6122e5b9`). The fetched upstream master
`416753b4ba90fe3b72952ace9954edb321657936` still has the struct-only check.

Validation used a separate source/build directory and a separately linked
test module. It reused the original module object files, kernel, LLVM,
and `test_progs`. Module `.text` is byte-identical before and after BTF
regeneration. With the corrected BTF, [all four tracing_struct subtests
pass](2026-09-06-tracing-struct-pahole-fixed.log), including `int128_args`:
1/4 passed, zero skips, zero failures.

The first experiment re-encoded an already processed module and failed
to load. The successful experiment relinked the original object files
before running the kernel's BTF-generation script, regenerating the
resolved/sorted BTF-ID data from a fresh link as well.

At this stage the installed pahole and default module remained unchanged.
The candidate was subsequently integrated into `build.sh`; see the integration
report above. The accepted full-suite baseline remains unchanged. Broader
architecture validation belongs with upstream preparation.

## 2. Four stack-argument status changes

Direct source comparison between pins
`520d7d7942025a58a0c79a61b905a556cf3cb524` and
`1b7415bf70be95b9a1e7e87d544867881065613f` shows that
`__BPF_FEATURE_STACK_ARGUMENT` was already required. The relevant change
for this compiler is adding `__skip(...)` to the unsupported fallback.
Three files also add RISC-V to their architecture guard; that does not
affect UML/x86. One dummy function is renamed.

The [archived and new runtime log excerpts](2026-09-06-stack-argument-evidence.log)
confirm the same fallback in all four cases:

| Parent test | Old baseline | New pin |
| --- | --- | --- |
| `stack_arg_fail` | unsupported dummy: OK | unsupported dummy: SKIP |
| `stack_arg_precision` | unsupported dummy: OK | unsupported dummy: SKIP |
| `verifier_stack_arg` | unsupported dummy: OK | unsupported dummy: SKIP |
| `verifier_stack_arg_order` | unsupported dummy: OK | unsupported dummy: SKIP |

LLVM 22.1.8 lacks the feature macro, but that did not newly break these
tests. LLVM 23 may enable their real bodies; that would add coverage which
the four old top-level passes did not demonstrate.

## Next steps

The pahole correction is now integrated and validated in the normal build.
The fresh [new-pin baseline](../selftests-baseline/2026-09-06-1b7415bf7-gate.md)
is now adopted, documenting the four upstream dummy-pass-to-skip changes
and the renamed raw-tracepoint test. Check newer upstream pahole next. Keep the
LLVM upgrade as a separate task for reproducibility and additional coverage,
with no need to require it merely to preserve these old dummy passes.
