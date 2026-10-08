// SPDX-License-Identifier: MIT
#pragma once
#include "nrfx/hal/nrf_gpio.h"
#define MICROPY_HW_BOARD_NAME "OpenMice nRF52840 prototype"
#define MICROPY_HW_MCU_NAME "nRF52840"
#define BOARD_HAS_CRYSTAL 1
// Deliberately no status LED: P0.15 is the sensor MISO, not an LED.
#define DEFAULT_SPI_BUS_SCK (&pin_P0_14)
#define DEFAULT_SPI_BUS_MOSI (&pin_P0_13)
#define DEFAULT_SPI_BUS_MISO (&pin_P0_15)
