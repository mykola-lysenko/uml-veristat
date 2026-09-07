# Parallel signing-key generation — 2026-09-07

The first pahole CI gate failed `atomics`, `fentry_fexit`, `fentry_test`
and `fexit_test` with ENOKEY, including the standalone retry. These use
three signed light skeletons. The other 625 tests passed, with six newly
enabled LLVM 23 passes. Package and all five distro checks passed.

The selftests Makefile gives the private key and DER certificate an
independent multi-target generation rule. Parallel make can run it twice,
allowing the compiled certificate header to capture one key pair while
skeletons are signed with another.

A small parallel Make harness using the actual upstream OpenSSL key
setup script reproduced two generations in all eight fresh builds. Three
of eight completed successfully with a certificate header whose public
key did not match the final private key. The fixed dependency graph
makes the private key the sole generation target and derives the DER
certificate from it. All eight fixed runs generated once and matched;
deleting and regenerating just the certificate preserved the private key.
See the [original results](2026-09-07-key-generation-old.json) and
[fixed results](2026-09-07-key-generation-fixed.json). No private keys
are included in these reports.

Patch 0024 now covers this dependency race as well as private-key changes.
The kernel patch count stays 29. All patches apply cleanly and pass
checkpatch. Running the actual patched selftests Makefile with `-j32`
also generates the pair once; the generated C header matches DER bytes
and its public key matches the private key. This changes a build recipe, not BPF or
kernel runtime code, and adds no gate exclusions. Refreshed CI is required
to confirm the full build and runtime path.
