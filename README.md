# PNG to SVG Converter

Convert PNG images to SVG by tracing pixel boundaries for pixel-perfect vector graphics.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 pixel_png_to_svg.py input.png [output.svg]
```

If no output path is specified, the SVG will be saved with the same name as the input file.

## Building Executables

```bash
make install-deps  # Install dependencies
make windows       # Build Windows executable
make mac          # Build macOS executable
make all          # Build both
```
