# Distro runtime validation follow-up — 2026-09-07

The kernel advancement passed the [full runtime gate](https://github.com/mykola-lysenko/uml-veristat/actions/runs/34089537688)
and [package build](https://github.com/mykola-lysenko/uml-veristat/actions/runs/34089525693).
The new tracing check exposed a missing `test_progs` binary in the distro
matrix. The Ubuntu 24.04 log identifies the blocking build failure:
`liburandom_read.so` invokes the bundled `ld.lld`, which cannot load
`libicui18n.so.70`. The existing host-linker fallback selected a working
`LD`, but these clang helper rules independently use `LLD`.

Pass the validated linker as both `LD` and `LLD` to the selftests build.
Also make `uml-test-progs` honor `UML_VERISTAT_WORKDIR`, matching `build.sh`,
so distro runs find the binary and matching kernel/modules under their
`/tmp/uml-veristat-build` directory.

Validation: both affected host targets, `liburandom_read.so` and
`urandom_read`, build successfully with LLVM 22.1.8 and explicit
`LLD=/usr/bin/ld` in a fresh output directory. The wrapper copied outside
its normal repository location finds the overridden work directory and
[passes all four tracing subtests](2026-09-07-runtime-workdir-check.log).
Shell syntax and whitespace checks pass. The refreshed distro matrix is
required to confirm all container environments.
