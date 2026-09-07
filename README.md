# `uml-veristat`

`uml-veristat` is a drop-in CLI replacement for `veristat` that runs BPF verification inside a User-Mode Linux (UML) guest running the `bpf-next` kernel pinned by [`bpf-next-commit`](bpf-next-commit).

It allows you to test BPF programs against that upstream verifier without needing root privileges, QEMU, KVM, or a dedicated VM.

## Current checkpoint

The [project status and roadmap](docs/project-status.md) records the kernel
pin, validation evidence, supported capabilities, and next work.
The runtime baseline on Linux 7.3-rc2 is **623 OK / 58 FAIL / 86 SKIP /
0 NORESULT**, measured in a fresh full sweep with LLVM 22.1.8. See the
[baseline report](reports/selftests-baseline/2026-09-06-1b7415bf7-gate.md)
for provenance, the four upstream dummy-test reporting corrections, and
known coverage gaps. The denylist and `timer_mim` flake policy are unchanged.

The normal build uses the upstream revision in [`pahole-commit`](pahole-commit).
It already fixes the 128-bit tracing case, so the local pahole patch has
been retired. See the [upstream comparison](reports/pahole-update/2026-09-07.md).
The full pahole comparison preserves every recorded test status. LLVM is
the next dependency update.

## How it works

When you run `uml-veristat prog.bpf.o`:
1. It boots a pre-compiled UML kernel (`linux`) in the background.
2. The UML guest mounts your host filesystem via `hostfs` so it can see your `.bpf.o` files.
3. It runs the real `veristat` binary *inside* the UML guest.
4. It streams the verifier output back to your terminal and exits with `veristat`'s exact exit code.

Boot overhead is typically under 1 second.

## Setup

Before you can use `uml-veristat`, you need to build the UML kernel and the `veristat` binary. A one-time setup script is provided.

```bash
cd uml-veristat
./build.sh
```

### What `build.sh` does
1. Installs host build dependencies (`apt`, `dnf`, `zypper`, or `pacman`).
2. Downloads a pre-built LLVM/Clang release from GitHub (or builds from source with `--llvm-source`).
3. Builds `pahole` from the upstream revision in `pahole-commit`.
4. Clones `bpf-next` and checks out the committed kernel pin.
5. Applies the UML/BPF patch stack (see [`patches/`](patches/)).
6. Builds the UML kernel (`linux`) with BPF and BTF enabled.
7. Builds the `veristat` binary.
8. Installs the artifacts to `~/.local/share/uml-veristat/`.

The selftests build runs in keep-going mode. A small set of UML-incompatible or
upstream-drifting selftests can fail to compile without aborting the overall
install. The supported standalone corpus is tracked by
`scripts/report_coverage.py`.

*Note: The initial build takes about 15–20 minutes depending on your CPU and network speed. Subsequent `./build.sh` runs reuse build artifacts. `--update` explicitly advances the kernel pin and requires a new regression baseline.*

## Usage

Simply use `uml-veristat` exactly as you would use `veristat`:

```bash
# Basic verification
./uml-veristat my_prog.bpf.o

# Show detailed verifier log on failure
./uml-veristat -l 1 my_prog.bpf.o

# Compare two programs
./uml-veristat -C old.bpf.o new.bpf.o
```

### GDB Debugging

To stop the UML guest before `veristat` runs and attach host `gdb` to the UML
kernel process, use:

```bash
./uml-veristat --gdb-wait my_prog.bpf.o
```

The wrapper will:

1. Boot UML and pause before `veristat` runs
2. Print the UML host PID and example `gdb` commands
3. Wait until you resume the guest by creating the trigger file it prints

This reuses the same host-attach model documented in
[`gdb_demo/`](gdb_demo), but against the real
installed `uml-veristat` kernel and binaries. The recommended
[`verifier.gdb`](gdb_demo/verifier.gdb) script
now includes the usual UML signal handling and default verifier breakpoints.

### Environment Variables

You can override the paths to the kernel and veristat binaries using environment variables:

- `UML_KERNEL`: Path to the UML kernel binary (default: `~/.local/share/uml-veristat/linux`)
- `VERISTAT`: Path to the veristat binary (default: `~/.local/share/uml-veristat/veristat`)
- `UML_MEM`: Memory to allocate to the UML guest (default: `512M`)
- `UML_VERBOSE`: Set to `1` to see the full UML kernel boot log (useful for debugging kernel panics)
- `UML_MODULES`: Space-separated kernel modules (`.ko`) to load before running veristat (defaults to the installed BPF selftest modules; set to `""` to disable)

### Running `test_progs` in UML

`uml-test-progs` runs the linked BPF selftests harness inside the same UML
kernel. It is intended for runtime triage and baseline collection, while
`uml-veristat` remains the standalone verifier tool.

```bash
./uml-test-progs --list
./uml-test-progs --count
./uml-test-progs -j1 --watchdog-timeout=60 -t arena
```

The runner mounts bpffs, cgroup2, and debugfs when available, brings loopback
up, and exposes the BPF selftest modules from the selftests output directory so
`test_progs` can load them through its normal helper path.

## Kernel Patches

`build.sh` applies 29 patches from three folders, in order:

| Folder | Patches | Purpose |
|--------|---------|---------|
| [`patches/uml-veristat/`](patches/uml-veristat/) | 11 | UML kernel, JIT, perf, tracing, irq_work, and nofault support |
| [`patches/bpf-selftests-uml/`](patches/bpf-selftests-uml/) | 13 | Runtime support, libbpf compatibility, and selftest fixes including cpumask |
| [`patches/test-coverage/`](patches/test-coverage/) | 5 | Program-iterator coverage, build dependency fixes, and optional gcov instrumentation |

All three folders participate in normal builds. The gcov markers only enable
instrumentation when `CONFIG_GCOV_KERNEL` is set (`UML_GCOV_BUILD=1`).

Pahole uses an upstream commit pin and source/recipe identity to rebuild
when its inputs change, regenerating kernel/module BTF and selftests.
Package and distro CI check the `tracing_struct` runtime test. The
[historical pahole correction](patches/pahole/) is no longer applied.

The stack now uses real BPF tracing/LSM and software perf implementations,
plus dynamic ftrace with direct calls. The former verification stubs and
arena allocation workarounds were removed. See the
[patch descriptions](patches/README.md) and
[current upstreaming plan](docs/upstreaming-series.md).
The [patch-impact comparison](docs/patch-impact.md) is historical;
use the [current baseline](reports/selftests-baseline/CURRENT) for runtime status.

## Verification Model

`uml-veristat` exposes an upstream kernel reality that is easy to miss: BPF
"verification" is not a single platform-independent pass.

In practice there are two layers:

1. Generic verifier checks
   - CFG validity, register typing, pointer provenance, bounds, lifetimes,
     reference tracking, helper/kfunc signatures, etc.
2. Backend-dependent compatibility checks
   - whether the selected execution target can actually lower the verified
     program: interpreter vs JIT, architecture-specific code generation, and
     feature-specific backend support.

The current kernel mixes those layers together in the verifier instead of
reporting them as two separate phases. For `uml-veristat`, that means some
failures are not "your program is invalid BPF", but "this UML/x86 JIT backend
does not support lowering this valid construct yet".

### Why arena requires JIT

Arena is the clearest example. In
`kernel/bpf/verifier.c`, `BPF_MAP_TYPE_ARENA` is rejected unless:

- `prog->jit_requested` is true
- `bpf_jit_supports_arena()` is true
- the arena has a user VM base address

This is not just a generic kfunc restriction. Arena pointers rely on
architecture-specific JIT lowering. As explained in `kernel/bpf/arena.c`,
arena pointers use the lower 32 bits of the user-space address as an offset
into a kernel VM area, and the JIT emits special addressing sequences for arena
loads/stores. `kernel/bpf/fixups.c` and `kernel/bpf/core.c` also contain
arena-specific instruction rewrites (`BPF_PROBE_MEM32`/`MEM32SX`) that are only
meaningful if the JIT backend knows how to lower them.

So arena currently means:

- generically valid verifier state is necessary but not sufficient
- the selected JIT backend must explicitly claim arena support

### Current backend-dependent gates

The upstream verifier currently folds several backend-dependent checks into
program load/verification:

- kfunc calls: `bpf_jit_supports_kfunc_call()`
- far kfunc calls: `bpf_jit_supports_far_kfunc_call()`
- arena programs: `bpf_jit_supports_arena()`
- arena-specific instruction forms: `bpf_jit_supports_insn(..., true)`
- percpu map instructions: `bpf_jit_supports_percpu_insn()`
- subprog tailcalls: `bpf_jit_supports_subprog_tailcalls()`
- private stack: `bpf_jit_supports_private_stack()`
- exceptions / throwing kfuncs: `bpf_jit_supports_exceptions()`
- fsession support: `bpf_jit_supports_fsession()`
- pointer exchange lowering: `bpf_jit_supports_ptr_xchg()`
- timed `may_goto`: `bpf_jit_supports_timed_may_goto()`

This is why `uml-veristat` should be interpreted as testing both:

- verifier semantics on the pinned `bpf-next`
- backend support of the current UML/x86 execution target

## Reproducible Coverage

Coverage numbers should be generated from the installed artifacts, not edited by
hand. Use:

```bash
cd uml-veristat
python3 scripts/report_coverage.py
```

The script runs two sweeps over the top-level installed selftest corpus:

- default `uml-veristat` output for file-level counts
- `uml-veristat -o csv` for per-program verdict counts

The default report now separates the top-level corpus into:

- standalone positive files that should load under `uml-veristat`
- expected-negative tests that are supposed to fail
- fixture-only linked/subskeleton objects that are not standalone load targets

The corpus classification and expected regression baseline live in the
machine-readable manifest
[`corpus_manifest.json`](corpus_manifest.json).
To assert that the current installed build still matches the expected file
bucket and errno baseline, run:

```bash
cd uml-veristat
python3 scripts/check_expectations.py
```

For arena-specific work, run the focused arena regression:

```bash
cd uml-veristat
python3 scripts/check_arena_expectations.py
```

That check covers the 11 top-level arena-family objects and asserts that none
fail at file-processing time. The current expected arena result is 66 processed
programs: 63 success rows and 3 expected verifier-failure rows.

The top-level CI expectation check uses exact failure-bucket checks plus
minimum aggregate thresholds from `corpus_manifest.json`. It intentionally does
not pin every top-level count exactly. CI uses the committed kernel pin;
refresh the manifest and runtime baseline when deliberately advancing it. The focused arena expectation check remains exact.

Reference output from the `e4287bf34` `bpf-next` snapshot (`919` `.bpf.o`
files) was:

| Metric | Value |
|--------|-------|
| Standalone input files | `902` |
| Excluded expected-negative tests | `5` |
| Excluded fixture-only objects | `12` |
| Processed files | `901` |
| Skipped files | `1` |
| Processed programs | `4514` |
| Successful CSV rows | `2413` |
| Failing CSV rows | `2101` |
| Remaining failed-to-process files | `6` |
| Remaining failed-to-open files | `1` |

### Clean Upstream Baseline

It is also possible to build a clean upstream UML variant with no local patch
stack:

```bash
cd uml-veristat
./build.sh --clean --rebuild-kernel --rebuild-bpftool --rebuild-selftests --rebuild-testmod
```

This installs to `~/.local/share/uml-veristat-clean` and leaves the normal
patched install untouched.

The important point is that the clean upstream build is still usable. The
headline corpus size is only slightly smaller, because `standalone input files`
is just the filename-based input corpus after excluding expected-negative and
fixture-only objects. It is not a success count.

A historical comparison from the `9012cf249` snapshot shows the real
difference in the verification results:

| Metric | Patched UML | Clean upstream UML |
|--------|-------------|--------------------|
| Standalone input files | `873` | `862` |
| Processed files | `871` | `860` |
| Processed programs | `4378` | `4323` |
| Successful CSV rows | `2282` | `1336` |
| Failing CSV rows | `2096` | `2987` |
| Remaining failed-to-process files | `0` | `104` |
| Remaining failed-to-open files | `1` | `2` |

So the local patch stack does not merely increase the input corpus a little. It
substantially improves effective coverage by:

- turning many hard file-level failures into processable objects
- converting a large number of per-program failures into successes
- restoring whole feature classes such as tracing/session-style programs,
  `bpf_testmod`/module-BTF-dependent objects, struct_ops-heavy cases, and more
  stable diagnostic runs

Excluded expected-negative tests:

- `bad_struct_ops.bpf.o`
- `struct_ops_autocreate.bpf.o`
- `test_pinning_invalid.bpf.o`
- `uptr_map_failure.bpf.o`
- `wakeup_source_fail.bpf.o`

Excluded fixture-only objects:

- `linked_funcs1.bpf.o`
- `linked_funcs2.bpf.o`
- `linked_maps1.bpf.o`
- `linked_maps2.bpf.o`
- `linked_vars1.bpf.o`
- `linked_vars2.bpf.o`
- `test_subskeleton.bpf.o`
- `test_subskeleton_lib.bpf.o`
- `test_subskeleton_lib2.bpf.o`
- `tracing_multi_attach.bpf.o`
- `tracing_multi_attach_module.bpf.o`
- `tracing_multi_intersect_attach.bpf.o`

Historical standalone file-level items from that comparison (current policy
is in `corpus_manifest.json`):

- `bpf_smc.bpf.o` (`-3`): SMC struct_ops and fentry targets are absent from
  the current UML kernel BTF.
- `struct_ops_module.bpf.o` (`-95`): the raw object contains intentionally
  incompatible struct_ops state that the selftest harness disables or mutates
  before load.
- `tcp_ca_kfunc.bpf.o` (`-22`): TCP congestion-control kfunc BTF, for example
  `bbr_cwnd_event_tx_start`, is absent from the current UML kernel/module BTF.
- `test_map_in_map.bpf.o` (`-22`): the legacy object relies on the harness
  calling `bpf_map__set_inner_map_fd()` before load.
- `test_select_reuseport_kern.bpf.o` (`-22`): the selftest relies on a
  harness-created reuseport array and `bpf_map__reuse_fd()` before load.
- `test_wakeup_source.bpf.o` (`-22`): `bpf_wakeup_sources_get_head` is absent
  from the current UML kernel BTF, matching the selftest's skip condition.
- `test_sk_assign.bpf.o` (`-95`): the old iproute2 object uses a legacy
  `SEC("maps")` map definition that libbpf v1 refuses; the standalone libbpf
  variant is `test_sk_assign_libbpf.bpf.o`.

With UML host CPU feature probing (`0017`) and BPF fault fixups (`0016`),
the arena family no longer fails at file-processing time in the focused corpus. Arena objects now produce normal per-program verifier
rows under `uml-veristat`; only `verifier_arena.bpf.o` contains
expected-negative rows,
`iter_maps2` and `iter_maps3`, which intentionally pass invalid arena kfunc
arguments to the verifier.

See `patches/README.md` for detailed descriptions of each patch.

## Limitations

- Each invocation boots a fresh guest; repeated calls incur boot overhead.
- Verification depends on the guest kernel configuration and UML/x86 backend
  capabilities. A load failure can indicate an unavailable feature or missing
  harness setup, as well as invalid BPF.
- Kprobes, uprobes, hardware perf, stack unwinding, and some JIT features
  remain incomplete or unavailable. Native per-CPU JIT lowering and private
  stacks are disabled on UML; supported per-CPU operations use helper paths.
- The guest runs as a host user process, with privileges managed inside the
  guest. Host restrictions on UML execution and host filesystem access still
  apply; guest BPF capabilities do not require granting host root privileges.
- The runtime gate excludes the known `uprobe_multi_test` hang and tolerates
  the documented `timer_mim` flake. It gates top-level results, which can
  include skipped subtests.

## Next work

Prepare the small independent upstream fixes, classify remaining runtime
failures, then refresh code coverage before choosing another gap. The
[project roadmap](docs/project-status.md#next-work-in-order) gives the order
and completion criteria. Runtime regression gating, package/distro CI,
compiler caching, and optional gcov/kmemleak workflows are already present.

## Repository layout

The project lives at the repository root (flattened from the former
`uml-veristat/` subdirectory in 2026-07): `build.sh`, the `uml-veristat`
wrapper, the `uml-test-progs` runner, `patches/`, `scripts/`,
`corpus_manifest.json`, and the `bpf-next-commit` pin. Build output goes
to `.build/` (override with `UML_VERISTAT_WORKDIR`). Also at the root:

- [`docs/`](docs/) — follow-ups, upstreaming plans, and design notes.
- [`gdb_demo/`](gdb_demo/) — verifier debugging walkthrough used by
  `--gdb-wait`.
- [`selftests/`](selftests/) — historical selftests reproduction scripts
  and reference artifacts; the legacy root wrappers `run_bpf_uml.sh`,
  `bpf_failslab_test.sh`, and `init_failslab` forward there.

If you have an existing checkout with build state under
`uml-veristat/.build/`, move it once with `mv uml-veristat/.build .build`
to keep the cached bpf-next and LLVM trees, then remove
`.build/pahole-build` and `.build/pahole-install` (pahole bakes absolute
library paths) and run `./build.sh` once — it rebuilds pahole and
refreshes the installed `selftests` symlink, which points into `.build`.
