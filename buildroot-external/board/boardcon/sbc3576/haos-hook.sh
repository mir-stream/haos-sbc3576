#!/bin/bash

function haos_pre_image() {
    local boot_data
    boot_data="$(path_boot_dir)"

    # The BSP Image is larger than the default 24 MiB kernel partition.
    KERNEL_SIZE=64M
    SYSTEM_SIZE=512M
    export KERNEL_SIZE SYSTEM_SIZE

    (cd "${BOARD_DIR}/firmware" && sha256sum -c SHA256SUMS)
    cp "${BOARD_DIR}/firmware/idbloader.img" "${BINARIES_DIR}/idbloader.img"
    cp "${BOARD_DIR}/firmware/uboot.img" "${BINARIES_DIR}/uboot.img"
    "${HOST_DIR}/bin/mkimage" -A arm64 -O linux -T script -C none \
        -n "SBC3576 HAOS" -d "${BOARD_DIR}/uboot-boot.ush" "${BINARIES_DIR}/boot.scr"
    python3 "${BOARD_DIR}/patch-boot-script.py" "${BINARIES_DIR}/boot.scr"
    cp "${BINARIES_DIR}/boot.scr" "${boot_data}/boot.scr"

    # Keep DTB and kernel together in each A/B slot.
    mkdir -p "${BINARIES_DIR}/kernel-slot"
    cp "${BINARIES_DIR}/Image" "${BINARIES_DIR}/kernel-slot/Image"
    cp "${BINARIES_DIR}/rk3576-evb1-v10-linux.dtb" "${BINARIES_DIR}/kernel-slot/board.dtb"
}

function haos_post_image() {
    convert_disk_image_xz
}
