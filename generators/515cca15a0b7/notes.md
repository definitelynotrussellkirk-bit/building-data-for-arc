# Working notes: 515cca15a0b7

## Review diagnosis

No retained associated-note lead was available (`evidence/associated_notes.jsonl`
was empty), so the repair was derived from the selected baseline, canonical
pairs, and fresh checks.

The baseline generated only literal-corner blobs. That accidentally taught
"keep components containing a corner cell" even though the authority keeps any
same-color 4-connected component touching one horizontal and one vertical
border. It also advertised ineffective controls, rejected canonical inputs in
its self-check, had no pinned rule hash or executable rivals, and supplied no
canonical-profile support.

## Selected design

The sampler is constructive rather than rejection-based. Every scene is built
from semantic roles:

- non-corner dual-border survivors;
- literal-corner survivors;
- one-axis edge rejects;
- optional interior rejects.

The exact axes are deliberately small: `grid_h`, `grid_w`, and `layout`. Every
legal override is observed exactly by `observe_overrides`; unknown, wrong-type,
and out-of-range overrides fail loudly through the shared draw contract.
Difficulty changes the literal-corner survivor geometry while preserving the
rule and distribution contract.

The five-position default schedule is:

`canonical_mix, dense, canonical_mix, edge_contrast, kept_variety`

Two canonical-profile positions keep each band's profile floor away from a
sampling threshold. Two split-color positions and two extended-shape positions
are interleaved so every cyclic three-demonstration window includes both kinds
of semantic evidence.

## Rival rules retained as executable probes

- `literal_corner_only`: rejects non-corner dual-border survivors.
- `keep_any_border`: incorrectly keeps one-axis components.
- `near_corner_radius2`: fits all canonical examples but rejects extended
  non-corner survivors.
- `keep_two_nearest`: fits all canonical examples but fails when more than two
  components should survive.
- `global_color_union`: fits all canonical examples by treating all cells of a
  color as one object. The generator refutes it with disconnected same-color
  horizontal-only and vertical-only components.

`workspace/semantic_probe.py` rotates all five schedule starts through the query
position, checks every currently declared competitor, verifies canonical
shortcuts against every canonical pair, and retains an exact disagreement
witness.

## Deliberate limits

Grid dimensions stay close to canonical dimensions (8..10 by 9..11), objects
use compact templates, and the sampler does not attempt arbitrary connected
polyominoes. The finite rival set and sampled lesson audits establish support
against the named hypotheses, not universal identifiability. The Racket rule was
not changed.
## Current reviewer considerations

Source SHA-256: `c2a56d8fb67cbd8c2204cb5de3780dc9e79d16373ca7cc9fd2bbded54ea63288`.

# Decisions for 515cca15a0b7

No retained associated-note lead existed: `evidence/associated_notes.jsonl` was
empty. The baseline's original rationale is therefore unknown; all choices below
come from the canonical pairs, selected Racket behavior, and fresh probes.

## D1 — Keep the selected Racket authority unchanged

**Choice.** Pin `RULE_HASH = "8a3c35320856"` and repair only the input
distribution and its test/probe surface.

**Reason.** The canonical pairs and direct Racket executions agree on a coherent
rule: operate on same-color 4-connected components and keep exactly components
touching a horizontal and a vertical border. The before battery already passed
rule smoke and authority synchronization.

**Alternative rejected.** Rewording or replacing the Racket rule would add
authority risk without correcting the observed defect. Final rule smoke,
Racket lint, and authority sync all pass; no authority file changed.

## D2 — Replace corner-only random blobs with constructive semantic roles

**Choice.** Build scenes from explicit roles: non-corner dual-border survivors,
literal-corner survivors, one-axis edge rejects, and optional interior rejects.

**Reason.** The baseline generated only literal-corner blobs, making
`literal_corner_only` indistinguishable from the intended rule. Constructive
roles guarantee both positive and negative evidence without rejection loops.

**Alternatives considered.** Random walks followed by rejection were more varied
but could starve rare witnesses and make exact overrides unreliable. Hand-copying
canonical grids would satisfy profiles but teach too little variation.

**Probe.** Task tests independently recover 4-connected components and role
counts. The semantic gate sampled 600 inputs without crash; the 300-lesson census
materialized 1,200 unique inputs.

## D3 — Use compact canonical-near dimensions

**Choice.** Advertise exact `grid_h=8..10` and `grid_w=9..11`, with default
shapes cycling through `(8,10)`, `(9,9)`, `(9,10)`, and `(10,11)`.

**Reason.** These cover all canonical dimensions while leaving enough room for
extended corner-adjacent shapes, one-axis components, and interior components.

**Alternative rejected.** A broad dimension range would increase superficial
variety but move the distribution away from the canonical morphology and make
small-grid placement failures more likely.

**Failure mode/limit.** The sampler does not teach very small, very large, or
highly crowded grids. This is deliberate and documented rather than advertised
as unsupported exact control.

## D4 — Use four layouts on a five-position witness-balanced schedule

**Choice.** Legal layout values are `canonical_mix`, `kept_variety`,
`edge_contrast`, and `dense`; the default schedule is:

`canonical_mix, dense, canonical_mix, edge_contrast, kept_variety`.

**Reason.** Two `canonical_mix` positions give a 40% canonical-profile share.
`dense`/`kept_variety` provide extended non-corner survivors and more than two
kept components. `dense`/`edge_contrast` provide split same-color edge rejects.
Every cyclic window of three consecutive demonstrations therefore contains both
semantic witness classes.

**Rejected intermediate.** A four-position schedule with one canonical-profile
layout sat exactly at a 25% expected share. After adding split-color witnesses,
the stochastic profile-floor sample obtained 13/60 exact hits and failed. The
five-position schedule passed with 20/60 exact hits (easy 9, medium 5, hard 6).
The failed report is retained under `checks/split-profile_floor/`.

**Limit.** The schedule is finite and patterned. The cyclic probe checks all five
starts, but that does not prove identifiability against undeclared rivals.

## D5 — Reuse one color across disconnected one-axis components

**Choice.** In layouts with two edge rejects, place one horizontal-only and one
vertical-only component and assign them the same color.

**Reason.** Canonical examples and the first repaired sampler used a distinct
color per component. That left a strong undeclared shortcut: union all cells of
a color globally, then test border contacts. The split-color pair makes
4-connectivity necessary.

**Alternative rejected.** Merely declaring `global_color_union` as a rival would
not help learners unless demonstrations actually refuted it.

**Probe.** The exact witness in `checks/shortcut-witness/counterexample.json`
passes `self_check`, belongs to an advertised layout, and was run through the
selected Racket authority. The rival differs exactly on the two color-8 pieces.

## D6 — Keep the public control surface small and exact

**Choice.** Expose only `grid_h`, `grid_w`, and `layout`. Implement
`observe_overrides`, reject unknown keys and wrong types, and rely on bounded
shared draws for range/value validation.

**Reason.** The baseline advertised controls that were frequently ignored. Its
before override audit reported thousands of mismatches/self-check failures. A
small exact surface is more useful than many nominal controls.

**Alternative rejected.** Exposing corner count, color count, template index,
and individual role counts would create many joint compatibility constraints and
little teaching benefit.

**Probe.** The final override stage reports 44 cases, no findings, no warnings,
and unknown keys rejected. Focused tests cover every legal layout, all difficulty
bands, exact dimensions, invalid ranges, invalid types, and unknown axes.

## D7 — Make difficulty observable without changing semantics

**Choice.** Difficulty selects among three literal-corner component shapes.

**Reason.** The earlier bands were byte-identical, triggering a detector and
providing no meaningful band variation. Geometry changes are visible while the
component predicate and profile envelope remain fixed.

**Limit.** Difficulty is modest shape variation, not a calibrated human hardness
scale. The report avoids claiming otherwise.

## D8 — Retain executable rivals and a cyclic source-bound probe

**Choice.** Export five competitors (`literal_corner_only`, `keep_any_border`,
`near_corner_radius2`, `keep_two_nearest`, `global_color_union`) plus four witness
predicates. Add `workspace/semantic_probe.py` to rotate every schedule start.

**Reason.** A single witness frequency or the shared census's sampled start
residues do not guarantee that every complete lesson teaches the distinction.
The local probe verifies canonical shortcut fit, all actual declarations, every
cyclic query start, source hashes, and exact witness outputs.

**Measured result.** Final probe: 375 lessons (25 seeds × 3 bands × 5 starts),
1,500 instance draws, 600 unique inputs; every competitor was refuted by the
three demonstrations in every lesson, with zero ambiguous or surviving cases.

## Current native recolor/connectivity promotion

The separate native adapter preserves exact canonical bytes and adds `gray_to_blue`:
recolor, recompute monochromatic cardinal components, then select both-axis border
contacts. A reverse-order protected-Racket ablation loses the newly joined blue
component. Native API supports 2–6 demos and four private prefix-stable queries;
the 30x30 stress has 295 nonzero cells and all-border content.

Self-review exposed a color-blind-component shortcut equivalent on the initial
native grammar. Added a touching foreign-color distractor; it must be discarded
while the adjacent blue union survives. Retained literal pre-repair scene, protected
before/after labels, and red/green regression. No demo-count increase.

Final bounded audit: 160 episodes / 1,280 label claims / 160 distinct inputs,
36 finite policies, 32 protected-Racket evaluations, zero failures. Full task
suite: 55 passed. Production and selected canonical rule unchanged. Native
qualification and separate owner acceptance govern promotion; no training claim.
