# RG DS Plus launcher prototype

The desktop preview and ROCKNIX package compile the same SDL2 source in `projects/ROCKNIX/packages/ui/rgds-launcher/sources/launcher.cpp`.

On macOS, install `sdl2` and `sdl2_ttf`, then run from this directory:

```sh
make check
./rgds-launcher
./rgds-launcher --rom-dir /path/to/nds
```

`make check` tests selection and launch/return with a harmless program, then writes ten 1024×768 screen captures to `captures/` using SDL's headless video driver. On macOS it also converts them to PNG for inspection. It does not open a browser or ROM.

Use arrows or D-pad to select, Enter/A or the lower Play button to preview, and Escape/B or the lower Return button to go back. The lower screen also accepts mouse or touch clicks. `--launcher PATH` runs that executable with the selected ROM path as one argument and returns to the library when it exits; omit it to see the preview placeholder.

The DS-only ROCKNIX build selects this package but keeps EmulationStation as the active frontend. For a manual trial, run `rgds-launcher --device`; add `--swap-displays` if the displays are reversed. The real DraStic handoff is deferred until device testing.

The library lists `.nds` only. Archives are withheld until their DraStic launch path is confirmed. Physical display placement, touch coordinates, controller mapping, and game handoff still need testing on the RG DS Plus.
