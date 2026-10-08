// SPDX-License-Identifier: MIT
#include "shared-bindings/board/__init__.h"
static const mp_rom_map_elem_t board_module_globals_table[] = {
    CIRCUITPYTHON_BOARD_DICT_STANDARD_ITEMS
    { MP_ROM_QSTR(MP_QSTR_SCK), MP_ROM_PTR(&pin_P0_14) },
    { MP_ROM_QSTR(MP_QSTR_MOSI), MP_ROM_PTR(&pin_P0_13) },
    { MP_ROM_QSTR(MP_QSTR_MISO), MP_ROM_PTR(&pin_P0_15) },
    { MP_ROM_QSTR(MP_QSTR_SPI), MP_ROM_PTR(&board_spi_obj) },
};
MP_DEFINE_CONST_DICT(board_module_globals, board_module_globals_table);
