#include <SDL.h>
#include <SDL_ttf.h>

#include <algorithm>
#include <cassert>
#include <cctype>
#include <filesystem>
#include <iostream>
#include <string>
#include <vector>

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
    return ext == ".nds" || ext == ".zip" || ext == ".7z";
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

void self_test() {
    assert(is_rom("game.NDS") && is_rom("game.zip") && is_rom("game.7z"));
    assert(!is_rom("notes.txt"));
    Library library{{"Alpha.nds", "Beta.zip"}};
    library.move(-1);
    assert(library.title() == "Beta");
    library.launch();
    library.move(1);
    assert(library.running && library.title() == "Beta");
    library.back();
    assert(!library.running);
    library.games.clear();
    library.launch();
    assert(!library.running && library.title() == "No DS games");
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

void render(SDL_Renderer* renderer, TTF_Font* heading, TTF_Font* body,
            const Library& library, bool lower) {
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
            text(renderer, body, "Pass --rom-dir to show your games", 52, 340, 900, muted);
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
    SDL_RenderPresent(renderer);
}

struct Screen {
    SDL_Window* window = nullptr;
    SDL_Renderer* renderer = nullptr;
};

int main(int argc, char** argv) {
    bool device = false;
    bool swap_displays = false;
    fs::path rom_dir;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--self-test") { self_test(); std::cout << "Launcher state check passed\n"; return 0; }
        if (arg == "--device") device = true;
        else if (arg == "--swap-displays") swap_displays = true;
        else if (arg == "--rom-dir" && i + 1 < argc) rom_dir = argv[++i];
        else { std::cerr << "Usage: rgds-launcher [--device] [--swap-displays] [--rom-dir PATH] [--self-test]\n"; return 2; }
    }
    Library library;
    library.games = rom_dir.empty() && !device
        ? std::vector<fs::path>{"Sample Adventure.nds", "Sample Puzzle.zip", "Sample Racing.7z"}
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
            x, y, device ? width : 560, device ? height : 420,
            device ? SDL_WINDOW_FULLSCREEN_DESKTOP : 0);
        if (!screens[i].window) { std::cerr << SDL_GetError() << '\n'; return 1; }
        screens[i].renderer = SDL_CreateRenderer(screens[i].window, -1, SDL_RENDERER_ACCELERATED);
        if (!screens[i].renderer) screens[i].renderer = SDL_CreateRenderer(screens[i].window, -1, SDL_RENDERER_SOFTWARE);
        if (!screens[i].renderer) { std::cerr << SDL_GetError() << '\n'; return 1; }
        SDL_RenderSetLogicalSize(screens[i].renderer, width, height);
    }
    SDL_GameController* controller = SDL_IsGameController(0) ? SDL_GameControllerOpen(0) : nullptr;
    bool active = true;
    while (active) {
        render(screens[0].renderer, heading, body, library, false);
        render(screens[1].renderer, heading, body, library, true);
        SDL_Event event;
        if (!SDL_WaitEvent(&event)) break;
        if (event.type == SDL_QUIT || (event.type == SDL_WINDOWEVENT && event.window.event == SDL_WINDOWEVENT_CLOSE)) active = false;
        else if (event.type == SDL_KEYDOWN && !event.key.repeat) {
            switch (event.key.keysym.sym) {
                case SDLK_UP: case SDLK_LEFT: library.move(-1); break;
                case SDLK_DOWN: case SDLK_RIGHT: library.move(1); break;
                case SDLK_RETURN: case SDLK_SPACE: library.running ? library.back() : library.launch(); break;
                case SDLK_ESCAPE: library.back(); break;
            }
        } else if (event.type == SDL_CONTROLLERBUTTONDOWN) {
            switch (event.cbutton.button) {
                case SDL_CONTROLLER_BUTTON_DPAD_UP: case SDL_CONTROLLER_BUTTON_DPAD_LEFT: library.move(-1); break;
                case SDL_CONTROLLER_BUTTON_DPAD_DOWN: case SDL_CONTROLLER_BUTTON_DPAD_RIGHT: library.move(1); break;
                case SDL_CONTROLLER_BUTTON_A: library.running ? library.back() : library.launch(); break;
                case SDL_CONTROLLER_BUTTON_B: library.back(); break;
            }
        } else if (event.type == SDL_MOUSEBUTTONDOWN && event.button.button == SDL_BUTTON_LEFT &&
                   event.button.windowID == SDL_GetWindowID(screens[1].window)) {
            int window_width = 0, window_height = 0;
            SDL_GetWindowSize(screens[1].window, &window_width, &window_height);
            int x = event.button.x * width / window_width;
            int y = event.button.y * height / window_height;
            if (y >= 620 && y < 712) {
                if (library.running) library.back();
                else if (x < 312) library.move(-1);
                else if (x >= 362 && x < 662) library.launch();
                else if (x >= 712) library.move(1);
            }
        }
    }
    if (controller) SDL_GameControllerClose(controller);
    for (auto& screen : screens) { SDL_DestroyRenderer(screen.renderer); SDL_DestroyWindow(screen.window); }
    TTF_CloseFont(body);
    TTF_CloseFont(heading);
    TTF_Quit();
    SDL_Quit();
}
