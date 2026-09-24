# RG DS Plus frontend simulator

Open `index.html` in a desktop browser. It previews two 1024×768 screens at a size that fits the window. No build or dependencies are needed.

- Up/Down or the on-screen arrows: select a game.
- Enter or Play: simulate launching DraStic.
- Escape or Return: go back to the library.
- Choose ROMs: use local `.nds`, `.zip`, or `.7z` filenames instead of the sample list. The browser does not read or run them.

The preview tests layout and navigation only. DraStic, device controls, touch calibration, lid/suspend, and actual display placement still need testing on the RG DS Plus.

Run the state check with `node simulator/model.test.js` from the repository root.
