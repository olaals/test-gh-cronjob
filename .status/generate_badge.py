#!/usr/bin/env python3
import argparse
from textwrap import dedent

def estimate_text_width(text: str, font_size: int = 11) -> int:
    # Rough estimate: each character ~7px width at font_size=11 plus some padding.
    return len(text)*7 + 10

def main():
    parser = argparse.ArgumentParser(description="Generate a GitHub-style shield SVG.")
    parser.add_argument("--left-text", type=str, required=True, help="Text on the left side of the badge.")
    parser.add_argument("--right-text", type=str, required=True, help="Text on the right side of the badge.")
    parser.add_argument("--left-color", type=str, default="#555", help="Hex color for the left side background.")
    parser.add_argument("--right-color", type=str, default="#4c1", help="Hex color for the right side background.")
    parser.add_argument("--output-path", type=str, required=True, help="Path to write the generated SVG file.")

    args = parser.parse_args()

    left_text = args.left_text
    right_text = args.right_text
    left_color = args.left_color
    right_color = args.right_color
    output_path = args.output_path

    # Dimensions
    height = 20
    left_width = estimate_text_width(left_text)
    right_width = estimate_text_width(right_text)
    total_width = left_width + right_width
    corner_radius = 3
    font_size = 11

    svg = dedent(f"""\
    <svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{height}" role="img" aria-label="{left_text}: {right_text}">
      <defs>
        <linearGradient id="gradLeft" x1="0" y1="0" x2="100%" y2="100%">
          <stop offset="0%" stop-color="{left_color}" stop-opacity="0.9"/>
          <stop offset="100%" stop-color="{left_color}" stop-opacity="1"/>
        </linearGradient>
        <linearGradient id="gradRight" x1="0" y1="0" x2="100%" y2="100%">
          <stop offset="0%" stop-color="{right_color}" stop-opacity="0.9"/>
          <stop offset="100%" stop-color="{right_color}" stop-opacity="1"/>
        </linearGradient>
      </defs>
      <rect rx="{corner_radius}" width="{total_width}" height="{height}" fill="#fff" fill-opacity="0"/>
      <clipPath id="round-corner">
        <rect rx="{corner_radius}" width="{total_width}" height="{height}" />
      </clipPath>
      <g clip-path="url(#round-corner)">
        <rect x="0" width="{left_width}" height="{height}" fill="url(#gradLeft)"/>
        <rect x="{left_width}" width="{right_width}" height="{height}" fill="url(#gradRight)"/>
      </g>
      <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,sans-serif" font-size="{font_size}">
        <text x="{left_width/2}" y="14" fill="#fff">{left_text}</text>
        <text x="{left_width + right_width/2}" y="14" fill="#fff">{right_text}</text>
      </g>
    </svg>
    """)

    with open(output_path, 'w') as f:
        f.write(svg)

if __name__ == "__main__":
    main()
