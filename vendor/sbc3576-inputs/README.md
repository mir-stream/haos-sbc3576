# SBC3576 vendor build inputs

These three unchanged files are tracked directly in Git. Run
`python3 tools/sbc3576/prepare_inputs.py` from the repository root to verify
their hashes and stage/extract them for the build.

| File | Vendor SDK origin |
| --- | --- |
| `idbloader.img` | `u-boot/rk3576_idblock_v1.09.107.img` |
| `uboot.img` | `u-boot/uboot.img` |
| `rtl8852be-sdk-source.tar.gz` | `external/rkwifibt/drivers/rtl8852be` |

The source SDK was `rk3576_linux6.1_sdk-20250623.tar.bz2` supplied with the
Boardcon SBC3576. The driver archive excludes generated objects and preserves
the original source notices. The loader files are SDK binaries, not dumps of a
configured device. They do not include the owner's HA accounts, network setup,
device backup or update-signing private key.

Realtek driver source headers identify Realtek copyright and GPL version 2.
The U-Boot/initial-loader containers combine vendor boot components; retain
their original provenance and component notices. The root HAOS license does not
relicense these third-party components.

`SHA256SUMS` identifies the exact bytes. For details on the tested factory-loader
path versus the SDK loader contained in generated images, see
[the recovery record](../../Documentation/boards/sbc3576-recovery.md).
