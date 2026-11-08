# Working notes: b3bfd59c2c43

The 2026-10-03 review replaced a retry-based, weakly validated sampler with a constructive source-bound sampler. Detailed rationale is in the return-level `DECISIONS.md`; executable regressions are in `tests/test_generator.py`; the 100-lessons-per-band rival sweep is `workspace/qualify_lessons.py` with retained output `workspace/qualification.json`.

Key retained failure: the first repaired version made irregular witnesses frequent but not lesson-complete. A medium lesson at seed `2021138044741`, sample index `33` let `bounding_box_perimeter_only` fit all demos and fail only on the query. The final sampler guarantees an actual rival disagreement in every ordinary input and rotates the teaching component among strips.
## Current reviewer considerations

Source SHA-256: `7a62d839585d7d2b0ab1333d28e026272b039cce3ad2cfe029ee6cedee7f1c8d`.

# Design decisions for b3bfd59c2c43

The baseline task notes contained no design history, so “original rationale” below is either inferred from the baseline code or marked unknown. The selected Racket rule was not changed.

## D1 — Pin the existing authority; do not rewrite the rule

- **Choice:** add `RULE_HASH = "28b8cf49f820"` and keep the selected canonical Racket transformation unchanged.
- **Original rationale:** unknown. The baseline omitted the required pin but its generated outputs were compatible with the selected rule.
- **Probe:** before and after `rule_smoke`, `racket_lint`, and `authority_sync`; canonical Python mirror checks in task tests.
- **Alternatives rejected:** changing the rule to match the baseline's restricted rectangles would alter a correct public task rather than repair its data.
- **Failure mode / limit:** an archival bank solution remains textually divergent, but selected execution parity is green and no authority bytes were edited.

## D2 — Replace nine mostly decorative axes with three exact observable controls

- **Choice:** advertise only `grid_h` (10..18), `grid_w` (12..20), and `object_count` (2..3). Unknown keys and wrong types are rejected. Every Cartesian combination is constructively feasible, so `INCOMPATIBLE_OVERRIDE_COMBINATIONS = []`.
- **Original rationale:** inferred: the baseline exposed texture, density, position, palette, and several size/count controls to appear diverse. In practice, several were dead, overlapping, band-restricted, or silently ignored.
- **Probe:** explicit extreme/midpoint overrides in all bands; battery override matrix; `observe_overrides` round trip.
- **Alternatives rejected:** retaining fake axes as “diagnostic” controls; band-specific exact domains; declaring thousands of incompatibilities around a fragile rejection sampler.
- **Failure mode / limit:** the reduced interface offers fewer knobs, intentionally preferring trustworthy controls over nominal combinatorics.

## D3 — Weight the three public canvas profiles without restricting the envelope

- **Choice:** strongly weight `(11,15)`, `(12,12)`, and `(13,15)`, while retaining all declared dimensions 10..18 × 12..20. Defaults usually create two objects and occasionally three.
- **Original rationale:** the baseline sampled dimensions independently and almost never hit a linked canonical profile.
- **Probe:** profile-floor moved from exact `0/60`, envelope `3/60`, with zero support in easy/hard, to final exact/profile support recorded in `checks/after/`; all three bands pass.
- **Alternatives rejected:** emitting only the three public sizes (too narrow); independent uniform size axes (too little linked support).
- **Failure mode / limit:** weighting intentionally makes the public profiles common, so this is not a uniform canvas sampler.

## D4 — Use constructive separated strips instead of retry placement

- **Choice:** partition rows or columns into two or three strips with a full blank separator, then place exactly one object per strip.
- **Original rationale:** inferred: the baseline used repeated random placement and silently returned fewer objects when attempts failed.
- **Probe:** 160 deterministic draws per band in tests, exact object-count recovery, one-cell separation, no underfill, full override matrix.
- **Alternatives rejected:** increase retry counts; silently reduce requested count; rejection-sample the whole scene.
- **Failure mode / limit:** strip construction is visibly structured. Random orientation, offsets, dimensions, colors, shape families, and witness strip reduce but do not erase that layout prior.

## D5 — Keep ordinary input colors distinct and limited to 1..7

- **Choice:** sample one distinct color per component from 1..7; reserve 8 for output.
- **Original rationale:** canonical examples use distinct nonzero object colors, and color 8 is the transformation marker.
- **Probe:** `self_check`, canonical acceptance tests, and rule-smoke.
- **Alternatives rejected:** repeated colors across separated components (legal under some interpretations but needlessly complicates object identity); input color 8 (confounds output semantics).
- **Failure mode / limit:** the generator does not teach repeated-color separated components. That is a deliberate conservative grammar choice, not a universal claim about all lawful inputs.

## D6 — Model the actual shape family and preserve a real inner core

- **Choice:** sample filled squares/rectangles, Manhattan diamonds, corner-rounded squares, and three-cell-thick crosses at fitting sizes. Every ordinary component is connected, hole-free, spans at least 3×3, and contains a four-neighbor-surrounded core.
- **Original rationale:** inferred: the baseline tried to add “irregular” templates, but most were one-cell thick and one alleged diamond was four disconnected singletons. Those shapes made whole-object recoloring accidentally correct.
- **Probe:** canonical representative tests; 480 draws across bands; core/connectivity/separation checks; minimal-impostor rejection.
- **Alternatives rejected:** only rectangles (bounding-box shortcut); thin outlines/singletons (no preserved core); arbitrary polyomino growth (harder to guarantee holes, core, and exact fit).
- **Failure mode / limit:** this remains a curated solid-object family, not all possible core-bearing polyominoes.

## D7 — Put an executable semantic counterexample in every ordinary input

- **Choice:** one component per grid is a sloped or concave teaching shape for which true four-neighbor boundary differs from bounding-box perimeter. Narrow strips use a notched core-bearing rectangle; wider strips use diamonds or the 7×7 thick cross. The teaching strip is selected independently rather than fixed to the first strip.
- **Original rationale:** the first repaired version only made irregular shapes frequent. The 12-lesson semantic smoke then found a medium lesson where all demos supported the bounding-box shortcut and only the query contradicted it.
- **Probe:** retained failed semantic report at `checks/intermediate-after-semantic-failure/`; regression that every default draw refutes the bounding-box rival; regression that the teaching object rotates across all three constructive strip ranks; final semantic gate and 300-lesson qualification census.
- **Alternatives rejected:** remove the rival; weaken `lesson_identifiable`; merely raise irregular-shape probability; pin the witness to the first object.
- **Failure mode / limit:** guaranteeing a teaching object changes the natural shape frequency. The rotating strip and varied witness family prevent the most obvious positional shortcut, but the first object family is still curated rather than unconstrained.

## D8 — Declare independently executable rivals and witnesses

- **Choice:** retain two named rivals: `recolor_entire_component` and `bounding_box_perimeter_only`. Witnesses must certify actual output disagreement, not just visual irregularity.
- **Original rationale:** absent in baseline; there was no semantic contract.
- **Probe:** final gate verifies both rival claims on 60/60 sampled witness checks each. A failed implementation taught an important distinction: a radius-1 diamond and a 5×5 three-thick “cross” can look irregular while remaining answer-equivalent to a bounding-box rule.
- **Alternatives rejected:** feature-only witness predicates; prose-only shortcut descriptions; self-referential rivals that call the intended rule.
- **Failure mode / limit:** these are the two highest-value observed rivals, not an exhaustive hypothesis class.

## D9 — Strengthen `self_check` and separate strict public support from lawful breadth

- **Choice:** `self_check` validates the full ordinary grammar; `strict_canonical_like` additionally requires one of the three public canvases, two components, and a canonical normalized shape template.
- **Original rationale:** the baseline check accepted singleton, line, 2×2, and full-grid impostors and mixed negative fixtures into ordinary texture values.
- **Probe:** standalone defect lint, explicit impostor tests, canonical acceptance tests, strict-rate census, and profile floor.
- **Alternatives rejected:** make strict canonical matching the whole lawful grammar (too narrow); allow negative fixtures through the ordinary path (poisons training rows).
- **Failure mode / limit:** strict matching uses normalized template membership and does not encode every geometric relation between the two public objects.

## D10 — Add source-bound task tests and a reusable qualification tool

- **Choice:** add `tests/test_generator.py` and `workspace/qualify_lessons.py`. The probe imports the selected source, hashes it, discovers declared rivals dynamically, checks canonical parity, materializes 100 lessons per band with an explicit schedule, and records unique-input and rival-survival counts.
- **Original rationale:** no selected-task tests existed; the general battery does not discover task-local tests automatically, and its lesson sample is intentionally small.
- **Probe:** final task suite and `workspace/qualification.json`.
- **Alternatives rejected:** hand-counted examples; hardcoded rival-name lists; claiming witness frequency proves complete lesson identifiability.
- **Failure mode / limit:** the large probe uses the independently checked Python `rule_mirror` rather than invoking Racket for all 1,200 rows. The battery remains the authority parity check.

## D11 — Do not change the selected Racket reference

No reference-rule file was edited. All behavioral changes are confined to the selected generator, selected-task tests, and task-local workspace/report artifacts.

## 2026-10-25 native parametric family

- The production generator and canonical ledger remain unchanged. The task-local native family is under `workspace/parametric/`.
- `layer_policy=outer_boundary` is byte-exact canonical. `layer_policy=signal_depth` counts the unique connected color-9 signal and uses that count as the onion-layer depth recolored to 8 in every nonzero non-9 binary component.
- Inputs are matched across settings; 2–6 demonstrations and 1–4 prefix-stable queries are supported, with four distinct queries and a substantive 30×30 case.
- The first draft encoded each signal count with one fixed topology. The final sampler rotates horizontal, vertical, and L-shaped connected signals and retains executable signal-width, signal-height, and signal-bounding-box-area rivals. The first two demonstrations decouple all three from cell count.
- Current bounded evidence: 60 copied-runtime tests, 384 audited episodes, 384 exact 30×30 pairs, 0 declared-rival survivors, 4 protected-Racket qualification jobs / 40 evaluations, 16 sequential public views, and a protected wrong-depth witness.
- Evidence is under `checks/b3bfd59c2c43/`; owner exact-byte integration, fresh qualification, acceptance, and explicit training admission are still required.
