"""Exercise boot policy with fake device commands; never accesses block devices.

This verifies script control flow in bash, not U-Boot hardware compatibility.
The script must also be packed with mkimage and eventually tested in U-Boot.
"""
import argparse, json, os, subprocess, tempfile
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--report', type=Path, help='optional JSON report path')
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
script = root/'buildroot-external/board/boardcon/sbc3576/uboot-boot.ush'
prelude = r'''
devtype=mmc
devnum=1
ramdisk_addr_r=0x4a200000
kernel_addr_r=0x40400000
fdt_addr_r=0x48300000
setenv() {
    local name="$1"
    shift
    if [ "$#" -eq 0 ]; then unset "$name"; else printf -v "$name" '%s' "$*"; fi
}
run() {
    local name
    for name in "$@"; do eval "${!name}" || return $?; done
}
part() {
    if [ "$1" = uuid ]; then
        case "$3" in
            1:6) value=33236519-7f32-4dff-8002-3390b62c309d ;;
            1:3) value=8d3d53e3-6d49-4c38-8349-aff6859e82fd ;;
            1:5) value=a3ec664e-32ce-4665-95ea-7ae90ce9aa20 ;;
            *) return 1 ;;
        esac
        if [ "${WRONG_UUID:-}" = "$3" ]; then value=unrelated-disk; fi
        printf -v "$4" '%s' "$value"
    elif [ "$1" = start ]; then
        printf -v "$5" '%s' 160000
    else return 1
    fi
}
mmc() {
    case "$1" in
        dev) return 0 ;;
        read) echo READ_STATE >> "$TEST_LOG" ;;
        write)
            echo "WRITE_STATE order=$BOOT_ORDER a=$BOOT_A_LEFT b=$BOOT_B_LEFT" >> "$TEST_LOG"
            [ "${FAIL_WRITE:-0}" = 0 ] ;;
        *) return 1 ;;
    esac
}
env() {
    case "$1" in
        import)
            [ "${BAD_CRC:-0}" = 0 ] || return 1
            BOOT_ORDER="${INITIAL_ORDER:-A B}"
            BOOT_A_LEFT="${INITIAL_A:-3}"
            BOOT_B_LEFT="${INITIAL_B:-3}"
            MACHINE_ID=0123456789abcdef0123456789abcdef ;;
        export) return 0 ;;
        *) return 1 ;;
    esac
}
fatload() {
    echo "LOAD $2 $4" >> "$TEST_LOG"
    if [ "$4" = board.dtb ]; then
        dtb_bootargs='root=PARTUUID=factory rw'
        dtb_bootargs_ext='root=PARTUUID=factory rw'
    fi
    [ "${FAIL_LOAD:-}" != "$2/$4" ] && [ "${FAIL_ALL_LOADS:-0}" = 0 ]
}
fdt() {
    if [ "$1" = addr ]; then return 0; fi
    [ "$1" = set ] && [ "$2" = /chosen ] || return 1
    case "$3" in
        bootargs) dtb_bootargs="$4" ;;
        bootargs_ext) dtb_bootargs_ext="$4" ;;
        *) return 1 ;;
    esac
}
booti() {
    [ -z "$dtb_bootargs" ] && [ -z "$dtb_bootargs_ext" ] || exit 1
    echo "BOOT slot=$BOOT_SLOT args=$bootargs" >> "$TEST_LOG"
    [ "${BOOT_RETURNS:-0}" = 0 ] || return 1
    exit 0
}
'''
cases = [
    ('slot_a', {}, ['WRITE_STATE order=A B a=2 b=3','BOOT slot=A']),
    ('slot_b_first', {'INITIAL_ORDER':'B A'}, ['WRITE_STATE order=B A a=3 b=2','BOOT slot=B']),
    ('exhausted_a', {'INITIAL_A':'0'}, ['WRITE_STATE order=A B a=0 b=2','BOOT slot=B']),
    ('bad_b_dtb', {'INITIAL_ORDER':'B A','FAIL_LOAD':'1:4/board.dtb'}, ['WRITE_STATE order=B A a=2 b=2','BOOT slot=A']),
    ('bad_state_crc', {'BAD_CRC':'1'}, ['WRITE_STATE order=A B a=2 b=3','BOOT slot=A']),
    ('both_exhausted', {'INITIAL_A':'0','INITIAL_B':'0'}, ['WRITE_STATE order=A B a=2 b=3','BOOT slot=A']),
    ('only_a_exhausted', {'INITIAL_ORDER':'A','INITIAL_A':'0'}, ['WRITE_STATE order=A B a=2 b=3','BOOT slot=A']),
    ('only_b_exhausted', {'INITIAL_ORDER':'B','INITIAL_B':'0'}, ['WRITE_STATE order=B A a=3 b=2','BOOT slot=B']),
    ('wrong_state_partition', {'WRONG_UUID':'1:6'}, []),
    ('wrong_root_partition', {'WRONG_UUID':'1:3'}, []),
    ('failed_state_write', {'FAIL_WRITE':'1'}, ['WRITE_STATE order=A B a=2 b=3']),
    ('no_kernel_loads', {'FAIL_ALL_LOADS':'1'}, ['WRITE_STATE order=A B a=2 b=2']),
    ('boot_returns', {'BOOT_RETURNS':'1'}, ['BOOT slot=A','BOOT slot=B','WRITE_STATE order=A B a=2 b=2']),
]
results=[]
with tempfile.TemporaryDirectory(prefix='sbc3576-boot-policy-test-') as td:
    for name, settings, expected in cases:
        log=Path(td)/(name+'.log')
        command=prelude+'\n'+script.read_text()
        proc=subprocess.run(['bash','-c',command],env={**os.environ,**settings,'TEST_LOG':str(log)},capture_output=True,text=True)
        events=log.read_text().splitlines() if log.exists() else []
        for needle in expected:
            assert any(line.startswith(needle) for line in events),(name,needle,events,proc.stderr)
        if name.startswith('wrong_'):assert not events,(name,events)
        if name in ('failed_state_write','no_kernel_loads'):assert not any(e.startswith('BOOT ') for e in events),(name,events)
        if name=='bad_b_dtb':assert not any(e.startswith('BOOT slot=B') for e in events)
        assert not proc.stderr,(name,proc.stderr)
        results.append({'case':name,'passed':True,'events':events})
if args.report:
    args.report.write_text(json.dumps({'method':'bash with mock mmc/part/env/fatload/booti commands; no device writes','cases':results},indent=2)+'\n')
print(f'{len(results)} boot-policy cases passed')
