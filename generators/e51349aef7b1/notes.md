# Working notes: e51349aef7b1

## Current rule and authority

Two full-height color-5 columns split the input into three equal square panels.
Crop each panel to its nonzero bounding box and compare binary shapes. Select the
**first** matching code in this fixed authority order: identity, clockwise
quarter-turn, half-turn, transpose, left-right reflection, up-down reflection.
Apply that code to cropped C and recolor its foreground with B's color.

The canonical Racket semantics were not changed. `RULE_HASH` is pinned to
`cb2d64bc2f44`. The selected base authority had comment-only `target_code` drift;
its `target_code` was replaced with the byte-identical canonical `raw_code`.
`checks/after/` confirms exact authority synchronization and Racket parity.

## Reversed baseline decisions

The v2.2.0 baseline required a unique, non-identity A→B transform and required the
chosen transform to visibly change C. That excluded four of the five canonical
A/B examples, because the canonical authority deliberately resolves symmetric
shapes by first-match precedence. The new validator accepts the lawful canonical
domain: identity, multiple matches, and transform-invariant C are all legal.
Generated lessons remain stricter only where needed for teaching.

The baseline transformed A and B in their complete padded panels, keeping their
placements aligned. Therefore the plausible shortcut “match whole panels rather
than cropped objects” fit every canonical example and every baseline draw. The
new constructor translates A and B independently and rejects any B placement that
restores a complete-panel match.

The baseline advertised eight mostly dead or singleton controls. The current
exact public contract has only three useful integer controls:

| Control | Exact domain | Pixel-derived observation |
|---|---:|---|
| `panel_n` | 5–6 | panel height and width |
| `c_cells` | 4–8 | occupied cells in C |
| `palette_id` | 0–4 | index in the canonical five-palette cycle |

Unknown keys, booleans, strings, floats, and out-of-range values fail explicitly.

## Four-profile curriculum

`LESSON_SCHEDULE_PERIOD = 4` and `EXAMPLES_NEEDED = 3`, so each lesson contains
three demonstrations and one query. Profiles 0 and 1 use canonical-style
ambiguous A shapes with cropped match sets `[2, 6]` and `[3, 6]`; their outputs
teach first-match precedence. Profiles 2 and 3 use asymmetric shapes with unique
transform codes. All profiles independently translate A and B.

The declared rivals are:

1. `uncropped_full_panels`: search complete padded panels and default to identity
   when no transform matches.
2. `last_matching_transform`: choose the last cropped transform instead of the
   first.

Every four-profile window contains two examples that disagree with both rivals.
Holding out any one pair therefore leaves at least one refuting demonstration.
The task-local `workspace/probe_semantics.py` independently reimplements the
transform law and exhausts every fixed-seed cyclic start/query rotation.
`workspace/probe_controls.py` exhausts every legal joint control setting across
all four bands and four profiles. `workspace/build_counterexample.py` materializes
the retained Racket-checked shortcut witness.

## Final evidence and limits

Final generator SHA-256:
`cc984e2ae59660958226e10cf9cf898649bdae2a04b288202c8bbe92ee110c74`.

- Full after battery: 12/12 green, zero advisory (`checks/after/`).
- Portable focused tests: 157 passed (`checks/task-tests-with-counterexample/`).
- Production lesson census: 300 lessons, 1,200 pair/query rotations, 1,198 unique
  inputs, zero ambiguity for the two declared rivals (`checks/lesson-census.json`).
- Declared-period census: all 12 band/start lessons and 48 rotations at seed 0,
  zero ambiguity (`checks/schedule-census.json`).
- Joint-control probe: 800 legal cases and 11 invalid cases, zero failures
  (`checks/tools/control-probe.json`).
- Visible-only exposed solve: 3/3 demonstrations on the first revision; masked
  query correctness is intentionally unknown (`solve/`).

These are finite checks against two executable rivals, not a proof of universal
induction. The production distribution intentionally uses panel sizes 5–6,
C sizes 4–8, five canonical palette roles, and a four-profile schedule. It does
not teach empty panels, malformed dividers, arbitrary palettes, or every possible
shape symmetry. No downstream model was trained or scored.
## Current reviewer considerations

Source SHA-256: `cc984e2ae59660958226e10cf9cf898649bdae2a04b288202c8bbe92ee110c74`.

# Decisions for e51349aef7b1

## D1 — Preserve the canonical Racket rule

**Prior choice:** the selected base copy had comment-only text drift from the
canonical source, while the Python generator did not pin a rule hash.
**Decision:** keep the canonical semantics and `RULE_HASH=cb2d64bc2f44`; replace
only the selected task-specific `target_code` with canonical `raw_code`.
**Why:** canonical outputs already define first-match behavior, and sampled rule
smoke showed the authority itself was not the defect. Changing Racket would have
rewritten labels to match a bad sampler.
**Evidence:** `checks/after/` authority sync and rule smoke.
**Rejected:** changing transform order or forcing uniqueness in the authority.

## D2 — Validate the lawful cropped domain, not the old sampler's restrictions

**Prior choice:** require one nonidentity whole-panel match and require C to
visibly change. This rejected four of five canonical inputs.
**Decision:** `self_check` now requires only three equal square panels, legal
colors, one foreground color per panel, and at least one cropped A→B authority
match. Identity, multiple matches, and invariant C are lawful.
**Why:** these are executable source semantics. Sampler policy belongs in
construction and lesson checks, not in a validator that claims canonical support.
**Probe:** canonical acceptance and independent output comparison for all five
pairs in `tests/test_generator.py`.
**Rejected:** weakening canonical support metrics or special-casing canonical
hashes.

## D3 — Teach ambiguity rather than avoiding it

**Prior choice:** rejection-sample until A→B has exactly one nonidentity match.
**Decision:** use a four-profile schedule: two fixed ambiguous legends with match
sets `[2,6]` and `[3,6]`, then two fully asymmetric unique-transform legends.
**Why:** the authority's order is semantically observable and appears in the
canonical data. A unique-only corpus teaches a simpler but wrong rule.
**Probe:** all cyclic starts and all query positions in
`checks/schedule-census.json` and `checks/tools/semantic-probe.json`.
**Rejected:** all-ambiguous lessons (too narrow) and all-unique lessons (fails to
teach precedence).

## D4 — Translate A and B independently

**Prior choice:** transform coordinates in the full panel, preserving padded
placement.
**Decision:** build cropped shapes first, choose A placement, then choose an
independent B placement from positions with no full-panel transform match.
**Why:** the actual rule crops; aligned padding creates a strong complete-panel
shortcut.
**Probe:** exact Racket-checked witness in
`generators/e51349aef7b1/counterexamples/uncropped_full_panels.json`.
**Rejected:** random independent placement without constructive filtering,
because accidental full-panel matches would reintroduce the shortcut.

## D5 — Use a small exact control contract

**Prior choice:** advertise eight axes, several of which were aliases, constants,
degenerate invalid textures, or ignored.
**Decision:** expose only `panel_n` 5–6, `c_cells` 4–8, and `palette_id` 0–4.
Derive all observations from pixels and reject unknown or mistyped values.
**Why:** these controls alter meaningful visible properties and their full joint
domain is constructive.
**Probe:** 800 joint band/control/profile cases and 11 invalid probes in
`checks/tools/control-probe.json`; public override gate in `checks/after/`.
**Rejected:** cosmetic controls, metadata-only observation, coercion, and a huge
axis surface that could not be honestly supported.

## D6 — Keep canonical color roles but broaden geometry

**Decision:** use the five exact canonical color triples, panel sizes 5–6,
connected C templates with 4–8 cells, keyed orientations, and independent
translations.
**Why:** palette roles are not part of the rule, but retaining canonical cycles
keeps profile support high while geometry supplies diversity. Size 5 preserves
canonical scale; size 6 adds output and placement variation.
**Probe:** profile floor in every band, 1,198 unique inputs among 1,200 production
pairs, and 65 distinct outputs in the 120-input Racket smoke.
**Rejected:** arbitrary colors before confirming role interchangeability, and
panel size 4 because the chosen ambiguous/connected templates and placement
counterexamples are cleaner at 5–6.

## D7 — Require arbitrary one-query rotations for the declared schedule

**Decision:** claim support only for three demonstrations plus one query, with
all four pair rotations tested.
**Why:** downstream assembly may hold out any materialized pair. Witness frequency
alone does not guarantee a complete lesson.
**Probe:** production census: 300 lessons and 1,200 required rotations; declared
period census: 12 lessons and 48 rotations. Both have zero ambiguity and zero
errors.
**Rejected:** reporting only the ordered production query or only individual
witness counts.

## D8 — Bound the semantic claim

**Decision:** declare two executable rivals—the strongest canonical shortcut
(`uncropped_full_panels`) and the precedence rival (`last_matching_transform`)—and
state that passing them is finite evidence, not universal induction.
**Why:** both are source-lawful and directly target the two baseline defects.
The separate audit of `e521d16d403e` demonstrates why undeclared rivals can still
survive a declared-rival census.
**Rejected:** wording such as “uniquely determines the rule” without a bounded
hypothesis class or downstream model evidence.
