# Makefile — Alternative simple au build.sh
# ─────────────────────────────────────────────────────────────────────────────
# Usage : make        (compile)
#         make clean  (nettoie)
#         make run    (compile + exécute)
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: all clean run cmake

all: cmake
	@cd build && make -j$$(nproc)
	@echo ""
	@echo "✅ Compilation OK → ./build/eragrok_test"

cmake:
	@mkdir -p build
	@cd build && cmake .. -DCMAKE_BUILD_TYPE=Release

clean:
	@rm -rf build/
	@echo "✅ Build nettoyé"

run: all
	@./build/eragrok_test
