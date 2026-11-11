# Building the SBC3576 port

## Required inputs

For the minimal third-party distribution set, see
[public assets](sbc3576-public-assets.md). It separates build inputs from
prebuilt installation/update files and excludes owner-specific backups.

The public repository contains the board support, kernel patches, configuration,
verification tools and these three vendor inputs in `vendor/sbc3576-inputs/`:

| File | Purpose |
| --- | --- |
| `idbloader.img` | SDK DDR/initial loader image; 344,064 bytes |
| `uboot.img` | SDK U-Boot/firmware container; 4,194,304 bytes |
| `rtl8852be-sdk-source.tar.gz` | Recovered Wi-Fi source; 10,227,273 bytes |

Their exact SHA-256 values and original SDK paths are in
[sbc3576-assets.json](sbc3576-assets.json). They are ordinary Git files, not Git
LFS pointers. Cloning this branch includes the board-specific inputs; there is
no separate owner/vendor download step. Component notices and provenance are
recorded in `vendor/sbc3576-inputs/README.md`.

The Linux base is downloaded from the pinned public Rockchip commit. It does
not require the entire damaged 17 GB vendor SDK. The larger recovered source
archive is retained as recovery/provenance material.

## Prepare a checkout

Use a case-sensitive Linux filesystem for building. The original preparation
used a case-sensitive source volume on macOS plus an isolated Linux builder.
These instructions use Python 3.12+ and a Linux Docker environment supporting
the privileged HAOS builder. Starting a Docker runtime is a separate local
action; the preparation/verification commands do not start one.

```sh
git clone --branch sbc3576-18.5 https://github.com/mir-stream/haos-sbc3576.git
cd haos-sbc3576
git submodule update --init
python3 tools/sbc3576/prepare_inputs.py
```

The helper defaults to the three files tracked in `vendor/sbc3576-inputs/` and
verifies all hashes before copying/extracting. An optional directory argument
can still select an external copy with the same hashes. Firmware is placed in the board's ignored
`firmware/` directory; Wi-Fi source is placed under ignored `vendor/sbc3576/`.
Existing different firmware or an existing extracted Wi-Fi tree is not replaced.

## Build

```sh
tools/sbc3576/build-in-container.sh
```

The wrapper uses the repository's upstream Dockerfile/entrypoint, mounts the
verified vendor input read-only at `/vendor`, and runs `make sbc3576`.
It does not mount a host Docker socket or invoke a flasher. It requires
privileged container support for the upstream HAOS build process; use a dedicated
Linux build environment without an attached production board. The original
successful build used a fresh nested Docker daemon with the `vfs` storage
driver; if a build fails, keep its logs before retrying.

Outputs are under `output/images/`:

- `haos_sbc3576-18.5.img.xz`: compressed whole-disk installation image.
- `haos_sbc3576-18.5.raucb`: signed update bundle for this board identity.
- `Image`: kernel, also embedded in the disk/update images.
- `rk3576-evb1-v10-linux.dtb`: board DTB, also embedded in the kernel slots.

The preserved baseline installer and update bundle are also downloadable from
[the experimental release](https://github.com/mir-stream/haos-sbc3576/releases/tag/sbc3576-18.5-20261111).
The release contains their checksums and manifest. The kernel/board code is the
same preserved baseline; packaging the inputs into Git does not constitute a
new full OS build.

These paths and commands were normalized when preserving the port. The original
full build passed; the normalized wrapper has syntax/preparation validation,
not a newly completed full build. A first clean build with this wrapper remains
an explicit reproduction check.

## Signing identity

HAOS generates a development `key.pem` and `cert.pem` in the build root if they
are absent. Both are ignored by Git. A newly generated key is fine for a new
installation, but an existing device will only accept update bundles signed by
a trusted key. To update the existing deployment, supply its preserved key and
certificate before building. The private key is in the separate private backup,
not in the public asset manifest or repository.

Do not replace an existing deployment's signing key casually. Restoring the
source alone does not restore its update-signing authority. No signing keys were
rotated and no images were deployed during the repository archival work.

## Offline checks

```sh
python3 tools/sbc3576/test_boot_policy.py
python3 tools/sbc3576/verify_image.py output/images/haos_sbc3576-18.5.img \
  --artifacts output/images
```

The first command exercises 13 boot-policy cases using mocked commands in Bash.
It never touches a block device and does not emulate the real U-Boot interpreter.
The second validates GPT CRCs/layout, embedded loader hashes, boot script CRCs
and source content, the A-slot kernel and DTB, initial empty B/state partitions,
and EROFS feature flags. It does not mount, write to, or boot a board.

The historical record additionally includes kernel configuration, module,
EROFS/ext4 and RAUC-signature checks. These are not replaced by the structural
checker, and none establishes power-loss or hardware recovery behavior.
