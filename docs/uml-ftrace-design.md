# UML ftrace / BPF-trampoline design (flagship, task #4)

Goal: make fentry/fexit/fmod_ret/LSM/struct_ops/tracing attach work on UML.
This is the largest FAIL family in the 511-OK baseline (149 FAILs total).

## Observed failure modes (2026-07-26, pin 520d7d794)

- `fentry_test`: skel load fails **-EOPNOTSUPP (-95)**, or loads and attach
  fails **-EINVAL (-22)** (`libbpf: prog 'test1': failed to attach`).
- Root cause: UML has no ftrace at all — no `CONFIG_FUNCTION_TRACER`, no
  fentry nops in kernel functions, no `ftrace_location()`, so
  `register_fentry` → `bpf_arch_text_poke` finds real instructions where it
  expects a 5-byte nop → -EINVAL.

## Trampoline-family FAILs expected to flip (~45-55 of 149)

fentry_test, fexit_test, fentry_fexit, fexit_stress, fsession_test,
get_func_args_test, get_func_args_fsession_test, get_func_ip_test,
get_func_ip_fsession_test, modify_return, module_attach,
module_fentry_shadow, tracing_struct, tracing_multi_test,
tracing_multi_attach_rollback, tracing_multi_bench_attach,
trampoline_count, recursion, missed, test_overhead, d_path,
sk_storage_tracing, task_local_storage(?), test_lsm, lsm_cgroup,
verifier_lsm, test_local_storage, test_bprm_opts, test_ima, deny_namespace,
lookup_key, verify_pkcs7_sig, kernel_flag(?), struct_ops_* (partly),
bpf_iter (uses fentry for some), vmlinux, exe_ctx(?), probe_user(?),
timer_interrupt(?), enable_stats(?). Exact set verified by the gate after
each milestone.

## Key facts discovered

- **Text patching**: UML kernel is a host process; 0003b already does JIT
  text pokes with plain `memcpy` (JIT pages are host-mmap RW). Kernel
  `.text` itself is loaded r-x by the host ELF loader → pokes there need
  `os_protect_memory()` (host mprotect) around the write.
- **±2GB range problem**: kernel text sits at 0x60000000;
  `VMALLOC_START = high_physmem + off` (≈0xd0000000 at mem=1792M, in range)
  but `VMALLOC_END = TASK_SIZE` (huge, out of range), and 0003b documents
  JIT images landing in far host-mmap space (hence its indirect-call
  fallback). A patched fentry site is a 5-byte `call rel32` — the
  trampoline **must** be within ±2GB of the site. x86 native guarantees
  this by allocator design; UML must too.
- **um pt_regs is not x86 pt_regs** (`regs.gp[HOST_*]` array); 0003b's
  `reg2pt_regs[]` remap is the precedent for any regs-shaped asm/C.
- **recordmcount**: UML has no objtool, so mcount_loc must come from
  `scripts/recordmcount` (`FTRACE_MCOUNT_USE_RECORDMCOUNT`) — operates on
  standard x86_64 ELF .o files, should work as-is.
- `kprobe_multi_testmod_test` is OK in baseline — verify why before trusting
  (probably degenerate pass).

## Milestones

**M0 — bounded execmem (standalone win + prerequisite)**
Give UML an `execmem_arch_setup()` that bounds EXECMEM_BPF /
EXECMEM_MODULE_TEXT / trampoline allocations to
`[VMALLOC_START, min(VMALLOC_END, _stext + 2G − margin)]`.
Also unlocks dropping 0003b's far-call indirection later (the
JIT-expansion work attributed ~10.4 expansion points to our call plumbing).
Validate: corpus + arena gates, full local sweep, JIT still green.

**M1 — DYNAMIC_FTRACE base on UML**
- `arch/x86/um/Kconfig`: select HAVE_FUNCTION_TRACER, HAVE_DYNAMIC_FTRACE,
  HAVE_FTRACE_MCOUNT_RECORD, HAVE_FENTRY (X86_64).
- `arch/x86/um/asm/ftrace.h`: MCOUNT_ADDR/MCOUNT_INSN_SIZE=5,
  ftrace_call_adjust.
- `__fentry__` stub + minimal `ftrace_caller` (see M1.5) in um asm.
- `arch/um/kernel/ftrace.c`: ftrace_init_nop / make_nop / make_call /
  modify_call / update_ftrace_func via memcpy inside an
  os_protect_memory(RW→RX) window; use 0003b's um nops.h for the 5-byte nop.
- Boot: ftrace_process_locs nops out every mcount site recorded by
  recordmcount.
Validate: boots, `ftrace_location(<func>)` works (function tracer smoke via
tracefs if enabled).

**M1.5 — ftrace_caller/ftrace_regs_caller asm**
x86's ftrace_64.S is too native (CET, %gs, ORC). Write a um-specific
minimal version: save arg regs into a um-pt_regs-shaped frame (HOST_*
offsets exported through um asm-offsets), call the ops func, restore.
Needed for: function tracer proper, fprobe/kprobe_multi later, and the
direct+ops shared-site path. BPF *direct* attach itself does not run
through it (site calls the BPF trampoline directly).

**M2 — WITH_ARGS + WITH_DIRECT_CALLS**
- HAVE_DYNAMIC_FTRACE_WITH_ARGS (struct ftrace_regs over um pt_regs +
  accessors), then HAVE_DYNAMIC_FTRACE_WITH_DIRECT_CALLS.
- `register_ftrace_direct` then patches fentry sites to `call <bpf tramp>`
  (in range thanks to M0).
- x86's `arch_prepare_bpf_trampoline` already compiles on UML (0003b), but
  audit its %gs/percpu/CET assumptions under 0003c's constraints.
Validate: fentry_test / fexit_test / tracing_struct green in guest, then
full gate sweep to measure the family flip.

**M3 — cleanup + follow-ups**
- fprobe → kprobe_multi tests; function_graph; get_stack fixes are separate
  (stack-unwind family).
- Consider dropping far-call indirection in JIT for in-range targets
  (measure with jit-expansion harness).

## Iteration workflow

Edit directly in `.build/bpf-next` (fast `make ARCH=um -j$(nproc)` loop);
build.sh RESETS the tree, so export to `patches/uml-veristat/00xx-*.patch`
before any build.sh run. Config toggles via `scripts/config` in-tree during
iteration; final enables go into build.sh CONFIG_ARGS. Gates before PR:
check_expectations, check_arena_expectations, selftests_gate.py (local
--jobs 6), checkpatch via scripts/check_patch_stack.sh.
