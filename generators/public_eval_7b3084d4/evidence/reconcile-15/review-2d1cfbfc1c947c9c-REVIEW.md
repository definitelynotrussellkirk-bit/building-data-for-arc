# Public evaluation family review

Both assigned public parents now have complete reviewer-authored source trees.  The work preserves the immutable `workspace/public-parent.json` records and does not edit the catalog, canonical authority, approvals, or shared runtime.  Both returns are **reviewer-ready prototypes** only: owner registration or reconciliation, unchanged native qualification, exact-source acceptance, and any training-admission decision remain pending.

## `public_eval_7b3084d4` — rotatable exact-cover packing

The canonical program parses four uniquely colored polyominoes whose total area is a perfect square.  A single color-5 cell replaces one cell of its cardinally adjacent piece and anchors that piece at output coordinate `(0,0)`.  The program enumerates quarter-turn rotations and translations, exact-covers the square without reflection, and preserves source colors plus the marker.  It reproduces all four supplied labelled pairs under protected Racket.

The matched-input alternate, `highlight_bottom_right_piece`, first reconstructs the complete packed owner grid, then recolors every cell owned by the piece at the packed bottom-right corner with color 5.  Input placement is independently scrambled, so packed-corner ownership cannot be replaced by piece area, the marked piece, another packed corner, or proximity to the input's bottom-right.  A reusable finite-rival audit covers those executable alternatives.

During implementation, generated scenes initially failed before exact-cover validation.  The root cause was an iterator consumed by the first coordinate minimum inside `_normalize_tagged`; the existing generated-scene tests reproduced the failure, and converting the iterable to a tuple before the two passes fixed it.  The final suite is green.

Evidence highlights:

- 4/4 supplied labels reproduced by the exact canonical program.
- 22/22 staged task tests and 22/22 focused tests passed.
- 16 audit seeds, 128 count-boundary requests, 736 pair instances, 160 distinct inputs, and 160 unique-packing checks.
- 96 protected-Racket rival/label evaluations; the selected setting is the sole survivor of the minimum demonstrations in every retained audit case.
- 16 saved one-query public views passed the packet export checker.
- Four-job authoring preflight passed and replayed byte-for-byte.
- The source-bound protected witness substitutes largest-piece selection for reconstructed bottom-right ownership and changes 54 final cells.
- The stress query is a substantive 30×30 scattered input packing to a 14×14 square.

## `public_eval_45a5af55` — row strip to concentric square

The canonical program reads the constant color of each horizontal input row and folds the first `h-1` rows around the center as one-cell concentric square layers, producing a `2(h-1) × 2(h-1)` output.  The final row repeats the innermost retained color, matching the supplied task grammar.  It reproduces all three supplied labelled pairs under protected Racket.

The matched-input alternate, `highlight_largest_region`, constructs the complete square, segments it into same-color four-connected regions, and recolors the unique largest realized region with color 9.  Generated demonstrations separate realized completed-region area from longest row run, raw color frequency, total completed color area, and fixed outermost/innermost choices.

Evidence highlights:

- 3/3 supplied labels reproduced by the exact canonical program.
- 22/22 staged task tests and 22/22 focused tests passed.
- 16 audit seeds, 128 count-boundary requests, 736 pair instances, and 160 distinct inputs.
- 168 protected-Racket rival/label evaluations; the selected setting is the sole survivor of the minimum demonstrations in every retained audit case.
- 16 saved one-query public views passed the packet export checker.
- Four-job authoring preflight passed and replayed byte-for-byte.
- The source-bound protected witness substitutes longest-run selection for completed-region area and changes 224 final cells.
- The stress case has a 16×30 input and a 30×30 output.

## Combined verification and limits

The fresh combined focused run passed 44/44 tests.  The two staged task runners independently passed 44/44 tests with zero failures, errors, or skips.  Ten Python source files compiled.  The retained finite audits cover 320 distinct generated inputs, 1,472 pair instances, 264 protected-Racket evaluations, and 32 saved public views.  Both canonical programs are byte-identical to their task-local `canonical.rkt` copies, and both preflight receipt triplets replayed byte-for-byte.

These checks are finite authored-rival and sampled-generator evidence, not proofs against arbitrary programs or all random seeds.  The causal intermediate descriptions are authored metadata whose final-output effect was replayed, not independently inferred by the tooling.  `training_admitted` remains false, and no owner acceptance is claimed.
