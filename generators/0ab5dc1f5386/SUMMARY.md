# 0ab5dc1f5386 — size-matched frame insertion

The input contains hollow monochrome color-8 rectangular destination frames and loose nonzero source components. Process frames in top-left order. For each frame, copy the first row-major loose source whose cropped bounding-box dimensions exactly equal the frame interior and whose complete `(height, width, crop)` value has not already been used. Copy only nonzero crop cells into the frame and leave every source component in place.

Generator version `4.1.0` pins canonical `RULE_HASH = 1529a4ef373b`. Its default four-example curriculum cycles through:

- `orientation_decoy`: a transposed source that must **not** be rotated;
- `scan_order`: two equal-size candidates where the first source wins;
- `single_use`: two byte-identical source occurrences, teaching that use is by crop value rather than occurrence identity;
- `multicolor`: a mixed-color crop whose colors must be preserved.

An explicit `unmatched` texture retains an unmatched frame and an unmatched loose shape. Exact overrides cover `grid_h=12..18`, `grid_w=16..22`, and all five textures. Default profiles rotate among canonical-scale `(12,16)`, `(13,17)`, and `(13,18)` grids with five observed colors including background.

Task-local tests and the independent `workspace/reference_probe.py` cover canonical acceptance, Racket/oracle parity, exact override boundaries, deterministic output, cyclic curriculum coverage, and five named rival rules. Final evidence is summarized under `checks/after-final/`, `checks/task-tests-final/`, and `checks/lesson-census-final.summary.json`.

Approval remains catalog-derived; this review does not change training admission.
