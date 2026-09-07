# Repository map

The active project lives at the repository root. See
[project status](project-status.md) for the current checkpoint and roadmap.

| Path | Purpose |
|------|---------|
| `build.sh` | Build the pinned UML kernel, tools, selftests, and packages |
| `uml-veristat` | Run verifier analysis inside UML |
| `uml-test-progs` | Run runtime BPF selftests inside UML |
| `bpf-next-commit` | Kernel base used by normal builds and CI |
| `patches/uml-veristat/` | Base UML/BPF support |
| `patches/bpf-selftests-uml/` | Runtime, libbpf, and selftest compatibility fixes |
| `patches/test-coverage/` | New tests, build-dependency fixes, and gcov markers |
| `pahole-commit` | Pinned upstream pahole revision |
| `scripts/build_pahole.sh` | Select pahole source and track installation identity |
| `scripts/` | Runtime gate, corpus checks, coverage, and patch validation |
| `reports/selftests-baseline/CURRENT` | Pointer to the adopted runtime baseline |
| `corpus_manifest.json` | Standalone verifier corpus policy and expectations |
| `.github/workflows/` | Runtime, packaging/distro, and kmemleak CI |
| `.build/` | Local build trees, binaries, and raw run logs (untracked) |
| `gdb_demo/` | UML/GDB verifier debugging examples |
| `selftests/` | Historical reproduction scripts, fault injection, and artifacts |

The root `run_bpf_uml.sh`, `bpf_failslab_test.sh`, and `init_failslab` wrappers
forward to the historical scripts under `selftests/`. The old nested
`uml-veristat/` product directory was flattened into the repository root.
