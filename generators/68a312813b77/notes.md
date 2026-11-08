# Working notes: 68a312813b77

## Native reviewer handoff: 2026-10-24 / `review-af4037a93b38e174`

Production v2.3.0, its canonical authority, and its existing tests remain
unchanged. The new native `completion` family preserves exact `bbox` default
bytes and adds `diagonal_gaps`: complete every original object's bbox, then
complete pairwise gaps in coordinates `u=row+column`, `v=row-column`.
Each object is a same-color 8-connected component. Pairing is color-agnostic.
For ordered disjoint-u objects, fill background between their facing u bounds
only within the intersection of their v intervals. Preserve every foreground
cell and derive all extents from the original input before painting.

### Specific inspiration and provenance

The assignment's pinned public-evaluation focus is `7666fa5d`, challenge hash
`1b19ed6f202f6b9addff88314b0697b2752f581a55994c0339948f7cf3f8cd6d`.
The transferred mechanism is whole-object diagonal projection followed by
interval-overlap completion. A separate protected-Racket candidate matches
both supplied focus demonstrations with background 8 and fill 2, without the
MAIN task's own-bbox stage. `checks/68a312813b77/source-probe.json` records those
executions, the assignment hash, exact programs, and an independent mirror.
It generates no focus test answer and reads no separate test-solution file.
This is inspiration, not a verified equivalent descendant: keep
`relationship_verified=false`, the original protected family partition, and
`training_admitted=false`. Native examples carry this metadata privately.

### Concrete teaching repairs in this build

The first working family passed its literal implementation tests and a Racket
smoke check, but independent semantic review found three real lesson gaps:

- Color-blind 8-connected grouping fit all small demos and disagreed on the
  30×30 query, where differently colored objects can touch. Seed-0 protected
  evidence has 62 different cells under bbox and 26 under diagonal gaps.
- A literal equal-v pixel scan fit a two-demo diagonal-gap lesson but missed
  interpolation between occupied projections on queries 0 and 3.
- Extracting new objects after bbox filling fit the small demos but produced
  false bridges from newly painted color-7 objects in the large query.

The private retained failures are `checks/68a312813b77/colorblind-before.json`
and `checks/68a312813b77/teaching-before.json`. Their source hashes describe the
pre-repair implementation; they are not final-source validation.

The first two demonstrations now contain separate projection bands for three
contrasts: same-parity thin strokes with partial overlap, touching objects of
different colors, and separated L shapes whose newly painted cells must not
be resegmented. Thick/non-line objects, inactive disjoint projections, and a
non-nearest eligible pair remain present. This strengthens the two-demo core
without increasing the demo count; the first two teaching canvases grow to
20×24 and 21×25 before seed-dependent symmetry/margins. Independent limits are
2..6 demos and 1..4 queries, centered at 3/4. Larger query geometry is stretched
across its canvas; the 30×30 query contains four populated motifs and central
interactions rather than an enlarged blank border. Relative gaps, lengths,
overlap offsets, colors, and internal shape details vary across seeds.

The broader geometry sampler also exposed a seed-0/six-demo boundary failure:
a slash starting at column 3 could choose length 5 and reach column -1. Its
length is now conditioned on available horizontal capacity, with an exact
regression retained in `checks/68a312813b77/family-screen.json`. The structural
screen is explicitly Python-only and author-reported from actual tool output.

The native worker discards adapter metadata when normalizing episodes. A real
example-builder test caught the resulting missing `authoring_focus` field; the
builder now reattaches this task's pinned evaluation inspiration only in private
metadata, including its challenge hash and unverified/admission flags. The
protected-execution certificate remains separate from acceptance status.

### Canonical-fitting rival requested by this assignment

Four-connected per-object bbox filling matches both canonical demonstrations.
It disagrees on the canonical test at `(1,2)`, `(1,3)`, `(2,4)`, `(3,4)`, leaving
0 where the canonical output is 7. The original upper component
`{(1,4),(2,2),(2,3),(3,2)}` separates under four-neighbor connectivity.
The protected source probe retains the full exact input, both complete rules,
and all comparison labels. The native family deliberately emits diagonal
connections and its finite audit includes the four-connected rival under both
completion settings. This is a concrete plausible shortcut, not a claim that
these finite demonstrations exclude every imaginable rule.

### Handoff and limits

The task-local native README gives the runnable entry points. `adapter.py`
loads the adjacent prototype, and `make_examples.py` requires protected
execution before exporting two controller challenges and isolated actor turns.
Public IDs depend only on exact visible bytes. Programs, settings, answers,
future query inputs, and turn ordering remain private to the controller.

Final tests, the bounded 16-rival audit, native inventory and qualification,
export conformance, and a source-bound causal counterfactual are indexed by
this return's `REVIEW.md` and `RESULTS.json`. The audit freezes demonstration
survivors before checking queries and reports equivalent survivors honestly.
Source/evidence inventory is not acceptance. After checked integration, the
owner must qualify and accept the exact live bytes; no training admission or
measured learning benefit is claimed. Earlier production evidence below is
retained as historical context and was not rerun as an unrelated full battery.

---

## 2026-10-24 review repair

**Root cause.** Version 2.1.0 clamped every bbox origin to at least row/column 1 and every bbox end to at most the penultimate row/column. The retained rival “fill a component bbox only when it does not touch an edge” consequently matched 600/600 ordinary draws, yet differs from canonical train example 0 at `(2, 0)`.

**Repair.** Version 2.3.0 generates exact separated bboxes with explicit teaching roles. Every default draw has at least one boundary-touching component and one interior component. A cached constructive shelf packer replaces the former 200,000-node search; the generator first chooses a feasible structural tuple, so legal single-axis controls such as `n_objects=5`, `grid_h=6`, and `size_distribution=large` remain realizable. Genuinely impossible multi-axis geometry raises `ValueError` with `incompatible_axes`. The old opt-in degenerate `texture` modes were removed because they violated the advertised grammar and did not provide stable object contracts.

**Semantic guard.** `RULE_HASH` is pinned to `0515ffa9320e`. The pure `rule_mirror` fills each 8-connected component bbox independently. `LESSON_COMPETITORS` names `skip_boundary`, `boundary_only`, and `global_bbox`; `CANONICAL_SHORTCUTS` is empty because these are lesson competitors rather than rules that fit all canonical pairs.

**Validation.** Inputs must be rectangular ARC grids, must not use output color 7, and every component must be monochrome, non-rectangular, and separated. Blank grids, solid rectangles, malformed values, unknown axes, and invalid public controls fail closed.

**Evidence.** The source-bound suite has 37 passing tests, including canonical pairs, boundary/interior witnesses, exact counts, valid single-axis geometry, structured incompatibility, mirror purity, and eight real-Racket comparisons. The semantic audit and lint stages pass. The full override matrix completes 128,970 draws with 124,680 accepted draws, 4,290 structured incompatibility rejections, and zero findings. Final receipts are under `WORK/checks/68a312813b77-{task-tests-final,lint-final,audit-final,override-after-v3}/`; the TDD failure is `WORK/checks/68a312813b77-structural-contract-red.log`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-7911721ff21359f8:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `469d4810f6f82c6c03c8569e715195a8c4af72f154c4ddcaeb78498c5a4e02ae`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted2.3.0constructively teaches edge-touching objects and replaces exponential packing search. Reviewer reports37tests plus reference and full override evidence; finite domain bounds retained.

### Assessment or prior finding

## 68a312813b77

**Reproduced shortcut — ordinary generation never teaches edge-touching objects.** The intended rule fills the bounding box of every 8-connected non-background object, including objects whose bounding box touches a grid edge. Ordinary generation clamps every placed bounding box to a one-cell interior margin. Consequently, the rival “fill an object's bbox only when it is wholly interior; leave edge-touching objects unchanged” fits all 600 sampled ordinary inputs (seed `20261004`, sample indices `0..199` in each of easy/medium/hard) yet disagrees with the selected authority on the first canonical training input.

The canonical input passes the target's current `self_check` with no errors and belongs to the documented task domain, but is unreachable under the ordinary placement code. Racket writes color 7 at cell `(2,0)`; the rival leaves 0 there. Exact generator SHA `469d4810f6f82c6c03c8569e715195a8c4af72f154c4ddcaeb78498c5a4e02ae`, rule hash `0515ffa9320e`, input, Racket output, rival output, differing cell, validator result, commands, and sampling counts are retained in `checks/audit/68a312813b77/boundary-shortcut.json`; the supported authority invocation is in `checks/audit/68a312813b77/racket.json`.

A separate official lint/defect-lint partial battery also reproduced the missing `RULE_HASH` pin and a mislabeled/overlapping `touching_objects` texture domain (`checks/audit/68a312813b77-battery/`). I made no changes to this audit target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-7911721ff21359f8-v0001/audit_assets.json), manifest SHA-256 `3b903b431e138061f0084cb8d72c2cea3185e1df0b009ef2ce529f413b52a04d`.
<!-- arcpuzzles-current-audit-assessment:end -->
