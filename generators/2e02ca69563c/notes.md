# Review notes — review-361d29beeb4e7c05

## Source and decision

Reviewed v2.1.1 (`9a2ab0850c883477bb76c8810e135310dfe015d517b0afd223333296b17a6891`)
and repaired to v3.0.0
(`c659d6a49ec1af31b1e9811e1425a21029fa5e2368f44fb7ca265fc41b522783`).
The canonical and archival Racket authorities are unchanged; normalized rule pin
`024c6f6dd0fa`. Earlier associated notes supplied no substantive rationale, so
attributions about the original author's intent are unknown beyond code/comments.

## Included fixes

R1: Reserve the full row-major horizontal-then-vertical route, not merely random
endpoint order. Allocate distinct variable-width strips for distinct routes;
noise is placed only outside the reserved paths. The old hard seed 0, sample 1
had an actual Racket output overwrite an endpoint (12,3), color 6 → 8.

R2: Restore frame-local counting as a learnable distinction by reusing endpoint
colors between frames. Add executable rivals and structural witnesses for global
counting, fixed frame color 8, and drawing only the first local pair.

R3: Replace decorative controls with nine exact controls and a pixel observer.
Construct feasible geometry before drawing defaults, and reject incompatible
requests explicitly. Replace the permissive nonzero-cell self-check with
structural frame, local multiplicity, and route-preservation checks.

R4: Add real support near canonical scale without replaying canonical grids.
Every consecutive three default sample indices contains core, broad, and contrast
roles; every cyclic start is checked. Broad draws independently vary features
that the contrast role deliberately combines.

## Evidence from this review

Thirty task-local tests pass. The full repository suite passes 240 tests (it does
not discover these 30 task-local tests). The full 12-stage after battery is green.
The reusable probe compares 1,800 generated draws plus five canonical pairs with
Racket. Those generated draws are 875 distinct grids across all difficulty bands;
600/600 are unique within each band. Three hundred overlapping complete-lesson
windows per band refute all three declared rivals in their demonstrations.

All five canonical pairs are accepted by the validator and matched by the
independent Python oracle and Racket. No output authority is implemented by the
sampler; `workspace/review_oracle.py` is a separate testing aid only.

## Explicit restrictions and open questions

Frames have common dimensions and a common border color within an emitted grid;
1–2 pairs live in disjoint strips, and paths add at least one new cell. Optional
ignored pixels use one color with multiplicity 1 or 3 per frame. These are a
tractable sampling subset, not a claimed complete characterization of the Racket
input domain. The validator also accepts unequal canonical frame dimensions.

Three-example lesson guarantees do not apply to arbitrary overrides, shorter
lessons, reordered/skipped indices, or undeclared rivals. Shape-aware clustering
without frame recognition is a plausible remaining alternative to investigate.
Broad draws reduce component correlations but do not establish universal
identifiability. No global catalog approval or training-admission flag was edited.
## Current reviewer considerations

Source SHA-256: `c659d6a49ec1af31b1e9811e1425a21029fa5e2368f44fb7ca265fc41b522783`.

# Decisions and rejected alternatives

Assignment `review-361d29beeb4e7c05`; repair only `2e02ca69563c`.
Final generator: `c659d6a49ec1af31b1e9811e1425a21029fa5e2368f44fb7ca265fc41b522783`.

## R1 — Path integrity; leave the reference rule alone

**Observed.** The old placement routine reasons about randomly ordered endpoints,
but the Racket rule obtains them in row-major order. Checking endpoints alone also
does not reserve the full route against later pairs. Two retained inputs have
route conflicts; the hard-band case, seed 0 / sample 1, actually changes an input
endpoint at zero-based (12,3), from 6 to 8. The medium seed 6 / sample 1 case has a
route conflict without an endpoint changing in its final Racket output. These are
sampling-invariant defects, not evidence that the Racket implementation is wrong.
See `checks/baseline-path-conflicts.json` and `checks/baseline-path-racket.json`.

**Decision.** Use exactly the rule's endpoint orientation. Place each local pair
in a separate variable-sized strip, reserve its complete route, then place ignored
markers outside every route. There is no rejection-until-lucky content placement.
The original author's intent beyond the path-preservation comment is unknown.

**Rejected.** Changing Racket to make random endpoint order authoritative would
alter the task. Retrying a small number of times and silently omitting pairs would
preserve a false count contract. A general nonintersecting-path search would widen
the distribution, but adds unnecessary backtracking and timeout risk here.

**Restriction.** Strip-separated paths are a strict subset of all noncrossing
routes. Minimum path length is three cells, so every generated pair visibly adds
at least one cell. Straight paths remain allowed and are present in canonical data.

## R2 — Teach local counting, not global palette uniqueness

**Observed.** All five canonical pairs admit global-color pairing, color-8-only
frame handling, and first-pair-only routing. Original generated colors are globally
unique between frames, so they do not teach why frame-local scope matters.

**Decision.** Permit shared pair palettes across frames, vary frame border colors
through all nonzero values, and emit two pairs per frame. Declare three executable
rivals, with observable structural witnesses and explicit witness-to-rival links.
A three-role default schedule guarantees all three witnesses within consecutive
three-example lessons. `checks/generated-containment-counterexample.json` is an
actual default seed 1000 / sample 1 / easy contrast draw, labeled by Racket.

**Rejected.** Merely increasing random sample count does not ensure a complete
lesson contains a discriminator. A predicate called "has two frames" would not
prove that a global-color rival fails. The saved probe evaluates the rivals against
actual reference outputs; its unit tests prevent exceptions and wrong-query
survivors from being misreported as refutations.

**Restriction.** Only these named rivals are claimed refuted. A spatial clustering
heuristic that infers local groups without using borders remains untested.

## R3 — Honest, jointly feasible controls and validation

**Observed.** Several legacy controls are ignored; actual per-band ranges disagree
with declarations. Unknown keys are accepted, and placement can lose requested
content. The old validator accepts nonzero junk rather than checking task structure.

**Decision.** Keep nine measurable integer controls. All declared ranges are
available in every band, subject to explicit joint feasibility. `observe_overrides`
recovers the controls from pixels. Unknown/retired controls and invalid integer
types fail immediately; incompatible controls raise `IncompatibleOverrides` with
actual axis names. The feasibility table caches geometry, never sampled inputs or
random choices. Palette count is bounded by the available colors by construction.

**Rejected.** Keeping dead aliases for compatibility would perpetuate misleading
control semantics. A blanket incompatibility waiver could hide mistakes. Silent
coercion (`True`, `1.5`, or `"2"`) obscures caller bugs.

**Compatibility.** Version advances to 3.0.0. Callers of `texture`, `palette_kind`,
`palette_size`, or other retired controls must migrate; they now receive an explicit
error. Geometry domains are 9–30 canvas dimensions, 4–10 frame dimensions, 1–3
frames, and 1–2 pairs per frame. These are documented sampler limits, not universal
limits of the rule. All canonical inputs pass the stricter structural validator.

## R4 — Canonical-scale support without canonical replay

**Observed.** The before profile audit found no canonical-profile or envelope hits
in 60 draws. No previous associated notes explained this departure.

**Decision.** Role `(seed + sample_index) % 3` selects a canonical-scale component,
a broad component, or a contrast component. Core uses 12×14, two 5×5 color-8 frames,
one unique local pair per frame, and no ignored color; origins, palette labels,
and endpoint pixels are freshly sampled. Contrast uses two 7×7 non-8 frames, two
shared pairs per frame and three ignored markers, on 18×18. Broad recombines all
feasible geometry/count/color/ignored-pixel choices with difficulty preferences.
Packing can be horizontal, vertical or a subset of a 2×2 arrangement.

**Rejected.** Exact canonical-grid replay would improve a profile statistic without
adding diversity. A stochastic-only mixture can miss the key witness in a short
lesson. A pure contrast distribution needlessly abandons canonical-scale support.

**Restriction.** Core guarantees one canonical profile, not all five profiles at
equal frequency. Frame size/color are uniform within each emitted grid; the rule
and validator also accept unequal canonical frame sizes. Contrast feature
correlations are intentional; broad samples reduce, but do not eliminate, them.
The three-example guarantee excludes overrides, shorter lessons, skipped/reordered
indices, and arbitrary sampling policies.

## R5 — Evidence, portability and solve exposure

The separate Python oracle is a test helper only. It was compared with public
canonical Racket execution on five canonical pairs plus 1,800 generated draws.
Seeds are 1000–1099, indices 0–5, in each of three bands. There are 600 unique grids
per band, but only **875 unique generated grids across bands**; shared core/contrast
behavior and keyed randomness explain overlap. The 900 lessons are overlapping
windows, not 900 independent experiments. No statistical confidence claim is made.

The task suite was written before the implementation: 20/28 baseline failures,
then 28/28 passes; the lesson-tool tests first failed because the tool was absent,
then passed. Final task suite is 30/30; repository suite is a separate 240/240.
Portable replay tests the mapped runtime source with reviewer tests copied beside
it. The original packet contains no mapped frozen tests for this selected task.
Fresh exact-delta replay and source hashes are recorded in `checks/final-handoff.json`.

The mandatory blind solve ran before source inspection: 3/3 visible examples in
one attempt, no earlier exposure. The later selected-task solve is explicitly
**exposed**: 3/3 visible examples in one attempt, no reference consultation during
that solve. Masked correctness remains withheld for both. Concise work logs and
program revisions are retained, not claimed to be token-level model traces.

## Failures retained and boundaries

The before battery has three failed stages and two advisory stages; the after
battery has 12 green stages. Baseline failures, the two deliberate test-first
failures for the missing tool, and invocation/assembly friction are retained.
Audit findings for the two separately drawn tasks are not fixed in this delta.
No helper, canonical data, archival rule, audit generator, approval flag, or other
repository task was modified. No inference-quality or hidden-test-score gain is
claimed from these local generator checks.

## R6 — Native matched-input relay family (`review-40f330dbd76de23e`)

**Base decision.** Keep the approved production `generator.py` and canonical
program unchanged. The exact native default is `rule_mode=all_local_pairs`; its
program SHA-256 is `3f5e71f9d7180264aaaa84cfa417d947ec629df7ead180342bbbeef6e0d99e78`.

**Added branch.** `rule_mode=relay_hit_color` uses the same generated inputs. In
the unique largest controller frame, it routes the sole endpoint pair
horizontal-first and reads the color of the singleton cue crossed by that route.
That input-dependent color is then relayed to every smaller frame, where only the
matching endpoint pair is routed. The alternative program SHA-256 is
`f9e6093e5766c12b43b6877f6a96edc75fa588699a2fffe67bffb5dad49e1e83`.
The two-example minimum alternates which candidate role is selected, and the
second example has multiple target frames, blocking fixed-role and first-target
shortcuts in the declared finite rival set.

**Retained evidence.** The task-local family supports 2–6 demonstrations and
1–4 queries; its four-query bank ends with a 30×30 scene containing three target
frames. The focused suite is 4/4 and the full changed-target suite is 34/34. A
40-seed audit covered 80 setting episodes and 240 pairs with matched inputs,
distinct setting outputs and no query-disagreeing survivor among the declared
finite rivals. Native authoring preflight executed 32 protected-Racket labels.
A separately replayed protected-Racket wrong-intermediate witness substitutes the
other cue color and changes the final routed target output. Sequential projection
produced 16 one-query views from four episodes and passed first-turn hidden-field
invariance checks.

**Boundary.** This is a reviewer-ready prototype, not owner acceptance or training
admission. The audit is bounded and finite-rival only. Exact-source owner
qualification, fresh replay and acceptance remain mandatory.
