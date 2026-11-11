# SBC3576 bring-up and recovery record

## Hardware identification and access

The tested device is a Boardcon SBC3576 using RK3576, 32 GB-class eMMC
(31,272,730,624 bytes on this sample), an RTL8852BE PCIe Wi-Fi module and a
factory Linux 6.1.99 image. The tested UART baud rate is **1,500,000**. UART
and USB ADB were both usable once the board had the correct power supply.
Use the board's schematic/manual for power and pin assignments; do not infer
them from another board with the same SoC.

The factory U-Boot was preserved on the tested board. Its 4 MiB image hash was
`d3ba7c58546d4b07e8dbb650d1bfa0057d7b6354a8a3889508838cbe1323f3b3`.
The SDK U-Boot used in generated full-disk images has a different hash
(`9339a13a...`; see the asset manifest). Therefore successful preserved-loader
boot does not prove that overwriting the loader on a blank board is equivalent.

## SDK recovery

The supplied Linux SDK archive failed bzip2 CRC validation. Recopying did not
provide a fully valid archive. Recovery scanned bzip2 block boundaries and
retained CRC-valid blocks, then recovered selected porting files. It did not
repair every SDK component or firmware image.

- 26,334 valid and 32 bad compressed blocks were reported by the recovery run.
- 112,891 regular porting-source files were verified after reconstruction.
- 13 filename case conflicts were repaired on a case-sensitive volume.
- The kernel base was identified as public Rockchip commit
  `fee15752e3222f759d20871fff1e66989c3f1e88`.
- The vendor patch was applied without fuzz and compared with the recovered
  source. The HAOS build contains that patch plus its two compatibility patches.
- The generated board DTB matched the actual board dump byte for byte.

The recovered source archives and original vendor material remain separate
assets. Their provenance and hashes allow a later recovery to be checked against
the same inputs even if a download link changes.

## Installation performed on this sample

A full eMMC backup and separate boot0/boot1 backups were taken first. The full
backup is a read of a running system, not an atomic filesystem snapshot. It was
checked for compressed-stream integrity, length, GPT and boot-region consistency;
full restoration has not been tested. RPMB was not backed up.

The historical installation replaced OS partitions but preserved bytes
32,768 through 16,777,215 containing the working loader chain. It wrote the HAOS
body beginning at byte 16,777,216, a separately prepared backup GPT at the
physical end of eMMC, then the primary GPT. Written ranges were CRC-checked.
The old plan/image predates the final boot fixes and is retained only as evidence.

Those exact sector numbers are sample-specific history, **not a reusable flash
script**. For any new install, identify the destination and actual capacity,
back up its own loader/partitions, derive both GPTs for that capacity, and ensure
the write ranges preserve the intended loader. The corrected baseline image is
identified in the manifest; do not reuse the initial `haos-sbc3576-emmc.img`
from the bring-up directory as a current installer.

`rkdeveloptool` was built on the Mac from public commit
`304f073752fd25c854e1bcf05d8e7f925b1f4e14`, but USB Loader/MaskROM flashing with
that tool was not hardware-tested. It is not presented as a verified recovery
route. UART access to the preserved U-Boot was the actual bring-up path.

## Boot failures and fixes

### Legacy script rejected by vendor U-Boot

The vendor U-Boot expects the script length-table terminator `0xffffffff`.
Upstream `mkimage` emits `0x00000000`. The board hook invokes
`patch-boot-script.py` after `mkimage` to replace the terminator and recompute
both data and header CRCs. The decoded script must match `uboot-boot.ush`.

### Kernel waiting for the factory root partition

Setting U-Boot's `bootargs` alone was insufficient. This BSP merges the DTB's
`/chosen/bootargs` and `bootargs_ext` after the environment, replacing the HAOS
root selection with factory values. The script now clears both DTB properties
before invoking `booti` with `root=PARTUUID=...` and `rauc.slot=A/B`.

### GPT at the wrong end of the device

The small build image and the actual 32 GB-class eMMC have different ends.
The backup GPT was relocated to the physical device end during installation.
Both table copies and recorded flash ranges were checked afterward.

After these corrections the board booted automatically, marked slot A good,
started Docker/Supervisor, and expanded its data partition. Network configuration
later allowed Core download and onboarding.

## Recovery assets to keep privately

Keep the original `mmcblk0.img.gz`, boot0/boot1 backups, and the original loader
backup. They may contain device-specific state and must not be uploaded as public
release assets. Keep the existing HAOS update-signing private key and certificate
separately from Git. The manifest identifies the classes of private backup,
while exact local locations live in the owner's private inventory.

A later derivative was signed, installed, and booted in both A and B slots.
Deliberate bad-update rollback, loss of power during writes, microSD recovery,
and a complete factory restore remain untested. Do not reboot a remotely managed
board just to re-run archival checks: one Wi-Fi/default-route startup incident
caused a roughly one-hour VPN outage, and its initiating cause was not isolated.
