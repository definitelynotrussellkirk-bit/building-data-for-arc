# Working notes: bc932ac8117a

## Intended rule

Find the one monochromatic object whose bounding box encloses one or more 4-connected background regions. Find the different-colored, same-bounding-box solid twin. Carve **all** enclosed template regions from the solid at identical local coordinates; leave all other cells unchanged. The selected canonical Racket authority remains `RULE_HASH = bcafd3a4dd95`.

## Review-23d35f89d6394ad3 decisions

The imported 2.0.1 sampler used broad random rectangles and interior growth, fixed the hollow at `(1,1)`, placed the solid to its right, advertised controls it did not honor, and accepted structural impostors. Its associated-notes ledger was empty, so the original rationale beyond source comments (“increase diversity”) is unknown.

Version 3.0.0 replaces that with a constructive curriculum:

- exact, observable axes: `grid_h`, `grid_w`, `box_size`, `palette_kind`, `hollow_side`, `hole_diagonal`;
- strict literal validation for `seed`, `sample_index`, `difficulty`, and overrides;
- strong but nonexclusive support for canonical profiles 5×11×3, 5×12×3, and 6×14×3;
- 4×4 or 5×5 square twins, horizontally separated and top-aligned;
- a connected interior divider that creates at least two enclosed holes and leaves colored interior cells;
- alternating hollow side across consecutive samples;
- three demonstrations per lesson, so every hold-one-out rotation of four consecutive pairs contains both left/right orientations;
- structural `self_check`, pixel-derived `observe_overrides`, independent rule mirror, witnesses, and declared canonical-fitting rivals.

The prior two-demonstration choice was reversed after the 300-lesson census's auxiliary search found that some rotations left two same-side demonstrations, allowing a rightmost-target positional gate. The final three-demonstration schedule and declared `rightmost_target_only` rival close that hole.

## Evidence and limits

Final generator SHA-256: `f102767753d74bdfb9838d93d0d8214f2d304fb029de49d25ed8ceec3467c873`.

The retained exact counterexample is `counterexamples/review-23d35f89d6394ad3/canonical-shortcuts.json`; focused tests replay it and compare the independent Python oracle with the real Racket authority. Final battery, task-test, and lesson-census receipts are under `WORK/checks/` and summarized in `WORK/REVIEW.md`.

Known domain limits: generated objects are exactly two squares of size 4 or 5 in a horizontal, top-aligned layout; divider shapes are the declared main/anti stair patterns; colors come from four fixed two-color families. These restrictions preserve the canonical family and test the main semantic rivals but do not prove universal induction over arbitrary rectangles, multiple pairs, rotations, or undeclared rules. Training approval is unchanged.

A proposed, nonproduction parametric extension lives in `workspace/parametric/`: episode-level `hole_selection ∈ {all_holes, largest_hole}` with separately materialized Racket programs and Racket-labelled episodes. Canonical `all_holes` remains the only selected behavior.
## Current reviewer considerations

Source SHA-256: `f102767753d74bdfb9838d93d0d8214f2d304fb029de49d25ed8ceec3467c873`.

# Decisions — bc932ac8117a

## D1 — Preserve the canonical Racket authority

**Choice.** Keep the selected `all enclosed holes` rule unchanged and pin `RULE_HASH = bcafd3a4dd95`.

**Rationale/evidence.** The before battery's rule smoke, grammar, Racket lint, and authority sync already passed. An independent component/hole oracle in `repo/generators/bc932ac8117a/workspace/hole_transfer_probe.py` reproduces all canonical labels, and real-Racket parity tests agree. The defects were in sampling, validation, metadata, and curriculum identifiability—not in the authority.

**Rejected alternative.** Rewriting the canonical program or refreshing approval metadata would add risk without addressing the measured failures. Proposed rule variation is instead isolated under `workspace/parametric/`.

## D2 — Replace random interior growth with a constructive multi-hole divider

**Prior choice.** Version 2.0.1 randomly grew an interior decoration inside 4–8 by 4–8 rectangles. Source comments say this was intended to increase diversity; `evidence/associated_notes.jsonl` is empty, so further rationale is unknown.

**New choice.** Generate 4×4 or 5×5 framed squares with one of two connected stair/diagonal dividers. The divider creates at least two enclosed zero regions while retaining colored interior cells.

**Why.** All canonical templates are plain frames. Therefore both `carve_full_interior` and `largest_hole_only` fit every canonical pair. The constructive divider makes every ordinary sample a direct counterexample to both. The exact 5×11 witness is retained in `counterexamples/review-23d35f89d6394ad3/canonical-shortcuts.json`.

**Rejected alternatives.** Continuing random growth made witness frequency and legal override support hard to guarantee. Arbitrary larger rectangles would increase surface diversity but were unnecessary for closing the semantic gap and weakened canonical-profile support.

**Limits.** Divider shapes and square sizes are deliberately bounded; this is curriculum coverage, not exhaustive topology coverage.

## D3 — Advertise only exact, pixel-observable controls

**Choice.** Replace the old ten-axis contract with six exact controls: `grid_h`, `grid_w`, `box_size`, `palette_kind`, `hollow_side`, and `hole_diagonal`. Implement `observe_overrides` from returned pixels and declare no incompatible cross-products.

**Why.** The before battery failed override checks: several axes were dead or semantically duplicated, `texture` values were ignored, and strict scalar probes produced hundreds of failures. Every final boundary combination is constructive, and the observer recovers the requested value from the grid rather than draw bookkeeping.

**Rejected alternatives.** Keeping aliases such as `texture`, `palette_size`, `position_bias`, or `density` would preserve misleading API surface. Declaring many incompatibilities was unnecessary because the 5×11 minimum canvas fits two 5×5 objects plus a gap.

## D4 — Make the call contract literal and deterministic

**Choice.** Reject booleans, floats, strings, negative `sample_index`, invalid difficulty values, unknown overrides, and coercible override scalars. Continue using keyed generator context draws; add a subprocess test under distinct `PYTHONHASHSEED` values.

**Why.** `bool` is an `int` subclass in Python, and silent coercion breaks reproducibility and override auditability. The same class of defect appeared again in assigned audit target `d546d87fec58`, suggesting this should eventually become a shared helper.

**Failure retained.** `checks/bc932ac8117a-tdd-red-round2.log` captured the initial strict-scalar and one-example lesson failures before the minimal fix.

## D5 — Weight canonical profiles without collapsing the domain

**Choice.** Keep broad support for heights 5–16 and widths 11–22, while strongly weighting exact canonical profiles 5×11×3, 5×12×3, and 6×14×3. Keep all four palette families and both sizes/diagonals/sides.

**Why.** The imported generator sampled heights 8–16 and therefore could not produce two of the three canonical heights. The final profile floor must cover every band while still retaining noncanonical variation.

**Evidence.** The first completed final-profile run on the predecessor final source recorded 38/60 exact and 42/60 envelope hits with support in every band; the final source is rechecked in `checks/after/`.

**Rejected alternative.** Emitting only the three canonical profiles would maximize profile scores but overfit dimensions and reduce robustness.

## D6 — Alternate object roles and require three demonstrations

**Initial repair choice.** Top-align the twins and alternate `hollow_side` by `sample_index`, with two demonstrations. This fixed ordered lessons and the declared topology rivals.

**Failure found.** The 300-lesson census's auxiliary generic search showed that a hold-one-out rotation could leave two same-side demonstrations. A canonical-fitting positional rule—apply the transfer only when the solid is the rightmost object—then survives the demonstrations and fails on the query.

**Final choice.** Declare `rightmost_target_only` as a semantic/canonical shortcut, add a `solid_on_left` witness, and set `EXAMPLES_NEEDED = 3`. Four consecutive alternating pairs have sides L/R/L/R, so every one-query holdout leaves three demonstrations containing both orientations.

**TDD evidence.** `checks/bc932ac8117a-tdd-red-round4.log` records the two expected failures before implementation; `checks/bc932ac8117a-tdd-green-round4.log` records 310/310 focused generator tests passing afterward.

**Rejected alternatives.** Two demonstrations cannot make every holdout of a three-pair binary orientation sequence contain both values. Random side choice would make the guarantee probabilistic. Multiple object pairs per grid would depart farther from the canonical grammar.

## D7 — Strengthen structural validation rather than admit degenerates

**Choice.** `self_check` now requires exactly two monochromatic 4-connected objects, one framed hollow and one same-size solid twin, different colors, valid separation, and generated/canonical dimensions. Malformed grids return diagnostics rather than exceptions.

**Why.** The old validator mainly counted colors and accepted no-hole, missing-twin, and size-mismatch impostors. Degenerate examples are not valid training inputs for this rule and should not share the ordinary generator path.

**Rejected alternative.** Keeping negative/degenerate `texture` modes would make exact override semantics contradictory and allow invalid lessons into ordinary generation.

## D8 — Build an episode-level rule-family prototype, but keep it proposed

**Choice.** Prototype `hole_selection ∈ {all_holes, largest_hole}`, chosen once per episode. Each setting has an exact Racket program, two Racket-labelled demonstrations, one hidden-answer query, and a public challenge view.

**Why.** This is a small, meaningful variation of the core reasoning: select all enclosed regions or only the unique largest region. Each demonstration differs between settings by one cell, so the hidden setting is inferable before the query.

**Evidence.** `repo/generators/bc932ac8117a/workspace/parametric/evidence.json`, `checks/parametric/materialize-attempt2.log`, and `checks/parametric/tests.log` (4/4 passed). The first failed materialization is retained in `checks/parametric/materialize.log`.

**Limits/status.** **Proposed prototype only.** It covers two fixed episodes, excludes largest-hole ties, and is not wired into production or approval. Canonical `all_holes` remains the selected behavior.

## D9 — Treat finite rival evidence as bounded, not universal

**Choice.** Run 100 production lessons per band with every query rotation and retain exact lessons, seeds, hashes, and rival outcomes. Report declared-rival and auxiliary generic-search results separately.

**Why.** The small semantic battery is only a smoke test. The source-bound census caught the two-demo positional weakness that the declared topology rivals did not.

**Limit.** Even the final census is finite and only exercises declared rivals plus bounded generic label mutations. It does not prove identifiability against all programs, all cyclic starts beyond the sampled schedule, arbitrary shapes, or semantic equivalence classes.
