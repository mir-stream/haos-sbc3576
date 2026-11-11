# SBC3576 Home Assistant OS port

Boardcon SBC3576(RK3576)에 HAOS 18.5를 올린 커뮤니티 포크입니다.
제조사 Linux 6.1.99, 기존 U-Boot, 보드 DTB와 RTL8852BE 드라이버를
HAOS 빌드에 연결한 코드와 재현 자료를 보관합니다.

- [포팅 내용과 확인된 동작](Documentation/boards/sbc3576.md)
- [실험용 설치 이미지·업데이트 다운로드](https://github.com/mir-stream/haos-sbc3576/releases/tag/sbc3576-18.5-20261111)
- [빌드 방법과 필요한 파일](Documentation/boards/sbc3576-build.md)
- [제3자에게 공유할 asset만 보기](Documentation/boards/sbc3576-public-assets.md)
- [설치 과정·복구 기록](Documentation/boards/sbc3576-recovery.md)
- [보관할 asset 목록과 SHA-256](Documentation/boards/sbc3576-assets.json)
- [검증 기록](Documentation/boards/sbc3576-validation.json)

`sbc3576-18.5`는 초기 포팅 범위입니다. 이후 추가한 가정용 방화벽 정책과
Home Assistant 기기·자동화 설정은 포함하지 않습니다. 공식 지원 보드나
공식 OS 업데이트 대상은 아닙니다. 아래는 upstream README입니다.

---

# Home Assistant Operating System

Home Assistant Operating System (formerly HassOS) is a Linux based operating system optimized to host [Home Assistant](https://www.home-assistant.io) and its [Apps](https://www.home-assistant.io/apps/).

Home Assistant Operating System uses Docker as its container engine. By default it deploys the Home Assistant Supervisor as a container. Home Assistant Supervisor in turn uses the Docker container engine to control Home Assistant Core and Apps in separate containers. Home Assistant Operating System is **not** based on a regular Linux distribution like Ubuntu. It is built using [Buildroot](https://buildroot.org/) and it is optimized to run Home Assistant. It targets single board compute (SBC) devices like the Raspberry Pi or ODROID but also supports x86-64 systems with UEFI.

[![Home Assistant - A project from the Open Home Foundation](https://www.openhomefoundation.org/badges/home-assistant.png)](https://www.openhomefoundation.org/)

## Features

- Lightweight and memory-efficient
- Minimized I/O
- Over The Air (OTA) updates
- Offline updates
- Modular using Docker container engine

## Supported hardware

The list of supported hardware is defined by [ADR-0015](https://github.com/home-assistant/architecture/blob/master/adr/0015-home-assistant-os.md).
Every new hardware addition must meet at least requirements defined in [ADR-0017](https://github.com/home-assistant/architecture/blob/master/adr/0017-hardware-screening-os.md) and pass through an architecture design proposal.

For documentation explaining details of the individual supported boards, see [Board support](https://contributors.home-assistant.io/os/operating-system/boards/) section of the Home Assistant contributor docs.

## Getting Started

If you just want to use Home Assistant the official [getting started guide](https://www.home-assistant.io/getting-started/) and [installation instructions](https://www.home-assistant.io/hassio/installation/) take you through how to download Home Assistant Operating System and get it running on your machine.

If you're interested in finding out more about Home Assistant Operating System and how it works read on...

## Development

If you don't have experience with embedded systems, Buildroot or the build process for Linux distributions it is recommended to read up on these topics first (e.g. [Bootlin](https://bootlin.com/docs/) has excellent resources).

The Home Assistant Operating System documentation can be found on the [Home Assistant contributors website](https://contributors.home-assistant.io/os/operating-system/).

### Components

- **Bootloader:**
  - [GRUB](https://www.gnu.org/software/grub/) for devices that support UEFI
  - [U-Boot](https://www.denx.de/wiki/U-Boot) for devices that don't support UEFI
- **Operating System:**
  - [Buildroot](https://buildroot.org/) LTS Linux
- **File Systems:**
  - [SquashFS](https://www.kernel.org/doc/Documentation/filesystems/squashfs.txt) for read-only file systems (using LZ4 compression)
  - [ZRAM](https://www.kernel.org/doc/Documentation/blockdev/zram.txt) for `/tmp`, `/var` and swap (using LZ4 compression)
- **Container Platform:**
  - [Docker Engine](https://docs.docker.com/engine/) for running Home Assistant components in containers
- **Updates:**
  - [RAUC](https://rauc.io/) for Over The Air (OTA) and USB updates
- **Security:**
  - [AppArmor](https://apparmor.net/) Linux kernel security module

### Development builds

The Development build GitHub Action Workflow is a manually triggered workflow
which creates Home Assistant OS development builds. The development builds are
available at [https://os-artifacts.home-assistant.io/index.html](https://os-artifacts.home-assistant.io/index.html).
