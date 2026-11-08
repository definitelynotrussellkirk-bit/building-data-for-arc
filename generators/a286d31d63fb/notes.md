# Current notes: a286d31d63fb

## Accepted rule and source identity

The canonical Racket authority is unchanged. Its rule hash is `bc2002d0a0d4`
(full recorded canonical hash `bc2002d0a0d4dd9628242b448e63f2a988832268d371b2f1b03c7540d031e7ac`).
For each monochromatic 4-connected nonzero component, count occupied cells in
each occupied row; recolor the component to 8 exactly when those counts are all
equal. Generator version `3.0.0` pins that authority. Final generator SHA-256:
`4226cd30d3bcb427a8b39aa49b368cc6c6deffc3cc5ce4737ea28128b9ec82a2`.

## Repair decisions

The prior source advertised controls it did not consistently implement, accepted
unknown/ill-typed values, used a degenerate all-flat path that violated its own
validator, and taught only solid rectangular positive examples. The replacement
keeps only five public controls with exact behavior in every difficulty band:

- `height`: integer 8..16
- `width`: integer 11..18
- `flat_component_count`: integer 1..3
- `nonflat_component_count`: integer 1..2
- `palette_kind`: `default|warm|cool|varied`

Unknown axes and the retired `texture`, `palette_size`, `n_distinct_colors`,
`position_bias`, and `density` controls are rejected. Seeds/sample indices and
numeric overrides require actual integers rather than accepting booleans,
strings, or floats. `observe_overrides` recovers both exact component-count axes
from returned grids.

Placement is now a constructive two-lane packer rather than a capped retry loop.
It supports the complete declared domain, including an 8x11 canvas with five
components. Distinct source colors prevent accidental same-color component
merges. Defaults retain canonical 9x15 and 10x16 scales and the canonical-like
2-flat/1-nonflat profile in every band.

Every generated lesson contains at least one connected nonrectangular component
with a constant row profile. `rectangle_only` is declared in
`SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`; the
`nonrectangular_flat_profile` witness explicitly claims and verifies that rival
through `WITNESS_RIVALS`. The retained fixture
`counterexamples/rectangle_only.json` is the compact concrete separator.

`self_check` now fails closed on malformed/ragged/non-integer/out-of-range grids,
reserved input color 8, repeated disconnected uses of a source color, and scenes
missing either semantic class. It intentionally accepts the canonical examples,
which need not contain the newer curriculum witness.

## Verification on the final source

- Portable staged tests: 59 passed.
- `lint`, strict `defect_lint`, `selfcheck`, and live `rule_smoke`: passed.
- Override contract: 25,200/25,200 draws accepted with zero findings.
- Semantic gate: 600 generated lessons; the declared nonrectangular witness and
  rectangle-only disagreement were verified throughout.
- Independent adversarial probe: 768 boundary draws across all bands, both
  numeric endpoints, count endpoints, all palettes, and three seeds; zero
  findings and 188 distinct inputs.
- Canonical Racket parity: minimum-canvas/max-count, maximum-canvas/max-count,
  canonical-scale, and retained-witness inputs all matched the independent
  row-profile oracle and disagreed with the rectangle-only rival.

Evidence is retained under `WORK/checks/a286d31d63fb-*`; the reusable bounded
probe is `workspace/adversarial_probe.py`.

## Limits and next action

The sampler deliberately uses a finite, compact shape bank with reflections; it
is not a claim that all lawful polyominoes or all possible rival hypotheses are
covered. The three canonical pairs themselves remain answer-equivalent under the
rectangle-only shortcut, so generated counterexamples carry that teaching load.
The declared rival set is targeted, not a universal lesson-identifiability proof.
Packaging this repair does not grant training admission or catalog approval.

Next action: ingest the delta and preserve the final-source receipts when
resolving the two old source-bound audits; no canonical Racket change is needed.


<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/a286d31d63fb/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-88cfe058026b16ea:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `a831e29015bb5b1fb90332adedd799655969ce0d925970debdd90d5d2eca5ac2`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit closure of this historical-source finding by accepted source 4226cd30d3bcb427a8b39aa49b368cc6c6deffc3cc5ce4737ea28128b9ec82a2. Strict exact live controls across bands; retired axes reject; constructive packing and independent counts; nonrectangular constant-row-profile witness defeats rectangle-only rival. Exact finite evidence and failures remain reviewer_reported under evidence/reported-support-limits-a9e67b06f9b80a56/manifest.json and the source-bound main review record. Canonical authority unchanged; no owner test rerun or parametric/training admission.

### Assessment or prior finding

## a286d31d63fb

**Classification: reproduced generator teaching-coverage and API contract defects. No Racket-rule defect is claimed. The audited source and authority were not modified.**

Generator SHA-256: `a831e29015bb5b1fb90332adedd799655969ce0d925970debdd90d5d2eca5ac2`. Canonical raw rule SHA-256: `bc2002d0a0d4dd9628242b448e63f2a988832268d371b2f1b03c7540d031e7ac`; the active base authority has exactly the same rule text. This is the same generator source as the existing unresolved API audit; the findings below do not close or supersede it.

### New finding: the sampler never refutes a rectangle-only shortcut

The selected rule recolors each component whose per-row cell counts are constant. However, every shape in `_FLAT` is a solid rectangle, and every shape in `_NON_FLAT` is a nonrectangle. The ordinary placement logic preserves those shapes as separate, monochromatic components; the three degenerate modes use the same templates. Consequently, the simpler rival **“recolor solid rectangles to 8; leave every other component unchanged”** agrees throughout the implemented template support. It also fits both canonical TRAIN examples.

A concrete lawful witness separates the two rules. `input.json` is a padded 10×12 grid with three distinctly colored components: a color-2 shifted shape at zero-based cells `(1,1), (1,2), (2,2), (2,3)`, and two ordinary nonflat components in colors 3 and 4. The shifted component has row profile `[2,2]` but does not fill its bounding rectangle. The generator's `self_check(..., difficulty="easy")` returns `[]`.

Actual execution through the supported `arcpuzzles apply` command recolors exactly those four color-2 cells to 8 and leaves the nonflat components unchanged. The rectangle-only rival leaves the entire input unchanged. The retained Racket receipt reports `valid_output: true`, `error: null`, and the expected executed rule hash `bc2002d0a0d4`. This is a reproduced teaching counterexample, not merely a request to expand the domain: it satisfies the stated constant-row-profile semantics, normal scene dimensions, component contrast, spacing, and distinct-color conditions.

Evidence: `checks/audit/a286d31d63fb/probe.py`, `probe.json`, `input.json`, `rectangle_rival.json`, `racket.json`, and `verification.json`. Six templates were inspected exhaustively; 15 ordinary draws (five seeds in each of three bands) agreed with the rival under an independent Python row-profile model. Those 15 checks are explicitly supplemental model comparisons, not 15 claimed Racket executions. The witness alone was executed with Racket.

### Fresh bounded reproduction of API findings

Six direct calls on the unchanged source produced:

| Request | Observed result |
|---|---|
| `generate(0, 0, difficulty="easy", height=8)` | Rejects the advertised height with `ValueError: draw_int('height'): override 8 outside [10, 11]`. |
| `generate(0, 3, difficulty="easy", texture="all_flat", height=10)` | Returns 12×14; its own validator reports no nonflat component. |
| `generate(0, 0, palette_size=2)` | Returns four foreground colors: 2, 3, 4, and 5. |
| `generate(0, 0, difficulty="hard", flat_component_count=3)` | Produces three flat components but only one nonflat component, contrary to the summary's two-nonflat-component promise. |
| `generate(0, 0, typo_profile="sentinel")` | Silently accepts the unknown override. |
| `generate(True, 0)` | Accepts a Boolean seed; request identity is not restricted to literal integers. |

The first five corroborate the existing unresolved API report. The Boolean call records an additional strict-scalar acceptance. Exact calls, working directories, exit codes, observed API facts, source identities, and artifact hashes are retained in `checks/audit/a286d31d63fb/receipt.json`.

**Repair direction:** add at least one connected, nonrectangular constant-row-profile shape and a regression that refutes the rectangle-only rival; repair or narrow advertised controls and align degenerate-mode validation. No repair or approval was performed in this audit.

**Scope:** source/rule inspection; all six shape templates; two canonical TRAIN pairs; 15 ordinary draws; six focused API requests; one constructed, self-check-accepted witness executed by actual Racket; and verification of its four-cell disagreement. No full battery was run. Source hashes were checked before and after.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-88cfe058026b16ea-v0001/audit_assets.json), manifest SHA-256 `96580d14ad329e4108ede430dd9884ad531439fb1c58774f7079d568a53413c5`.
<!-- arcpuzzles-current-audit-assessment:end -->
