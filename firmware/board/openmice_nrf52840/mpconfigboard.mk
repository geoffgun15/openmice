# Shared pid.codes test ID: private prototypes only; allocate a production PID.
USB_VID = 0x1209
USB_PID = 0x0001
USB_PRODUCT = "OpenMice Prototype"
USB_MANUFACTURER = "OpenMice"
MCU_CHIP = nrf52840
SRC_C += boards/openmice_nrf52840/openmice_native.c
SOFTDEV_VERSION = 6.1.1
INTERNAL_FLASH_FILESYSTEM = 1
# Build application HEX for initial SWD provisioning as well as UF2 updates.
CIRCUITPY_BUILD_EXTENSIONS = uf2,hex
# Radio file/REPL workflows are not part of the product protocol.
CIRCUITPY_BLE_FILE_SERVICE = 0
CIRCUITPY_SERIAL_BLE = 0
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_BLE
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_Register
FROZEN_MPY_DIRS += $(TOP)/frozen/Adafruit_CircuitPython_BusDevice
# Omit unrelated display/audio modules from this USB/BLE input-device runtime.
CIRCUITPY_AUDIOBUSIO = 0
CIRCUITPY_AUDIOCORE = 0
CIRCUITPY_AUDIOMIXER = 0
CIRCUITPY_AUDIOPWMIO = 0
CIRCUITPY_SYNTHIO = 0
CIRCUITPY_RGBMATRIX = 0
CIRCUITPY_FRAMEBUFFERIO = 0
CIRCUITPY_DISPLAYIO = 0
CIRCUITPY_BUSDISPLAY = 0
CIRCUITPY_EPAPERDISPLAY = 0
CIRCUITPY_VECTORIO = 0
CIRCUITPY_BITMAPTOOLS = 0
CIRCUITPY_GIFIO = 0
CIRCUITPY_FONTIO = 0
CIRCUITPY_TERMINALIO = 0
