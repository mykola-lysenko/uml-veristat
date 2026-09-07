#!/usr/bin/env bash
# Build the pinned upstream pahole and track its source identity.
set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 SOURCE_DIR BUILD_DIR INSTALL_DIR" >&2
    exit 2
fi

src="$1"
build="$2"
install="$3"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_ref="${PAHOLE_TAG:-$(cat "${script_dir}/../pahole-commit")}"
source_repo="${PAHOLE_REPO:-https://github.com/acmel/dwarves.git}"

if [ ! -d "${src}/.git" ]; then
    git init -q "${src}"
    git -C "${src}" remote add origin "${source_repo}"
fi

# Never overwrite a developer's edits while selecting the requested revision.
if ! git -C "${src}" diff --quiet HEAD -- 2>/dev/null && \
   git -C "${src}" rev-parse --verify HEAD >/dev/null 2>&1; then
    echo "pahole source has local edits: ${src}; use a clean checkout." >&2
    exit 1
fi
if ! resolved=$(git -C "${src}" rev-parse --verify "${source_ref}^{commit}" 2>/dev/null); then
    git -C "${src}" fetch --depth=1 "${source_repo}" "${source_ref}"
    resolved=$(git -C "${src}" rev-parse 'FETCH_HEAD^{commit}')
    if [[ "${source_ref}" =~ ^[0-9a-f]{40}$ ]] && [ "${resolved}" != "${source_ref}" ]; then
        echo "pahole fetch did not resolve requested commit ${source_ref}" >&2
        exit 1
    fi
fi
if [ "$(git -C "${src}" rev-parse --verify HEAD 2>/dev/null || true)" != "${resolved}" ]; then
    git -C "${src}" checkout --detach "${resolved}"
fi

# Include the source revision and build recipe.
# Exclude absolute paths so identical inputs have the same identity in CI.
build_id=$(
    {
        git -C "${src}" rev-parse HEAD
        sha256sum "${BASH_SOURCE[0]}" | cut -d ' ' -f1
    } | sha256sum | cut -d ' ' -f1
)
stamp="${install}/.uml-build-id"
if [ "${REBUILD_PAHOLE:-0}" != 1 ] && [ -x "${install}/bin/pahole" ] && \
   [ -f "${stamp}" ] && [ "$(cat "${stamp}")" = "${build_id}" ]; then
    "${install}/bin/pahole" --version
    echo "pahole: source and recipe identity unchanged; reusing installation."
    exit 0
fi

# Invalidate first: an interrupted build must never reuse an old success stamp.
rm -f "${stamp}"
if [ "${REBUILD_PAHOLE:-0}" = 1 ]; then
    rm -rf "${build}"
fi
cmake -S "${src}" -B "${build}" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="${install}" \
    -DCMAKE_INSTALL_RPATH="${install}/lib" \
    -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON \
    -DLIB_INSTALL_DIR=lib \
    -DLIBBPF_EMBEDDED=ON
cmake --build "${build}" -j "$(nproc)"
cmake --install "${build}"
"${install}/bin/pahole" --version
printf '%s\n' "${build_id}" > "${stamp}"
