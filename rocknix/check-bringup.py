#!/usr/bin/env python3
"""Off-device regression check. Argument: prepared ROCKNIX source directory."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

r = Path(sys.argv[1]).resolve()
b = r / 'projects/ROCKNIX/packages/baseos/baseos'
sway = r / 'projects/ROCKNIX/packages/wayland/compositor/sway'

def bash(script, *args):
    return subprocess.check_output(['bash', '-e', '-c', script, 'check', *map(str, args)], text=True)

# Source the actual device options: ordinary ROCKNIX keeps its original drivers.
for profile, expected in [('yes', ['panfrost', '', '', '']), ('no', ['mali panfrost', 'mali-bifrost', 'libmali', 'libmali'])]:
    result = bash('get_kernel_make_extracmd() { :; }; BASEOS=$1; source "$2"; printf "%s\\n" "$GRAPHIC_DRIVERS" "$ADDITIONAL_DRIVERS" "$ADDITIONAL_PACKAGES" "$ADDITIONAL_PACKAGES_32BIT"', profile, r / 'projects/ROCKNIX/devices/RK3566/options')
    assert result.splitlines() == expected, result

# Exercise the generic installer's actual autostart-copy block as well as hooks.
installer = (r / 'scripts/install').read_text()
start = installer.index('    if [ -d ${PKG_TMP_DIR}/autostart ]; then')
end = installer.index('\n    fi', start) + len('\n    fi')
generic_autostart = installer[start:end]

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    for profile in ('yes', 'no'):
        image = root / profile
        image.mkdir()
        bash('''INSTALL=$1; PKG_DIR=$2; DEVICE=RK3566; BASEOS=$3
listcontains() { return 1; }
safe_remove() { rm -rf "$@"; }
enable_service() { echo "$1" >> "$INSTALL/enabled"; }
source "$PKG_DIR/package.mk"
post_makeinstall_target
PKG_TMP_DIR=$PKG_DIR
''' + generic_autostart + '''
post_install
''', image, sway, profile)
        assert (image / 'usr/lib/autostart/common/111-sway-init').exists() == (profile == 'no')
        assert (image / 'enabled').exists() == (profile == 'no')
        if profile == 'yes':
            bash('INSTALL=$1; PKG_DIR=$2; VULKAN=vulkan-loader; source "$PKG_DIR/package.mk"; makeinstall_target', image, b)
            assert (image / 'usr/share/sway/config').read_text() == (b / 'config/sway.config').read_text()
            assert (image / 'usr/lib/modules-load.d/baseos.conf').read_text().strip() == 'panfrost'

launcher = (b / 'scripts/baseos-launch').read_text()
subprocess.run(['bash', '-n', str(b / 'scripts/baseos-launch')], check=True)
# Execute the production readiness loop against one-panel, inactive-panel and ready states.
loop = launcher[launcher.index('ready=false'):launcher.index('\nreport\nif [ "${ready}"')]
for outputs, expected in [([{'name': 'DSI-1', 'active': True}], 'false'),
                          ([{'name': 'DSI-1', 'active': True}, {'name': 'DSI-2', 'active': False}], 'false'),
                          ([{'name': 'DSI-1', 'active': True}, {'name': 'DSI-2', 'active': True}], 'true')]:
    result = bash('swaymsg() { printf "%s" "$OUTPUTS"; }; sleep() { :; }; OUTPUTS=$1; ' + loop + '; echo "$ready"', json.dumps(outputs))
    assert result.strip() == expected, result
assert 'After=sway.service rocknix-autostart.service' in (b / 'system.d/baseos-launcher.service').read_text()
dts = (r / 'projects/ROCKNIX/devices/RK3566/linux/dts/rockchip/rk3568-anbernic-rg-ds-plus.dts').read_text()
assert 'constant-charge-current-max-microamp = <2000000>;' in dts
print('PASS: install hooks, stock/BaseOS driver selection, two-panel readiness, shell syntax and 2 A charging limit')

# macOS AppleDouble files end in .nds too; auto-selection must skip them.
selection = launcher[launcher.index('rom=""'):launcher.index('\nif [ -n "${rom}" ]; then')]
with tempfile.TemporaryDirectory() as temporary:
    roms = Path(temporary)
    (roms / 'nds').mkdir()
    game = roms / 'nds/New Super Mario Bros. (USA).nds'
    game.touch()
    (roms / 'nds/._New Super Mario Bros. (USA).nds').touch()
    (roms / 'nds/.hidden.zip').touch()
    assert bash('ROMS=$1; ' + selection + 'printf "%s" "$rom"', roms) == str(game)
    (roms / 'baseos').mkdir()
    (roms / 'baseos/autostart.txt').write_text('nds/New Super Mario Bros. (USA).nds\r\n')
    assert bash('ROMS=$1; ' + selection + 'printf "%s" "$rom"', roms) == str(game)
print('PASS: ROM selection skips macOS metadata and preserves explicit paths with spaces')

# DS Plus hardware report: DSI-1 is lower, DSI-2 upper; native dmabuf
# fullscreen targets use registry indices independently of Sway window rules.
config = (b / 'config/sway.config').read_text()
for expected in ('workspace 1 output DSI-2', 'workspace 2 output DSI-1',
                 'map_to_output DSI-1', 'output DSI-2 mode 1024x768 position 0 0',
                 'output DSI-1 mode 1024x768 position 1024 0'):
    assert expected in config, expected
command = next(line for line in launcher.splitlines() if '/usr/bin/start_dsperate.sh' in line)
with tempfile.TemporaryDirectory() as temporary:
    bash('''LOG=$1; rom='game with spaces.nds'
start_dsperate() { printf '%s\n' "$DS_DUAL_SCREENS" "$DS_FPS" "$DS_FRAME_STATS" "$DS_GPU3D" "$DS_MIC_LOG" "$1" "$2"; }
''' + command.replace('/usr/bin/start_dsperate.sh', 'start_dsperate'), temporary)
    assert (Path(temporary) / 'dsperate.log').read_text().splitlines() == [
        'upper=1,lower=0', '1', '1', '1', '1', 'game with spaces.nds', 'nds']
print('PASS: physical panel/touch mapping, explicit GPU request and timing/mic diagnostics')
wrapper_path = r / 'projects/ROCKNIX/packages/emulators/standalone/dsperate-sa/scripts/start_dsperate.sh'
wrapper = wrapper_path.read_text()
subprocess.run(['bash', '-n', str(wrapper_path)], check=True)
options = wrapper[wrapper.index('OPTS=('):wrapper.index('#Default layout')]
for requested, expected in [('', ['--fullscreen']), ('0', ['--fullscreen']), ('1', ['--fullscreen', '--gpu3d'])]:
    result = bash('DS_GPU3D=$1; ' + options + '\nprintf "%s\\n" "${OPTS[@]}"', requested)
    assert result.splitlines() == expected, result
print('PASS: GPU override reaches the CLI/menu without changing ordinary launch options')


# Reports expose video settings, not credentials from other INI sections.
filter_command = next(line for line in launcher.splitlines() if "awk '/^" in line)
with tempfile.TemporaryDirectory() as temporary:
    config_file = Path(temporary) / 'dsperate.ini'
    config_file.write_text('[video]\ngpu3d = false\nlayout = horizontal\n[cheevos]\ntoken = secret-fixture\n[paths]\ngpu3d = private-fixture\n')
    assert bash('cfg=$1; ' + filter_command, config_file).splitlines() == [
        'gpu3d = false', 'layout = horizontal']

# BaseOS package installs vendor logind policy, without touching stock builds.
import configparser
with tempfile.TemporaryDirectory() as temporary:
    image = Path(temporary)
    bash('INSTALL=$1; PKG_DIR=$2; VULKAN=vulkan-loader; source "$PKG_DIR/package.mk"; makeinstall_target', image, b)
    policy_path = image / 'usr/lib/systemd/logind.conf.d/60-baseos-power.conf'
    policy = configparser.ConfigParser()
    policy.read(policy_path)
    assert dict(policy['Login']) == {
        'handlepowerkey': 'ignore', 'handlepowerkeylongpress': 'poweroff',
        'handlelidswitch': 'suspend', 'handlelidswitchexternalpower': 'suspend',
        'handlelidswitchdocked': 'suspend'}
    fake = (r / 'projects/ROCKNIX/packages/rocknix/sources/scripts/rocknix-fake-suspend').read_text()
    subprocess.run(['bash', '-n', str(r / 'projects/ROCKNIX/packages/rocknix/sources/scripts/rocknix-fake-suspend')], check=True)
    guard = fake[fake.index('# BaseOS assigns Power'):fake.index('# Check if HDMI is connected', fake.index('# BaseOS assigns Power'))]
    guard = guard.replace('/usr/lib/systemd/logind.conf.d/60-baseos-power.conf', '"$POLICY"')
    assert bash('SOURCE=power; POLICY=$1; ' + guard + 'echo continued', policy_path) == ''
    assert bash('SOURCE=lid; POLICY=$1; ' + guard + 'echo continued', policy_path).strip() == 'continued'
    policy_path.unlink()
    assert bash('SOURCE=power; POLICY=$1; ' + guard + 'echo continued', policy_path).strip() == 'continued'
print('PASS: BaseOS lid-only sleep, long-press shutdown and ordinary fake-suspend preservation')

# Reports must survive boot-008/009 rather than treating the suffix as octal.
count = launcher[launcher.index('n=$(('):launcher.index('\nLOG=')]
assert bash('last=008; ' + count + '; echo "$n"').strip() == '9'
assert dts.count('M clock=62411 ') == 2
assert 'timeout 15 vulkaninfo --summary' in launcher

# Generate the actual boot configuration without writing an SD card.
import shutil
import xml.etree.ElementTree as ET
fdt = ET.parse(r / 'projects/ROCKNIX/config.xml').find('RK3566/Specific').get('fdt')
with tempfile.TemporaryDirectory() as temporary:
    for baseos, ds_only, expected in [('yes', 'false', 'device_trees/rk3568-anbernic-rg-ds-plus.dtb'),
                                     ('no', 'true', 'device_trees/rk3568-anbernic-rg-ds-plus.dtb'),
                                     ('no', 'false', fdt)]:
        bash('''cd "$1"
IMG_TMP=$2; RELEASE_DIR=$2/release; DEVICE=RK3566; SUBDEVICE=Specific
BASEOS=$3; DS_ONLY=$4; DEFAULT_FDT=$5; DISTRO=""; KERNEL_NAME=KERNEL
get_fdt() { echo "$DEFAULT_FDT"; }
get_fdt_type() { echo FDT; }
get_fdt_overlays() { :; }
mcopy() { :; }
mkimage_all() { :; }
NOONEXIT=yes
source projects/ROCKNIX/bootloader/mkimage
DISTRO=ROCKNIX
mkimage_extlinux
''', r, temporary, baseos, ds_only, fdt)
        conf = (Path(temporary) / 'extlinux/extlinux.conf').read_text()
        assert f'  FDT /{expected}\n' in conf, conf
    # Exercise the diagnostic variant on a disposable copy.
    root = Path(temporary) / 'diagnostic'
    device = Path('projects/ROCKNIX/devices/RK3566')
    (root / device / 'linux/dts/rockchip').mkdir(parents=True)
    (root / device / 'patches/linux').mkdir(parents=True)
    shutil.copy(r / device / 'linux/dts/rockchip/rk3568-anbernic-rg-ds-plus.dts', root / device / 'linux/dts/rockchip')
    patch = '0030-soc-rockchip-add-suspend-config-driver-for-RK3568.patch'
    shutil.copy(r / device / 'patches/linux' / patch, root / device / 'patches/linux')
    subprocess.run([sys.executable, str(r / 'rocknix/disable-suspend.py'), str(root)], check=True)
    diagnostic = (root / device / 'linux/dts/rockchip/rk3568-anbernic-rg-ds-plus.dts').read_text()
    assert 'rockchip,pm-rk3568' not in diagnostic
    assert 'regulator-off-in-suspend;' not in diagnostic[diagnostic.index('regulator-name = "vdd_logic";'):][:250]
    assert 'pmic-sleep' in diagnostic
    assert 'constant-charge-current-max-microamp = <2000000>;' in diagnostic
    assert not (root / device / 'patches/linux' / patch).exists()

# Package graph excludes frontend/emulators/lib32 even if generic defaults enable them.
with tempfile.TemporaryDirectory() as temporary:
    deps = bash('''INSTALL=$1; DEVICE=RK3566; BASEOS=yes; BASE_ONLY=true; DS_ONLY=false
EMULATION_DEVICE=yes; ENABLE_32BIT=true
source "$2/projects/ROCKNIX/packages/virtual/image/package.mk"
printf "%s" "$PKG_DEPENDS_TARGET"
''', temporary, r).split()
    assert 'baseos' in deps
    assert not {'emulationstation', 'emulators', 'lib32', 'gamesupport'}.intersection(deps)
print('PASS: decimal boot numbering, panel clocks, generated FDT, diagnostic suspend variant and BaseOS package graph')
