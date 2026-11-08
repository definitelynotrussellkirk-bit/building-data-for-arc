# Working notes: 6b5d8752c5c4

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/6b5d8752c5c4/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Parametric divider-source review (2026-10-24)

The prior production grammar kept every nuisance-color lane marker in the two
central positions, so a marker-relative divider and the intended bounding-box
midpoint produced the same labels. The proposed native family closes that
specific identifiability hole without changing the selected production source:

- `bbox_midpoint` is the exact canonical Racket program byte-for-byte.
- `lane_marker` uses the one colored marker in each short-axis lane as the
  divider, then performs the same one-cell outward movement.
- Both settings receive identical seed-derived inputs. All markers are outside
  the central pair, with lane-varying positions, so two demonstrations leave
  only the selected declared setting and reject global-marker, wrong-axis,
  toward-marker, and canvas-midpoint shortcuts.
- Episodes support 2–6 demonstrations and exactly four queries. The fixed
  profile schedule covers 8x8 through a substantive 30x30 six-object query,
  both orientations, non-movement boundary contacts, palette changes, and D4
  transforms.

Bounded self-audit evidence is in
`workspace/parametric/evidence/current/self-audit.json`: 320 episodes over 32
seeds, both settings, and every supported demonstration count passed with zero
reported failures. This is finite construction/teaching evidence only.

Native protected-Racket qualification is complete at
`WORK/checks/6b5d8752c5c4/qualification/`: four source-bound jobs cover seeds 0
and 17 for both settings, with three demonstrations, four queries, 40 Racket
evaluations, and only the selected setting surviving each demonstration set.
The causal witness at `WORK/checks/6b5d8752c5c4/causal/` was independently
replayed: Step A derives each object's bounding-box midpoint; Step B uses that
intermediate to select the outward movement direction; replacing it with the
lane marker changes the final output.

The existing target regression also had two stale assumptions unrelated to the
new family: it derived the repository root from a fixed `parents[]` depth and
required archival base Racket source to equal the canonical source byte-for-byte.
The test now uses `reviewer_support` for portable source selection and executes
both archival base programs in real Racket against all four canonical pairs.
The final staged suite passed 35 tests and 217 subtests.

Next useful action: the owner should review the divider-source semantics and
replay acceptance against these exact integrated bytes. Reviewer qualification
does not grant owner acceptance or training admission.
