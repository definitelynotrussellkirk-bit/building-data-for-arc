# Working notes: 9da02d5e3ac0

## Current rule and source identity

For each row independently, replace every color-5 cell with the first value in that row that is not 5. Preserve all non-5 cells. If a row is entirely 5, leave it unchanged. Canonical rule hash: `aab70f56593c`; reviewed generator version: `3.1.0`; reviewed generator SHA-256: `c118ec9adb64248311ec663e8d3b0fef9ff23236f2f9e5bc3d6e43bc58593a8d`.

The canonical puzzle source was not changed. The selected base authority's active `target_code` was synchronized exactly to canonical; its archival `raw_code` remains preserved and intentionally divergent.

## Distribution decisions

The prior v2 sampler used 5-filled rows with repetitions of one row color. In a 300-draw baseline probe, last-non-5 and unique-row-color rivals matched all 300 grids, so correct labels did not teach left-to-right selection.

The final sampler uses:

- exact `grid_h` 8–14, `grid_w` 8–16, and `n_key_colors` 2–4;
- two or three connected vertical 5-bands plus a bottom all-5 bridge row;
- preserved zero texture and multiple row-specific signal colors;
- a row whose first non-5 value is zero but which has a later signal;
- a variable-depth interior key at column 2 or later;
- one all-5 row to retain the no-key branch.

Unknown, wrong-type, and out-of-range overrides are rejected. Public density/distribution/degenerate controls were removed because they were not exact or contradicted the old validator.

## Reversed decisions and evidence

The first repair used a fixed pattern: column 1 was the key whenever column 0 was 5, otherwise column 0 was the key. A final self-review rival matched 300/300 draws. Version 3.1 replaces that pattern with a sampled deep interior key, declares the rival, and retains a regression witness. Final measurement: 0/300 rival matches; 32/32 focused tests; 12/12 battery stages green; 300 lessons and all 1,200 query rotations had zero ambiguity against seven declared rivals.

An earlier semantically rich repair also fragmented inputs too much and failed morphology/defect gates. Connected bands and a bridge replaced the peppered texture. The failed iteration is retained under `checks/after/`.

## Assumptions and limits

- Three demonstrations plus one query are used. Rotation diagnostics hold out each labelled pair once while preserving the remaining order.
- The generator intentionally models a canonical-like connected-block family, not every input lawful under the Racket rule.
- The seven executable rivals are finite evidence, not a proof of unique induction.
- Catalog approval/train safety remains a maintainer decision.
- Minimal witness: `counterexamples/shortcut_witness.json`; portable tests: `tests/test_generator_review.py`.
## Current reviewer considerations

Source SHA-256: `c118ec9adb64248311ec663e8d3b0fef9ff23236f2f9e5bc3d6e43bc58593a8d`.

# Decisions for `9da02d5e3ac0`

Final generator SHA-256: `c118ec9adb64248311ec663e8d3b0fef9ff23236f2f9e5bc3d6e43bc58593a8d`.

## D1 — Rule and authority boundary

- **Prior choice:** version 2.0 described the correct row rule but did not pin `RULE_HASH`; a selected base authority carried behaviorally equivalent, text-divergent Racket.
- **New choice:** pin canonical rule hash `aab70f56593c`; leave canonical `puzzles.jsonl` untouched; synchronize only the selected active `target_code` to canonical and preserve archival `raw_code`.
- **Reason/evidence:** before lint failed the missing hash; intermediate `authority_sync` failed exact selected-source synchronization even though execution parity passed. Final authority sync is green.
- **Rejected alternative:** change the canonical program or delete the archival source. Neither was needed and either would erase provenance.
- **Limit:** exact text synchronization is administrative; semantic correctness still depends on rule smoke/execution checks.

## D2 — Exact public axes

### `grid_h`

- **Prior:** advertised `3..18`, default 5–14; exact rationale undocumented.
- **New:** exact integer `8..14`, with canonical anchor 12 and difficulty weighting.
- **Reason:** height 8 is the smallest size that comfortably supplies zero-key, deep-key, multiple-color, all-5, and connected-band rows. Canonical inputs are 12 rows.
- **Alternatives tested/rejected:** retain 3–7 heights (too small for all witnesses without distortion); force 12 only (unnecessary loss of shape diversity).
- **Failure mode/limit:** no evidence for lawful heights outside 8–14 is supplied.

### `grid_w`

- **Prior:** advertised `3..18`; the implementation accidentally used height bounds for width.
- **New:** exact integer `8..16`, canonical anchor 12.
- **Reason:** width 8 supports two separated 5-bands and a variable-depth interior key; width 16 broadens placement without exceeding common ARC scale.
- **Alternatives:** 12 only was rejected as too narrow; widths below 8 could not guarantee the semantic layout cleanly.
- **Limit:** larger lawful widths are intentionally not claimed.

### `n_key_colors`

- **Prior:** `row_palette_size` 1–9 plus density/distribution controls; multiple advertised settings were not semantically observable in a single grid.
- **New:** exact 2–4 nonzero, non-5 signal colors, observed by `observe_overrides`.
- **Reason:** at least two colors refute a global-color rule; up to four fits the available rows and canonical palette envelope.
- **Alternatives:** one color was rejected because it cannot teach row-specific keys; 5–8 was rejected as morphologically remote and row-starved at minimum height.
- **Limit:** canonical profiles count total input colors (0, 5, and signals), so the exact canonical hits correspond to 2 or 3 signal colors.

### Removed controls

- **Prior:** `five_density`, `row_distribution`, `texture`, and loose palette controls, including `all_fives`, `no_fives`, and `single_non5_per_row`.
- **New:** remove them from the public contract.
- **Reason:** they either were not exact/observable or produced grids rejected by the generator's own `self_check`. A smaller truthful interface is preferable to nominal combinatorics.
- **Alternative:** declare a large incompatibility matrix. Rejected as harder to teach, test, and maintain than three orthogonal controls.

## D3 — Morphology

- **Prior:** imported sampler used random per-row marker positions; the first repair used semantically rich but overly fragmented texture.
- **New:** two or three vertical 5-bands with variable widths/gaps, optional staggered tops, and a final all-5 bridge row.
- **Reason:** the first repaired hash failed morphology/defect gates (generated median object count about 10 versus canonical 3). Connected bands retained witnesses while bringing the component distribution back into the canonical regime.
- **Probe:** `test_generated_morphology_retains_canonical_connected_blocks` plus final `dist_gate`/`defect_lint`.
- **Limit:** the bottom bridge and band grammar are a designed family, not a model of every lawful grid.

## D4 — Row-key placement and shortcut defense

- **Prior v2:** rows contained one repeated non-5 color, so first/last/unique-color rules were equivalent.
- **First repair v3.0:** row 0 always used column 1 when column 0 was 5; other keyed rows used column 0.
- **Final v3.1:** one interior row has a sampled key depth at column 2 or later, another row has zero as its first non-5 with a later signal, and ordinary signal keys vary by row/color.
- **Reason:** final self-review showed the fixed-position rival matched 300/300 v3.0 draws. The new failing test was observed before implementation; final probe is 0/300.
- **Evidence:** `checks/tdd-fixed-position-red.log`, `checks/tdd-fixed-position-green.log`, `checks/fixed-position-self-review/report.json`, and retained `shortcut_witness.json`.
- **Rejected alternative:** merely add the rival to reports without changing generation; that would document but not repair the teaching defect.
- **Limit:** other highly tailored generator-recognition programs remain possible; the contract covers seven plausible semantic rivals.

## D5 — Validation and exact overrides

- **New choice:** reject unknown axes, non-integer exact controls (including booleans), and out-of-range values; `self_check` never raises on malformed input and checks dimensions, ARC colors, 0/5 presence, 2–4 signals, keyed rows, key coverage, and preserved texture.
- **Reason:** override and self-check claims must describe actual observable outputs, not only accepted arguments.
- **Evidence:** 11,970 final override draws with zero findings and 32 focused tests.
- **Limit:** `self_check` validates the authored family, not all possible inputs accepted by the canonical rule.

## D6 — Lesson assembly and ordering

- **Choice:** `EXAMPLES_NEEDED = 3`; each materialized lesson has three demonstrations and one query. Production order is retained. Rotation testing holds out each of the four labelled pairs once and preserves the remaining order.
- **Reason:** the task's canonical examples admit multiple shortcuts; three generated demonstrations provide repeated witness opportunities without inflating context.
- **Evidence:** final census requested/materialized 100 lessons per band (300 total), 1,200 labelled pairs, and 1,200 hold-one-out rotations. Both production and rotation statuses are `no_ambiguity_found`, with 0 hook/scoring errors.
- **Schedule:** no deterministic `LESSON_SCHEDULE_PERIOD` is declared; this was a seeded production-sampler census, not exhaustive seed enumeration.
- **Limit:** the result is finite and only scores declared rivals.

## D7 — Counterexample retention

- **Choice:** retain one compact 8×8 generated grid at seed 7301/sample 4 with exact overrides and expected output.
- **Reason:** it is validator-lawful and refutes every declared rival, including the late fixed-position finding.
- **Evidence:** `repo/generators/9da02d5e3ac0/counterexamples/shortcut_witness.json`, enforced by a focused regression test.
- **Limit:** one witness is not distribution coverage; the 300-lesson census supplies the broader measurement.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/9da02d5e3ac0/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Proposed native parametric family: row fill, then vertical bridge

The canonical production generator and selected authority remain unchanged. A
separate task-local adapter proposes two episode-fixed settings:

- `row_fill_only`: exact canonical Racket bytes.
- `row_fill_then_vertical_bridge`: run the canonical row completion, then fill
  zero cells strictly between vertically aligned signals only when every signal
  in that completed column has one shared color.

The alternate is genuinely sequential. Stage A creates colored endpoints from
input color-5 cells; Stage B consumes that completed grid. A protected-Racket
wrong-intermediate counterfactual that applies Stage B to the raw input changes
107 cells in the retained 30x30 query.

Inputs are setting-independent and prefix-stable. Requests support 2–6
demonstrations and 1–4 queries; the four-query schedule reaches 30x30 with dense
content on all four boundaries. Public turns contain demonstrations plus one
current query input only. Every minimum lesson member explicitly teaches that
literal zero can be the first non-5 row key, closing a first-nonzero shortcut
found by the bounded audit.

The reusable audit executes eleven plausible rivals in protected Racket. At
seed 19 with two demonstrations and four queries it performed 62 Racket
evaluations and found no demo-surviving rival that changed a query. This finite
rival set is not a proof against arbitrary programs. Native qualification and
the causal witness are reviewer handoff evidence; owner acceptance and training
admission remain pending.
