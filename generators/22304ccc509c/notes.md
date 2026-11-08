# Working notes: 22304ccc509c

## Prior retained evidence

The accepted audit `review-3cc9a95fb3bce145:v0001` identified two concrete defects in source SHA-256 `345b6df87ea6066c903b1dc6ae1fca06b517247d0b86bde5303f101217a4ba90`:

- the constructor never occupied the last input row, so “erase the bottom input row, then apply ordinary gravity” matched 120/120 generated draws while failing a canonical example;
- `palette_size=1` was accepted but did not control the realized palette.

The current review reproduced the broader contract failure in `checks/before/`: lint, defect-lint, and override failed; profile-floor and semantic-gate were only advisory. The old surface also advertised dead or overlapping texture-like axes, silently accepted unknown keys, and did not expose a meaningful semantic/lesson contract.

## Root cause

The generator described more variability than its actual sampler implemented. In particular, generation restricted all payload rows to `range(h - 1)`, making the bottom-input-row case impossible, while override metadata and draw provenance did not correspond to independently observable output properties. The weak validator checked generic shape/color facts but did not require a rule-revealing, non-identity scene.

The canonical demonstrations have a second ambiguity: every multi-value column happens to be numerically ascending. Therefore the plausible wrong rule “sort each column’s nonzeros ascending, then bottom-pack” fits all 3 canonical labels. A training distribution that merely repairs the bottom-row omission would still fail to teach order preservation.

## Repair decisions

- Kept the canonical rule and all selected Racket authority bytes unchanged; `RULE_HASH` remains `c3638032481f`.
- Replaced the overclaimed contract with four exact, observable axes: height, width, populated-column count, and distinct foreground-palette size.
- Chose domains that are jointly feasible without hidden incompatibility declarations: heights/widths 6..18, columns 2..6, palette size 1..9.
- Added five deterministic curriculum profiles: three canonical anchors and two broad sparse/dense profiles.
- Reserved one empty cell so every returned grid produces a non-identity transformation.
- Forced one bottom-row payload and one descending stack in every default draw. These are semantic witnesses, not decorative metadata.
- Added an independent Python mirror, executable rivals, `lesson_identifiable`, strict validation, mutation fixtures, and exact override observation.
- Added 35 task-local regressions plus `workspace/probe_shortcuts.py` for deterministic future shortcut and cyclic-query audits.

## Evidence and limits

- TDD red baseline: `checks/tdd/red.log` (26 failed, 9 passed before implementation).
- Focused green: `checks/task-tests-final/result.json` (35 passed in the final portable rerun).
- Full after battery: `checks/after/checks/22304ccc509c_after_battery_summary.json` (12/12 green).
- Semantic gate: 600/600 strict draws; both witnesses fired on 600/600; 12/12 three-demo lessons identifiable; 0/48 diagnostic rotation ambiguities.
- Large census: `checks/lesson-census.json` (300 lessons, 1,200 unique labeled pairs, 0 production ambiguities, 0/1,200 rotation ambiguities).
- Reusable probe: `checks/shortcut-probe.json` (300 draws, both witnesses and both rival disagreements on every draw, 0/300 cyclic-lesson ambiguities).
- Exact Racket-labelled witness: `checks/shortcut-witness/report.json`.

These are finite checks against two declared rivals, not a proof of unique induction against every possible hypothesis. The production lesson assembly uses 3 demonstrations and 1 query; the large census tested every materialized pair as query but did not enumerate all possible seeds or undeclared rivals. Exact user overrides remain lawful controls, but the production sampler—not every arbitrary override combination—is what the lesson census measures.
## Current reviewer considerations

Source SHA-256: `f765aa107e6e5c50a9c3d9908f3f3d57a0cce91958b6306fc230192f9e78ea05`.

# Decisions: 22304ccc509c

## D1 — Treat the retained audit as a root-cause lead, then reproduce it

**Input:** accepted audit `review-3cc9a95fb3bce145:v0001` reported that the old constructor never used the bottom row and ignored `palette_size`.

**Decision:** reproduce through the official baseline battery and direct generated-data analysis before changing code. The baseline confirmed lint, defect-lint, and override failures; the earlier bottom-row rival was retained as an executable semantic competitor.

**Alternative rejected:** patch only `palette_size`. That would leave the generated-data shortcut, dead axes, unknown-key swallowing, weak validation, and absent lesson contract untouched.

## D2 — Preserve the canonical and Racket authority

**Decision:** keep the task rule as independent per-column downward gravity preserving top-to-bottom order. `RULE_HASH` remains `c3638032481f`; no canonical labels or selected Racket sources changed.

**Why:** rule smoke and canonical execution were already correct. The defect was in sampling, contracts, and teaching support, not in the authority.

**Failure mode avoided:** changing the rule to fit the old sampler would erase lawful canonical bottom-row cases and redefine the task around a generator accident.

## D3 — Replace overclaimed controls with four exact pixel-observable axes

**Decision:** expose only `grid_h`, `grid_w`, `columns`, and `palette_size`; reject unknown keys and non-integer/coercible values; recover every realized value with `observe_overrides()`.

**Domains:** height/width 6..18, populated columns 2..6, palette size 1..9. These are jointly feasible even at the minimum geometry, so no hidden incompatibility table is necessary.

**Alternatives rejected:**

- Preserve old `texture`, `density`, or `position_bias` labels that did not represent independently observable behavior. This would perpetuate alias/dead-axis findings.
- Let impossible combinations fail opportunistically. That makes the public contract non-falsifiable and burdens downstream curriculum code with undocumented rejection behavior.
- Permit `columns=1`. Two or more columns keep the task manifold from collapsing into a single-stack special case while still accepting all canonical inputs.

**Probe:** the official override matrix exercised 621 cases / 55,890 accepted draws with no finding or warning (`checks/after/checks/22304ccc509c_after_override_results.json`).

## D4 — Use canonical anchors plus broad sparse/dense profiles

**Decision:** schedule five profiles cyclically: `canonical_6x6_p7`, `canonical_7x7_p6`, `canonical_6x6_p5`, `broad_sparse`, and `broad_dense`.

**Rationale:** the anchors guarantee recurring support near all three canonical shape/palette signatures. The two broad profiles expand size, density, and difficulty without letting random draws accidentally starve canonical support.

**Alternative rejected:** unconstrained random sampling over the full Cartesian domain. It increases superficial diversity but makes profile-floor support probabilistic and can produce curricula dominated by large grids.

**Observed result:** all five profiles appeared in every difficulty band in the semantic census; each appeared exactly 20 times per band in the deterministic 100-draw workspace probe.

## D5 — Make every production draw teach both ambiguous distinctions

**Decision:** every default draw must contain:

1. at least one occupied input bottom-row cell; and
2. a column whose nonzero values are not numerically sorted ascending.

A reserved gap guarantees the transformation is non-identity.

**Rationale:** the first witness closes the accepted prior shortcut “discard bottom row before gravity.” The second closes the strongest canonical-fitting shortcut “sort each column, then drop.” A witness in every default draw means any three-demo production lesson refutes both competitors, regardless of query position.

**Alternative rejected:** include each witness only probabilistically. That could pass aggregate diversity while still emitting ambiguous lesson windows or rotations.

**Evidence:** both witnesses fired 600/600 in the official semantic gate and 300/300 in `workspace/probe_shortcuts.py`; both rivals disagreed on every probed draw.

## D6 — Keep the canonical-fitting sort rival explicit

**Decision:** declare `sort_values_then_drop` in `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`; declare `discard_bottom_row_then_drop` in the generated-data rival sets.

**Why only sort is canonical-fitting:** sorting matches all 3 canonical labeled pairs because their columns happen to be ascending. Bottom-row deletion already fails canonical train[0], but it survived the old generated distribution and therefore remains a necessary curriculum competitor.

**Probe:** `checks/shortcut-witness/report.json` retains a full input, Racket output, and both rival outputs; `QUESTION_ANSWER.md` reproduces the strongest case.

## D7 — Strengthen self-validation at the task manifold

**Decision:** `self_check()` validates rectangular ARC colors, 6..18 geometry, 2..6 populated columns, 1..9 foreground colors, at least five foreground cells, an occupied bottom row, and at least one moving column. `strict_canonical_like()` delegates to this contract. Mutation fixtures preserve representative near-misses.

**Alternative rejected:** validate only ARC syntax. A syntactically valid all-background or already-settled grid teaches no transformation and previously allowed structural defects to hide behind a passing self-check stage.

**Caveat:** requiring a bottom-row witness is a production/task-manifold choice, not a mathematical requirement of gravity. The canonical inputs satisfy it, and the selected generator intentionally teaches that branch.

## D8 — Use three demonstrations and verify arbitrary materialized query positions

**Decision:** retain `EXAMPLES_NEEDED=3`; assemble four-pair lessons with three demonstrations and one query. `lesson_identifiable()` scores both declared rivals. Run both the battery rotation smoke test and a 300-lesson source-bound census with every pair rotated into the query position.

**Observed:** 12/12 battery lessons identifiable; 0/48 diagnostic rotation ambiguities. Large census: 300/300 materialized, 1,200 unique pairs, 0 production ambiguities, and 0/1,200 rotation ambiguities.

**Alternative rejected:** infer teachability from individually correct labels or only the ordered production query. Correct labels do not guarantee demonstrations distinguish plausible wrong rules.

## D9 — Add reusable task-local tooling

**Decision:** add `workspace/probe_shortcuts.py`, source-hashed and deterministic. It checks canonical shortcut fit, per-band profile/witness/rival coverage, self-check failures, uniqueness, and every query rotation in consecutive four-pair windows.

**Why:** future agents can rerun one small, interpretable audit after modifying the distribution instead of reconstructing the two known rivals from prose.

**Authority boundary:** the probe uses the independent Python mirror. Official Racket battery, census, and the explicit `arcpuzzles apply` witness remain the authority-backed checks.

## D10 — Do not repair the two assigned audit targets

The audit assignment explicitly requested adversarial findings, not fixes. `generic_extraction_gen1` has a reproduced 500/500 shortcut and real Racket counterexample. `5f6fdf4f9900` has intake/contract failures but no established wrong-output counterexample. Both are documented in `AUDIT.md` without modifying their sources.

## Limitations and unresolved hypothesis space

- Two declared rivals are not a complete program search.
- The production schedule and sampled rotations were tested; arbitrary user-built curricula from extreme overrides were not exhaustively enumerated.
- A learner could still adopt an undeclared rule equivalent on the finite support tested.
- The five-profile schedule deliberately prioritizes canonical support and rule-revealing examples over uniform sampling of every axis tuple.
- Post-repair solve success is independent usability evidence on visible examples, not masked-query scoring or training admission.

## 2026-10-24 native parametric gravity policy

**Decision:** retain the exact canonical default `(rule! (gravity g "down"))` and add one task-local proposed setting, `gravity_policy=edge_directed`. The alternative locates the unique color-1 marker on a non-corner border, converts that edge to the intermediate direction `up`, `down`, `left`, or `right`, and stable-packs rows or columns in that direction.

**Why this is sequential:** step A must recover the marker edge before step B can select the gravity axis and sign. The retained counterfactual witness forces the intermediate to `down` on an `up`-marker input and changes the final output, so the dependency is causal rather than descriptive.

**Sampling contract:** inputs are deterministic and setting-neutral; requests support 2–6 demonstrations and exactly four distinct queries. The first two demonstrations use `up` and `left`, while the four queries cover `right`, `down`, `up`, and `left`. The final query is 30×30 with 96 foreground cells and touches all four boundaries.

**Learnability contract:** certificates use demonstration labels only. Against the finite declared family—fixed directions, edge opposites/clockwise, vertical-only, value sorting, marker removal, and identity—the selected policy is the sole survivor for the audited episodes. This is not a proof against every possible program.

**Source binding:** generator SHA-256 `f765aa107e6e5c50a9c3d9908f3f3d57a0cce91958b6306fc230192f9e78ea05`; canonical rule/program SHA-256 `c3638032481f10b4c0fe0b2da3ab073f52aa3ff398f6448ee2c4cb6495ed2a64`; adapter SHA-256 `07d0d019f53d3ab87b815a7a787b9002eb00a5f31e9c03d8f2c55b3ba0adc4e8`.

**Verification:** 22 focused tests and 57 staged task tests passed. Native qualification covered both settings at seeds 0 and 17 with two demonstrations and four queries. The broader task-local audit covered seeds 0, 17, and 91 at 2 and 6 demonstrations and replayed 98 labels through protected Racket. Four content-addressed public projections passed byte, schema, masking, and private-metadata checks.

**Remaining boundary:** this is reviewer-ready, not owner-accepted or training-admitted. Owner replay must use the exact integrated bytes; finite seeds and declared rivals do not establish universal identifiability or measured training gain.

