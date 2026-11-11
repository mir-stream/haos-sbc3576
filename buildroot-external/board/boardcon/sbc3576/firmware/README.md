# External boot firmware

Supply the exact `idbloader.img` and `uboot.img` listed in `SHA256SUMS`.
They are local build inputs and are ignored by Git.

The existing board's factory U-Boot was retained during the verified eMMC install;
the SDK binary included in a generated installation image is not identical to it.
See `Documentation/boards/sbc3576-recovery.md` for this distinction and the
private recovery backup inventory.

Use `python3 tools/sbc3576/prepare_inputs.py /path/to/inputs` from the repository
root to verify and install the inputs. Do not use files from an unrelated RK3576
board just because the filenames match.
