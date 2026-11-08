# Working notes: ce3c6d414140

## Current rule and domain

For every same-color 8-connected object, cells on the object's bottommost row
or rightmost column remain fixed. Every other object cell moves one column to
the right. The selected canonical Racket rule is unchanged and pinned by
`RULE_HASH = "e5b989176419"`.

The production sampler now emits only three observable canonical-profile
families: `small_one` (8×9, one object), `square_one` (10×10, one object), and
`tall_two` (14×9, two objects). Objects are hollow right-slanting
parallelograms, fit in bounds, and are separated under 8-connectivity. Two-object
inputs use distinct nonzero colors.

## Review repair

Baseline source SHA-256
`7fc550f395bb70e8fec7a43e3aa06920aac2f246c27568b3348d0f2fe5182b1a`
used a capped rejection loop plus a blank 5×5 fallback. The exact replay
`seed=17, sample_index=17, difficulty="easy"` returned that blank grid;
`self_check` accepted it and the authority produced an identity label. The
minimal retained witness is
`counterexamples/blank_fallback_seed17_sample17.json`.

Version 3.0.0 replaces rejection/fallback with constructive placement. It also:

- removes eight advertised controls that were inert or not recoverable;
- exposes one exact `profile` control and rejects unknown/ill-typed requests;
- provides mutation-sensitive structural validation and `observe_overrides`;
- adds an independent Python rule mirror, strict canonical predicate, semantic
  witnesses, executable rivals, and lesson identifiability;
- schedules all three profile families in every difficulty band.

Final generator SHA-256 is
`87b4b461605597ab7fc61d8c02f3c21043b930730165c6afc283421903e50244`.
The final 12-stage after battery passes, canonical-profile support is 60/60
(20/20 in each band), the override matrix has 360 accepted draws and no
findings, and portable task tests pass 11/11.

## Authority synchronization

The canonical Racket semantics were not changed. The selected base-solution
`target_code` contained only formatting drift from canonical text; a generated
`authority-sync --selected-only` proposal was applied after execution parity
passed. Archival `raw_code` remains untouched.

## Parametric proposal

`workspace/parametric/` contains a **proposed**, non-production
`shift_distance ∈ {1,2}` extension. The parameter is chosen once per episode;
its Racket rule and independent Python mirror agree on all retained pairs, and
the two settings disagree on every pair. This does not alter or approve the
canonical production rule.

## Limits and open findings

The production manifold intentionally follows the three observed canonical
shape/object-count profiles rather than claiming all lawful object arrangements.
Finite witnesses, 12 lessons, 48 query rotations, and task tests do not prove
universal identifiability. No prior return or task-local review index was
available as a repair lead; the baseline battery and exact replay above were the
primary evidence.
## Current reviewer considerations

Source SHA-256: `87b4b461605597ab7fc61d8c02f3c21043b930730165c6afc283421903e50244`.

# Decisions: ce3c6d414140

## D1 — Replace rejection sampling rather than tune its retry count

**Original choice:** independent random dimensions and object sizes, followed by
a capped placement loop and blank 5×5 fallback. The original rationale is
unknown; there was no task-local prior review index or associated note.

**Evidence:** `generate(17, 17, difficulty="easy")` on baseline SHA
`7fc550f395bb70e8fec7a43e3aa06920aac2f246c27568b3348d0f2fe5182b1a`
returned a blank grid. `self_check` returned `[]`, and rule smoke recorded an
identity row. See the retained counterexample and `checks/before/`.

**Alternatives considered:** increase 300 attempts; return the partially placed
grid; shrink shapes after failure; keep rejection but raise. All retain hidden
failure probability or silently change requested structure.

**Decision:** construct placements from prevalidated profile geometry. Every
selected profile now has a guaranteed feasible layout, so generation has no
fallback path.

**Limit:** constructive profiles intentionally cover three canonical
shape/object-count families, not every authority-lawful arrangement.

## D2 — Use canonical profiles as the sole production axis

**Original choice:** nine advertised axes, including palette, density, position,
texture, and distinct-color controls. Several were inert or could not be
recovered from returned pixels.

**Alternatives considered:** implement all legacy axes; mark singleton axes
diagnostic; preserve separate height/width/object-count controls with a large
incompatibility table.

**Decision:** expose only `profile=small_one|square_one|tall_two`. It is exact,
observable, valid in every band, and maps directly to source-supported canonical
signatures. `INCOMPATIBLE_OVERRIDE_COMBINATIONS` is empty because every profile
is constructive in every band.

**Failure mode addressed:** typoed or placebo overrides no longer look like
success; unknown and ill-typed controls raise.

## D3 — Keep colors semantically generic

**Choice:** choose one nonzero color for one-object profiles and two distinct
nonzero colors for `tall_two`.

**Rationale:** the authority depends on object geometry, not color identity.
Distinct colors prevent two nearby shapes from being mistaken for one same-color
component and make per-object semantics observable.

**Alternatives:** fixed canonical colors; repeated colors with larger separation;
a palette axis. Fixed colors add no reasoning value; repeated colors complicate
component identity; a palette axis would be nuisance-only and reintroduce a
large advertised surface.

## D4 — Separate object components by at least one blank Chebyshev layer

**Choice:** two-object layouts are disjoint under 8-connectivity, not merely
non-overlapping by bounding box.

**Rationale:** the Racket rule operates on 8-connected objects. Diagonal contact
would merge same-color shapes and make object-local bottom/right extrema
ambiguous. The generator and independent tests verify this separation.

## D5 — Make `self_check` structural, not acceptance-only

**Choice:** validate rectangular integer colors, known dimensions/object counts,
monochrome 8-components, exact hollow parallelogram geometry, in-bounds movable
cells, distinct colors when two objects exist, and inter-object separation.

**Evidence:** baseline rejected 0/51 destructive mutations; final rejects 54/58.
The four accepted `swap_two_colors` mutations remain lawful because palette
identity is deliberately irrelevant.

**Alternative:** simply reject blank grids. That would fix the exact replay but
leave malformed solids, broken outlines, merged objects, and incorrect profiles
accepted.

## D6 — Add an independent rule mirror and explicit semantic rivals

**Choice:** implement output-oriented `rule_mirror`, witnesses for the bottom and
right stay branches, rivals `bottom_only`, `right_only`, and
`shift_everything`, plus `lesson_identifiable`.

**Rationale:** generation and marginal similarity cannot show that lessons teach
both boundary conditions. The rival set makes the two easiest partial rules
executable and checkable.

**Evidence:** final semantic gate verifies both witness/rival claims, all 12
lessons, and all 48 query rotations.

**Limit:** this is a bounded rival inventory. Unnamed rules may still fit finite
examples.

## D7 — Preserve canonical Racket semantics

**Choice:** no semantic rule edit. Pin normalized hash `e5b989176419`.

**Evidence:** canonical pairs match the independent mirror; rule smoke has
120/120 mirror agreement. The selected base `target_code` differed only in
formatting, so I used a generated, hash-bound `authority-sync --selected-only`
proposal. Archival `raw_code` remains unchanged.

## D8 — Parametric extension is proposed, not production

**Choice:** prototype `shift_distance ∈ {1,2}` chosen once per episode. Distance
1 is the canonical/default setting; distance 2 is the alternative. Object
geometry is generated with enough right margin for both.

**Why suitable:** it changes the executed transformation while preserving the
core reasoning: identify object-local stay cells and move all others right.
Demonstrations distinguish the settings on every retained pair.

**Why separate:** the production API has no parametric-rule contract and the
canonical rule hash must remain fixed. The prototype therefore lives only under
`workspace/parametric/` with separate Racket sources and evidence.

## D9 — Testing and stopping

Tests were written before each behavior change. The original generator failed
9/10 regression tests. The missing prototype produced a separate expected RED
failure. Final portable tests pass 11/11, and the final 12-stage battery passes.
The incomplete baseline battery is retained as incomplete rather than relabeled.
I stopped because all selected-task required gates are green and remaining
uncertainty is scope/induction, not a reproduced failure.
