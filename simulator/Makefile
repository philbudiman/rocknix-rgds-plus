CXX ?= c++
CXXFLAGS ?= -O2 -std=c++17 -Wall -Wextra
SOURCE = ../projects/ROCKNIX/packages/ui/rgds-launcher/sources/launcher.cpp

rgds-launcher: $(SOURCE)
	$(CXX) $(CXXFLAGS) -I$(shell sdl2-config --prefix)/include $< -o $@ $(shell sdl2-config --libs) -lSDL2_ttf

.PHONY: check clean
check: rgds-launcher
	./rgds-launcher --self-test --launcher ./fake-launch.sh
	SDL_VIDEODRIVER=dummy SDL_RENDER_DRIVER=software ./rgds-launcher --capture captures
	@for name in library selected preview returned empty; do test -s captures/$$name-upper.bmp && test -s captures/$$name-lower.bmp || exit 1; done
	@if command -v sips >/dev/null; then for image in captures/*.bmp; do sips -s format png "$$image" --out "$${image%.bmp}.png" >/dev/null; done; fi

clean:
	rm -f rgds-launcher
