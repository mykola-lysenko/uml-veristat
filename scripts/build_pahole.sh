#!/usr/bin/env bash
# Build the repository's patched pahole and track its source identity.
set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 SOURCE_DIR BUILD_DIR INSTALL_DIR" >&2
    exit 2
fi

src="$1"
build="$2"
install="$3"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
patch_dir="${script_dir}/../patches/pahole"

if [ ! -d "${src}/.git" ]; then
    git clone --depth=1 --branch "${PAHOLE_TAG:-v1.31}" \
        "${PAHOLE_REPO:-https://github.com/acmel/dwarves.git}" "${src}"
fi

for patch in "${patch_dir}"/*.patch; do
    [ -f "${patch}" ] || { echo "No pahole patches found in ${patch_dir}" >&2; exit 1; }
    if git -C "${src}" apply --check "${patch}" 2>/dev/null; then
        git -C "${src}" apply "${patch}"
        echo "pahole: applied $(basename "${patch}")"
    elif ! git -C "${src}" apply --reverse --check "${patch}" 2>/dev/null; then
        echo "Cannot apply pahole patch $(basename "${patch}") to ${src}; review the source checkout." >&2
        exit 1
    fi
done

# Include local source edits as well as HEAD and the patch/build recipe.
# Exclude absolute paths so identical inputs have the same identity in CI.
build_id=$(
    {
        git -C "${src}" rev-parse HEAD
        git -C "${src}" diff --no-ext-diff --no-textconv --binary HEAD
        sha256sum "${BASH_SOURCE[0]}" "${patch_dir}"/*.patch | cut -d ' ' -f1
    } | sha256sum | cut -d ' ' -f1
)
stamp="${install}/.uml-build-id"
if [ "${REBUILD_PAHOLE:-0}" != 1 ] && [ -x "${install}/bin/pahole" ] && \
   [ -f "${stamp}" ] && [ "$(cat "${stamp}")" = "${build_id}" ]; then
    "${install}/bin/pahole" --version
    echo "pahole: source and patch identity unchanged; reusing installation."
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
