# Makefile for building pixel_png_to_svg executables for Windows and Mac
# Usage:
#   make windows  - Build Windows executable
#   make mac      - Build macOS executable
#   make all      - Build both executables
#   make clean    - Remove build artifacts

PYTHON := python3
PYINSTALLER := pyinstaller
SCRIPT := pixel_png_to_svg.py
APP_NAME := pixel_png_to_svg

# Output directories
DIST_DIR := dist
BUILD_DIR := build
SPEC_DIR := .

# PyInstaller options
PYINSTALLER_OPTS := --onefile --windowed --console --clean

.PHONY: all windows mac clean help install-deps

all: windows mac

# Install Python dependencies
install-deps:
	@echo "Installing Python dependencies..."
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install pyinstaller

# Build Windows executable
windows: install-deps
	@echo "Building Windows executable..."
	$(PYINSTALLER) $(PYINSTALLER_OPTS) \
		--name $(APP_NAME).exe \
		--icon NONE \
		$(SCRIPT)
	@echo "Windows executable created at: $(DIST_DIR)/$(APP_NAME).exe"

# Build macOS executable
mac: install-deps
	@echo "Building macOS executable..."
	$(PYINSTALLER) $(PYINSTALLER_OPTS) \
		--name $(APP_NAME) \
		--icon NONE \
		--target-arch universal2 \
		$(SCRIPT)
	@echo "macOS executable created at: $(DIST_DIR)/$(APP_NAME)"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(BUILD_DIR) $(DIST_DIR)
	rm -f *.spec
	rm -rf __pycache__
	@echo "Clean complete."

# Display help
help:
	@echo "Makefile for pixel_png_to_svg"
	@echo ""
	@echo "Usage:"
	@echo "  make windows      Build Windows executable (.exe)"
	@echo "  make mac          Build macOS executable"
	@echo "  make all          Build both Windows and Mac executables"
	@echo "  make install-deps Install required Python dependencies"
	@echo "  make clean        Remove build artifacts"
	@echo "  make help         Display this help message"
	@echo ""
	@echo "Requirements:"
	@echo "  - Python 3.x"
	@echo "  - pip"
	@echo ""
	@echo "The executables will be created in the '$(DIST_DIR)' directory."
	@echo "Drag and drop PNG files onto the executable to convert them to SVG."
