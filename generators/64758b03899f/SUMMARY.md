# 64758b03899f — stamp a normalized mask at colored anchors

The input contains one connected color-5 mask and two or three isolated, distinctly colored non-{0,5} anchors on a zero background. Normalize the mask by the top-left of its bounding box, clear the source, and stamp the same normalized offsets at every anchor using that anchor's color.

Generator 3.0.0 covers the four canonical mask families plus four additional connected families, including three whose bounding-box top-left is empty. Grid size is exactly controllable over 9..13 × 12..18, anchor count over 2..3, and mask family over eight named values. Constructive placement keeps source and projected stamps in bounds and mutually disjoint. Four scheduled profiles include two guaranteed hollow-origin cases, so a five-pair lesson retains a counterexample to the canonical-fitting “first row-major 5-cell is the origin” shortcut under every single query rotation.

The canonical Racket rule hash remains `daa4a7279074`; no semantic authority change was made. The selected bank's behavior-equivalent commented target text was synchronized byte-for-byte to the canonical program to remove authority-source divergence. See `notes.md`, `tests/test_generator.py`, and `counterexamples/first-mask-cell-origin.json` for exact scope and retained evidence. Approval remains catalog-derived; this summary is not approval.
