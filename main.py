"""Full-repository CIRCUITPY compatibility entry; prefer packaged flat payloads.
Requires root boot.py, custom runtime and BLE dependencies. See docs/SETUP.md.
"""
import sys
sys.path.insert(0,"/firmware/common")
sys.path.insert(0,"/firmware/mouse")
import code
