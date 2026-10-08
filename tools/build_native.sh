#!/usr/bin/env bash
# Build in fresh source trees. Requires git, GNU make, Python, native C compiler,
# arm-none-eabi-gcc 13.2.Rel1, and pip dependencies documented in BUILD.md.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
build="${1:?Usage: build_native.sh ABSOLUTE_BUILD_DIRECTORY}"
mkdir -p "$build"
git clone --branch 9.2.8 https://github.com/adafruit/circuitpython.git "$build/circuitpython"
git clone https://github.com/adafruit/Adafruit_nRF52_Bootloader.git "$build/bootloader"
git -C "$build/bootloader" checkout c67f0bcf0fa8e841426335b1bbde91cda6ca1f50
git -C "$build/bootloader" submodule update --init --recursive
git -C "$build/circuitpython" submodule update --init --recursive
cp -R "$root/firmware/board/openmice_nrf52840" "$build/circuitpython/ports/nordic/boards/"
cp -R "$root/firmware/bootloader/openmice_nrf52840" "$build/bootloader/src/boards/"
cp -R "$build/bootloader/lib/softdevice/s140_nrf52_6.1.1" "$build/circuitpython/ports/nordic/bluetooth/"
git -C "$build/circuitpython" apply "$root/firmware/patches/circuitpython-9.2.8-packetbuffer.patch"
for lib in Adafruit_CircuitPython_BLE Adafruit_CircuitPython_Register Adafruit_CircuitPython_BusDevice; do
    git -C "$build/circuitpython/frozen/$lib" fetch --tags
done
# GCC 15 warns about intentional 3-byte mnemonic arrays in upstream mpy-cross.
# This exception is limited to host mpy-cross; target firmware retains -Werror.
host_flag=""
if [[ "$(gcc -dumpversion)" == 15* ]]; then
    host_flag=-Wno-error=unterminated-string-initialization
fi
make -C "$build/circuitpython/mpy-cross" CFLAGS_EXTRA="$host_flag" -j4
make -C "$build/bootloader" BOARD=openmice_nrf52840 SD_VERSION=6.1.1 -j4
make -C "$build/circuitpython/ports/nordic" BOARD=openmice_nrf52840 BUILD=build-openmice611 -j4
python "$root/tools/package_native.py" "$build/circuitpython" "$build/bootloader"
python "$root/tools/package_firmware.py"
