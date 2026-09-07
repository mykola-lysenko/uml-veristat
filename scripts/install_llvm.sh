#!/usr/bin/env bash
# Install one explicit LLVM release; never fall back to a different release.
set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 RELEASE WORK_DIR INSTALL_DIR" >&2
    exit 2
fi
release="$1"
work="$2"
install="$3"
version="${release#llvmorg-}"
version="${version%%-rc*}"

tools_work() {
    local prefix="$1" tool
    for tool in clang llc llvm-config llvm-strip llvm-objcopy; do
        [ -x "${prefix}/bin/${tool}" ] && \
            "${prefix}/bin/${tool}" --version >/dev/null 2>&1 || return 1
    done
    [ "$("${prefix}/bin/clang" -dumpversion)" = "${version}" ] && \
        [ "$("${prefix}/bin/llvm-config" --version)" = "${version}" ]
}

if [ "${REUSE_LLVM:-0}" = 1 ]; then
    if ! tools_work "${install}"; then
        echo "ERROR: --reuse-llvm requires usable LLVM ${version} at ${install}." >&2
        echo "Set LLVM_RELEASE_TAG and LLVM_INSTALL explicitly to compare another installed release." >&2
        exit 1
    fi
    echo "LLVM: reusing requested release ${release}."
    exit 0
fi
if [ "${REBUILD_LLVM:-0}" != 1 ] && [ "${DO_UPDATE:-0}" != 1 ] && tools_work "${install}"; then
    echo "LLVM: installed tools match ${release}; reusing installation."
    exit 0
fi

mkdir -p "${work}"
metadata=$(mktemp "${work}/llvm-release.XXXXXX.json")
staging=""
cleanup() {
    rm -f "${metadata}"
    [ -z "${staging}" ] || rm -rf "${staging}"
}
trap cleanup EXIT

curl_args=(-fsSL -H 'Accept: application/vnd.github+json' \
    -H 'X-GitHub-Api-Version: 2022-11-28' -H 'User-Agent: uml-veristat-build')
if [ -n "${GITHUB_TOKEN:-${GH_TOKEN:-}}" ]; then
    curl_args+=(-H "Authorization: Bearer ${GITHUB_TOKEN:-${GH_TOKEN}}")
fi
api="https://api.github.com/repos/llvm/llvm-project/releases/tags/${release}"
if ! curl "${curl_args[@]}" "${api}" -o "${metadata}"; then
    echo "ERROR: Cannot resolve pinned LLVM release ${release}; no alternate release will be selected." >&2
    exit 1
fi

# Prefer the oldest Ubuntu archive when older releases offer several builds.
# Verify published digests; older releases may not expose one in the API.
asset=$(python3 - "${metadata}" "${release}" <<'PY'
import json, re, sys
r = json.load(open(sys.argv[1]))
if r.get('tag_name') != sys.argv[2]:
    sys.exit('ERROR: LLVM release response does not match the requested tag')
assets = [a for a in r.get('assets', []) if a['name'].endswith('.tar.xz')
          and ('Linux-X64' in a['name'] or 'x86_64-linux-gnu' in a['name'])]
def osver(a):
    m = re.search(r'ubuntu-(\d+)\.(\d+)', a['name'])
    return tuple(map(int, m.groups())) if m else (999, 0)
assets.sort(key=osver)
if not assets:
    sys.exit('ERROR: requested LLVM release has no Linux x86-64 archive')
a = assets[0]
digest = a.get('digest') or ''
if digest and not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
    sys.exit('ERROR: unrecognized LLVM archive digest')
print(a['browser_download_url'])
print(digest.split(':', 1)[1] if digest else 'unpublished')
PY
)
url="${asset%%$'\n'*}"
digest="${asset##*$'\n'}"
archive="${work}/$(basename "${url}")"
echo "LLVM release: ${release}"
echo "Tarball URL: ${url}"
if [ ! -f "${archive}" ]; then
    curl --fail --location --retry 3 --output "${archive}.part" "${url}"
    mv "${archive}.part" "${archive}"
fi
digest_verified=0
if [ "${digest}" != unpublished ]; then
    printf '%s  %s\n' "${digest}" "${archive}" | sha256sum --check --status || {
        echo "ERROR: LLVM archive checksum mismatch: ${archive}" >&2
        exit 1
    }
    digest_verified=1
else
    digest=$(sha256sum "${archive}" | cut -d ' ' -f1)
fi

mkdir -p "$(dirname "${install}")"
staging=$(mktemp -d "${install}.new.XXXXXX")
tar -xf "${archive}" -C "${staging}" --strip-components=1
if ! tools_work "${staging}"; then
    echo "ERROR: downloaded LLVM ${version} tools cannot run on this host; existing installation preserved." >&2
    exit 1
fi
python3 - "${staging}" "${release}" "${url}" "${digest}" "${digest_verified}" <<'PY'
import json, pathlib, re, subprocess, sys
prefix = pathlib.Path(sys.argv[1])
line = subprocess.check_output([str(prefix/'bin/clang'), '--version'], text=True).splitlines()[0]
m = re.search(r'\b[0-9a-f]{40}\b', line)
(prefix/'.uml-llvm-release.json').write_text(json.dumps({
    'release': sys.argv[2], 'archive_url': sys.argv[3], 'archive_sha256': sys.argv[4],
    'archive_digest_verified': sys.argv[5] == '1',
    'clang_version': line, 'commit': m.group(0) if m else 'unknown',
}, indent=2) + '\n')
PY
if [ -e "${install}" ]; then
    backup=$(mktemp -d "${install}.previous.XXXXXX")
    mv "${install}" "${backup}/install"
    echo "LLVM: previous installation retained at ${backup}/install"
fi
mv "${staging}" "${install}"
staging=""
"${install}/bin/clang" --version
