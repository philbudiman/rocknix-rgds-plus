// SPDX-License-Identifier: GPL-2.0

#include <SDL2/SDL.h>
#include <SDL2/SDL_ttf.h>

#include <algorithm>
#include <cassert>
#include <cctype>
#include <cerrno>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <spawn.h>
#include <string>
#include <sys/wait.h>
#include <vector>

extern char** environ;
namespace fs = std::filesystem;

constexpr int width = 1024;
constexpr int height = 768;
constexpr SDL_Color ink{30, 57, 65, 255};
constexpr SDL_Color muted{74, 98, 107, 255};
constexpr SDL_Color accent{18, 109, 122, 255};

struct Library {
    std::vector<fs::path> games;
    size_t selected = 0;
    bool running = false;

    void move(int step) {
        if (!games.empty() && !running)
            selected = (selected + games.size() + step) % games.size();
    }

    void launch() { running = !games.empty(); }
    void back() { running = false; }
    std::string title() const {
        return games.empty() ? "No DS games" : games[selected].stem().string();
    }
};

bool is_rom(const fs::path& path) {
    std::string ext = path.extension().string();
    std::transform(ext.begin(), ext.end(), ext.begin(), [](unsigned char c) { return std::tolower(c); });
    return ext == ".nds";
}

std::vector<fs::path> load_games(const fs::path& directory) {
    std::vector<fs::path> games;
    std::error_code error;
    for (fs::directory_iterator it(directory, error), end; !error && it != end; it.increment(error)) {
        if (it->is_regular_file(error) && is_rom(it->path())) games.push_back(it->path());
    }
    if (error) std::cerr << "ROM directory: " << error.message() << '\n';
    std::sort(games.begin(), games.end(), [](const auto& a, const auto& b) {
        return a.filename().string() < b.filename().string();
    });
    return games;
}

void fill(SDL_Renderer* renderer, SDL_Rect rect, SDL_Color color) {
    SDL_SetRenderDrawColor(renderer, color.r, color.g, color.b, color.a);
    SDL_RenderFillRect(renderer, &rect);
}

void text(SDL_Renderer* renderer, TTF_Font* font, const std::string& value,
          int x, int y, int max_width, SDL_Color color = ink) {
    SDL_Surface* surface = TTF_RenderUTF8_Blended(font, value.c_str(), color);
    if (!surface) return;
    SDL_Texture* texture = SDL_CreateTextureFromSurface(renderer, surface);
    if (texture) {
        float scale = std::min(1.0f, static_cast<float>(max_width) / surface->w);
        SDL_Rect rect{x, y, static_cast<int>(surface->w * scale), static_cast<int>(surface->h * scale)};
        SDL_RenderCopy(renderer, texture, nullptr, &rect);
        SDL_DestroyTexture(texture);
    }
    SDL_FreeSurface(surface);
}

void button(SDL_Renderer* renderer, TTF_Font* font, SDL_Rect rect,
            const std::string& label, SDL_Color background, SDL_Color foreground) {
    fill(renderer, rect, background);
    int label_width = 0, label_height = 0;
    TTF_SizeUTF8(font, label.c_str(), &label_width, &label_height);
    text(renderer, font, label, rect.x + (rect.w - label_width) / 2,
         rect.y + (rect.h - label_height) / 2, rect.w - 20, foreground);
}

bool save_bmp(SDL_Renderer* renderer, const fs::path& path) {
    SDL_Surface* surface = SDL_CreateRGBSurfaceWithFormat(0, width, height, 32, SDL_PIXELFORMAT_ARGB8888);
    if (!surface) return false;
    bool saved = SDL_RenderReadPixels(renderer, nullptr, surface->format->format,
                                     surface->pixels, surface->pitch) == 0 &&
                 SDL_SaveBMP(surface, path.string().c_str()) == 0;
    if (!saved) std::cerr << "Capture " << path << ": " << SDL_GetError() << '\n';
    SDL_FreeSurface(surface);
    return saved;
}

bool render(SDL_Renderer* renderer, TTF_Font* heading, TTF_Font* body,
            const Library& library, bool lower, const fs::path& capture = {}) {
    fill(renderer, {0, 0, width, height}, lower ? SDL_Color{225, 233, 228, 255}
                                                  : SDL_Color{237, 240, 227, 255});
    if (library.running) {
        text(renderer, heading, "DraStic preview", 52, 50, 900);
        text(renderer, body, library.title(), 52, 220, 900);
        text(renderer, body, lower ? "Touch screen placeholder" : "Upper screen placeholder",
             52, 330, 900, muted);
        if (lower) button(renderer, body, {290, 630, 444, 82}, "Return to library", accent, {255, 255, 255, 255});
    } else if (lower) {
        text(renderer, heading, "Selected game", 52, 50, 900);
        text(renderer, body, library.title(), 52, 250, 900);
        if (library.games.empty()) {
            text(renderer, body, "Add .nds games to your ROM folder", 52, 340, 900, muted);
        } else {
            text(renderer, body, std::to_string(library.selected + 1) + " of " +
                 std::to_string(library.games.size()), 52, 340, 900, muted);
            button(renderer, body, {52, 620, 260, 92}, "Previous", ink, {255, 255, 255, 255});
            button(renderer, body, {362, 620, 300, 92}, "Play", accent, {255, 255, 255, 255});
            button(renderer, body, {712, 620, 260, 92}, "Next", ink, {255, 255, 255, 255});
        }
    } else {
        text(renderer, heading, "Nintendo DS", 52, 50, 900);
        fill(renderer, {52, 150, 920, 555}, {252, 252, 246, 255});
        if (library.games.empty()) text(renderer, body, "No games found", 80, 200, 860, muted);
        const size_t first = library.selected > 5 ? library.selected - 5 : 0;
        for (size_t i = first; i < library.games.size() && i < first + 8; ++i) {
            int y = 180 + static_cast<int>(i - first) * 64;
            if (i == library.selected) fill(renderer, {68, y - 8, 888, 56}, accent);
            text(renderer, body, library.games[i].filename().string(), 86, y, 840,
                 i == library.selected ? SDL_Color{255, 255, 255, 255} : ink);
        }
    }
    bool saved = capture.empty() || save_bmp(renderer, capture);
    SDL_RenderPresent(renderer);
    return saved;
}

struct Screen {
    SDL_Window* window = nullptr;
    SDL_Renderer* renderer = nullptr;
};

enum class Action { None, Previous, Next, Play, Back };

int run_launcher(const fs::path& command, const fs::path& rom) {
    std::string program = command.string();
    std::string game = rom.string();
    char* args[] = {program.data(), game.data(), nullptr};
    pid_t child = 0;
    int error = posix_spawn(&child, program.c_str(), nullptr, nullptr, args, environ);
    if (error) { std::cerr << "Launch failed: " << std::strerror(error) << '\n'; return 1; }
    int status = 0;
    while (waitpid(child, &status, 0) == -1) {
        if (errno != EINTR) { std::cerr << "Wait failed: " << std::strerror(errno) << '\n'; return 1; }
    }
    return WIFEXITED(status) ? WEXITSTATUS(status) : 1;
}

int act(Library& library, Action action, const fs::path& launcher = {}, Screen* screens = nullptr) {
    switch (action) {
        case Action::Previous: library.move(-1); break;
        case Action::Next: library.move(1); break;
        case Action::Back: library.back(); break;
        case Action::Play: {
            if (library.running) { library.back(); break; }
            if (library.games.empty()) break;
            if (launcher.empty()) { library.launch(); break; }
            if (screens) for (int i = 0; i < 2; ++i) SDL_HideWindow(screens[i].window);
            int status = run_launcher(launcher, library.games[library.selected]);
            if (status != 0)
                std::cerr << "Game exited with an error\n";
            if (screens) for (int i = 0; i < 2; ++i) SDL_ShowWindow(screens[i].window);
            library.back();
            return status;
        }
        case Action::None: break;
    }
    return 0;
}

Action action_for(const SDL_Event& event, SDL_Window* lower, bool running) {
    if (event.type == SDL_KEYDOWN && !event.key.repeat) {
        switch (event.key.keysym.sym) {
            case SDLK_UP: case SDLK_LEFT: return Action::Previous;
            case SDLK_DOWN: case SDLK_RIGHT: return Action::Next;
            case SDLK_RETURN: case SDLK_SPACE: return Action::Play;
            case SDLK_ESCAPE: return Action::Back;
        }
    } else if (event.type == SDL_CONTROLLERBUTTONDOWN) {
        switch (event.cbutton.button) {
            case SDL_CONTROLLER_BUTTON_DPAD_UP: case SDL_CONTROLLER_BUTTON_DPAD_LEFT: return Action::Previous;
            case SDL_CONTROLLER_BUTTON_DPAD_DOWN: case SDL_CONTROLLER_BUTTON_DPAD_RIGHT: return Action::Next;
            case SDL_CONTROLLER_BUTTON_A: return Action::Play;
            case SDL_CONTROLLER_BUTTON_B: return Action::Back;
        }
    } else if (event.type == SDL_MOUSEBUTTONDOWN && event.button.button == SDL_BUTTON_LEFT &&
               event.button.windowID == SDL_GetWindowID(lower)) {
        int window_width = 0, window_height = 0;
        SDL_GetWindowSize(lower, &window_width, &window_height);
        if (window_width == 0 || window_height == 0) return Action::None;
        int x = event.button.x * width / window_width;
        int y = event.button.y * height / window_height;
        if (y >= 620 && y < 712) {
            if (running && x >= 290 && x < 734) return Action::Back;
            if (x >= 52 && x < 312) return Action::Previous;
            if (x >= 362 && x < 662) return Action::Play;
            if (x >= 712 && x < 972) return Action::Next;
        }
    }
    return Action::None;
}

void self_test(const fs::path& launcher) {
    assert(is_rom("game.NDS"));
    assert(!is_rom("game.zip") && !is_rom("game.7z") && !is_rom("notes.txt"));
    Library library{{"Alpha.nds", "Beta.nds"}};
    act(library, Action::Previous);
    assert(library.title() == "Beta");
    act(library, Action::Play);
    act(library, Action::Next);
    assert(library.running && library.title() == "Beta");
    act(library, Action::Back);
    assert(!library.running);
    library.games = {"A Game.nds"};
    library.selected = 0;
    assert(act(library, Action::Play, launcher.empty() ? "/usr/bin/true" : launcher) == 0);
    assert(!library.running && library.title() == "A Game");
    assert(run_launcher("/usr/bin/false", "A Game.nds") != 0);
    library.games.clear();
    act(library, Action::Play);
    assert(!library.running && library.title() == "No DS games");
}

bool capture_scenarios(Screen* screens, TTF_Font* heading, TTF_Font* body, const fs::path& directory) {
    std::error_code error;
    fs::create_directories(directory, error);
    if (error) { std::cerr << error.message() << '\n'; return false; }
    Library library{{"Sample Adventure.nds", "Sample Puzzle.nds", "Sample Racing.nds"}};
    auto capture = [&](const char* name) {
        return render(screens[0].renderer, heading, body, library, false, directory / (std::string(name) + "-upper.bmp")) &&
               render(screens[1].renderer, heading, body, library, true, directory / (std::string(name) + "-lower.bmp"));
    };
    if (!capture("library")) return false;
    act(library, Action::Next);
    if (!capture("selected")) return false;
    act(library, Action::Play);
    if (!capture("preview")) return false;
    act(library, Action::Back);
    if (!capture("returned")) return false;
    library.games.clear();
    return capture("empty");
}

int main(int argc, char** argv) {
    bool device = false;
    bool swap_displays = false;
    bool test = false;
    fs::path rom_dir;
    fs::path capture_dir;
    fs::path launcher;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--self-test") test = true;
        else if (arg == "--device") device = true;
        else if (arg == "--swap-displays") swap_displays = true;
        else if (arg == "--rom-dir" && i + 1 < argc) rom_dir = argv[++i];
        else if (arg == "--capture" && i + 1 < argc) capture_dir = argv[++i];
        else if (arg == "--launcher" && i + 1 < argc) launcher = argv[++i];
        else { std::cerr << "Usage: rgds-launcher [--device] [--swap-displays] [--rom-dir PATH] [--launcher PATH] [--capture DIR] [--self-test]\n"; return 2; }
    }
    if (test) { self_test(launcher); std::cout << "Launcher state check passed\n"; return 0; }
    Library library;
    library.games = rom_dir.empty() && !device
        ? std::vector<fs::path>{"Sample Adventure.nds", "Sample Puzzle.nds", "Sample Racing.nds"}
        : load_games(rom_dir.empty() ? "/storage/roms/nds" : rom_dir);

    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_GAMECONTROLLER) != 0 || TTF_Init() != 0) {
        std::cerr << "SDL initialization failed: " << SDL_GetError() << ' ' << TTF_GetError() << '\n';
        return 1;
    }
    if (device && SDL_GetNumVideoDisplays() < 2) {
        std::cerr << "Device mode requires two displays\n";
        return 1;
    }
    const char* font_path = device ? "/usr/share/fonts/truetype/noto-cjk/NotoSansCJKsc-Regular.otf"
                                   : "/System/Library/Fonts/Supplemental/Arial.ttf";
    TTF_Font* heading = TTF_OpenFont(font_path, 48);
    TTF_Font* body = TTF_OpenFont(font_path, 34);
    if (!heading || !body) {
        std::cerr << "Cannot open font " << font_path << ": " << TTF_GetError() << '\n';
        return 1;
    }
    Screen screens[2];
    for (int i = 0; i < 2; ++i) {
        int display = swap_displays ? 1 - i : i;
        int x = device ? SDL_WINDOWPOS_CENTERED_DISPLAY(display) : 80 + i * 590;
        int y = device ? SDL_WINDOWPOS_CENTERED_DISPLAY(display) : 90;
        screens[i].window = SDL_CreateWindow(i ? "RG DS Plus - lower" : "RG DS Plus - upper",
            x, y, device || !capture_dir.empty() ? width : 560,
            device || !capture_dir.empty() ? height : 420,
            !capture_dir.empty() ? SDL_WINDOW_HIDDEN : device ? SDL_WINDOW_FULLSCREEN_DESKTOP : 0);
        if (!screens[i].window) { std::cerr << SDL_GetError() << '\n'; return 1; }
        screens[i].renderer = SDL_CreateRenderer(screens[i].window, -1, SDL_RENDERER_ACCELERATED);
        if (!screens[i].renderer) screens[i].renderer = SDL_CreateRenderer(screens[i].window, -1, SDL_RENDERER_SOFTWARE);
        if (!screens[i].renderer) { std::cerr << SDL_GetError() << '\n'; return 1; }
        SDL_RenderSetLogicalSize(screens[i].renderer, width, height);
    }
    if (!capture_dir.empty()) {
        bool captured = capture_scenarios(screens, heading, body, capture_dir);
        for (auto& screen : screens) { SDL_DestroyRenderer(screen.renderer); SDL_DestroyWindow(screen.window); }
        TTF_CloseFont(body);
        TTF_CloseFont(heading);
        TTF_Quit();
        SDL_Quit();
        return captured ? 0 : 1;
    }
    SDL_GameController* controller = SDL_IsGameController(0) ? SDL_GameControllerOpen(0) : nullptr;
    bool active = true;
    while (active) {
        render(screens[0].renderer, heading, body, library, false);
        render(screens[1].renderer, heading, body, library, true);
        SDL_Event event;
        if (!SDL_WaitEvent(&event)) break;
        if (event.type == SDL_QUIT || (event.type == SDL_WINDOWEVENT && event.window.event == SDL_WINDOWEVENT_CLOSE)) active = false;
        else act(library, action_for(event, screens[1].window, library.running), launcher, screens);
    }
    if (controller) SDL_GameControllerClose(controller);
    for (auto& screen : screens) { SDL_DestroyRenderer(screen.renderer); SDL_DestroyWindow(screen.window); }
    TTF_CloseFont(body);
    TTF_CloseFont(heading);
    TTF_Quit();
    SDL_Quit();
}
