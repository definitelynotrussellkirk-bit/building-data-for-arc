# Current notes: a8a99930c51a

## Intended rule

Distinct nonzero colors in row 0, read left to right, define a cyclic successor map. Row 0 stays fixed. Matching colors below it change to their successor; background and out-of-strip colors stay fixed. Canonical rule hash: `e5c43869717c`.

## Current generator

Version 2.0.0 generates 7–14 by 9–16 boards with 3–6 distinct strip codes, a blank row 1, and one connected 3–5-cell body object per code. It may add 0–4 cells of one out-of-strip distractor color. Exact axes are `grid_h`, `grid_w`, `n_codes`, `cells_per_code`, and `n_distractors`; all advertised values work in every difficulty band.

A one-third sample-index core supplies the three canonical profiles (7x9/10/11 with four total colors). `self_check` intentionally accepts 2–5 cells per code so it owns the observed 2-cell canonical case while generation remains 3–5.

## Teaching decisions

Both numeric color succession and first-body-appearance succession fit every labeled canonical pair. Every generated board therefore forces the strip order to differ cyclically from both orders. The rivals are executable through `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`; two demonstrations are requested.

Retained witness: `counterexamples/shortcut_seed71_index2.json`, checked against Racket authority in `checks/shortcut-counterexample-racket.json` and covered by focused tests. The final 100-per-band rotated census found 0 ambiguities in 300 lessons / 900 rotations against the declared rivals.

## Reversed choices and evidence

- Replaced the baseline sparse-pixel distribution and dead/duplicated axes after lint, defect-lint, profile, and override failures.
- Removed the repaired uint32 seed cap after the profile gate's 48-bit pinned seeds produced 60/60 crashes.
- Raised canonical-core cadence from every fifth to every third sample index after the exact/envelope rate was 11/60, below 25%; final is 22/60 with every band represented.

## Known limits

The finite rival census does not establish unique induction against all possible rules. Object geometry comes from separated segments of one of four serpentine paths; only one unknown color is generated; and dimensions outside 7–14 by 9–16 are outside this selected domain. The Racket authority was not changed.
## Current reviewer considerations

Source SHA-256: `59bd366d4c1a56755da18736805c8f303ea1b519212bf6db66d1f3a1049bd994`.

# Decisions: a8a99930c51a

## D1 — Keep the canonical authority unchanged

- **Prior choice:** The selected Racket/canonical rule already implemented a top-row cyclic color mapping.
- **Rationale available from prior notes:** unknown; the imported notes contained no design record.
- **Probe:** canonical pairs were checked with an independent Python oracle, and authority/rule-smoke stages were run before and after.
- **Decision:** do not edit the rule. Pin `RULE_HASH = "e5c43869717c"` in the generator.
- **Alternatives rejected:** changing the rule to numeric successor order or body-order successor. Both happen to fit all labeled canonical pairs but contradict the top-strip program and are weaker explanations.
- **Failure mode/limit:** the canonical pairs alone do not distinguish those rivals, so generator teaching must do so.

## D2 — Replace sparse pixels with connected canonical-like objects

- **Prior choice:** each color was scattered as independent pixels, with weak relation to canonical rings/objects.
- **Original rationale:** unknown.
- **Probe:** baseline profile floor had 0/60 exact/envelope support, and defect lint reported structural mismatch and minimal impostor acceptance.
- **Decision:** emit one 4-connected object per code, separated from the row-0 key by a blank row. Generated object size is exactly controlled at 3–5 cells.
- **Alternatives considered:** keep sparse pixels and only repair metadata; use arbitrary polyomino growth; use rectangular blocks. The path-segment design was chosen because it is deterministic, always connected, makes exact counts observable, and fits every declared dimension combination.
- **Failure mode/limit:** segment geometry comes from a small family of serpentine traversals. Geometry is irrelevant to the authority, but an undeclared learner shortcut could exploit it.

## D3 — Teach against the strongest canonical-fitting shortcuts

- **Finding:** `numeric_successor` and `body_first_successor` each reproduce every labeled canonical output.
- **Decision:** sample a strip permutation that is not cyclic-equivalent to sorted numeric color order, then assign object colors so body first-appearance order is not cyclic-equivalent to the strip. Declare both as `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`, with executable witnesses and `lesson_identifiable`.
- **Probe:** focused tests first proved both rivals fit all canonical pairs, then require every generated board to disagree. Seed 71/index 2 is retained with a Racket output.
- **Alternatives rejected:** rely on random color permutations and hope for witnesses; add more demonstrations without controlling their information. Both allow avoidable ambiguous lessons.
- **Failure mode/limit:** only declared rivals are exhaustively scored. This does not prove universal rule identification.

## D4 — Use two demonstrations and one query

- **Decision:** `EXAMPLES_NEEDED = 2`; each generated demonstration independently refutes both declared rivals, so two provide redundancy without wasting a large lesson window.
- **Probe:** 300 production lessons (100 per band), 900 pairs, and all 900 query rotations had zero ambiguity against the declared rivals.
- **Alternative:** one demonstration would distinguish these two rivals, but two better protects against accidental learner overfitting and matches the generated curriculum's three-pair lesson format.
- **Limit:** arbitrary unseen rivals may require more evidence.

## D5 — Exact, band-independent controls

- **Prior choice:** metadata advertised many controls that were ignored, duplicated, coerced, or narrowed by difficulty.
- **Decision:** expose only five structural axes: `grid_h`, `grid_w`, `n_codes`, `cells_per_code`, `n_distractors`. Overrides use their full advertised domain in every band; difficulty only changes default weighting.
- **Probe:** tests enumerate representative extremes in `None`, easy, medium, and hard; the public override gate passed.
- **Alternatives rejected:** keep palette/texture aliases with no independent effect; advertise band-specific exact domains. Both make the public contract misleading.
- **Failure mode/limit:** palette identities and object geometry are intentionally stochastic rather than exact controls.

## D6 — Canonical profile support every third sample index

- **Prior repair attempt:** a one-fifth core generated 11/60 exact/envelope hits under the profile gate, below its 25% threshold.
- **Decision:** use a one-third core with height 7, width 9/10/11, three codes, no distractor, and canonical-like object counts.
- **Probe:** a regression reproduces the gate's SHA-derived seeds; final support is easy 6/20, medium 8/20, hard 8/20 (22/60 overall), with 0 crashes.
- **Alternatives rejected:** key the schedule to the raw census index (not available to the generator); make every board canonical-sized (would unduly collapse diversity).
- **Limit:** profile support is deterministic by sample-index residue, not an iid probability statement.

## D7 — Accept non-negative integer seeds of arbitrary width

- **Prior repair attempt:** uint32 validation rejected the profile gate's 12-hex-digit SHA seeds and caused 60/60 census crashes.
- **Decision:** reject booleans and negative/non-integer seeds, but do not impose a 32-bit maximum. Keep sample indices non-negative integers.
- **Probe:** the exact 48-bit boundary test failed before the change and passed afterward; profile floor has 0 crashes.
- **Alternative rejected:** truncate or mask seeds, which would silently merge reproducibility identities.

## D8 — Preserve unknown body colors

- **Decision:** permit 0–4 cells of one color absent from the strip; the authority leaves them unchanged.
- **Rationale:** this explicitly teaches that membership in the key, not merely nonzero color, controls recoloring.
- **Probe:** focused tests and the post-repair visible example include such distractors.
- **Limit:** only one out-of-strip distractor color is generated; multiple unknown colors remain valid under the authority but are outside this generator domain.

## D9 — Strict but canonical-owning validation

- **Decision:** validate rectangular color grids, dimensions, 3–6 distinct row-0 codes, blank row 1, one connected 2–5-cell object per code, and at most one/four distractor color/cells. Generated boards use the narrower 3–5 object range, while `self_check` accepts the canonical 2-cell case.
- **Probe:** all three canonical inputs pass; minimal empty, header-only, disconnected, and incomplete impostors fail.
- **Alternative rejected:** make `self_check` exactly mirror generated defaults, which would reject lawful canonical input.
- **Limit:** `self_check` validates the selected domain, not every grid on which the authority could execute.
