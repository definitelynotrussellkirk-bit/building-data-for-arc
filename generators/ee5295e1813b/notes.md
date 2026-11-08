# Working notes: ee5295e1813b

## Current rule and authority

Fill each blank interior cell exactly when its four diagonal neighbors are the same nonzero color, using that color; preserve all other cells and evaluate all centers from the original input. The selected canonical/Racket authority was not changed. `RULE_HASH = ff3c83fdb4d7`; reviewed generator v3.0.0 SHA-256 is `2687dcacbd7fa1b7bf9fbb4162cf54cea15f2236bf05970da5c21ac3ae736aa4`.

## Reversed decisions

The imported v2.1.0 source described the right local rule but did not bind `RULE_HASH`. It exposed ten axes, while several were ignored, one-value metadata, aliases, or incompatible with difficulty-specific draw ranges. Degenerate `texture` branches returned fixed-size scenes and bypassed normal controls; capped random placement could silently miss requested negatives. The repair replaces that surface with five exact, observable controls and rejects unknown, mistyped, or out-of-domain overrides.

The prior ordinary sampler taught only positive diamonds plus partial/mismatched distractors. The repair adds a nonzero-center negative, shared-color positives, and sparse orthogonal context. Those cases falsify plausible shortcuts that fit every canonical pair: one center per color, “color occurs exactly four times,” ignore diagonal equality, accept three-of-four, overwrite a nonzero center, and require blank orthogonals.

No prior review return was adopted. The current derived assignment/catalog was the defect lead. The mature same-rule generator `dee38d045bc9` was used as an implementation pattern, then rebound to this task’s authority, canonical dimensions `(7×8, 8×8, 9×9)`, IDs, tests, and evidence.

## Distribution and assumptions

- Grid dimensions are 7–17; active-center count is 2–3.
- Active colors are either all shared or pairwise distinct.
- Each ordinary grid contains exactly one disjoint controlled negative: three matching diagonals, four nonzero mismatched diagonals, or four matching diagonals around a nonzero center.
- At most one valid center carries an opposite equal-color orthogonal context pair, using a color different from its diagonal ring.
- Recognized 3×3 motif footprints are disjoint, and motif/context cells cover every nonzero generated cell.
- Canonical inputs may contain incidental overlapping near-misses; `strict_canonical_like` accepts them while generated authored controls remain disjoint.

## Teaching contract

`EXAMPLES_NEEDED = 5`, so a lesson has five demonstrations plus one query. The production schedule has period three; in any six consecutive samples each negative texture appears twice, shared-color evidence appears four times, and orthogonal context appears twice. Holding out any one pair therefore retains evidence against all ten declared rivals. This is checked both by focused exhaustive cyclic-start tests and by the shared rotated lesson census.

## Evidence and reusable tooling

- Baseline battery: 7 green, 2 advisory, 3 failed (`lint`, `defect_lint`, `override`).
- Final battery: 12/12 green under `WORK/checks/after/`.
- Canonical profile floor: 31 exact hits and 52 envelope hits in 60 draws, with exact support in every band.
- Focused portable task tests: 36/36 passed under `WORK/checks/task-tests-final/`.
- Rotated lesson census: 300/300 lessons materialized, 1,800/1,800 rotations checked, zero ambiguity, 1,800 unique inputs (`WORK/checks/lesson-census.json`).
- `workspace/reference_probe.py` is the future-agent source-local probe. Its full run passed 3/3 labeled canonical pairs, 1,152/1,152 generated cases, and 228/228 lessons (`WORK/checks/probe-final.json`).
- `counterexamples/fill_colors_occurring_exactly_four_times.json` is the retained generated disagreement against the principal global-frequency shortcut. The selected Racket authority fills both repeated-color centers; the rival fills neither (`WORK/checks/shortcut-counterexample/racket.json`).

## Known limits / open findings

The finite rival set and sampled census do not prove unique induction over every conceivable rule. The grammar intentionally excludes arbitrary noise and supports only the documented orthogonal context form. Authority synchronization reports the selected canonical rule synchronized while one archival raw-code copy remains divergent; selected execution parity passes and that archival source was not edited. Catalog training approval remains outside this review and is not claimed.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `2687dcacbd7fa1b7bf9fbb4162cf54cea15f2236bf05970da5c21ac3ae736aa4`.

# Decisions for `ee5295e1813b`

## D1 — Preserve the selected authority

- **Prior choice:** the source described the intended transformation but did not pin its authority.
- **Decision:** add `RULE_HASH = "ff3c83fdb4d7"`; leave canonical data, selected Racket code, and the archival base record unchanged.
- **Reason:** the selected canonical and task-rule authorities already agree and solve all three labeled pairs. The defect was generator binding and teaching support, not the transformation.
- **Evidence:** `checks/after/checks/ee5295e1813b_after_authority_sync.json`.
- **Rejected alternative:** rewriting the archival divergent `raw_code`. It is outside the task-local repair and execution parity already passes.

## D2 — Replace misleading controls with five exact axes

- **Prior choice:** ten axes mixed real controls with aliases, ignored values, and one-valued declarations (`palette_kind`, `diamonds`, `n_neg`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, `texture`, dimensions).
- **Decision:** expose only `grid_h`, `grid_w`, `cross_count`, `color_mode`, and `texture`.
- **Reason:** every retained axis changes observable pixels and is exactly recoverable by `observe_overrides`; invalid keys/types/domains fail loudly.
- **Evidence:** 36 focused tests and the final `override` battery stage; `checks/task-tests-final/result.json` and `checks/after/checks/ee5295e1813b_after_battery_summary.json`.
- **Rejected alternative:** keeping compatibility aliases. That would preserve ambiguity and permit accepted requests whose returned pixels do not prove the requested value.

## D3 — Construct disjoint motifs instead of relying on fallback placement

- **Prior choice:** randomized placement and fallback could silently produce fewer requested negatives or interactions between motifs.
- **Decision:** backtracking-pack `cross_count + 1` disjoint 3×3 footprints, author positives and one negative, then validate and retry deterministic layouts only when an accidental cross-boundary predicate appears.
- **Reason:** counts, separation, and rule opportunities become structural rather than probabilistic.
- **Evidence:** `self_check`, exact override tests, 1,152-case probe, and 600/600 strict semantic-gate draws.
- **Rejected alternative:** post-hoc deletion of accidental motifs. It would make requested axes harder to observe and could introduce output-dependent construction.

## D4 — Use three condition-specific negative textures

- **Decision:** retain `partial_diagonals`, `mismatched_diagonals`, and add `blocked_center`.
- **Reason:** together they teach all four arms, equality of arm colors, nonzero arm color, and the blank-center precondition. Each is a separate observable axis value and a direct rival witness.
- **Evidence:** semantic witnesses/rivals in `generator.py`; every texture/color-mode profile appeared in the 600-draw semantic census.
- **Rejected alternative:** `no_diamonds`. A scene with no positive action teaches little about which predicate caused a fill and bypassed ordinary controls in the old implementation.

## D5 — Cross shared/distinct color modes with every texture

- **Decision:** schedule one distinct-color residue and two shared-color residues per three samples, independently of texture.
- **Reason:** canonical examples use each color on one center, allowing both “one center per color” and “fill only colors occurring exactly four times” shortcuts. Shared-color positives force multiple same-color fills, while independence from texture refutes scene-gated reuse rules.
- **Evidence:** `counterexamples/fill_colors_occurring_exactly_four_times.json`, `checks/shortcut-counterexample/racket.json`, and the 300-lesson census.
- **Rejected alternative:** random color reuse without a schedule. It can leave a five-demo lesson with no repeated-color witness.

## D6 — Add recognizable orthogonal context, not arbitrary noise

- **Decision:** one seed-dependent residue per three samples places an equal-color opposite north/south or west/east pair around one active center, using a color different from its diagonal ring.
- **Reason:** it refutes “all orthogonals must be blank” without making arbitrary stray cells part of the accepted grammar.
- **Evidence:** focused six-pair rotation test and semantic witness `orthogonal_context_pair`.
- **Rejected alternative:** unrestricted random noise. It creates many unenumerated local predicates and weakens exact validation.

## D7 — Use five demonstrations and support every query rotation

- **Decision:** set `EXAMPLES_NEEDED = 5`, making six-pair episodes. Textures, shared colors, and context each have duplicate support within every six consecutive samples.
- **Reason:** after any one pair becomes the query, the remaining five demonstrations still refute all declared rivals.
- **Evidence:** exhaustive focused cyclic starts and query positions; shared census of 300 lessons and all 1,800 rotations, zero ambiguity (`checks/lesson-census.json`).
- **Rejected alternative:** three demonstrations. One held-out pair could remove the sole witness for a texture or context-dependent rival.

## D8 — Anchor canonical scale while retaining broader dimensions

- **Decision:** use the repeating shape schedule `(7×8, 8×8, 9×9, 7×8, broader difficulty-aware draw)` unless dimensions are explicitly overridden.
- **Reason:** the baseline profile floor had only 1/60 exact and 9/60 envelope hits with zero exact support in medium/hard. The new schedule makes canonical-scale support routine while preserving 7..17 exact dimension overrides and broader draws.
- **Evidence:** final profile floor 31/60 exact and 52/60 envelope, exact support in all bands (`checks/after/checks/ee5295e1813b_after_profile_floor.json`).
- **Rejected alternative:** canonical shapes only. It would overfit dimensions and erase useful spatial variation.

## D9 — Treat validation, rivals, and probes as source-local maintainability features

- **Decision:** add focused portable tests, semantic contracts, a retained shortcut counterexample, and `workspace/reference_probe.py`.
- **Reason:** future agents can distinguish authority, construction, override, lesson, and shortcut failures without reconstructing this review session.
- **Evidence:** 36/36 staged tests; probe 3/3 canonical, 1,152/1,152 generated, 228/228 lessons.
- **Rejected alternative:** report-only evidence. It would not travel with or guard later source edits.

## D10 — Keep the accepted teaching grammar intentionally bounded

- **Decision:** accept rectangular 7..17 grids containing two or three disjoint positive motifs, zero or one disjoint recognized negative, shared or pairwise-distinct active colors, and at most one recognizable orthogonal context pair; reject unexplained nonzero cells.
- **Reason:** strict validation makes every authored cell explainable and keeps rival checks meaningful.
- **Limit:** this is not the full mathematical domain of the local Racket rule. Arbitrary noise, overlapping motifs, one-positive scenes, and other context forms remain outside the generator grammar.
- **Evidence:** `self_check`, `strict_canonical_like`, semantic gate, probe, and final review self-check.

## D11 — Audit without modifying audited tasks

- **Decision:** retain a concrete even-dimension midpoint witness for `ee6a99e8b7f9`; report no issue for `9a7579840f41` after finite canonical/generated/rotation/Racket checks.
- **Reason:** the audit assignment asks for adversarial evidence, not opportunistic repairs.
- **Evidence:** `AUDIT.md` and `checks/audit/<task_id>/`.

## Parametric family review — 2026-10-25

The reviewed v3.0.0 base generator and exact canonical program were retained. The
native family adds episode-fixed `composition` with `fill_centers` as the exact
canonical/default program and `connect_equal_centers` as the composed alternative.
Step A derives and fills valid diamond centers. Step B consumes those
input-dependent `(row, column, color)` anchors and connects aligned equal-color
centers through zero cells. The grammar includes blocked, partial, mismatched,
and orthogonal-context negative controls. Streams are setting-independent,
independent, and prefix-stable for 2–6 demonstrations and 1–4 queries; the fourth
query is a substantive 30×30 scene with seven authored relay pairs.

A shared packet-tool defect was isolated: `review_base_preflight._base_checks`
iterates singleton canonical `test` mappings as strings, although 148 canonical
rows use that supported storage form. `workspace/parametric/preflight_compat.py`
normalizes only the in-memory pair container, delegates every other check to the
shared preflight, and preserves the raw canonical-record hash. A focused red→green
regression covers the normalization.

Retained evidence:

- 51/51 focused target tests passed, including a protected-Racket regression that
  proves the wrong-intermediate program preserves step A's center fills and
  corrupts only step B's anchors.
- The source-local audit passed 12 seeds, 480 count/setting episodes, and 120
  full-bank pairs; all 120 shifted-anchor ablations disagreed.
- Authoring preflight passed all three original labels, both ordinary staged
  draws, both settings, four jobs, and 32 protected-Racket evaluations.
- The 30×30 causal witness contains 15 derived centers and seven relay pairs;
  shifting only step B's anchors changes the final output.
- Public projection produced 16 independent one-query views; four first turns
  passed 24 private-field invariance checks and four positive controls.

This is reviewer-ready authoring evidence only. Exact-source owner review, native
qualification, fresh acceptance, and any training admission remain separate.
