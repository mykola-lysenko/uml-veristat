#!/bin/bash
# Build and run the probe-mem guard microbenchmark inside the UML guest.
#
# Usage: benchmarks/probe-mem/run.sh [label]
#   REPEAT (default 2000000)  test_run repetitions per trial
#   TRIALS (default 7)        trials per program
#
# Prints per-trial average ns for guard_bench (192 guard sites) and
# plain_bench (same loads, no guards), plus jited instruction counts and
# guard-site stats measured from the disassembly. Results land in
# .build/probe-mem-bench/<label>/.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD="${ROOT}/.build"
LABEL="${1:-run}"
OUT="${BUILD}/probe-mem-bench/${LABEL}"
REPEAT="${REPEAT:-2000000}"
TRIALS="${TRIALS:-7}"

CLANG="${BUILD}/llvm-install/bin/clang"
BPFTOOL="${BUILD}/bpftool-output/bpftool"
VMLINUX_H_DIR="${BUILD}/bpftool-output"
UML="${BUILD}/bpf-next/linux"
OBJ="${SCRIPT_DIR}/probe_mem_bench.bpf.o"

mkdir -p "${OUT}"

if [ ! -f "${OBJ}" ] || [ "${SCRIPT_DIR}/probe_mem_bench.bpf.c" -nt "${OBJ}" ]; then
    echo "[bench] compiling probe_mem_bench.bpf.o"
    "${CLANG}" -O2 -g -target bpf -D__TARGET_ARCH_x86 \
        -I "${VMLINUX_H_DIR}" -I "${ROOT}/.build/bpf-next/tools/lib" \
        -I "${ROOT}/.build/bpf-next/tools/bpf/resolve_btfids/libbpf/include/bpf" \
        -c "${SCRIPT_DIR}/probe_mem_bench.bpf.c" -o "${OBJ}"
fi

# 64-byte all-zero frame is a valid XDP test_run input
head -c 64 /dev/zero > "${OUT}/pkt.bin"

INIT="${OUT}/init"
cat > "${INIT}" <<EOF
#!/bin/sh
PATH=/usr/sbin:/usr/bin:/sbin:/bin:\$PATH
mount -t proc proc /proc 2>/dev/null || true
mount -t sysfs sysfs /sys 2>/dev/null || true
mkdir -p /sys/fs/bpf && mount -t bpf bpf /sys/fs/bpf 2>/dev/null || true
{
  ${BPFTOOL} prog loadall ${OBJ} /sys/fs/bpf/pmb && echo LOADED
  for prog in guard_bench plain_bench; do
    ${BPFTOOL} prog dump jited pinned /sys/fs/bpf/pmb/\${prog} > ${OUT}/\${prog}.jited.txt
    echo "== \${prog} =="
    t=0
    while [ \$t -lt ${TRIALS} ]; do
      ${BPFTOOL} prog run pinned /sys/fs/bpf/pmb/\${prog} \\
          data_in ${OUT}/pkt.bin repeat ${REPEAT} 2>&1 | grep -i "duration\|error" || true
      t=\$((t+1))
    done
  done
} > ${OUT}/bench.log 2>&1
sync
halt -f 2>/dev/null || poweroff -f 2>/dev/null || echo o > /proc/sysrq-trigger
EOF
chmod +x "${INIT}"

echo "[bench] booting UML (${TRIALS} trials x ${REPEAT} reps per prog)"
"${UML}" mem=1792M rootfstype=hostfs hostfs=/ rw "init=${INIT}" \
    quiet loglevel=0 con=null con0=null >/dev/null 2>&1 || true

echo "[bench] guest log:"
cat "${OUT}/bench.log"

echo
echo "[bench] static stats:"
python3 - "$OUT" "$ROOT" <<'PYEOF'
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(sys.argv[2]) / "scripts"))
from jit_expansion import scan_jited
for prog in ("guard_bench", "plain_bench"):
    p = pathlib.Path(sys.argv[1]) / f"{prog}.jited.txt"
    if p.exists():
        s = scan_jited(p.read_text())
        print(f"  {prog}: jited_insns={s['jited_insns']} "
              f"guard_sites={s['guard_sites']} guard_insns={s['guard_insns']}")
PYEOF
