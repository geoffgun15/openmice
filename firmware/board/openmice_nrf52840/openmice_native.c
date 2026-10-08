// SPDX-License-Identifier: MIT
// Critical PAW3395 startup polling uses the Cortex-M4 cycle counter, not
// CircuitPython's RTC-based monotonic clock. Missed deadlines fail explicitly.
#include "py/obj.h"
#include "py/runtime.h"
#include "shared-bindings/busio/SPI.h"
#include "shared-bindings/digitalio/DigitalInOut.h"
#include "shared-bindings/microcontroller/__init__.h"
#include "nrf.h"

static mp_obj_t openmice_poll_ready(mp_obj_t spi_obj, mp_obj_t cs_obj) {
    if (!mp_obj_is_type(spi_obj, &busio_spi_type) ||
        !mp_obj_is_type(cs_obj, &digitalio_digitalinout_type)) {
        mp_raise_TypeError(MP_ERROR_TEXT("Expected SPI and DigitalInOut"));
    }
    busio_spi_obj_t *spi = MP_OBJ_TO_PTR(spi_obj);
    digitalio_digitalinout_obj_t *cs = MP_OBJ_TO_PTR(cs_obj);
    if (!common_hal_busio_spi_try_lock(spi)) {
        mp_raise_RuntimeError(MP_ERROR_TEXT("SPI busy during startup"));
    }
    bool ready = false;
    bool transfer_ok = common_hal_busio_spi_configure(spi, 4000000, 1, 1, 8);
    bool cadence_ok = true;
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
    const uint32_t period = SystemCoreClock / 1000;
    const uint32_t tolerance = SystemCoreClock / 100000; // 10us, +/-1% of 1ms
    uint32_t deadline = DWT->CYCCNT;
    for (unsigned attempt = 0; transfer_ok && attempt < 60; attempt++) {
        while ((int32_t)(DWT->CYCCNT-deadline) < 0) {
            __NOP();
        }
        if ((uint32_t)(DWT->CYCCNT-deadline) > tolerance) {
            cadence_ok = false;
            break;
        }
        common_hal_digitalio_digitalinout_set_value(cs, false);
        common_hal_mcu_delay_us(1);
        uint8_t address = 0x6c;
        uint8_t value = 0;
        transfer_ok = common_hal_busio_spi_write(spi, &address, 1);
        common_hal_mcu_delay_us(2);
        if (transfer_ok) {
            transfer_ok = common_hal_busio_spi_read(spi, &value, 1, 0);
        }
        common_hal_mcu_delay_us(1);
        common_hal_digitalio_digitalinout_set_value(cs, true);
        common_hal_mcu_delay_us(5);
        if (transfer_ok && value == 0x80) {
            ready = true;
            break;
        }
        deadline += period;
    }
    common_hal_digitalio_digitalinout_set_value(cs, true);
    common_hal_busio_spi_unlock(spi);
    if (!transfer_ok) {
        mp_raise_RuntimeError(MP_ERROR_TEXT("Startup SPI transfer failed"));
    }
    if (!cadence_ok) {
        mp_raise_RuntimeError(MP_ERROR_TEXT("PAW startup 1ms cadence missed"));
    }
    return mp_obj_new_bool(ready);
}
static MP_DEFINE_CONST_FUN_OBJ_2(openmice_poll_ready_obj, openmice_poll_ready);
static const mp_rom_map_elem_t openmice_globals_table[] = {
    {MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_openmice_native)},
    {MP_ROM_QSTR(MP_QSTR_poll_ready), MP_ROM_PTR(&openmice_poll_ready_obj)},
};
static MP_DEFINE_CONST_DICT(openmice_globals, openmice_globals_table);
const mp_obj_module_t openmice_native_module = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t *)&openmice_globals,
};
MP_REGISTER_MODULE(MP_QSTR_openmice_native, openmice_native_module);

