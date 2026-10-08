# First article: not yet run

There is no assembled board. Every physical test below is **NOT RUN**. Record
board revision, firmware hashes, equipment, conditions and measured results;
do not infer a pass from the CAD checks or host tests.

1. Inspect solder joints, PAW seating, antenna keep-out and optical alignment.
   Check resistance from USB/battery/system/3.0 V/1.9 V rails to GND before power.
   Leave the battery disconnected initially. Use a current-limited USB supply.
2. Measure MCU/VDDIO at 3.0 V and sensor/LED at 1.9 V under startup and load.
   Check VDDREG against the PAW datasheet. Stop on excess current or heating.
   Confirm USB input stays within the selected 100 mA limit.
3. Connect an SWD probe to SWDIO, SWCLK, GND and target-reference 3.0 V.
   Never drive the target with a 5 V probe supply. Program and verify
   output/native/openmice-factory.hex, including UICR and bootloader settings.
   Confirm normal startup, Pair held during reset enters UF2, and SWD recovery.
4. Copy the mouse/receiver application payload to the corresponding CIRCUITPY
   drive and power-cycle. Confirm USB HID mouse, keyboard and configuration
   CDC enumerate; recovery storage remains accessible. Test runtime UF2 update.
5. Capture SPI with a logic analyser: mode 3, <=4 MHz, reset and startup waits,
   1 ms ±1% ready polling cadence, burst address delay, and CS timing. Confirm
   product ID 0x51/inverse 0xAE. Exercise unsuccessful initialization recovery.
   The compiled DWT polling helper fails explicitly on missed cadence, but this
   does not replace a waveform measurement.
6. Run `python tools/bench_config.py --port COMx --report results/wired.json`
   after installing pyserial. It tests hello/get, an invalid DPI rejection and
   live set/readback, then restores the original live configuration. It does
   not save or move the pointer. Repeat through the paired receiver.
7. Exercise DPI 50, 800, 1600, 9000 and 26000. Measure counts over a calibrated
   travel distance in both axes, jitter and lift-off on several surfaces.
   Test all five contacts, wheel direction, debounce and every binding class,
   including overlapping keyboard chords and release after disconnect.
8. Apply and Save a distinct configuration in the browser. Power-cycle and Read
   device. Cut power during repeated saves; recover the old or completed new
   profile, never corrupted data. Recheck receiver pairing after configuration
   saves and across power cycles (separate NVM erase pages).
9. Pair both devices after startup. Test automatic reconnect, receiver offline
   errors, fragmented traffic, interference/range and stale-input release within
   the 500 ms watchdog allowance. Record motion/input latency, packet loss and
   current; no wireless polling-rate or battery-life claim exists yet.
10. Connect the specified protected battery with NTC after polarity/ratings
    checks. Measure USB100 charging, charge termination, system power-path
    transitions, NTC hot/cold inhibition and case/charger temperature. Test with
    the battery supplier's limits. Measure active, idle and switched-off current
    and run battery endurance. MCU deep sleep/firmware cutoff are not implemented.

Acceptance: all physical measurements meet the applicable component datasheets
and chosen pack specifications; USB, input and persistence behave as above.
Document failures and revise the board/firmware before another article or larger
order. EMC/ESD and regulatory tests are separate from this prototype bring-up.
