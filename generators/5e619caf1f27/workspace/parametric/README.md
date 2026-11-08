# Edge-cap frame parametric prototype

This source-bound prototype keeps the original nested solid rectangles and
varies exactly one term of the frame-thickness rule:

- `capped` is the exact canonical Racket program: thickness is the minimum of
  inner height, inner width, and all four grid-edge margins.
- `uncapped_inner` uses only the smaller inner dimension and lets the finite
  canvas clip the expanded frame.

The same deterministic inputs are used for both settings. Every episode has an
edge-limited demonstration, 2–6 demonstrations total, and exactly four private
queries including a substantive 30×30 case. All labels and rival certificates
are replayed in the packet's Racket runtime. This directory proposes no
production approval or training admission.
