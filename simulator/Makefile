CXX ?= c++
CXXFLAGS ?= -O2 -std=c++17 -Wall -Wextra

rgds-launcher: launcher.cpp
	$(CXX) $(CXXFLAGS) $(shell sdl2-config --cflags) $< -o $@ $(shell sdl2-config --libs) -lSDL2_ttf

.PHONY: check clean
check: rgds-launcher
	./rgds-launcher --self-test

clean:
	rm -f rgds-launcher
