# Pahole integration validation

The wide-scalar parameter fix is now part of the normal build in
[`patches/pahole`](../../patches/pahole/). It has not been submitted upstream.
LLVM remains 22.1.8 and the kernel pin remains
`1b7415bf70be95b9a1e7e87d544867881065613f`.

## Build behavior

`build.sh` invokes `scripts/build_pahole.sh` to apply the patch and build
pahole. An existing unpatched install is rebuilt automatically. A source
revision, tracked source diff, patch, or helper-recipe change invalidates
the installation identity. An inapplicable patch fails explicitly.

The kernel and test modules are relinked after a pahole identity change,
because Kbuild does not otherwise track the contents of that executable.
The BTF identity is only recorded after module build success, allowing a
failed or interrupted build to retry. `--rebuild-pahole` also forces BTF
regeneration. Installed and packaged version manifests record the pahole
source commit and build identity.

## Validation

Normal build command (no diagnostic source or module overrides):

```bash
SKIP_DEP_INSTALL=1 ./build.sh --reuse-llvm
```

The build passed, applying the patch to the normal source checkout,
rebuilding pahole, regenerating kernel/module BTF, and rebuilding selftests.
The installed kernel and all three test modules are byte-identical to the
in-tree artifacts. The kernel BTF identity stamp matches the installed
pahole identity. The installed version manifest records:

- pahole source: `1f2805b6eef104df3125143c949b391f6122e5b9` (v1.31)
- pahole build identity: `da97565eed531cfab10e39bf977efc760d13fd8e6b1196d3b29388fc4f627ec7`
- LLVM: 22.1.8, `ca7933e47d3a3451d81e72ac174dcb5aa28b59d1`

The [normal runtime check](2026-09-06-pahole-integrated-runtime.log) for
`tracing_struct,aggregate_ret,kfunc_call` passed: the runner reports
4/51 passed, two skipped, zero failures. All four tracing subtests pass,
including `int128_args`. The compiler-dependent aggregate-return dummy
test remains skipped.

The [exact arena check](2026-09-06-pahole-integrated-arena.log) passed:
11 files, 66 programs, 63 successes and three expected rejections.

The [standalone corpus check](2026-09-06-pahole-integrated-corpus.log) passed:
991 standalone input files, 3,071 success rows, 1,940 failure rows, and the
expected five failed-to-process and three failed-to-open files. This is
one additional successful verifier result compared with the original
new-pin build's 3,070 successes and 1,941 failures.

The [unchanged-input check](2026-09-06-pahole-reuse.log) reused the installed
pahole and left the executable timestamp unchanged. A separate deliberately
conflicting source checkout was [rejected before build](2026-09-06-pahole-conflict.log),
without writing a success stamp. Shell syntax and repository whitespace
checks passed.

Package and distro CI now include the `tracing_struct` runtime check.
Those new workflow steps have not yet been executed remotely. A subsequent
fresh [full sweep](../selftests-baseline/2026-09-06-1b7415bf7-gate.md) is now
the accepted baseline: 623 OK / 58 FAIL / 86 SKIP, no missing results or
host timeouts. Focused results were not substituted into that measurement.
