#!/usr/bin/env python3
"""Disable patch 0003's BL31 configuration and rails in a disposable CI checkout."""
from pathlib import Path
import re
import sys

r = Path(sys.argv[1])
d = r / 'projects/ROCKNIX/devices/RK3566'
p = d / 'linux/dts/rockchip/rk3568-anbernic-rg-ds-plus.dts'
t = p.read_text()
t, count = re.subn(r'\n\t/\*\n\t \* Suspend mode and wakeup sources.*?\n\t};\n', '', t, count=1, flags=re.S)
assert count == 1, 'stock suspend node not found'
for rail, old, new in [
    ('vdd_logic', 'regulator-off-in-suspend;', 'regulator-on-in-suspend;'),
    ('vcc3v3_pmu', 'regulator-suspend-microvolt = <3000000>;', 'regulator-suspend-microvolt = <3300000>;'),
]:
    start = t.index('regulator-name = "' + rail + '";')
    end = t.index('\n\t\t\t};', start)
    section = t[start:end]
    assert old in section
    section = section.replace(old, new)
    section = re.sub(r'\n\s*/\* (?:off in suspend as on stock; needs rockchip-suspend|3.0 V in suspend as on stock) \*/', '', section)
    t = t[:start] + section + t[end:]
p.write_text(t)
(d / 'patches/linux/0030-soc-rockchip-add-suspend-config-driver-for-RK3568.patch').unlink()
print('Disabled BL31 suspend configuration and stock sleep rails; RK817 sleep-pin handling retained.')
