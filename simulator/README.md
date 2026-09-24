# RG DS Plus launcher prototype

The desktop preview and proposed device launcher use the same SDL2 source: `launcher.cpp`. This replaces the separate Tkinter mock. It currently previews the launcher only; Play shows a placeholder and does not run DraStic.

On macOS, install `sdl2` and `sdl2_ttf`, then:

```sh
cd simulator
make check
./rgds-launcher
./rgds-launcher --rom-dir /path/to/nds
```

On ROCKNIX, build this source with its existing SDL2 and SDL2_ttf packages and run `rgds-launcher --device`. Device mode opens one fullscreen window per SDL display and scans `/storage/roms/nds` by default. Add `--swap-displays` if SDL assigns the screens in reverse. It has not been added to the firmware build yet.

Use arrows or D-pad to select, Enter/A or the lower Play button to preview, and Escape/B or the lower Return button to go back. The lower screen also accepts mouse or touch clicks.

Physical display order, touch coordinates, controller mapping, and DraStic handoff need checking on the RG DS Plus before firmware integration.
