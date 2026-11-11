#!/usr/bin/env bash
set -euo pipefail

port_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
port_cache=${SBC3576_BUILD_CACHE:-${HOME}/.cache/haos-sbc3576}
port_image=haos-sbc3576-builder:18.5

if [[ ! -f "$port_root/vendor/sbc3576/external/rkwifibt/drivers/rtl8852be/Makefile" ]]; then
    echo "Run python3 tools/sbc3576/prepare_inputs.py first." >&2
    exit 1
fi
if [[ ! -f "$port_root/buildroot/Makefile" ]]; then
    echo "Run git submodule update --init first." >&2
    exit 1
fi
if [[ $(id -u) -eq 0 ]]; then
    echo "Run this wrapper as a non-root user, as with upstream scripts/enter.sh." >&2
    exit 1
fi
mkdir -p "$port_cache"
docker build -t "$port_image" "$port_root"
port_run_args=(--rm --privileged)
if [[ -t 0 ]]; then port_run_args+=(-it); fi
docker run "${port_run_args[@]}" \
    --mount "type=bind,source=$port_root,target=/build" \
    --mount "type=bind,source=$port_cache,target=/cache" \
    --mount "type=bind,source=$port_root/vendor/sbc3576,target=/vendor,readonly" \
    -e "BUILDER_UID=$(id -u)" -e "BUILDER_GID=$(id -g)" \
    "$port_image" bash -c 'make sbc3576'
