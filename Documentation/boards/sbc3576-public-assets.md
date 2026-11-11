# Assets needed by a third party

This is the minimal distribution inventory for reproducing the SBC3576 HAOS
port. It is separate from the owner's historical/recovery archive. The exact
identities are in [sbc3576-public-assets.json](sbc3576-public-assets.json).

## Build the OS from source

Clone this repository at `sbc3576-18.5` and initialize its Buildroot submodule.
The current board build uses **three vendor input files**, all included in Git
under `vendor/sbc3576-inputs/`:

| File | Exact size | Role |
| --- | ---: | --- |
| `idbloader.img` | 344,064 bytes (336 KiB) | Vendor SDK initial DDR/loader image |
| `uboot.img` | 4,194,304 bytes (4 MiB) | Vendor SDK U-Boot/firmware container |
| `rtl8852be-sdk-source.tar.gz` | 10,227,273 bytes (about 9.75 MiB) | Vendor Wi-Fi driver source |

Together these are 14,765,641 bytes, about **14.08 MiB**. Both `.img` files
come from the SDK; neither is a dump of the owner's board. Run
`python3 tools/sbc3576/prepare_inputs.py` after cloning; it verifies and stages
the tracked files automatically. No Git LFS or separate input download is needed.

The other dependencies already have a public source route:

- HAOS board configuration, boot script, kernel patches and verification tools:
  this Git repository.
- Buildroot: the pinned `home-assistant/buildroot` submodule.
- Linux: the pinned `rockchip-linux/kernel` commit; downloaded during the build.
- DTB: built from the patched kernel tree. No separately supplied DTB is needed.
- Normal userspace packages and HA containers: fetched by the HAOS build process.

This is an online build path, not an offline mirror of all dependencies. It
reproduces the port's inputs, not byte-identical images across different package
mirrors, timestamps and signing keys. A third-party builder creates their own
development signing identity; the owner's private signing key is not needed.

## Install a prebuilt image

For a user who does not build the OS, download
**`haos_sbc3576-18.5.img.xz`**, 440,438,364 bytes (about 420 MiB), together
with its SHA-256 and the installation instructions from
[the experimental release](https://github.com/mir-stream/haos-sbc3576/releases/tag/sbc3576-18.5-20261111).

The image already contains the loader region, kernel, DTB and Wi-Fi module.
The three build inputs, standalone `Image`/DTB and uncompressed `.img` are not
additional downloads for this workflow. The uncompressed image is recovered
from the `.xz` file.

The hardware-tested installation preserved the sample board's existing factory
loader. The SDK loader embedded in the full image is different, and blank-board
installation of that chain has not been tested. Sharing the image does not turn
the historical installation record into a verified universal flashing procedure.
Use the [installation/recovery record](sbc3576-recovery.md) to understand that
limit before planning a new board's installation.

## Optional update artifact

**`haos_sbc3576-18.5.raucb`**, 162,307,615 bytes (about 155 MiB), is useful
for the update workflow, but is not required for the initial build or install.
The receiving system must have compatible `haos-sbc3576` slots and trust the
bundle's signing certificate. A self-build with a different development key
does not automatically trust this bundle. This preserved bundle is the same
baseline version, not a newer firmware release.

## Distribution metadata

The release contains the two large images, `SHA256SUMS` for those two files, and
`MANIFEST.json` with the Git input locations, versioned download URLs and hashes.
The three Git inputs have their own `vendor/sbc3576-inputs/SHA256SUMS`.
The tag `sbc3576-18.5-20261111` includes the packaged inputs and download docs;
`sbc3576-port-18.5-20261111` records the earlier preserved port code. The archived
OS images have not been rebuilt or changed by this packaging step.

Vendor component notices are retained with the inputs; the repository's own
license does not replace component-specific notices. Future build outputs need
their own hashes and versioned release record.

The full damaged SDK, the large recovered SDK archive, the old overlay archive,
standalone kernel/DTB artifacts, household network-guard images and all
owner-device backups are unnecessary in this minimal distribution set.
