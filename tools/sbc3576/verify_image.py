"""Read-only structural checks of the generated HAOS disk image; no hardware boot."""
import argparse
import hashlib
import json
import struct
import uuid
import zlib
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Disk:
    def __init__(self, path):
        self.path = path
        self.file = path.open('rb')
        self.size = path.stat().st_size

    def read(self, offset, size):
        self.file.seek(offset)
        data = self.file.read(size)
        assert len(data) == size, (offset, size, len(data))
        return data

    def gpt(self, lba):
        header = bytearray(self.read(lba * 512, 512))
        assert header[:8] == b'EFI PART'
        header_size, crc = struct.unpack_from('<II', header, 12)
        assert 92 <= header_size <= 512
        header[16:20] = b'\0' * 4
        assert zlib.crc32(header[:header_size]) == crc
        current, other, first, last = struct.unpack_from('<4Q', header, 24)
        assert current == lba
        entry_lba, count, size, entry_crc = struct.unpack_from('<QIII', header, 72)
        entries = self.read(entry_lba * 512, count * size)
        assert zlib.crc32(entries) == entry_crc
        parts = []
        for i in range(count):
            entry = entries[i * size:(i + 1) * size]
            if not any(entry[:16]):
                continue
            start, end = struct.unpack_from('<QQ', entry, 32)
            assert first <= start <= end <= last
            parts.append(dict(number=i + 1,
                              name=entry[56:128].decode('utf-16le').rstrip('\0'),
                              uuid=str(uuid.UUID(bytes_le=entry[16:32])),
                              offset=start * 512, size=(end - start + 1) * 512))
        return other, parts

    def is_zero(self, part):
        for pos in range(0, part['size'], 4 * 1024 * 1024):
            if any(self.read(part['offset'] + pos, min(4 * 1024 * 1024, part['size'] - pos))):
                return False
        return True

    def fat_file(self, part, filename):
        base = part['offset']
        boot = self.read(base, 512)
        assert boot[510:512] == b'\x55\xaa'
        sector = struct.unpack_from('<H', boot, 11)[0]
        cluster_sectors = boot[13]
        reserved = struct.unpack_from('<H', boot, 14)[0]
        fats = boot[16]
        roots = struct.unpack_from('<H', boot, 17)[0]
        total = struct.unpack_from('<H', boot, 19)[0] or struct.unpack_from('<I', boot, 32)[0]
        fat_sectors = struct.unpack_from('<H', boot, 22)[0] or struct.unpack_from('<I', boot, 36)[0]
        root_sectors = (roots * 32 + sector - 1) // sector
        first_data = reserved + fats * fat_sectors + root_sectors
        cluster_count = (total - first_data) // cluster_sectors
        bits = 12 if cluster_count < 4085 else 16 if cluster_count < 65525 else 32
        cluster_bytes = sector * cluster_sectors
        fat = self.read(base + reserved * sector, fat_sectors * sector)

        def chain(cluster, limit=None):
            chunks = []
            visited = set()
            while cluster >= 2:
                assert cluster not in visited and len(visited) <= cluster_count
                visited.add(cluster)
                chunks.append(self.read(base + (first_data + (cluster - 2) * cluster_sectors) * sector,
                                        cluster_bytes))
                if limit is not None and len(chunks) * cluster_bytes >= limit:
                    break
                if bits == 12:
                    nxt = struct.unpack_from('<H', fat, cluster * 3 // 2)[0]
                    nxt = (nxt >> 4 if cluster & 1 else nxt & 0xfff)
                    end = 0xff8
                elif bits == 16:
                    nxt = struct.unpack_from('<H', fat, cluster * 2)[0]
                    end = 0xfff8
                else:
                    nxt = struct.unpack_from('<I', fat, cluster * 4)[0] & 0x0fffffff
                    end = 0x0ffffff8
                if nxt >= end:
                    break
                cluster = nxt
            return b''.join(chunks)[:limit]

        if bits == 32:
            directory = chain(struct.unpack_from('<I', boot, 44)[0])
        else:
            directory = self.read(base + (reserved + fats * fat_sectors) * sector, root_sectors * sector)
        for pos in range(0, len(directory), 32):
            entry = directory[pos:pos + 32]
            if entry[0] == 0:
                break
            if entry[0] == 0xe5 or entry[11] & 0x18 or entry[11] == 0x0f:
                continue
            name = entry[:8].decode('ascii').rstrip()
            ext = entry[8:11].decode('ascii').rstrip()
            if ext:
                name += '.' + ext
            if name.lower() != filename.lower():
                continue
            cluster = struct.unpack_from('<H', entry, 26)[0]
            if bits == 32:
                cluster |= struct.unpack_from('<H', entry, 20)[0] << 16
            length = struct.unpack_from('<I', entry, 28)[0]
            data = chain(cluster, length) if length else b''
            assert len(data) == length
            return data
        raise AssertionError(f'{filename} missing in {part["name"]}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('image', type=Path)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--artifacts', type=Path, required=True,
                        help='directory containing Image and rk3576-evb1-v10-linux.dtb')
    parser.add_argument('--report', type=Path, help='optional JSON report path')
    args = parser.parse_args()
    root = args.root
    board = root / 'buildroot-external/board/boardcon/sbc3576'
    artifacts = args.artifacts
    manifest = json.loads((root / 'Documentation/boards/sbc3576-assets.json').read_text())
    expected_firmware = {entry['name']: entry for entry in manifest['build_inputs']}
    disk = Disk(args.image)
    backup_lba, parts = disk.gpt(1)
    assert backup_lba == disk.size // 512 - 1
    primary_lba, backup_parts = disk.gpt(backup_lba)
    assert primary_lba == 1 and parts == backup_parts
    names = ['hassos-boot', 'hassos-kernel0', 'hassos-system0', 'hassos-kernel1',
             'hassos-system1', 'hassos-bootstate', 'hassos-overlay', 'hassos-data']
    assert [p['name'] for p in parts] == names
    assert parts[0]['offset'] == 16 * 1024 * 1024
    assert parts[1]['size'] == parts[3]['size'] == 64 * 1024 * 1024
    assert parts[2]['size'] == parts[4]['size'] == 512 * 1024 * 1024
    assert parts[2]['uuid'] == '8d3d53e3-6d49-4c38-8349-aff6859e82fd'
    assert parts[4]['uuid'] == 'a3ec664e-32ce-4665-95ea-7ae90ce9aa20'
    assert parts[5]['uuid'] == '33236519-7f32-4dff-8002-3390b62c309d'
    for left, right in zip(parts, parts[1:]):
        assert left['offset'] + left['size'] <= right['offset']
    firmware = []
    for offset, name in [(32768, 'idbloader.img'), (8388608, 'uboot.img')]:
        entry = expected_firmware[name]
        actual = disk.read(offset, entry['bytes'])
        assert sha(actual) == entry['sha256'], f'{name}: embedded firmware hash mismatch'
        firmware.append(dict(name=name, offset=offset, sha256=sha(actual)))
    boot_script = disk.fat_file(parts[0], 'boot.scr')
    header = bytearray(boot_script[:64])
    magic, crc, timestamp, length, load, entry, data_crc = struct.unpack_from('>7I', header)
    assert magic == 0x27051956
    header[4:8] = b'\0' * 4
    assert zlib.crc32(header) == crc
    assert zlib.crc32(boot_script[64:64 + length]) == data_crc
    assert boot_script[68:72] == b'\xff' * 4, 'Vendor U-Boot requires IMAGE_PARAM_INVAL sentinel'
    script = (board / 'uboot-boot.ush').read_bytes()
    assert boot_script[72:] == script
    kernel = disk.fat_file(parts[1], 'Image')
    dtb = disk.fat_file(parts[1], 'board.dtb')
    assert kernel == (artifacts / 'Image').read_bytes()
    assert dtb == (artifacts / 'rk3576-evb1-v10-linux.dtb').read_bytes()
    assert kernel[56:60] == b'ARM\x64'
    assert dtb[:4] == b'\xd0\x0d\xfe\xed'
    empty = {p['name']: disk.is_zero(p) for p in [parts[3], parts[4], parts[5]]}
    assert all(empty.values())
    sb = disk.read(parts[2]['offset'] + 1024, 128)
    assert struct.unpack_from('<I', sb)[0] == 0xe0f5e1e2
    incompat = struct.unpack_from('<I', sb, 80)[0]
    assert not incompat & ~0x3f, f'EROFS features unsupported by vendor 6.1: {incompat:#x}'
    assert sb[12] == 12, 'Kernel uses 4 KiB pages'
    blocks = struct.unpack_from('<I', sb, 36)[0]
    filesystem_bytes = blocks * (1 << sb[12])
    assert filesystem_bytes <= parts[2]['size']
    result = dict(image=args.image.name, bytes=disk.size, hardware_boot_tested=False,
                  primary_and_backup_gpt_valid=True, partitions=parts,
                  firmware_exact=firmware, boot_script_matches_source=True,
                  boot_script_crcs_valid=True, kernel_sha256=sha(kernel), dtb_sha256=sha(dtb),
                  initial_empty_partitions=empty,
                  erofs=dict(feature_incompat=hex(incompat), kernel_supported_mask='0x3f',
                             block_size=1 << sb[12], filesystem_bytes=filesystem_bytes))
    if args.report:
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
