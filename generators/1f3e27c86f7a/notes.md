# Working notes: 1f3e27c86f7a

## Current canonical behavior and lesson support

The canonical rule `a3f0a934419a` copies nested payloads into same-color plain
rectangles using preserved borders and proportional/open-side alignment, with
a stripe fallback. Its source, `VERSION=3.0.0`, and all pointwise generation
logic remain unchanged. A new input-only `lesson_identifiable` guard requires
each query branch to occur among valid demonstrations. Automatic unsupported
lessons now fail explicitly; explicit-count use retains a diagnostic.

The retained audit `review-f4b6932b6f3357f6:v0001` is concretely reproduced at
seed 10: branches `stripe,stripe,stripe,stripe,bottom_align`; all inputs pass
self-check, and a stripe-only rival fits four Racket-labeled demonstrations but
disagrees on the query. The exact grids, labels and verdict are retained in
`counterexamples/branch-support/witness.json`; rerun with
`workspace/parametric/replay_lesson.py`.
The guard addresses silent lesson admission. It does not reschedule draws or
prove universal identifiability. The existing audit record remains unchanged
for explicit maintainer assessment; no automatic closure is asserted.

## Proposed parameter extension

`workspace/parametric/prototype.py` implements one episode-fixed
`payload_orientation` in `{identity, mirror_lr}`. Identity preserves the exact
canonical program; mirror reflects source columns before the existing mapping.
The original row-striped payload could not teach horizontal reflection, so
the prototype uses four solid asymmetric color quadrants. This leaves production
input draws unchanged and avoids extra bbox-defined templates.

Default episodes have six branch-covering demonstrations and four distinct
queries. Both counts are configurable in `1..12`; fewer demonstrations restrict
queries to the demonstrated branches. Matching Racket supplies every label.
Demonstration-only assessment checks both parameter alternatives and the
identity/skip-branch rivals. Other plausible alignment rivals are not exhaustively
covered. The prototype and its source-bound manifest are authoring evidence,
not rule-variant approval or training admission.

The exact visible export determines public bytes and IDs; seeds, parameters,
programs and query labels remain private. Use the commands and limits in
`workspace/parametric/README.md`. Retained examples and the manifest live in
`workspace/parametric/evidence/`; all 30 selected tests passed with Racket.
The inherited tests now use the source-bound loader and canonical data locator,
so they run directly from this repository instead of requiring a stale layout.

## Next useful work

Design a production lesson schedule that supports each actually accepted query
without changing rule authority. Keep the current fail-closed guard. A later
prototype review can add explicit proportional/edge-alignment competitors;
the present two-setting evidence does not claim that wider coverage.
