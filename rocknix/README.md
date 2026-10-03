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
  two-panel Sway config, Goodix touch mapped to lower DSI-1, no frontend config writer
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

Validation run [36954725526](https://github.com/philbudiman/rocknix-rgds-plus/actions/runs/36954725526)
passed the local bring-up checks and actual kernel integration with no rejected
hunks. It confirmed both existing USB-input-limit assignments and successfully
published draft release `baseos-smoke-36954725526` with only
`SMOKE-TEST-DO-NOT-FLASH.img.gz` and its checksum.

Full BaseOS build [36954906825](https://github.com/philbudiman/rocknix-rgds-plus/actions/runs/36954906825)
completed from port commit `80096ae859`, with suspend changes enabled.

Build 16 published, and downloaded-image checks confirmed its SHA256, correct
DS Plus FDT and compiled 2,000,000 µA charging value. Rootfs inspection then found
that `scripts/install` independently copied `111-sway-init` back into the image,
bypassing patch 0005's build-hook exclusion. **Do not flash BaseOS 16 for bring-up.**
The fix removes that initializer in Sway's final install hook; the regression check
now executes the actual generic installer's copy block, and CI checks the completed
rootfs before uploading a BaseOS image.

Corrected full build [36967236204](https://github.com/philbudiman/rocknix-rgds-plus/actions/runs/36967236204)
from `49916c3a07` succeeded and published
[BaseOS 18](https://github.com/philbudiman/rocknix-rgds-plus/releases/tag/rocknix-baseos-18-36967236204).
Downloaded-image verification passed: SHA256 matches, extlinux selects the DS Plus
DTB, the compiled charging value is 2,000,000 µA, both panels use 62411 kHz and
stock suspend configuration is present. The final SquashFS excludes `111-sway-init`,
EmulationStation and libmali; its dedicated Sway configuration matches the source,
generic touch remapping is disabled, DSperate GPU 3D is enabled and Panfrost loads
early. Persistent toolchain and image compiler caches were saved successfully.
These are off-device checks; rendering, touch, audio and suspend still need hardware
confirmation. Scheduled build follow-up stops at this handoff.

Source build #6 (`36952934140`) completed successfully. It was left running
during this port; no existing builds were cancelled.

The earlier `rocknix-baseos-4` card reached the ROCKNIX logo/userspace after its
wrong FDT was corrected, then went black. Retrieved reports showed missing Sway
configuration and GPU initialization problems. Source patch 0005 addressed these
but has not been confirmed on hardware. This port makes no hardware-success claim.

## First BaseOS 18 hardware report

The first TF2 report confirmed both 59.826 Hz panel modes, Panfrost/EGL startup,
Vulkan device enumeration and a reported 2,000,000 µA charge limit. The battery
reported 16%, consistent with the red status LED. The launcher selected macOS's
4 KB `._New Super Mario Bros. (USA).nds` metadata file instead of the actual ROM;
auto-selection now skips hidden files, with a regression check for this case.
For image 18, set `roms/baseos/autostart.txt` to
`nds/New Super Mario Bros. (USA).nds` to select the real game without reflashing.
Speaker amplifier initialization errors also appear in the report. Gameplay,
GPU 3D, audible sound, touch and suspend remain unconfirmed; retest the actual
ROM first before changing audio or GPU behavior.

## BaseOS 18 follow-up hardware reports

Boot 002 selected the actual ROM. The user reports smooth gameplay, working
controls, audible sound and working volume buttons; menu/back buttons remain
untested. Physical screens were reversed, preventing touch confirmation.
DSperate v3.0.0 identifies DSI-1 as lower; the dedicated Sway configuration had
assumed it was upper. The correction assigns upper to DSI-2, lower/touch to DSI-1
and explicitly sets `DS_DUAL_SCREENS=upper=1,lower=0` for DSperate's native dmabuf
fullscreen targets, which use output indices independently of window rules.
This correction still requires hardware retesting. Corrective build
[37038104273](https://github.com/philbudiman/rocknix-rgds-plus/actions/runs/37038104273)
completed from `f0360355cb` with suspend enabled and published
[BaseOS 19](https://github.com/philbudiman/rocknix-rgds-plus/releases/tag/rocknix-baseos-19-37038104273).
Downloaded-image verification passed: checksum, DS Plus boot tree, compiled
2,000,000 µA charging limit, panel clocks, corrected Sway/touch assignment and
DSperate output/timing environment all match the intended sources. Frontend
initializer/libmali remain absent; Panfrost/GPU3D remain enabled. Persistent
compiler caches were saved. These checks are off-device; retest physical screen
order and lower touch before claiming the correction works on hardware.
Scheduled follow-up stops at this verified-image handoff.

The next image enables DSperate's existing `DS_FPS=1` and `DS_FRAME_STATS=1`:
`dsperate.log` receives FPS, percent of nominal DS speed, emulation/presentation/
wait/pacing timings approximately every 60 emulated frames. Frame statistics are
printed on emulator exit. Existing reports contain no measured performance
numbers; smoothness is a user observation, not a quantified full-speed result.
The built-in FPS overlay is mapped to modifier+Y (modifier is SDL `guide`);
physical menu/back mapping still needs confirmation.

Boot 003's journal records short Power-key events, deep suspend entry and resume.
This confirms sleep occurred in that session, not a clean shutdown; it does not
resolve repeated-button/cold-start behavior. Initial speaker errors remain logged,
but audible playback and volume control are now confirmed for the tested session.

## BaseOS 19 hardware report (boot 004)

The user confirmed correct physical top/bottom screen order and working touch.
The actual New Super Mario Bros. ROM launched. Across 344 approximately one-second
reporting windows (about 345.4 seconds), median FPS was 59.8; aggregate throughput
was approximately 59.75 FPS. Most windows reported 100% nominal DS speed; four
reported below 99%, with a minimum of 52.5 FPS / 88%. Mean reported emulation work
was 5.17 ms/frame and presentation work 0.32 ms/frame. At 59.8 FPS the frame period
is approximately 16.72 ms. These are rounded reporting-window measurements for
this session, not individual-frame percentiles or proof about other games.
The emulator did not exit in the report, so end-of-run frame statistics are absent.
No explicit `gpu3d: on` line is present; actual GPU 3D activation remains to be
verified despite the image's intended setting and working Panfrost compositor.

Menu/Back presses and holds alone produced no action. The device tree assigns
Menu's function key `BTN_MODE`; the DSperate profile uses SDL `guide` as its
modifier, with modifier+X pause/menu, modifier+Y FPS and modifier+Start quit.
Test these chords before treating Menu as broken. The physical Back key is a
separate `adc-keys-back` input emitting `BTN_Z`, without an explicit DSperate
binding. Confirm its events in the planned button test app before assigning an
action; it must not be confused with SDL `back`, which represents DS Select.

## GPU 3D and microphone investigation after boot 004

The image's RG DS INI requests GPU 3D, but boot 004 has neither `gpu3d: on` nor
`gpu3d: unavailable` from the actual emulator, which contains both messages.
The v3.0.0 configuration parser was compiled off-device against the extracted
image INIs: the generic RK3566 INI leaves GPU 3D off, the RG DS INI enables it,
and later per-game settings can override it. The device's effective persisted
configuration is not in earlier reports, so its exact origin remains unknown.

The BaseOS launcher now supplies `DS_GPU3D=1`, which v3.0.0 applies after loading
configuration. This makes BaseOS's intended GPU mode explicit without replacing
saved configurations or changing ordinary ROCKNIX launches. The next report must
contain `gpu3d: on` or a concrete failure reason; shader/rendering success still
requires hardware testing. `system.txt` records only relevant video settings from
the persisted/per-game INIs, plus ALSA cards/capture devices/mixer state. It does
not copy whole emulator configuration files containing account credentials.

`DS_MIC_LOG=1` adds microphone sample/peak/RMS reports without recording speech.
Use a game that actually reads the microphone; DSperate opens capture lazily.
Synthetic mic hotkeys must be left unused during the real microphone test.
Corrective build [37051990104](https://github.com/philbudiman/rocknix-rgds-plus/actions/runs/37051990104)
started at `26aaae743a` with stock suspend enabled. Follow-up will verify the
downloaded image before the next GPU/microphone device test.

Physical Back mapping remains unchanged. The lid-only power policy below, Menu
modifier chords, true shutdown/cold boot and suspend/wake require device evidence.

## BaseOS power policy: lid-only sleep

BaseOS now installs a vendor logind drop-in: short Power presses are ignored
while running, a five-second hold requests clean poweroff, and lid close requests
suspend (including on external power or when docked). The packaged systemd 255.8
source confirms its five-second long-press timer. Unlike the old long-press-ignore
setting, this distinguishes short/long presses instead of suspending immediately
on the initial press. The shared fake-suspend handler also ignores Power when
this BaseOS policy is installed, so changing the suspend mode to `off` cannot
restore Power-triggered fake sleep. Ordinary ROCKNIX policy remains unchanged.

Power still starts the device when off; hardware may also wake it from sleep.
Opening the lid is the intended wake path. Cold-start, held-key events, clean
shutdown, wake and audio/touch recovery need hardware confirmation. This userspace
change does not prove the reported first-press cold-start issue is fixed, and
cannot remove a PMIC's forced-off behavior on an excessively long hold.
`system.txt` now includes the effective logind configuration for diagnosis.
Combined GPU/microphone/power build
[37055711060](https://github.com/philbudiman/rocknix-rgds-plus/actions/runs/37055711060)
completed successfully at `2693875fbd`. Its published **BaseOS 25** image passed
the off-device checks below; GPU, microphone and power changes await hardware retesting.

### Verified BaseOS 25 image

[Release and Specific image](https://github.com/philbudiman/rocknix-rgds-plus/releases/tag/rocknix-baseos-25-37055711060).
SHA256: `41f8c7d907bc1c47f0c7d9189e115d02de4ca66c67d0c9e6c2903b7d3f49315c`.
The downloaded image matches its published checksum. Extracted boot/rootfs checks
confirm the DS Plus FDT, 2,000,000 µA charging, both 62411 kHz panels, stock suspend,
and exact source matches for Sway, launcher, logind policy and fake-suspend guard.
GPU/microphone/timing flags, metadata exclusion and early Panfrost are installed;
frontend initializer, EmulationStation, libmali, GPU blacklist and enabled generic
touch service are absent. Toolchain and image compiler caches were saved.
These checks do not establish GPU acceleration, microphone capture, cold startup,
clean shutdown or lid wake on hardware. Return new boot reports after testing.

## Two-press startup investigation

Boot 003 provides evidence for an apparent failed start caused by early sleep:
Linux starts at the device's reported 16:52:18, logind receives Power events and
requests suspend at 16:52:20, and the sleep operation starts at 16:52:23. The
charger driver reports about 150 seconds asleep; userspace resumes at 16:54:57,
and Sway starts at 16:54:58. Thus that boot slept before the compositor started.
These are timestamps from the device's incorrectly dated clock, not real-world
wall-clock dates. The relative sequence and sleep-duration report are the evidence.

The leading hypothesis is that a startup press/held or queued Power event is
accepted again by logind during early boot, immediately requesting sleep under
the old policy. A subsequent press wakes it and lets display initialization finish,
which can look like the first press never powered on. The log confirms early
Power-triggered sleep; it does not identify precisely which physical press produced
each event or prove this explains every card-reinsertion/cold-start occurrence.
The new lid-only policy already addresses this userspace trigger; no further PMIC,
bootloader or sleep-rail change is justified yet.

After the new image is verified, test several clean shutdown/cold-start cycles
with lid open and charger disconnected, then repeat with card removal/reinsertion
only after confirmed shutdown. Use a normal startup hold and release, then wait
for boot; do not keep holding throughout startup because the new running-system
five-second hold intentionally requests shutdown. Compare stock only if needed.
If the first start still fails without an early Power-triggered suspend, obtain
serial/early-boot evidence before attributing it to PMIC state or SD-card startup.

## Remaining bring-up work

- [x] User confirmed gameplay, audible sound and volume buttons with the actual ROM.
- [x] BaseOS 19 hardware confirmed corrected panels and lower touch. Boot 004
  measured about 59.75 FPS overall (59.8 median); GPU 3D remains unconfirmed.
- [ ] Test BaseOS 25 GPU 3D, microphone, Menu+X pause, Menu+Y FPS and Menu+Start
  quit; Back remains unmapped. Compare performance and investigate speaker startup
  errors if playback or resume audio becomes unreliable.
- [ ] Test real microphone input in a game that requests it. DSperate 3.0.0
  enables `audio.mic` by default and lazily opens ALSA `plughw:0,0` on the game's
  first microphone read. Boot 002 identifies card 0 as `rk817_hp`; the DS Plus
  DT routes `MICL` to `Mic Jack`, and ALSA is included. Capture/mixer routing and
  gain still need hardware confirmation; playback alone does not prove capture.
  Use `DS_MIC_LOG=1` during a focused test to log sample counts/peak/RMS, and
  distinguish actual microphone input from the synthetic `mic = leftstick`
  hotkey. No microphone-specific patch is justified by the current reports.
- [ ] Diagnose power-button behavior reported on BaseOS 18: after card removal
  and reinsertion, the first hold appears to do nothing and the second starts
  the device. While running, holding Power turns screens/LED off, but release
  can turn them back on; subsequent holds can change the LED to green and
  alternate between apparent off/on states. These are user observations,
  not confirmed clean shutdowns or cold boots.
- [ ] Hardware-test the new long-press clean-shutdown control and verify cold boot after
  shutdown, including card removal/reinsertion. Image 18 inherits
  `HandlePowerKey=suspend`, with `HandlePowerKeyLongPress=ignore` shown as the
  default in its logind configuration. Capture button-event and suspend/resume/
  shutdown logs before assigning a cause; the first boot report ends before
  these interactions. Dark screens and an extinguished LED alone do not prove
  shutdown. Use an explicit `poweroff` command when available before removing
  cards on image 19; retest the new policy before relying on its long-press shutdown.
- [ ] Verify lid-close suspend/lid-open wake, display/audio/touch recovery, sleep
  drain and subsequent stock-card boot without disconnecting the battery.
- [ ] After basic bring-up succeeds, port MinUI and `rgds-hwkeys` from
  `philbudiman/ds-plus-minios`, including brightness and KMS CTM/gamma night mode.
  Include its button, touchscreen and microphone test apps in MinUI Tools,
  adapting miniOS paths and hardware access to ROCKNIX.

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
   and check it powers on without disconnecting the battery. Test that short
   Power presses stay awake, a five-second hold requests clean shutdown, lid
   close sleeps and lid open wakes. Check audio/touch recovery and measured
   sleep drain versus stock.
   Compare charge before/after sleep; do not keep the CPU awake to sample it.

Wait for hardware results before MinUI and `rgds-hwkeys`. Later hotkeys:
Select+Up/Down brightness; Select+Left/Right night mode through KMS CTM/gamma.

## Boot 005: BaseOS 25 hardware follow-up

The user reports short Power no longer suspends and a hold requests shutdown.
A startup hold appears to work on its first attempt, with delayed screens/LED;
this is user evidence, not proof of every cold-start/card-reinsertion case.
Lid suspend/resume and real microphone remain untested. The report snapshot was
taken before gameplay/power tests ended, so its journal does not prove shutdown.

`dsperate.log` reports `gpu3d: on` at startup, before the user changed the menu.
The menu reads configuration, while the `DS_GPU3D` environment override starts
the renderer without updating that configuration. The launcher wrapper now adds
`--gpu3d` when `DS_GPU3D=1`, keeping the runtime configuration/menu consistent.
This wrapper correction is in source for the next image; BaseOS 25 is unchanged.
Ordinary launches without this override retain their original options.

Across 199 reporting windows, median throughput was 59.8 FPS. Three windows had
large `other` interruptions; excluding those, ten windows fell below 99% speed,
with a minimum 53.9 FPS. The worst window averaged 16.2 ms emulation + 1.1 ms
presentation, exceeding the approximately 16.7 ms frame budget. These are window
averages, not individual-frame percentiles or a controlled same-scene comparison
with Boot 004. Menu pauses/reconfiguration cannot be treated as gameplay stalls.
The panels' 59.826 Hz matches the emulated DS rate; changing to 60 Hz is not a
justified fix for these 54–58 FPS workload-related dips.

The log also switches from RGA presentation at startup to CPU scanline scaling
after display reopens. The user subsequently confirmed toggling integer scaling
over/under, then off, before noticing jitter; integer-scaling changes call this
reopen path. There was little gameplay before opening the menu, so a controlled
before/after comparison is still needed. Pinned DSperate v3.0.0 `parse_video()` omits `gpu_present`
and `gpu_mode`, leaving them disabled/default in a new `VideoSetup`; startup
sets them separately, but `reopen_display()` only calls `parse_video()`. This is
a credible mechanism for losing RGA after video changes, distinct from GPU 3D.
The package currently installs a prebuilt emulator. Correcting the reopen path
requires a patched DSperate source build; do not claim that changing an INI or
the wrapper fixes it. Preserve explicit off/rga/vulkan settings in that fix.

Early boot feedback remains outstanding. The DS Plus kernel tree already sets
the green PWM power LED `default-state = "on"`, and PWM/GPIO LED drivers are
built in. The Specific image's U-Boot uses the Quartz64 configuration without
DS Plus LED initialization. Earlier-than-kernel feedback needs board-specific
bootloader work, or a separately tested early GPIO status-LED approach. Current
reports do not timestamp physical LED illumination; do not claim a precise
savings or change PMIC/charging behavior to achieve it.

## Boot 006: second lid-wake failure

The user reports one successful lid close/open at the New Super Mario Bros menu,
then frozen gameplay, static-like corruption and unresponsive controls after
closing/opening in a level. Treat repeat suspend/wake as failing; defer MinUI
and hwkeys until this recovery issue is understood. Microphone testing is
explicitly deferred until after MinUI/its test tools and does not block bring-up.

Boot 006 starts GPU 3D and both RGA presenters successfully. The emulator log
continues recording frame windows; a transient 13.1 FPS window is followed by
59.8 FPS windows. That does not prove the game or its displayed contents advanced.
There is no renderer restart, RGA-to-CPU transition, explicit GPU error or logged
lid transition in this report. Unlike Boot 005, it does not establish the display
reopen bug as the cause. Guest lid/wake handling and GPU/display recovery remain
hypotheses, not confirmed diagnoses.

The saved journal, kernel and compositor reports end around launcher startup
(~20 seconds), before either lid test. They are snapshots taken before launch
and again only after the emulator exits; a frozen emulator never triggers that
final report. They cannot establish whether both cycles entered deep suspend or
whether the kernel/GPU/compositor reported an error on wake.

The next diagnostic image streams `journal-live.txt` (maximum 8 MiB) and
`sway-live.txt` (maximum 2 MiB) in each boot report, independently of emulator
exit. Readers belong to the launcher service and are stopped with it; ten-boot
retention still applies. Suspend/GPU settings and charging limits are unchanged.
Reproduce menu close/open followed by level close/open and return the full newest
boot folder, including these live logs. Do not infer hardware recovery from FPS
output alone or claim this logging change fixes the freeze.
