# RG DS Plus BaseOS in ROCKNIX

This is the direct port of `philbudiman/rg-ds-plus-baseos` at
`6062ff33a62bd44997b0b09957e9a24e451d8bfc`, compared with its pinned ROCKNIX
upstream `a55d58a1209b35e287dd55a3aad67a5543b467ce`. The fork remains on its
working `next` branch; unrelated differences from that upstream are retained.

## Build

Run **BaseOS preflight and publishing smoke test** first. It runs the bring-up
check, unpacks the actual kernel and verifies the integrated patches and USB
input limit. It exercises the production publisher using a clearly labelled
**DO NOT FLASH** dummy image in a draft prerelease.

Then run **Build** with `BASEOS=true`. Only RK3566 is selected. `SUSPEND=true`
includes stock BL31 configuration (`0x5ec`, wakeup `0x10`) and sleep rails.
For diagnosis, `SUSPEND=false` disables source patch 0003's configuration and
rails in disposable CI checkouts; RK817 sleep-pin handling remains enabled.
Do not combine `DS_ONLY` and `BASEOS`.

Both the toolchain and image jobs receive `BASE_ONLY=true`, `BASEOS=yes`,
`EMULATION_DEVICE=no`, `ENABLE_32BIT=no`. BaseOS skips the ARM, Rust, Qt,
libretro and other standalone-emulator jobs. The existing aarch64 job builds
its final Specific image directly; no second image rebuild is needed.
Ordinary builds and the existing DS_ONLY frontend profile remain available
with `BASEOS=false` (default).

The existing release-backed compiler caches still restore/save from
`${CACHE_REPO}` (default `distribution-cache`) under the same asset names.
These archives contain compiler results, not package install stamps. Compiler
content/options are part of ccache keys; profile-sensitive package stamps are
transferred only within the current run, whose toolchain/image profiles match.
`gcc glibc libtool flex` survive cleanup. Publication runs in a fresh job,
checks `gh` and SHA256 tools, verifies checksums and publishes exactly one
Specific image plus checksum to a `rocknix-baseos-N-RUNID` prerelease in this
fork. No upstream nightly or official release credentials are needed.

## Ported behavior

- Both panels: 62411 kHz, about 59.826 Hz.
- Stock RK817 sleep-pin flow and BL31 suspend configuration/sleep rails.
- Stock 2,000,000 µA battery charging; kernel USB input limit remains 1.5 A.
- BaseOS excludes EmulationStation, other emulators and 32-bit packages;
  includes Sway, audio, SDL2, Vulkan and DSperate 3.0.0 with GPU 3D enabled.
- Panfrost only: no libmali or its blacklist; early module loading, dedicated
  two-panel Sway config, Goodix touch mapped to DSI-2, no frontend config writer
  or generic touch remapping. Launcher waits for autostart and both active panels.
- Specific boot configuration selects
  `/device_trees/rk3568-anbernic-rg-ds-plus.dtb` using the fork's existing FDT
  override, extended to BaseOS. Ordinary Specific retains its previous default.
- Boot reports and bounded Vulkan diagnostics go to `roms/baseos-logs/`.
- The pinned upstream's STI8070A CPU regulator patch is restored because this
  fork predates it. Batteryplus is disabled for BaseOS to match source behavior.

## Checks and hardware status

Local: `python3 rocknix/check-bringup.py .` checks actual install hooks,
stock/BaseOS GPU selection, two-panel readiness, generated boot configuration
(BaseOS, DS_ONLY and ordinary), panel timings, 2 A DT value, diagnostic suspend
variant and package selection. Run `actionlint -shellcheck='' .github/workflows/*.yml`
for workflow schemas/expressions; Bash syntax and publisher shellcheck are also
checked. These checks do not prove rendering, Vulkan, touch, sound or suspend.

Source build #6 (`36952934140`) was still compiling during initial port inspection;
its stage-0 kernel check passed. It was left running.

The earlier `rocknix-baseos-4` card reached the ROCKNIX logo/userspace after its
wrong FDT was corrected, then went black. Retrieved reports showed missing Sway
configuration and GPU initialization problems. Source patch 0005 addressed these
but has not been confirmed on hardware. This port makes no hardware-success claim.

## Focused hardware test

1. Flash the new **BaseOS Specific** image to spare TF1. Check its checksum and
   the boot partition's FDT line above. Keep the stock card.
2. Put a `.nds` or `.zip` ROM on FAT32/exFAT TF2 under `roms/nds/`. Optionally set
   `roms/baseos/autostart.txt` to a path relative to `roms/` to select a game.
3. Check both panels, DSperate GPU 3D, full speed, sound and lower-panel touch.
   Without a ROM expect dark gray panels, not a menu.
4. Return `roms/baseos-logs/boot-NNN/`, especially `launch.txt`, `dsperate.log`,
   `sway.log`, `system.txt`, `dmesg.txt` and `journal.txt`. Confirm both 62411 kHz
   modes, active panels, Vulkan device detection and a 2,000,000 µA charge limit.
5. Then test several shutdown/power-on and reboot cycles; boot stock afterward
   and check it powers on without disconnecting the battery. Then test lid/power
   sleep and wake, audio/touch recovery and measured sleep drain versus stock.
   Compare charge before/after sleep; do not keep the CPU awake to sample it.

Wait for hardware results before MinUI and `rgds-hwkeys`. Later hotkeys:
Select+Up/Down brightness; Select+Left/Right night mode through KMS CTM/gamma.
