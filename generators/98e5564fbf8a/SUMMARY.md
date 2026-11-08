# 98e5564fbf8a

Two-panel grid: LEFT panel (cols 0..fw-1) is mostly filled with frame color (5 or 8) with 2-3 'hole' regions (small 0-shapes punched out). RIGHT panel (cols fw+1..w-1) has 2-3 small shapes in distinct non-frame colors, separated by zero rows. Each hole shape (normalized) matches exactly one right shape. Rule: detect hole sections in left frame. For each hole, find right shape with matching normalized pattern. Fill the hole with that shape's color. Output is left panel only (cropped).

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
