# public_eval_21897d95 — region-routing arrows

New general Racket rule and standalone generator. All four original training
labels and both original test labels match. Blue T glyphs point from their
source region to the first different region on a ray. A nonblue center carries
the destination ink; otherwise the original source ink is used. Restore all
glyphs, recover four-connected regions and destinations from that immutable
canvas, and apply recoloring simultaneously. A five-cell burgundy top-left
corner turns clockwise; a top-right corner turns counterclockwise. Absent that
command, orientation is unchanged. Other rotation-glyph grammars are not claimed.

Alternative `ink=source_color` ignores explicit center payloads, while preserving
region restoration, direction, first-hit lookup and quarter-turn semantics.
Both settings use identical scenes. The two minimum demonstrations include
explicit payloads, ordinary source-ink arrows, both rotation directions,
disconnected equal-color regions, jagged region boundaries, and a first-hit
island with a diagonal-only same-color satellite. Queries also include no-turn
scenes. Supports 2–6 demos, 1–4 prefix-stable queries and substantive 30×30 boards.

Adversarial construction found rotation symbols could overwrite the nonblue
context needed to decode nearby arrows despite not touching their blue cells.
Rotation placement now excludes the one-cell neighborhood of every blue cell.
The three observed seeds are retained as a regression. Sources and targets are
measured before recoloring; no action may use an earlier action's new ink.

A 16-seed audit spans all supported demo counts and 14 declared rivals; it has
no harmful survivors in that finite set. All 38 copied-runtime tests pass.
Protected-Racket authoring preflight and source-bound witness are retained under
checks/public_eval_21897d95. The owner must register/review exact source, perform
native qualification and fresh acceptance; training remains unadmitted.

## Current repeated-return reconciliation

Preserve exact payload/source-color programs/default and incumbent room parser. Retain compatible c9df constructors as a disjoint episode-level bank and identify equivalent setting names as aliases. review-03cc38e69e8971fc remains unresolved: its boundary-adjacent T inputs produce conflicting destinations under the preserved source-corner/ray parser; no contribution from that incompatible constructor is claimed incorporated. Keep its exact source and minimal inputs for owner design review. Evidence: `evidence/reconcile-13/`. Private native qualification, fresh private acceptance and a fresh accepted episode passed. Live owner publication and training admission remain separate.
