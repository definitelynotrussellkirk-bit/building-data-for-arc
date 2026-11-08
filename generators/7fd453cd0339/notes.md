# Current notes: `7fd453cd0339`

## Intended rule and authority

For each nonzero 4-connected object, clear the grid and paint the distinct four corners of that object's bounding box in its original color. Production inputs intentionally restrict objects to solid rectangles, including one-cell-wide rectangles. Canonical Racket authority is unchanged and pinned at rule hash `de0c1931e97a`; generator version is `3.0.0`.

## Current production design

- Exact axes: `grid_h=6..14`, `grid_w=8..18`, `rectangles=2..4`, three disjoint `palette_kind` values, and `texture=canonical|counterexample`.
- Inputs contain 2–4 solid halo-separated rectangles and at least one non-corner cell to delete.
- Six-step schedule alternates three randomized linked canonical-profile anchors with a joint counterexample.
- A counterexample contains a line and a separate same-color 2D rectangle, refuting local-degree and one-bbox-per-color shortcuts.
- Three demonstrations are required. Every four-pair window retains a joint witness under every query rotation.

## Reversed baseline choices

The imported generator's broad nominal axes, ignored texture aliases, ordinary negative fixtures, permissive `self_check`, and unpinned rule were removed. Difficulty bands initially shared one schedule phase during this repair; that was reversed after `defect_lint` showed the band semantics were dead. An informational deletion predicate was initially listed as a semantic witness; it was removed because it had no rival claim.

## Evidence

Final battery: 12/12 green. Portable focused tests: 50/50. Production census: 300 lessons, 0 ambiguous; 1,200 query rotations, 0 ambiguous; 936 unique inputs. Fixed-seed complete schedule census: 18 lessons and 72 rotations, 0 ambiguous. Exact retained witness: `counterexamples/line-plus-same-color-rectangle.json`.

## Known limits

The teaching claim covers the three executable canonical-fitting rivals and the tested generator domain. It is not a proof of unique induction against arbitrary hypotheses. Schedule enumeration covers every declared start and query position at seed 0; the larger census samples production seeds but does not exhaust all seeds. The Python rule mirror is test tooling only; Racket remains label authority.
## Current reviewer considerations

Source SHA-256: `acde40f1e723619145d8c75a37ae956ec9b6acb4e19448701334e5d60ee8d240`.

# Decisions for `7fd453cd0339`

## D1 — Preserve canonical authority

**Choice.** Keep the canonical Racket program unchanged and pin `RULE_HASH = "de0c1931e97a"`.

**Rationale.** Rule smoke, grammar, Racket lint, authority sync, and all three public labels passed. The defects were in input generation, validation, API truthfulness, and teaching support—not the reference transformation.

**Alternative rejected.** Rewriting the Racket rule to special-case filled rectangles would narrow an already-correct per-object bounding-box-corner program and create unnecessary authority risk.

**Probe.** Real Racket parity is exercised in the focused tests on all public inputs plus the retained counterexample.

## D2 — Replace broad nominal axes with five exact observable axes

**Choice.** Expose only `grid_h`, `grid_w`, `rectangles`, `palette_kind`, and `texture`.

**Original baseline.** The generator advertised size ranges it did not reach, ignored palette texture aliases, declared unused palette-size/color-count controls, accepted unknown names, and mixed negative fixtures into `texture`.

**Rationale.** A small exact API is more useful than a large fictional one. Each retained axis changes returned pixels and can be reconstructed by `observe_overrides`.

**Alternatives rejected.** Keeping `density` or `position_bias` as one-token axes would add no controllable variation. Keeping `palette_size` and `n_distinct_colors` would duplicate the component/palette controls without a unique observable contract.

**Evidence.** The final exact-control matrix covers 311 cases × 3 bands × 30 seeds = 27,990 draws with zero findings.

## D3 — Use a strict rectangle grammar

**Choice.** Require 2–4 solid monochrome rectangles, one-cell halo separation, ARC integer colors, dimensions 6–14 by 8–18, and at least one non-identity deletion.

**Rationale.** This is the shared structure of all public inputs and gives unambiguous connected components. One-cell-wide rectangles remain lawful because the Racket rule takes distinct bbox corners; they are also essential semantic witnesses.

**Alternatives rejected.** Allowing blank, single-cell-only, or pre-solved negative fixtures in ordinary production would teach identity cases and hide malformed generation. Allowing touching rectangles would entangle component parsing with the intended transformation.

**Failure modes checked.** Empty/ragged/bool grids, solid whole-grid impostors, holes/mixed cells, wrong component counts, touching objects, and all-corner identity collections.

## D4 — Make palette families disjoint

**Choice.** `canonical_24 = {2,4}`, `canonical_35 = {3,5}`, and `broad = {1,6,7,8,9}`.

**Rationale.** Disjoint families make the exact string override inferable even when a lesson uses only one foreground color. They preserve both canonical palettes and add broader color support without encoding numerical color rank.

**Alternative rejected.** Overlapping palette sets make `palette_kind` unverifiable from output pixels and caused the baseline's alias controls to be semantically dead.

**Limitation.** Disjoint families are an observability device, not a claim that colors have semantic roles. The transformation remains color-equivariant.

## D5 — Anchor all three public linked profiles without replay

**Choice.** Schedule exact dimension/color/shape signatures for the three public inputs, but randomize rectangle order, rows, horizontal slack, and gap.

**Rationale.** Profile-floor support should cover the true linked public structures, not independent marginal ranges. Random placement prevents memorizing canonical coordinates.

**Alternative rejected.** Pure independent sampling reached canonical envelopes but left the hard band with zero exact linked-profile support.

**Evidence.** All three signatures are generated; profile floor is 31/60 with support in every band; strict linked-profile rate is 290/600.

## D6 — Alternate anchors with a joint counterexample

**Choice.** Six-step schedule: three canonical anchors alternating with a line plus a separate same-color 2D rectangle.

**Rationale.** Public pairs use different colors per object and only 2D rectangles, so three strong shortcuts fit them. One joint example refutes all three while remaining lawful.

**Alternatives considered.** A line alone refutes local-degree rules but not one-bbox-per-color. Repeated colors alone refute merging-by-color but not both degree shortcuts. Randomly hoping for both witnesses does not guarantee lesson-level support.

**Ordering/query policy.** Lessons use three demonstrations and one query. Every four consecutive schedule positions contain two joint witnesses, so every possible held-out query leaves at least one in the demonstrations.

## D7 — Use even difficulty phase shifts

**Choice.** Easy/none phase 0, medium phase 2, hard phase 4.

**Rationale.** Even shifts make band sequences different without breaking anchor/counterexample alternation.

**Earlier intermediate choice reversed.** Identical phases made difficulty bands semantically dead and were caught by `defect_lint`. The regression was written first, then the phase map was changed.

## D8 — Declare only discriminating witnesses

**Choice.** Keep `line_rectangle` and `separate_same_color_rectangles` in `SEMANTIC_WITNESSES`; remove the informational `visible_corner_extraction` predicate.

**Rationale.** The strict semantic gate correctly requires each declared witness to carry a rival claim. “Some deletion occurs” is useful validation but does not by itself distinguish a named competitor.

**Evidence.** The first strict run retained the weak-witness warning; the corrected run passed with 2/2 witnesses and 2/2 rival claims.

## D9 — Retain independent and authoritative probes

**Choice.** Keep an independent Python geometry probe for fast structural tests and a staged real-Racket execution path for authority parity.

**Rationale.** A Python mirror alone could reproduce the same misunderstanding as generator code. The Racket test prevents that while the independent implementation keeps local failures interpretable.

**Limitation.** The mirror is supplementary test evidence and never replaces canonical labels.

## D10 — Scope of the conclusion

The final census establishes no ambiguity among the three declared rivals over 300 sampled production lessons, 1,200 query rotations, and all declared schedule starts at one fixed seed. It does **not** prove unique induction against every possible rule, nor exhaust all seeds, dimensions, or legal override combinations beyond the tested matrix. No prior task-specific return was adopted; the passing `b90d4c3d5553` task was used only as a portability pattern for real-Racket testing.

## Current audit assessment

The bounded no-issue audit and its 50-test receipt are retained in `evidence/current-audit-assessment.json`; this does not claim exhaustive coverage or an independent rerun.
