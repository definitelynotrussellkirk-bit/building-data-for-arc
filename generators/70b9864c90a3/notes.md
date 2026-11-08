# Working notes: 70b9864c90a3

## Review `review-50d575e3add2d4ef` — 2026-10-02

The inherited v3.0.0 generator and Racket authority passed all 12 baseline gates, but a distribution probe found three untested correlations:

- Every positive center was on residue `(row mod 3, col mod 3) = (1, 1)`.
- Every positive center had four blank orthogonal neighbors, so a stricter blank-orthogonals rule fit all canonical and generated pairs.
- Shared positive colors occurred only with the partial-diagonal distractor. A rule allowing repeated-color fills only when that distractor was present survived every sampled lesson.

The selected v3.1.0 repair keeps the local transformation and Racket rule unchanged. It random-packs disjoint 3x3 motif footprints, schedules exactly one distinct-color and two shared-color examples in each three-sample window with a seed-dependent phase, and schedules one recognizable opposite orthogonal context pair per window. New semantic rivals and witnesses make those requirements executable. Malformed one-cell or asymmetric context remains outside the grammar.

Evidence retained in the review return:

- The regression tests failed 65 subcases on v3.0.0 and pass on v3.1.0.
- A 1,080-grid census covers all nine mod-3 center residues, includes context in 360 grids, and leaves none of the three distractor-conditioned color shortcuts alive in 600 sampled lessons each.
- A separate stress run covered 2,880 ordinary draws, 3,072 explicit override draws, and 2,160 lesson windows with zero failures.
- The after battery is all-green across all 12 stages, including 29,070 override-contract draws and strict semantic-gate checks.

The focused legacy file `test_generator.py` still has a source-checkout path bug in its canonical-data test (`parents[3] / data/...`). It passes in neither this source layout nor the packet root; the review did not edit that file because the return contract permits new tests only under `tests/`. The battery itself is unaffected.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `57fa79cde7f571c9e60e801152351c8e7a70b7534da3767e8a2ddcbaab03c37b`.

# Decisions for `70b9864c90a3`

## 1. Preserve the transformation and Racket authority

**Choice.** Keep the canonical row and selected Racket program unchanged.

**Rationale.** Canonical replay, rule smoke, Racket lint, and authority-sync were green. The observed defects were in generated input support, not output semantics.

**Alternatives considered.** Rewriting the Racket program or broadening the canonical rule. Both would add risk without addressing the measured shortcuts.

**Probe/failure mode.** The selected authority was run on generated grids and on the exact orthogonal-context counterexample. It filled both valid centers and ignored the controlled partial diagonal as intended.

## 2. Random-pack motifs instead of jittering the old lattice

**Choice.** Select all positive and negative centers with randomized backtracking over disjoint 3x3 footprints.

**Original behavior.** Centers came only from `range(1, size - 1, 3)`, so every answer was at residue `(1,1)` modulo 3.

**Why this choice.** It removes both row and column phase as shortcuts while preserving the existing non-overlap invariant and supporting explicit 7x7, three-positive overrides.

**Alternatives considered.**

- Apply a single global offset to the old lattice. This would expose at most nine whole-grid phases and retain rigid spacing.
- Sample centers greedily. This can strand the final motif on small grids and make legal overrides fail nondeterministically.
- Allow overlapping footprints. This complicates semantic classification and can create accidental answers.

**Probe/failure mode.** The after census observed all nine residue pairs and 159 distinct active positions. Build-and-validate retries reject accidental cross-boundary predicates. A 5,952-draw stress run found no packing failures.

## 3. Add structured orthogonal context, not arbitrary noise

**Choice.** In exactly one example per three-sample window, place one equal-color opposite pair north/south or east/west around an active center. Its color differs from the diagonal ring.

**Why this choice.** It directly falsifies the strongest canonical-fitting rival: “the diagonal rule applies only when all orthogonals are blank.” Opposite pairing makes the allowed context recognizable to `self_check`.

**Alternatives considered.**

- Add arbitrary single-cell clutter. This would weaken the existing mutation-sensitivity contract because a destructive stray-cell mutation could become accepted.
- Add context to every example. That would replace one shortcut with another and drift farther from the canonical distribution.
- Add same-color orthogonals. That could encourage a plus/combined-shape interpretation and blur which color is copied.

**Probe/failure mode.** Malformed one-cell, unequal-color, adjacent, or same-as-diagonal context is rejected. The valid pair appears in 360/1,080 sampled grids and makes the blank-orthogonal rival wrong in every such grid.

## 4. De-correlate color reuse from negative texture

**Choice.** Keep the texture cycle, but choose a seed-dependent distinct-color slot; the other two slots use shared positive colors.

**Original behavior.** The only shared-color profile was `partial_diagonals + shared`, making partial-diagonal presence a perfect signal for when repeated fills of one color were allowed.

**Why this choice.** In every three-example window, each of the three texture-conditioned rivals encounters a shared-color example without its favored texture.

**Alternatives considered.**

- Randomize color mode independently per sample. This can leave short lessons without a repeated-color witness.
- Use shared colors in all examples. This rejects the one-per-color rule but loses canonical-like distinct-color support.
- Hard-code one new six-profile sequence. A seed-dependent phase avoids a new global texture/color alignment while retaining guaranteed window coverage.

**Probe/failure mode.** All three texture-conditioned rivals survive 0/600 sampled lessons after the change, compared with 600/600 survival for the partial-conditioned rival before it.

## 5. Make the new assumptions executable

**Choice.** Add explicit rivals, witnesses, witness-to-rival mappings, canonical shortcuts, and tests.

**Why this choice.** A prose-only distribution intention is easy to regress. The strict semantic gate now has named evidence for context invariance and cross-factor de-correlation.

**Alternatives considered.** Rely only on the external review probe. That evidence is useful, but it would not travel with the selected generator after integration.

**Probe/failure mode.** `tests/test_review_improvements.py` failed before implementation and passes after. The strict semantic gate is green with `--require-contract --require-rival-witness --require-shortcut-counterexample`.

## 6. Keep the declared override surface stable

**Choice.** Do not add an `orthogonal_context` override axis. Context is a scheduled latent teaching factor; all five existing override axes remain exactly observable.

**Rationale.** The task needs guaranteed lesson coverage, not a new public control. Adding an axis would expand a 29,070-draw contract and make callers responsible for a detail that should be automatic.

**Limitation.** A caller cannot directly force context through an override. It can reproduce it from the documented deterministic seed/sample schedule.
