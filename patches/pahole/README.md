# Retired pahole correction

There are no active pahole patches. The upstream revision in
[`pahole-commit`](../../pahole-commit) already handles wide scalar argument
register slots. Unpatched upstream passes all four `tracing_struct`
subtests, including `int128_args`, with unchanged kernel/module code and
LLVM 22.1.8.

The former `0001` correction was necessary for the v1.31 release and was
validated as part of the kernel-pin advancement. It was never submitted
upstream and is now removed from the build. Its original diagnostic patch
and evidence remain in the [historical investigation](../../reports/pin-update/2026-09-06-regression-investigation.md).
See the [upstream comparison](../../reports/pahole-update/2026-09-07.md).
