#!/usr/bin/env python3
"""
Convert PNG to SVG: traces black pixel boundaries at integer coordinates.
Traces edges between black and white pixels to create pixel-perfect paths.
"""

import sys
import os
from pathlib import Path
import cv2
import numpy as np


def png_to_svg(png_path, output_path=None):
    """
    Convert a PNG image to SVG by tracing pixel boundaries.

    Args:
        png_path: Path to the input PNG file
        output_path: Path for the output SVG file (optional, defaults to same name with .svg)
    """
    # Read the image
    if not os.path.exists(png_path):
        print(f"Error: File '{png_path}' not found")
        sys.exit(1)

    img = cv2.imread(png_path)
    if img is None:
        print(f"Error: Could not read image '{png_path}'")
        sys.exit(1)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Get image dimensions
    height, width = gray.shape

    # Convert to binary (black and white)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    # Set output path
    if output_path is None:
        output_path = str(Path(png_path).with_suffix('.svg'))

    # Find contours to get hierarchy
    inverted = cv2.bitwise_not(binary)
    contours, hierarchy = cv2.findContours(inverted, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    # Generate SVG
    svg_content = generate_svg(binary, width, height, contours, hierarchy)

    # Write SVG file
    with open(output_path, 'w') as f:
        f.write(svg_content)

    print(f"Successfully converted '{png_path}' to '{output_path}'")


def generate_svg(binary_image, width, height, contours, hierarchy):
    """
    Generate SVG by tracing actual pixel-grid edges.
    Creates one <path> element per disconnected black region (including holes).

    Args:
        binary_image: Binary image (0 = black, 255 = white)
        width: Image width
        height: Image height
        contours: OpenCV contours
        hierarchy: Contour hierarchy

    Returns:
        SVG string
    """
    # Start SVG document
    svg_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'  <rect width="{width}" height="{height}" fill="white"/>',
    ]

    if hierarchy is None or len(contours) == 0:
        svg_lines.append('</svg>')
        return '\n'.join(svg_lines)

    hierarchy = hierarchy[0]

    # Trace all edges from all black pixels
    edges = set()
    for y in range(height):
        for x in range(width):
            if binary_image[y, x] == 0:  # Black pixel
                # Check each direction for edges
                # Top edge
                if y == 0 or binary_image[y-1, x] == 255:
                    edges.add(((x, y), (x+1, y)))
                # Right edge
                if x == width-1 or binary_image[y, x+1] == 255:
                    edges.add(((x+1, y), (x+1, y+1)))
                # Bottom edge
                if y == height-1 or binary_image[y+1, x] == 255:
                    edges.add(((x+1, y+1), (x, y+1)))
                # Left edge
                if x == 0 or binary_image[y, x-1] == 255:
                    edges.add(((x, y+1), (x, y)))

    # Trace edges into connected paths
    if edges:
        paths = trace_edges(edges)

        # Group paths by top-level contour using hierarchy
        processed = set()

        for idx in range(len(contours)):
            if idx in processed or hierarchy[idx][3] != -1:
                continue  # Skip processed and non-top-level contours

            # Collect all contour indices for this region (outer + holes)
            region_indices = {idx}
            child_idx = hierarchy[idx][2]
            while child_idx != -1:
                region_indices.add(child_idx)
                processed.add(child_idx)
                child_idx = hierarchy[child_idx][0]

            processed.add(idx)

            # Find which paths belong to this region by checking contour bounds
            region_path_data = []
            region_contours = [contours[i] for i in region_indices]

            for path in paths:
                if len(path) >= 3 and paths_belongs_to_contours(path, region_contours):
                    path_parts = []
                    path_parts.append(f"M {path[0][0]} {path[0][1]}")
                    for point in path[1:]:
                        path_parts.append(f"L {point[0]} {point[1]}")
                    path_parts.append("Z")
                    region_path_data.append(" ".join(path_parts))

            # Output one path element per region
            if region_path_data:
                path_data = " ".join(region_path_data)
                svg_lines.append(f'  <path d="{path_data}" fill="black" fill-rule="evenodd" shape-rendering="crispEdges"/>')

    # Close SVG
    svg_lines.append('</svg>')
    return '\n'.join(svg_lines)


def paths_belongs_to_contours(path, contours):
    """
    Check if a traced path belongs to any of the given contours.
    Uses bounding rectangle check.
    """
    if not path or not contours:
        return False

    # Get path bounds
    xs = [p[0] for p in path]
    ys = [p[1] for p in path]
    path_min_x, path_max_x = min(xs), max(xs)
    path_min_y, path_max_y = min(ys), max(ys)
    path_center_x = (path_min_x + path_max_x) / 2
    path_center_y = (path_min_y + path_max_y) / 2

    # Check if path center is within any contour's bounding box
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if x <= path_center_x <= x + w and y <= path_center_y <= y + h:
            return True

    return False


def trace_edges(edges):
    """
    Trace edges into connected paths.
    Returns list of paths, each path is a list of points.
    """
    # Create a lookup dictionary for fast edge finding
    edge_dict = {}  # Maps starting point -> list of (edge_index, edge)
    edges_list = list(edges)

    for idx, edge in enumerate(edges_list):
        start_point = edge[0]
        if start_point not in edge_dict:
            edge_dict[start_point] = []
        edge_dict[start_point].append((idx, edge))

    used = set()
    paths = []

    for start_edge_idx in range(len(edges_list)):
        if start_edge_idx in used:
            continue

        # Start a new path
        path = []
        current_edge = edges_list[start_edge_idx]
        used.add(start_edge_idx)
        path.append(current_edge[0])
        current_point = current_edge[1]

        # Follow connected edges
        while True:
            path.append(current_point)

            # Find next edge that starts at current_point
            found = False
            if current_point in edge_dict:
                for edge_idx, edge in edge_dict[current_point]:
                    if edge_idx not in used:
                        used.add(edge_idx)
                        current_point = edge[1]
                        found = True
                        break

            if not found:
                break

        paths.append(path)

    return paths


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: pixel_png_to_svg <input_png1> [input_png2] [input_png3] ...")
        print("\nExample: pixel_png_to_svg image.png")
        print("         pixel_png_to_svg image1.png image2.png image3.png")
        print("\nDrag and drop PNG files onto this executable to convert them to SVG.")
        input("Press Enter to exit...")
        sys.exit(1)

    # Get list of input files
    input_files = sys.argv[1:]

    # Filter for PNG files only
    png_files = [f for f in input_files if f.lower().endswith('.png')]

    if not png_files:
        print("Error: No PNG files provided")
        input("Press Enter to exit...")
        sys.exit(1)

    # Process each file with progress indicator
    total_files = len(png_files)
    print(f"\nProcessing {total_files} file(s)...\n")

    successful = 0
    failed = 0

    for idx, input_file in enumerate(png_files, 1):
        print(f"[{idx}/{total_files}] Processing: {os.path.basename(input_file)}")
        try:
            png_to_svg(input_file, None)
            successful += 1
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            failed += 1
        print()  # Empty line for readability

    # Summary
    print("=" * 50)
    print(f"Conversion complete!")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print("=" * 50)

    input("\nPress Enter to exit...")
