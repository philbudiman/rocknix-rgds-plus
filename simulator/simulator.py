#!/usr/bin/env python3
"""Desktop preview of the proposed RG DS Plus launcher."""

from pathlib import Path
import sys


SAMPLES = ("Sample Adventure.nds", "Sample Puzzle.zip", "Sample Racing.7z")


class Model:
    def __init__(self, names=SAMPLES):
        self.load(names)

    def load(self, names):
        self.games = sorted(
            {Path(name).name for name in names if Path(name).suffix.lower() in {".nds", ".zip", ".7z"}},
            key=str.casefold,
        )
        self.selected = 0
        self.running = False

    def move(self, step):
        if self.games and not self.running:
            self.selected = (self.selected + step) % len(self.games)

    def launch(self):
        if self.games:
            self.running = True

    def exit_game(self):
        self.running = False

    @property
    def game(self):
        return self.games[self.selected] if self.games else None


def self_test():
    model = Model(["/roms/Zeta.NDS", "Alpha.zip", "notes.txt", "Zeta.NDS"])
    assert model.games == ["Alpha.zip", "Zeta.NDS"]
    model.move(-1)
    assert model.game == "Zeta.NDS"
    model.launch()
    model.move(1)
    assert model.running and model.game == "Zeta.NDS"
    model.exit_game()
    assert not model.running
    model.load([])
    model.launch()
    assert not model.running and model.game is None


def run_gui():
    import tkinter as tk
    from tkinter import filedialog

    model = Model()
    root = tk.Tk()
    root.title("RG DS Plus frontend simulator")
    root.configure(bg="#111923")
    root.resizable(False, False)

    heading = tk.Frame(root, bg="#111923")
    heading.pack(fill="x", padx=20, pady=(16, 10))
    tk.Label(heading, text="RG DS Plus frontend simulator", bg="#111923", fg="#e7eef3", font=("Helvetica", 18, "bold")).pack(side="left")

    screens = tk.Frame(root, bg="#111923")
    screens.pack(padx=20)
    top = tk.Frame(screens, width=560, height=420, bg="#edf0e3", highlightbackground="#05090d", highlightthickness=7)
    bottom = tk.Frame(screens, width=560, height=420, bg="#e1e9e4", highlightbackground="#05090d", highlightthickness=7)
    top.grid(row=1, column=0, padx=(0, 16))
    bottom.grid(row=1, column=1)
    top.grid_propagate(False)
    bottom.grid_propagate(False)
    tk.Label(screens, text="UPPER DISPLAY · 1024 × 768", bg="#111923", fg="#aab8c3").grid(row=0, column=0, sticky="w", pady=(0, 6))
    tk.Label(screens, text="LOWER TOUCH DISPLAY · 1024 × 768", bg="#111923", fg="#aab8c3").grid(row=0, column=1, sticky="w", pady=(0, 6))

    top_library = tk.Frame(top, bg="#edf0e3")
    tk.Label(top_library, text="Nintendo DS", bg="#edf0e3", fg="#173b47", font=("Helvetica", 24, "bold")).pack(anchor="w", padx=24, pady=(22, 16))
    game_list = tk.Listbox(top_library, bg="#fcfcf6", fg="#203842", selectbackground="#126d7a", selectforeground="white", font=("Helvetica", 17), activestyle="none", borderwidth=0, highlightthickness=0)
    game_list.pack(fill="both", expand=True, padx=24, pady=(0, 24))

    top_running = tk.Frame(top, bg="#edf0e3")
    tk.Label(top_running, text="DraStic · simulated", bg="#edf0e3", fg="#173b47", font=("Helvetica", 24, "bold")).pack(anchor="w", padx=24, pady=22)
    running_game = tk.Label(top_running, bg="#edf0e3", fg="#203842", font=("Helvetica", 21), wraplength=470)
    running_game.pack(expand=True)

    bottom_library = tk.Frame(bottom, bg="#e1e9e4")
    tk.Label(bottom_library, text="Selected game", bg="#e1e9e4", fg="#173b47", font=("Helvetica", 24, "bold")).pack(anchor="w", padx=24, pady=22)
    selected_game = tk.Label(bottom_library, bg="#e1e9e4", fg="#203842", font=("Helvetica", 22, "bold"), wraplength=470)
    selected_game.pack(expand=True, padx=24)
    position = tk.Label(bottom_library, bg="#e1e9e4", fg="#48616c", font=("Helvetica", 14))
    position.pack(pady=(0, 18))
    controls = tk.Frame(bottom_library, bg="#e1e9e4")
    controls.pack(pady=(0, 24))

    bottom_running = tk.Frame(bottom, bg="#e1e9e4")
    tk.Label(bottom_running, text="Lower screen · simulated", bg="#e1e9e4", fg="#173b47", font=("Helvetica", 24, "bold")).pack(anchor="w", padx=24, pady=22)
    tk.Label(bottom_running, text="DraStic touch screen placeholder", bg="#e1e9e4", fg="#48616c", font=("Helvetica", 18)).pack(expand=True)

    status = tk.Label(root, bg="#111923", fg="#aab8c3", font=("Helvetica", 13))
    status.pack(anchor="w", padx=20, pady=(12, 16))

    for frame in (top_library, top_running, bottom_library, bottom_running):
        frame.place(x=0, y=0, relwidth=1, relheight=1)

    def render():
        if model.running:
            top_running.tkraise()
            bottom_running.tkraise()
            running_game.configure(text=model.game)
            status.configure(text="Simulated DraStic session · Esc or Return goes back. No ROM is running.")
        else:
            top_library.tkraise()
            bottom_library.tkraise()
            game_list.selection_clear(0, tk.END)
            if model.game:
                game_list.selection_set(model.selected)
                game_list.see(model.selected)
            selected_game.configure(text=Path(model.game).stem if model.game else "No DS games")
            position.configure(text=f"{model.selected + 1} of {len(model.games)} · {model.game}" if model.game else "Choose ROMs to preview your library.")
            for button in (previous, play, next_game):
                button.configure(state="normal" if model.game else "disabled")
            status.configure(text="↑ ↓ Select · Enter Play · Esc Return. ROM files are never opened or executed.")

    def move(step):
        model.move(step)
        render()

    def launch():
        model.launch()
        render()

    def exit_game():
        model.exit_game()
        render()

    def choose_roms():
        names = filedialog.askopenfilenames(title="Choose DS ROM filenames", filetypes=[("DS ROMs", "*.nds *.zip *.7z"), ("All files", "*")])
        if names:
            model.load(names)
            game_list.delete(0, tk.END)
            for name in model.games:
                game_list.insert(tk.END, name)
            render()

    def on_select(_event):
        selection = game_list.curselection()
        if selection and not model.running and selection[0] != model.selected:
            model.selected = selection[0]
            render()

    previous = tk.Button(controls, text="↑ Previous", command=lambda: move(-1), font=("Helvetica", 16))
    previous.pack(side="left", padx=8)
    play = tk.Button(controls, text="Play", command=launch, font=("Helvetica", 16, "bold"), bg="#126d7a", fg="white")
    play.pack(side="left", padx=8)
    next_game = tk.Button(controls, text="Next ↓", command=lambda: move(1), font=("Helvetica", 16))
    next_game.pack(side="left", padx=8)
    tk.Button(bottom_running, text="Return to library", command=exit_game, font=("Helvetica", 16, "bold")).pack(pady=(0, 24))
    tk.Button(heading, text="Choose ROMs", command=choose_roms, font=("Helvetica", 14)).pack(side="right")

    game_list.bind("<<ListboxSelect>>", on_select)
    game_list.bind("<Up>", lambda _event: (move(-1), "break")[1])
    game_list.bind("<Down>", lambda _event: (move(1), "break")[1])
    root.bind("<Up>", lambda _event: move(-1))
    root.bind("<Down>", lambda _event: move(1))
    root.bind("<Return>", lambda _event: launch() if not model.running else exit_game())
    root.bind("<Escape>", lambda _event: exit_game())

    for name in model.games:
        game_list.insert(tk.END, name)
    render()
    root.mainloop()


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
        print("Simulator state check passed")
    else:
        run_gui()
