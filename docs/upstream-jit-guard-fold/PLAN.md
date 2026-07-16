# Upstream campaign: bpf, x86 probe-mem guard fold

Target: bpf-next, single patch (no series needed).
Patch: `docs/upstream-jit-guard-fold/0001-bpf-x86-fold-the-probe-mem-low-bound-into-the-guard-.patch`
— the **mainline variant** (stock `VSYSCALL_ADDR` code), NOT our stack's
0009c (which is written against 0009b's renamed locals). Apply-tested and
compile-tested (`make O=... arch/x86/net/bpf_jit_comp.o`, x86_64 defconfig)
at pin 520d7d794; checkpatch clean.

Keep 0009c in the local stack regardless — it keeps UML builds and the
jit-expansion measurements reproducible. Drop it only after the mainline
patch lands and the next `--update` pulls it in (then 0009c will show
"already applied — skipping" or conflict; delete it at that point).

## Phase 0 — background (read before touching anything)

- `arch/x86/net/bpf_jit_comp.c`, the `BPF_LDX | BPF_PROBE_MEM` case
  (~line 2380 at the pin): the guard you are changing. Read the stock
  sequence until you can write it from memory; reviewers will ask about
  the compare/jump/extable interplay, which the patch does not touch.
- `is_simm32()` in the same file; `insn->off` is `s16`
  (`include/uapi/linux/bpf.h`, struct bpf_insn).
- Why the bound always folds: VSYSCALL_ADDR = -10 MiB, so
  `insn->off - VSYSCALL_ADDR` ∈ [10 452 992, 10 518 527] — always imm32.
  The `is_simm32()` gate is therefore provably always-true on mainline;
  it exists as a safety net if the span expression ever changes. Expect a
  reviewer to ask "why the fallback?" — the honest answer is defensive
  coding against future span changes; be ready to drop the else-branch
  if the maintainers prefer (trivial respin).
- `Documentation/process/submitting-patches.rst` and
  `Documentation/bpf/bpf_devel_QA.rst` (bpf-next etiquette, CI).

## Phase 1 — fresh tree + patch

```bash
git clone https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git
cd bpf-next
git am /path/to/0001-bpf-x86-fold-the-probe-mem-low-bound-into-the-guard-.patch
# if bpf-next drifted and am fails: git am --3way, resolve, re-verify hunks
make defconfig && ./scripts/config -e BPF_JIT -e BPF_SYSCALL -e DEBUG_INFO_BTF
make olddefconfig && make -j$(nproc)
```

## Phase 2 — functional validation on native x86 (boot the kernel)

Run on a dev server / VM booted into the patched kernel:

```bash
cd tools/testing/selftests/bpf && make -j$(nproc)
./test_progs -t jit_probe_mem,ksyms_btf,map_kptr,rcu_read_lock,iters,task_kfunc,verifier
./test_progs   # full run if the machine allows; diff against unpatched run
```

Eyeball the generated code (this is what convinces reviewers fastest):

```bash
bpftool prog loadall jit_probe_mem.bpf.o /sys/fs/bpf/t
bpftool prog dump jited pinned /sys/fs/bpf/t/<prog>
# stock:  movabsq $-10485760,%r10; movq %rsi,%r11; addq $N,%r11; subq %r10,%r11
# folded: movq %rsi,%r11; addq $(N+10485760),%r11
```

## Phase 3 — performance evidence (see checklist below)

Minimum for the commit message: the microbench A/B on bare metal.
Port `benchmarks/probe-mem/probe_mem_bench.bpf.c` (it is upstream-clean:
vmlinux.h + libbpf only) and drive it identically:

```bash
bpftool prog run pinned /sys/fs/bpf/pmb/guard_bench data_in pkt.bin repeat 2000000
```

Native numbers replace the UML ones before sending; keep the UML result
as corroboration only if asked.

## Phase 4 — submit

```bash
./scripts/checkpatch.pl --strict 0001-*.patch      # --strict for bpf-next
./scripts/get_maintainer.pl arch/x86/net/bpf_jit_comp.c
# expect: Alexei Starovoitov, Daniel Borkmann, Andrii Nakryiko, bpf@vger.kernel.org,
#         x86 JIT reviewers (John Fastabend et al.), netdev on Cc per get_maintainer
git send-email --to bpf@vger.kernel.org --cc <maintainers> 0001-*.patch
```

- Subject prefix is already `bpf, x86:` — bpf-next patches want
  `[PATCH bpf-next]`; pass `--subject-prefix='PATCH bpf-next'` to
  format-patch when regenerating.
- Watch patchwork (patchwork.kernel.org/project/netdevbpf) — BPF CI runs
  the full selftest matrix on it automatically; a CI failure means respin.

## Phase 5 — anticipated review questions

1. "Why keep the fallback?" — see Phase 0; offer to drop it.
2. "Does this change the guard semantics for any address?" — no:
   both forms compute src+off-VSYSCALL_ADDR mod 2^64 into r11;
   `is_simm32` guarantees the folded imm is lossless (sign-extended
   imm32); compare/limit/jcc/extable untouched.
3. "Numbers?" — microbench + corpus-wide static delta are in the commit
   message; have the per-site byte math ready (off≠0: 20B→7B, off==0:
   13B→7B).
4. "Why not also hoist the limit?" — opt #2 in our notes: needs a free
   callee-saved reg + multi-pass-stable gating; deliberately out of
   scope, can be a follow-up.

## Evidence checklist — what makes the claim believable

In descending order of reviewer/production weight:

1. **Native microbench A/B** (required): guard_bench vs plain_bench on
   bare metal, patched vs unpatched kernel, `perf stat -e
   cycles,instructions` for IPC — explains why time savings can exceed
   the 14% insn reduction (movabsq is a 10-byte decode on the
   address-check dependency chain).
2. **Fleet canary with `sysctl kernel.bpf_stats_enabled=1`** (the
   production argument): per-program `run_time_ns/run_cnt` from
   `bpftool prog show` on canary vs control hosts, focusing on the
   guard-heavy LSM/tracing programs from the fbk5 snapshot. This is the
   number that translates directly to your dashboards.
3. **Dynamic-weighted guard census via evpf-viz**: static guard sites ×
   run_cnt per program → projected fleet-wide saved instructions/sec.
   Turns "up to 2 insns/site" into "N billion insns/sec across the tier".
4. **No-regression control**: katran bench (`bench_xdp_lb`) native A/B —
   expected identical (guard-free programs JIT byte-identically; we
   proved this on the selftests corpus).
5. **Full test_progs + test_verifier** pass on the patched native kernel
   (CI will do this too, but do it first).
6. **icache/frontend counters** on a guard-heavy realistic program
   (dump_tcp6-shaped, 48% guard code): `perf stat -e
   icache_misses,idq.mite_uops` style evidence that smaller guard code
   relieves the front end — optional, but preempts "microbench-only"
   pushback.
