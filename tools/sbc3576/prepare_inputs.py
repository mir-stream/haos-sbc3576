#!/usr/bin/env python3
"""Verify and stage local SBC3576 build inputs. No device or network access."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="?", type=Path,
                        default=root / "vendor/sbc3576-inputs",
                        help="input directory (default: tracked vendor/sbc3576-inputs)")
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        parser.error("Python 3.12 or later is required for safe tar extraction")
    manifest = json.loads((root / "Documentation/boards/sbc3576-assets.json").read_text())
    records = {item["name"]: item for item in manifest["build_inputs"]}
    firmware = root / "buildroot-external/board/boardcon/sbc3576/firmware"
    target = root / "vendor/sbc3576/external/rkwifibt/drivers/rtl8852be"
    if target.exists():
        parser.error("extracted Wi-Fi source already exists; use a clean checkout to re-stage it")
    for name, item in records.items():
        source = args.inputs / name
        if not source.is_file() or source.stat().st_size != item["bytes"] or digest(source) != item["sha256"]:
            parser.error(f"missing or mismatched input: {name}")
        if name.endswith(".img") and (firmware / name).exists():
            if digest(firmware / name) != item["sha256"]:
                parser.error(f"existing firmware differs: {name}; refusing to replace it")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent, prefix=".stage-") as staging:
        staging = Path(staging)
        with tarfile.open(args.inputs / "rtl8852be-sdk-source.tar.gz") as archive:
            members = archive.getmembers()
            if any(Path(m.name).parts[:1] != ("rtl8852be",) for m in members):
                parser.error("unexpected top-level archive path")
            archive.extractall(staging, filter="data")
        if not (staging / "rtl8852be/Makefile").is_file():
            parser.error("Wi-Fi archive does not contain its Makefile")
        (staging / "rtl8852be").rename(target)
    for name in ("idbloader.img", "uboot.img"):
        if not (firmware / name).exists():
            shutil.copy2(args.inputs / name, firmware / name)
    print("Verified three inputs; firmware and Wi-Fi source staged in Git-ignored paths.")


if __name__ == "__main__":
    main()
