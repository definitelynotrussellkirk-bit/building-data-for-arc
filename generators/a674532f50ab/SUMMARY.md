# a674532f50ab

Any colored grid of size at least 3×3 (typical h, w ~3-14). The grid is filled with a TEXTURE (noise / sparse / blob / stripes / gradient / checkerboard / frame / ring / plus) using a 5-color palette + a chosen background color. The TOP-RIGHT 3×3 CORNER is overlaid with a specific pattern (mixed_9, two_colors, one_color, or palette_corner). Rule: EXTRACT the TOP-RIGHT 3×3 CORNER of the input grid (rows 0, 1, 2 × cols w-3, w-2, w-1) and RETURN it as the entire output. The rest of the input is discarded. Output is a 3×3 grid. Net: rule is just 'crop to top-right 3×3 corner' regardless of input size or content.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
