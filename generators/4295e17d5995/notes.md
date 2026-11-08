# Working notes: 4295e17d5995

## Current parametric family

`workspace/parametric/` contains a native-ready matching/opposite-wall family.
Its canonical default is the exact selected Racket program; the alternate
changes only the wall-color/direction list. The production generator and its
canonical authority are unchanged. Fresh owner qualification and acceptance
after integration remain required; this return does not admit training data.

The adapter supports 2–6 demonstrations and 1–4 queries independently. Ordinary
qualification uses three demos and four queries. Identical seeds/counts have
identical inputs across settings; extending a split leaves its prefix and the
other split unchanged. Queries cover 9×9, 16×20, 24×27 and 30×30, with 24 objects
and substantive content across the largest canvas. The first two demonstrations
teach both color roles, diagonal connectivity, rigidity and sequential packing.

The actual sequential dependency is preceding settled shapes → their occupied
cells → the next shape's minimum allowed translation. Protected Racket witnesses
for both settings replace the intermediate with walls-only occupancy and change
the final answer. In the retained cases, the following shape's shift changes
from 3 to 5 cells and from 11 to 13 cells. See the returned
`checks/4295e17d5995/causal/witness.json` and sibling `replay.json`.

## Scope and retained evidence

Native qualification passed all four jobs (two settings, seeds 0 and 17,
three demos/four queries), with exact Racket labels. The task-local
`workspace/parametric/evidence/current/audit.json` records four additional
edge-count episodes, 160 protected Racket evaluations and 28/28 demonstration
rejections of seven executable rivals. Its example writer masks private answers
and settings, hashes only visible bytes, and checks first-turn equivalence to
single-query use. Focused tests passed 15 tests and 58 subtests. The native
source/evidence inventory is `workspace/parametric/evidence/manifest.json`.

The returned `checks/4295e17d5995/final-review.json` adds 32 protected-Racket
Python/rival parity evaluations at a held-out seed and ten bounded sampler
requests that all completed (maximum 15 of 64 attempts). These are finite
rival/seed checks, not universal identifiability or all-seed guarantees. Geometry
uses finite shape libraries and row bands; retries fail explicitly at the cap.

## Canonical overlap boundary

The loose canonical structural checker admits an input where the first color's
settled C-shape covers a second-color object's original position. The canonical
scan then overwrites one first-color cell. Protected Racket and the existing
Python mirror agree; the retained source-bound counterexample is
`checks/4295e17d5995/canonical-overlap.json`. This is a documented authority/domain
boundary, not a change to that authority. The separate sampler requires
collision-free original positions, non-overwriting destinations and color-count
conservation under **both** settings before admitting an input. Its focused
regression rejects the retained counterexample.

Imported associated notes retain original evidence in `evidence/associated_notes.jsonl`.
