# c6a422753abe

A zero-background grid contains exactly one complete blue row or one complete
blue column, never both. A connected shape using exactly two non-background
colors lies wholly on one side of that separator, while the opposite side is
empty. Reflect the shape once across the separator. In the canonical output,
swap the two colors at the original source and keep the reflected copy in the
original colors; the separator stays blue.

The reviewed sampler covers row and column separators, both source sides,
multiple two-color palettes, connected shapes from 4 to 24 cells, and 8×8
through 30×30 canvases. This replaces the imported cross-divider/three-reflection
sampler, which represented a different transformation.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical rule hash:
`1781c378782f`.

A separate task-local proposal adds `swap_location = source | reflection`.
`source` is the selected canonical program byte-for-byte; `reflection` preserves
the source and swaps only the reflected copy. This finite family is proposed,
not owner-qualified, accepted, or training-admitted.
