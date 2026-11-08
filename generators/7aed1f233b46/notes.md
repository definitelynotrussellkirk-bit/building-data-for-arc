# Working notes: 7aed1f233b46

## 2026-10-02 review

The imported `1.5.0` generator had drifted away from the canonical task. It drew
wide panels separated by color-9 columns and filled every candidate as an already
solid rectangle. The selected rule instead compares sparse colors after
row-closure followed by column-closure. The old distribution therefore removed
the rule's counterfactual and made the task solvable by unrelated shortcuts.
Measured baseline evidence is under `checks/before/`: five of twelve battery
stages failed, including exact canonical-profile support `0/60`.

Version `2.0.0` replaces the panel ontology with canonical-scale sparse scenes.
A deterministic five-slot schedule cycles through:

1. `canonical_corners` — minimal four-corner winner;
2. `dense_decoy` — a more populous decoy defeats “most cells”;
3. `larger_decoy` — a larger-bbox decoy defeats “largest bbox”;
4. `extra_winner` — a six-cell winner defeats “exactly four cells”;
5. `position_decoy` — a left/top decoy defeats position selection.

Winner color is scheduled across 2, 3, and 4 so fixed-color selection also fails.
Every consecutive five-example lesson contains all profiles. The generator now
exports a source-pinned rule hash, pure Python rule mirror, strict and ordinary
validators, named semantic witnesses/rivals, lesson identifiability, exact axis
observation, unknown-override rejection, and an exact finite output codomain of
24 cyan rectangle sizes (`4` heights × `6` widths).

Regression coverage is in `tests/test_generator_7aed1f233b46.py`; the reusable
semantic census is `workspace/shortcut_probe.py`. Final evidence: 27 focused
tests pass, the shortcut probe finds no surviving five-demo rival, and all 12
battery stages are green. No Racket/canonical authority was edited.

## Known limits

- The output alphabet is intrinsically finite and monochrome, so output uniqueness
  is low even though all 24 lawful shapes are reachable.
- The named rivals cover the strongest simple shortcuts visible in the canonical
  examples; they do not prove that every possible learned heuristic is excluded.
- Default scenes use the canonical three nonzero colors. Four-color scenes are
  available only as an override-contract stress case, not as canonical training.
## Current reviewer considerations

Source SHA-256: `8611cbb884c2babafac47be4e66e6ed1d96f42fee51c2da02143b41e4723d3ea`.

# Design decisions: 7aed1f233b46

## 1. Remove panels and color-9 dividers

**Original state/rationale.** The imported comments claimed panels were part of
the rule and said solid rectangles were introduced to increase output diversity.
No retained evidence justified that ontology. The canonical inputs contain no
panel dividers and no color 9.

**Decision.** Remove panels and place independent sparse colors in one canonical-
scale grid.

**Rejected alternative.** Keeping panels but changing their motifs to sparse
shapes would still teach segmentation cues absent from the source task and would
continue failing exact-profile support.

**Probe.** Before profile support was `0/60`; after support is `60/60`.

## 2. Preserve exact canonical input profiles

**Decision.** Default shapes are exactly `(8,12)`, `(8,13)`, and `(9,12)`, each
with background plus three candidate colors.

**Reason.** Shape, palette count, and open-grid layout are relevant nuisance
variables. Expanding them before restoring source support would spend examples on
a distribution shift rather than the rule.

**Limitation.** This deliberately does not explore much larger canvases. Such an
extension should be evaluated separately, after source-faithful lessons are
stable.

## 3. Make double closure necessary

**Decision.** The winner is sparse, spans at least two rows and columns, and gains
cells under row-close then column-close. Decoys are constructed so their double
closure is not their full bounding rectangle.

**Rejected alternatives.** Already-filled rectangles, one-cell candidates, and
single-row/single-column candidates were rejected because they make closure a
no-op or leave the intended operation underdetermined.

**Probe.** `self_check` rejects no-winner, multiple-winner, and no-added-cell
impostors; canonical examples pass the same Python mirror.

## 4. Use a five-profile counterexample curriculum

**Decision.** Cycle `canonical_corners`, `dense_decoy`, `larger_decoy`,
`extra_winner`, and `position_decoy`. Winner colors are scheduled across 2, 3,
and 4. Every consecutive five-example window therefore contains explicit
counterexamples to five shortcuts that fit every public example.

**Rejected alternative.** Independent random profile sampling could leave a
small lesson with no counterexample even when the pooled corpus looked healthy.
A deterministic cycle gives a falsifiable lesson-level guarantee.

**Probe.** The semantic gate found all `12/12` sampled lessons identifiable; the
workspace census found no surviving rival across any sliding five-demo window.

**Limitation.** Named rivals are not exhaustive. New empirically observed model
shortcuts should be added as competitors and given a scheduled witness.

## 5. Keep the full lawful output-size range

**Decision.** Winner height is `3..6` and width is `3..8`, drawn over the full
range in every difficulty band. This yields an exact 24-output codomain.

**Original failed attempt.** Difficulty-skewed integer draws compressed the easy
band to only five output shapes. A regression test caught this before final
verification.

**Rejected alternative.** Adding output noise or preserving input colors would
raise uniqueness but change the canonical rule. Declaring and exhausting the
finite codomain is the honest fix.

## 6. Keep default candidate count canonical; stress it by override

**Decision.** Defaults use three nonzero colors. `n_colors=4` remains a valid,
observable override for contract and robustness testing.

**Reason.** Canonical training support should dominate defaults; a fourth color is
useful for testing that the solver is not hard-coded to exactly three candidates.

**Limitation.** Four-color scenes do not pass `strict_canonical_like` and are not
part of normal training draws.

## 7. Make every control observable and reject lies

**Decision.** Limit `AXES` to `scene_profile`, winner dimensions, candidate count,
and winner color. `observe_overrides` recovers all five from the realized grid;
unknown and out-of-range overrides raise.

**Rejected alternative.** Retaining generic `palette_kind`, `texture`,
`position_bias`, and `density` metadata would repeat the baseline's dead axes and
inflate the override matrix without adding degrees of freedom.

**Probe.** The focused suite exercises endpoint combinations in all three bands;
the battery accepted all `16,020` contract draws with no finding.

## 8. Pin source semantics in executable hooks

**Decision.** Add `RULE_HASH`, pure `rule_mirror`, ordinary and strict validators,
semantic witnesses, declared rivals, and lesson identifiability.

**Reason.** Comments can drift. Executable hooks let the battery compare generated
inputs, canonical examples, intended outputs, and shortcut claims directly.

**Rejected alternative.** A prose-only summary would not have caught the imported
panel/solid-rectangle collapse.

## 9. Do not edit Racket authority

**Decision.** Keep the selected canonical Racket program unchanged.

**Reason.** The rule matches all canonical examples; the defect was entirely in
the generator distribution and its missing contracts. Both Racket-specific
battery stages are green after the generator-only repair.

## 10. Leave reusable diagnostics

**Decision.** Add task-local tests and `workspace/shortcut_probe.py`.

**Reason.** Future changes need a cheap way to detect semantic drift before a full
battery. The probe reports validators, profile coverage, output shapes, per-rival
witnesses, and sliding-window survivors in machine-readable JSON.
