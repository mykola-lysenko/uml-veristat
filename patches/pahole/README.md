# Local pahole fixes

These patches target pahole, not the kernel. `scripts/build_pahole.sh`
applies them before building pahole; `build.sh` invokes that helper for
all build modes. They are separate from the 29-patch kernel stack.

`0001` corrects the register-mapping heuristic for wide scalar parameters.
On x86-64, `__int128` occupies two argument registers, so the following
parameters do not match a one-register-per-parameter model. Pahole's
`consistent_func` filtering otherwise drops valid function BTF, breaking
`tracing_struct/int128_args`. The patch preserves that filtering and
extends its existing struct exception to wide scalar types.

The source revision, tracked source diff, patch contents, and helper recipe
identify an installation. Missing or changed identity rebuilds pahole;
unchanged inputs reuse it. An inapplicable patch fails explicitly. After
a pahole change, the main build relinks the kernel and test modules to
regenerate BTF, and records the identity in the installed `version.txt`.

The package and distro workflows run `tracing_struct` to check module BTF,
attachment, and argument values. See the
[investigation](../../reports/pin-update/2026-09-06-regression-investigation.md)
for the original diagnosis and isolated proof.

Upstream submission is pending the user's decision; this patch has not
been sent upstream.
