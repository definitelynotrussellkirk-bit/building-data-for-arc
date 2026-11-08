# Working notes: dfc4967f816f

## Current account (generator 2.0.0)

The intended rule is local classification of a one-row strip of 3×3 tiles: split at full color-9 divider columns and output 8 for each tile equal to its left-right mirror, otherwise 0. The canonical Racket authority was not changed and is pinned by `RULE_HASH = "136bfe841cf2"`.

### Reversed baseline choices

Version 1.2.1 generated 2–5 tile rows, per-tile cycling colors, and eight loosely specified controls. Its source comment gave output-shape diversity as the rationale, but the result had no exact or envelope canonical-profile support and failed lint/defect/override gates. Version 2.0.0 instead uses one tile row, 3–6 tile columns weighted toward canonical four, one shared foreground color in 1..8, and only two exact observable axes: `tile_cols` and `foreground_color`.

### Teaching decisions

Every normal sample contains positive and negative tiles. At least one negative has a symmetric top row but lower-row asymmetry, refuting the strongest content shortcut `top_row_only`. Normal flag sequences are also forbidden from matching the canonical fixed-even-position pattern, refuting positional replay. Both rivals fit all three canonical pairs, so they are declared as semantic rivals/shortcuts/lesson competitors and covered by focused tests plus `counterexamples/top-row-only.json`.

### Measured status

- Final generator SHA-256: `c3e1e264f25bd4839eec5d91889b22330b83b745bc7cf027246171abf817f452`.
- After battery: 12/12 green.
- Strict profile: 38/60 exact and envelope hits; all bands supported.
- Selected task tests: 82 passed.
- Lesson census: 300 bundles, 2 demonstrations + 1 query, 0 ordered ambiguities and 0/900 rotation ambiguities against the two declared rivals.

### Parametric prototype

`workspace/parametric/` proposes episode-level `output_color ∈ {8,4}`. Setting 8 is exactly canonical; setting 4 changes only the positive marker. All labels are produced by instantiated Racket through the protected bridge. This is prototype evidence only and is not production-approved.

### Limits / open findings

The sampler deliberately excludes multi-row strips, per-tile palettes, blank tiles, and all-positive/all-negative episodes. Finite rival checks do not prove unique induction against every possible program. The output-color prototype has bounded two-setting evidence and requires a separate integration decision.

Imported historical notes remain in `evidence/associated_notes.jsonl`; no prior reviewer return was used as a repair lead.
## Current reviewer considerations

Source SHA-256: `c3e1e264f25bd4839eec5d91889b22330b83b745bc7cf027246171abf817f452`.

# Decisions: dfc4967f816f

## D1 — Preserve the canonical authority

**Prior choice:** the baseline omitted `RULE_HASH`, although it relied on the canonical Racket rule.
**New choice:** pin `RULE_HASH = "136bfe841cf2"` and leave the canonical Racket source unchanged.
**Reason:** the rule already correctly splits the strip into 3×3 tiles and emits 8 exactly for vertically symmetric tiles. The defect was the input distribution and contract, not the transformation.
**Evidence:** `checks/final-after/checks/dfc4967f816f_after_rule_smoke.json` and `checks/final-after/checks/dfc4967f816f_after_authority_sync.json`.

## D2 — Return to a one-row 3×3-tile strip

**Prior choice:** version 1.2.1 widened normal generation to 2–5 tile rows and 3–6 tile columns. Its source comment says this was intended to widen output shapes; no task-local note justified the departure.
**New choice:** generate exactly one tile row, 3–6 tile columns, with full color-9 divider columns. Weight four columns more heavily so the exact canonical 3×15 profile remains common while lawful length variation remains.
**Alternatives rejected:** retaining multi-row macro-grids, arbitrary tile sizes, or partial dividers. Those may be executable under parts of the Racket implementation, but they are not demonstrated by the canonical task and caused zero canonical-profile support.
**Probe/result:** exact profile support rose from 0/60 to 38/60, with easy/medium/hard support 14/20, 13/20, and 11/20 (`checks/final-after/checks/dfc4967f816f_after_profile_floor.json`).

## D3 — Use one shared foreground color

**Prior choice:** the baseline cycled colors by tile and advertised palette controls that were not part of the canonical grammar.
**New choice:** every tile uses background 0 plus one shared foreground color in 1..8; color 9 is reserved for dividers. `foreground_color` is an exact observable override.
**Reason:** all canonical inputs use one shared object color, while the rule is shape-based and should remain color-invariant. Varying the shared color tests invariance without adding an unsupported per-tile-color composition.
**Alternatives rejected:** per-tile palettes, color-dependent labels, and divider-color variation. They add unrelated hypotheses and weaken canonical profile support.

## D4 — Keep only truthful public axes

**Prior choice:** eight axes mixed real controls, aliases, constants, palette metadata, and degenerate textures.
**New choice:** advertise only `tile_cols` and `foreground_color`; validate types/ranges, reject unknown keys, and implement `observe_overrides`.
**Reason:** every advertised exact control must be independently observable and honored. Diagnostic/degenerate cases belong in tests, not ordinary training axes.
**Evidence:** baseline override failed; final override stage is green in `checks/final-after/checks/dfc4967f816f_after_battery_summary.json`. Focused tests cover every legal value, bad scalar types, out-of-range values, and unknown keys.

## D5 — Force informative positives and negatives

**Prior choice:** random flags were repaired only when all-positive or all-negative; asymmetry had a fixed conspicuous construction.
**New choice:** sample a nontrivial flag pattern with at least one positive and one negative. Positive tiles are arbitrary nonblank vertically symmetric 3×3 binary patterns. Negative tiles span asymmetric patterns, and every sample contains at least one “deep” negative whose top row is symmetric while a lower row breaks symmetry.
**Reason:** this directly teaches that all three rows matter and prevents blank positives. Difficulty changes negative-pattern emphasis without changing the rule or structural profile.
**Failure mode considered:** if all negatives differ in the first row, `top_row_only` fits every lesson. The deep-negative witness blocks that shortcut.

## D6 — Break the fixed-position rival

All three canonical outputs happen to be `8,0,8,0`, so a positional replay rule fits them. Normal generation therefore excludes the fixed even-position flag sequence for every supported tile count. The retained four-tile witness has intended labels `8,8,0,8`; the fixed-position rival predicts `8,0,8,0` (`checks/counterexamples/dfc4967f816f-probe.json`).

An alternative was to randomize tile order after independent generation. I rejected a separate shuffle stage because directly sampling a noncanonical flag pattern is simpler, deterministic, and easier to test.

## D7 — Parse and validate the actual grammar

The new parser requires exactly three rectangular rows; widths encoding 3–6 width-3 tiles; full divider columns of 9; no 9 inside tiles; and ARC integer colors. `self_check` further requires one shared foreground color, nonblank tiles, and both label classes. `strict_canonical_like` intentionally accepts the complete canonical manifold plus the sampler’s 3–6-column extension.

This is narrower than the raw Racket function may tolerate. That restriction is intentional: the generator is an input sampler for the demonstrated family, not a test of every incidental input the implementation can execute.

## D8 — Declare only the two strongest evidenced rivals

The canonical pairs are fit by both `top_row_only` and `fixed_even_positions`, so these are exposed through `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`, with matching executable witnesses. The 300-lesson census refuted both on every lesson and every held-out-pair rotation.

I did not claim universal uniqueness. The census covers these two named rivals plus generic framework probes; it does not enumerate all possible programs or semantic equivalences.

## D9 — Build an output-color parameter as a separate prototype

**Parameter:** `output_color ∈ {8,4}`, default 8.
**Scope:** chosen once per episode and reused for all pairs; input constraints are unchanged.
**Why this parameter:** it changes the executed transformation while preserving the core vertical-symmetry reasoning. Demonstrations necessarily reveal the chosen marker whenever a positive tile appears.
**Why separate:** the production API remains fixed to the canonical rule, so the variant lives under `workspace/parametric/` and is explicitly not approved.
**Evidence:** `checks/parametric/manifest.json`, including exact Racket hashes, two complete episodes, and a shared input whose outputs differ between settings.

I rejected direction (horizontal versus vertical) as the prototype parameter because it changes the core discriminant and would require stronger episode construction to separate the settings reliably. I also rejected divider/background colors as mere input variation rather than a rule change.

## Known limits and open findings

- The sampler deliberately does not cover multi-row outputs, per-tile colors, blank tiles, or degenerate all-positive/all-negative strips.
- `tile_cols=3..6` extends length beyond the demonstrated four tiles, but keeps the same local classification law.
- The exact canonical profile is frequent rather than universal; 22/60 strict draws use a different lawful tile count.
- Finite rival tests cannot certify universal induction.
- The parametric prototype has bounded evidence only and needs a separate shared-runtime/product decision before any production integration.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/dfc4967f816f/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## D10 — Extend the existing prototype to the current promotion contract

The earlier output-color idea is retained, but the implementation now supports independent 2–6 demonstration and 1–8 query counts, four-query sequential projection, a native `adapter.py`, and `promotion.json`. The production generator remains `c3e1e264f25bd4839eec5d91889b22330b83b745bc7cf027246171abf817f452`; canonical setting 8 remains byte-for-byte program hash `136bfe841cf24485694f6df9d0855cfdb4b396323de4f3a468e301f65b84944b` and rule hash `136bfe841cf2`.

## D11 — Vary only the positive output marker

`output_color ∈ {8,4}` is chosen once per episode. The input grammar and vertical-symmetry classification are identical across settings, and matched inputs make the label difference observable. The alternative program hash is `4e99f1926f13331c28aca6698d6bdfc83569d7209e588537aa0ab749563b1d40`.

## D12 — Record the lawful size ceiling instead of inventing a 30×30 case

The four query inputs use 3, 4, 5, and 6 width-3 tiles, producing 3×11, 3×15, 3×19, and 3×23 grids. Exact 30×30 is not representable without abandoning the reviewed one-row 3×3-tile grammar, so 3×23 is the explicit lawful maximum.

## D13 — Bind exact public bytes and current evidence

A saved-file adversarial check found pretty-JSON/full-SHA drift. Public evidence now uses exact `public_challenge_bytes`; a regression covers the writer, while label tampering, query-output leakage, and invalid counts fail closed. Focused Racket-backed tests passed 11/11 and the staged task suite passed 86/86. The current source inventory is `workspace/parametric/evidence/source-inventory.json` (SHA-256 `873047019af6f1f3a443b41e3252733721287a1a82e24b3c03075dc9fe569935`). This remains a proposed prototype pending owner qualification and acceptance.
