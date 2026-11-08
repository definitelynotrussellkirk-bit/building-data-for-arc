# 28268c57c367 — row shadows to a gray wall

Version **2.1.0**. Canonical authority **b4fa0726be56**, unchanged.

Read original nonzero, non-5 sources left of the full-height gray wall in row-major order; fill only still-zero cells to their right, stopping before the wall. Thus the leftmost source in a row owns downstream blanks, while later sources, off-wall gray and right-side material are preserved. Gray is neither an active source nor a local ray terminator.

Inputs alternate a canonical-like core and a rich counterexample profile. Use consecutive same-seed draws with three demonstrations plus one query; every holdout of the four pairs retains a rich demonstration under unrestricted defaults. Arbitrarily filtered or witness-erasing overridden lessons need a fresh semantic check.

Seven exact integer controls: grid_h, grid_w, wall_col, n_cells, n_distinct_colors (left active source palette), n_gray (left off-wall gray), n_right (right colored distractors). Contradictory value pairs and unknown/retired controls fail loudly. See generator.py AXES and observe_overrides().

`tests/` contains portable regression tests; `workspace/review_probe.py` adds legal joint-boundary and Racket-labeled cyclic-start checks. Distribution decisions and limitations are in notes.md. Approval remains catalog-derived; passing checks here does not approve training.
