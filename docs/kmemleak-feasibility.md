# kmemleak inside the UML guest — feasibility study (2026-07-27)

Question: can we run the kernel's leak detector inside the UML guest under
the BPF selftests and veristat, and is it worth integrating?

**Verdict: yes — works out of the box, ~2× runtime, pipeline validated by
a positive control. Recommended as an opt-in wrapper mode plus an
on-demand/nightly CI job, not as part of the per-PR gate.**

## Measurements (pin 520d7d794, post-PR-#25 tree)

| experiment | result |
|---|---|
| arch support | `arch/um` already selects `HAVE_DEBUG_KMEMLEAK`; `DEBUG_KMEMLEAK=y` + pool 40000 boots clean (39,775 free), no self-disable through any workload |
| positive control | `samples/kmemleak/kmemleak-test.ko` planted leaks **are detected** with symbolized backtraces incl. module names (`kmemleak_test_init+0x59 [kmemleak_test]`), across kmalloc, vmalloc and percpu object types. 3 of ~14 reported — kmemleak's documented conservatism (stale stack/register pointers hide leaks; repeated scans converge), not UML-specific |
| selftests slice (10 families) | all pass, **0 leaks** |
| veristat, 150 corpus objects | 31.9 s wall incl. boot + double scan, **0 leaks** |
| full 736-test sweep, `--jobs 6` | **8m10s** vs 4m00s stock (≈2×; serial-equivalent 33.7 vs 18.7 min). Results virtually identical: 602 OK / 58 FAIL / 76 SKIP vs 603 baseline — the one delta is flaky-listed `timer_mim`. No debug-overhead breakage |
| scan cost | one `scan` over the 1.75 GB guest ≈ a few seconds; double-scan + aging sleeps adds ~14 s fixed per guest |

## Method notes

- Trigger/read: `echo scan > /sys/kernel/debug/kmemleak; sleep 7;`
  (repeat) `; cat /sys/kernel/debug/kmemleak` — the double scan + sleeps
  handle kmemleak's `min_age` filtering of young objects. debugfs is
  already mounted by both wrappers' init.
- Reports written to `/tmp/...` inside the guest land on the host via
  hostfs — trivially collectable.
- `uml-test-progs` can inject post-run commands today via
  `UML_TEST_PROGS_PREFIX` (`sh -c '"$0" "$@"; <scan>' `);
  **`uml-veristat` has no such hook** — integration needs a small
  wrapper change.
- A clean report is only meaningful if kmemleak didn't disable itself:
  always check dmesg for `kmemleak:` warnings (pool exhaustion) —
  40000 leaves ~99% headroom for this workload.
- Config gotcha: `.config` persists across build.sh runs — after a
  kmemleak experiment, explicitly `--disable DEBUG_KMEMLEAK` or the 2×
  overhead silently stays in subsequent local builds.

## Proposed integration (not yet implemented)

1. **`UML_KMEMLEAK=1` mode in both wrappers**: build.sh gains an optional
   config flavor (or a `scripts/config` toggle documented in the
   wrapper); guest init appends the double-scan and copies
   `/sys/kernel/debug/kmemleak` + a dmesg `kmemleak:` grep next to the
   test output; wrapper surfaces "N unreferenced objects" in its exit
   summary (nonzero exit optional).
2. **Chunked sweeps**: each chunk's guest scans before halt, so
   `run_test_chunks.py --kmemleak` aggregates per-chunk reports and the
   summary JSON records a leak count per chunk — leak attribution then
   narrows to ≤25 tests for free.
3. **CI**: a `workflow_dispatch`/nightly job (not the per-PR gate — 2×
   runtime and leak-noise triage don't belong in the merge path) running
   the full sweep + corpus with kmemleak, uploading reports as
   artifacts, failing only on `unreferenced object` count > 0 after the
   FLAKY-style allowlist treatment for any recurring false positives.
4. **veristat**: same scan block in its init; 150-object slices cost
   ~30 s each, so even per-PR veristat-with-kmemleak would be cheap if
   ever wanted.

## Caveats

- False negatives are inherent (see positive control) — kmemleak proves
  presence, never absence, of leaks.
- Both measured workloads scanned clean, so day-one integration value is
  regression *detection* (a future patch introducing a leak), not
  paying down existing leaks.
- `DEBUG_KMEMLEAK_AUTO_SCAN` (10-min timer) is irrelevant for short
  guests; explicit scans are what matter.
