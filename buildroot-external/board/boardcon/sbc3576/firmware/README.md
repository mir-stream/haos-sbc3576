# Staged boot firmware

The exact `idbloader.img` and `uboot.img` listed in `SHA256SUMS` are tracked in
`vendor/sbc3576-inputs/`. Their staged copies in this directory are ignored by Git.

The existing board's factory U-Boot was retained during the verified eMMC install;
the SDK binary included in a generated installation image is not identical to it.
See `Documentation/boards/sbc3576-recovery.md` for this distinction and the
private recovery backup inventory.

Use `python3 tools/sbc3576/prepare_inputs.py` from the repository
root to verify and stage the inputs. Do not use files from an unrelated RK3576
board just because the filenames match.
