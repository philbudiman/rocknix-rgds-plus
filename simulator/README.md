# RG DS Plus frontend simulator

Run `python3 simulator/simulator.py` from the repository root. The native window previews two 1024×768 screens at a smaller desktop scale. It uses Python's standard Tkinter library; no browser or package installation is needed.

- Up/Down or the on-screen controls: select a game.
- Enter or Play: simulate launching DraStic.
- Escape or Return to library: end the simulated game.
- Choose ROMs: show local `.nds`, `.zip`, or `.7z` filenames instead of the sample list. The simulator does not open or run them.

Run `python3 simulator/simulator.py --self-test` to check selection, launch, and return behavior without opening a window.

This previews layout and navigation only. DraStic, physical controls, touch calibration, lid/suspend, and display placement still need testing on the RG DS Plus.
