# Working notes: dee38d045bc9

## Current rule and authority

Fill every blank interior cell whose four diagonal neighbors are the same nonzero color with that color. Preserve all other cells; evaluate centers from the original input. The selected canonical/Racket authority was not changed. `RULE_HASH = 3de95ecac741`; reviewed generator v3.0.0 SHA-256 is `859652267ce3879e635f8e72d41ec23501a74e9c2240edb8414155fef4e83975`.

## Reversed decisions

The imported v2.0.1 generator used pairwise-distinct motif colors, lacked a rule binding and semantic lesson contract, and advertised controls that were not exact over the actual sampler. It was replaced with five observable controls and strict unknown/type/domain rejection. The strongest baseline shortcut—fill only colors appearing exactly four times—is now broken by shared-color scenes with two or three answer centers.

The first v3 attempt used three demonstrations. Ordered lessons passed, but required query rotation failed 23/48 positions. `EXAMPLES_NEEDED` was raised to five: a six-pair period gives each period-three critical witness twice, so every one-pair holdout retains support. Final smoke rotations pass 72/72 and the 300-lesson census passes 1,800/1,800.

## Distribution and assumptions

- Grid dimensions are 7–17; positive center count is 2–3.
- Positive colors are either all shared or pairwise distinct.
- Exactly one ordinary authored negative is drawn from mismatched diagonals, three-of-four diagonals, or blocked center.
- Authored negative footprints are disjoint from positives. Canonical incidental near-misses may overlap positives and remain lawful.
- At most one valid center receives an opposite equal-color orthogonal context pair, with a color different from its diagonal ring.
- Motif footprints and context cover every nonzero generated cell; no arbitrary noise is admitted.

## Evidence and tools

`workspace/reference_probe.py` is the portable future-agent probe. The retained full report checks 4 canonical pairs, 1,152 generated cases, and 228 lessons. `counterexamples/exact_four_occurrence_shortcut.json` is the minimal retained generated disagreement against the principal shortcut. Focused tests are under `tests/test_review_repair.py`.

## Known limits / open findings

The declared rivals cover ten concrete shortcut families and all final sampled lessons refute them, but this is finite hypothesis testing rather than a proof of unique induction. The grammar intentionally excludes arbitrary stray noise and supports only the documented orthogonal context form. No unresolved gate failure remains.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `859652267ce3879e635f8e72d41ec23501a74e9c2240edb8414155fef4e83975`.

# Decisions for `dee38d045bc9`

## D1 — Preserve the rule; replace the generator contract

**Prior choice:** v2.0.1 described the right diagonal-center rule but did not bind `RULE_HASH`, exposed axes that were not exact controls, and offered no executable teaching contract.

**New choice:** keep the selected canonical/Racket rule unchanged and rebuild only the Python generator, task-local tests, notes, workspace probe, and counterexample. The final source declares `RULE_HASH = "3de95ecac741"` and has SHA-256 `859652267ce3879e635f8e72d41ec23501a74e9c2240edb8414155fef4e83975`.

**Reason/evidence:** the canonical outputs and selected Racket authority already agree. The defect was support and instruction, not rule semantics. `checks/after-final/` shows rule smoke and authority sync green without editing canonical or Racket data.

## D2 — Expose only five exact, observable controls

Chosen axes are dimensions (`grid_h`, `grid_w`), positive-center count (`cross_count`), positive color relationship (`color_mode`), and controlled negative predicate (`texture`). Each is observable from returned pixels by `observe_overrides`; strict type, domain, and unknown-key checks happen before sampling.

Rejected alternatives:

- palette-choice/count controls were rejected because they can become nominal metadata without a unique pixel-level observation;
- placement strategy and density knobs were rejected because packing feasibility would create silent incompatibilities or approximate rather than exact controls;
- difficulty-specific narrower domains were rejected because they contradicted a single advertised axis domain and caused baseline override failures.

The final override sweep has no findings or warnings. Dimensions 7–17 were chosen because they cover all selected canonical shapes and leave room for two or three disjoint 3×3 motifs plus one negative control. Canonical-size anchors remain in the normal sampler so the profile floor is hit in every band.

## D3 — Separate authored negatives from canonical incidental near-misses

Canonical grids can create local partial/mismatched patterns where neighboring valid motifs interact. Treating every local near-miss as an authored negative would reject lawful canonical inputs; ignoring negatives entirely would hide key predicates.

The selected distinction is geometric: an authored negative has a 3×3 footprint disjoint from every active answer motif. Incidental overlap remains accepted and preserved. This definition is observable, compatible with all four canonical inputs, and lets strict generated scenes require exactly one controlled negative without rewriting the rule.

## D4 — Cross color reuse with all three negative textures

Shared colors are deliberately used for multiple valid centers. This breaks the strongest canonical shortcut—fill a color only when it occurs exactly four times—and also breaks one-center-per-color. The lesson schedule crosses `shared|distinct` with:

1. four nonzero but mismatched diagonals;
2. three matching diagonals plus one blank;
3. four matching diagonals around a nonzero center.

Rejected alternative: coupling shared colors to only one texture. That would teach a new texture-conditioned reuse rule. Three explicit conditional rivals are declared and every final census lesson refutes them.

## D5 — Add sparse orthogonal context rather than random noise

One sample in each period adds one equal-color opposite orthogonal pair around a valid center, using a different color from the diagonal ring. This refutes “fill only when orthogonals are blank” while retaining a recognizable, testable scene grammar.

Rejected alternative: arbitrary stray-cell noise. It would make strict validation ambiguous, allow malformed scenes to pass by accident, and could create unintended local motifs.

## D6 — Use five demonstrations, not three

Initial choice: `EXAMPLES_NEEDED = 3`. It passed the ordered production smoke but failed the explicitly required query-rotation gate: 23 of 48 held-out positions remained ambiguous (`checks/required-rotations/`).

Final choice: `EXAMPLES_NEEDED = 5`, yielding a six-pair episode. The core schedule has period three, so six pairs provide two occurrences of each critical texture/context phase. Holding out any one pair still leaves each required predicate represented. The final smoke gate passes 72/72 rotations, and the larger census passes 1,800/1,800.

Rejected alternatives:

- resampling only “unlucky” query positions would make the contract dependent on a fixed ordering and would not support arbitrary query rotation;
- adding more than five demonstrations would raise lesson cost without adding evidence needed by the tested rivals;
- weakening the rotation claim to diagnostic-only was unnecessary after the minimal five-demo repair passed.

## D7 — Keep canonical authority unchanged

No canonical row, base Racket solution, or shared runtime was edited. All selected-rule outputs were checked through the supported `arcpuzzles apply` path. The exact-four counterexample has three valid same-color centers; selected Racket output fills all three, while the rival fills none (`checks/shortcut-counterexample/`).

## D8 — Build a reusable task-local probe

`workspace/reference_probe.py` loads the generator through a portable repository-root search, obtains canonical pairs through public reviewer helpers, and enumerates the generator’s actual rival declarations rather than copying a stale name list. It checks canonical parity, generated determinism/self-check/override observation, and lesson identifiability.

The retained full run (`checks/probe-final.json`) covers 4/4 canonical pairs, 1,152/1,152 generated cases, and 228/228 lessons. This is intended for future agents and source replay, not as a replacement for Racket authority or the public battery.

## D9 — Preserve failures and limit claims

The incomplete baseline battery and the failed three-demo rotation gate are retained. Neither is relabeled as success. The final evidence establishes correctness over the selected authority, exact advertised controls, the declared semantic rivals, and sampled production support; it does not prove that no undeclared rival exists over the infinite task domain.
