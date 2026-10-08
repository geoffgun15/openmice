// SPDX-License-Identifier: MIT
#ifndef OPENMICE_BOOT_BOARD_H
#define OPENMICE_BOOT_BOARD_H
// MDBT50Q includes the Reg1 DC/DC inductor. Normal VDD/VDDH supply is 3.0 V.
#define ENABLE_DCDC_1 1
#define ENABLE_DCDC_0 0
#define UICR_REGOUT0_VALUE UICR_REGOUT0_VOUT_3V0
#define LEDS_NUMBER 0
#define BUTTON_DFU PINNUM(0,27)
#define BUTTON_PULL NRF_GPIO_PIN_PULLUP
#define BLEDIS_MANUFACTURER "OpenMice"
#define BLEDIS_MODEL "OpenMice nRF52840"
// Shared test IDs: private development only, not a production assignment.
#define USB_DESC_VID 0x1209
#define USB_DESC_UF2_PID 0x0001
#define USB_DESC_CDC_ONLY_PID 0x0001
#define UF2_PRODUCT_NAME "OpenMice Bootloader"
#define UF2_VOLUME_LABEL "OPENMICE"
#define UF2_BOARD_ID "nRF52840-openmice"
#define UF2_INDEX_URL "https://github.com/geoffgun15/OpenMice-Proto"
#endif
