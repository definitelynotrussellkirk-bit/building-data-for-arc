# Working notes: 0a9ee3cbb232

## 2026-10-04 review repair

The selected 3.2.0 sampler had no `RULE_HASH`, always used background 1, missed canonical-size support in the easy band, mixed helpful and degenerate texture labels, and exposed an acceptance-only `self_check`. Its default distribution did not guarantee examples that distinguish horizontal runs from 4-connected components, occupied rows, or overflow-dropping behavior.

Version 4.0.0 keeps the canonical transformation unchanged and rebuilds the sampler around four exact axes: canonical canvas profile, number of 3-runs, number of 2-runs, and background. A two-zone constructive layout realizes every advertised Cartesian combination without rejection. Default draws always include a vertically connected rectangle and two separated same-row runs; alternating draws exceed the six-cell tally. Structural witnesses use color 3 in overflow cases so truncation cannot hide their output effect.

The active selected `target_code` fields in the training and augmented base records were synchronized to the canonical program text. Archival `raw_code` was preserved. Execution parity and the declared rule hash remain unchanged.

Reusable probes live in `workspace/reference_probe.py` and `workspace/qualify.py`. Final evidence: 12/12 battery stages green, 29/29 portable task tests, 23,400/23,400 override-contract draws accepted, and 300/300 production lessons identified against all declared canonical-fitting rivals.
## 2026-10-21/22 review repair and parametric prototype

The pinned 4.0.0 sampler and canonical Racket authority were already semantically strong, but the fresh before battery found one public-API defect: `generate` accepted coercible or invalid scalar controls (`bool`, `float`, and string seeds; boolean/negative sample indices; and invalid difficulties). Defect lint reported 39 strict-scalar warnings. Version 4.0.1 now validates `seed`, `sample_index`, `difficulty`, and overrides before constructing the generation context. Exact integers are required, booleans are rejected, sample indices must be nonnegative, and difficulty is restricted to `None`, `easy`, `medium`, or `hard`. Three focused regression tests were written before the fix and initially produced 21 expected failures.

The canonical execution path and `RULE_HASH = "54a0bdf9c500"` remain unchanged. Final verification on generator SHA-256 `80ed7c2df14a6009a0322a6f3d81ea8e8297ebcd5a4438ea3baefa7052578b1c` produced 12/12 green battery stages, 53/53 portable task tests, and a 300-episode / 1,200-rotation lesson census with zero ambiguity, hook warnings, materialization errors, or scoring errors against the declared rivals.

A separate task-local prototype under `workspace/parametric/` adds one proposed episode-level parameter, `run_axis ∈ {horizontal, vertical}`. Horizontal is byte-for-byte the canonical/default Racket program; vertical changes only the direction used to count maximal color-3 and color-2 runs, preserving the original tally reasoning. The setting is fixed once per episode and omitted from the public challenge. At retained seed 20261021, both settings have three demonstrations plus one query; all 6/6 demonstrations and all 8/8 Racket-checked pairs distinguish the settings, and all five canonical pairs replay under the horizontal default. This is prototype evidence only: it does not change production axes, authority, approval, or training admission, and it tests only one nearby rival family at one retained seed.

The strongest canonical-fitting shortcut remains 4-connected component counting. It fits all five canonical labeled pairs but disagrees on the valid default draw `(seed=20261021, sample_index=0, difficulty=easy)`: canonical Racket returns `[[3,3,3],[3,2,2]]`, while the shortcut returns `[[3,3,3],[2,2,0]]`. The production sampler emits this discriminator directly; retained evidence is in `WORK/checks/shortcut/`.
## Current reviewer considerations

Source SHA-256: `80ed7c2df14a6009a0322a6f3d81ea8e8297ebcd5a4438ea3baefa7052578b1c`.

# Decisions: 0a9ee3cbb232

## D13 — Reject invalid public controls before generation context construction

**Choice.** Add task-local `_validate_request(seed, sample_index, difficulty, overrides)` and call it before `gen_ctx`.

**Rationale.** The fresh baseline was otherwise clean but accepted values that violate the public contract: booleans/floats/strings as seeds, booleans and negative integers as sample indices, and nondeclared difficulties. Allowing coercion makes reproducibility and override evidence ambiguous.

**Alternatives rejected.** Silent coercion was rejected because `True` and `1`, or `1.0` and `1`, become indistinguishable recipes. A shared `gen_ctx` change was rejected because it could alter unrelated generators and exceeds the selected-task scope. Validation after drawing was rejected because invalid recipes would already have influenced context construction.

**Probe and evidence.** Three test groups were added before implementation and produced 21 expected failures. The baseline defect lint recorded 39 warnings across easy/default/hard probes. After the fix, the same detector reports zero findings and all 53 portable task tests pass.

## D14 — Keep the canonical horizontal rule and authority unchanged

**Choice.** Retain `RULE_HASH = "54a0bdf9c500"`, the canonical Racket text, the sampler, and all production axes.

**Rationale.** Rule smoke, semantic gate, authority synchronization, canonical replay, and the large lesson census all pass. The defect was API validation, not task semantics.

**Alternative rejected.** Promoting connected-component counting or the new vertical variant would contradict the canonical written solution and generated Racket evidence.

## D15 — Prototype one nearby episode-level parameter outside production

**Choice.** Build `run_axis ∈ {horizontal, vertical}` under `workspace/parametric/`; choose it once per episode and hide it from the public challenge. Horizontal is the canonical default. Vertical changes only the direction of maximal-run counting while preserving color roles, count order, output shape, and truncation.

**Rationale.** This is the smallest rule parameter that preserves the original reasoning pattern and yields a meaningful, executable alternative. It tests whether demonstrations communicate the directional relation rather than a memorized tally.

**Alternatives rejected.** Swapping colors would alter fixed task-defined roles. Changing output dimensions or tally order would combine multiple mechanisms. Making axis a per-grid choice would destroy episode-level consistency. Adding the parameter to `AXES` now would mix experimental rule selection with production input controls and authority.

**Evidence.** Both exact Racket programs are materialized. At seed 20261021 each setting has three demonstrations and one query; all 6 demonstrations and all 8 retained pairs distinguish the other setting. Five canonical pairs replay under horizontal.

**Limitations.** One seed and one declared alternative do not establish broad learnability. Inputs are selected for disagreement, so this evidence measures constructibility and local teachability, not natural prevalence.

## D16 — Preserve the three-demonstration lesson policy

**Choice.** Keep `EXAMPLES_NEEDED = 3` and the alternating bounded/overflow schedule.

**Rationale.** The final source-bound census checked 100 episodes in each difficulty band. All 300 production lessons and every one of 1,200 held-out query rotations refuted the declared canonical-fitting rivals, with no materialization, hook, or scoring errors.

**Limit.** The finite census does not exhaust undeclared hypotheses or every possible seed.

## D17 — Name connected components as the strongest canonical shortcut

**Choice.** Use the task's declared `connected_components` rival in `QUESTION_ANSWER.md`.

**Rationale.** It is simple, visually plausible, and fits every retained canonical labeled pair. The repaired production generator deliberately contains vertically touching horizontal runs that make component count smaller than run count in a visible prefix.

**Evidence.** At seed 20261021, sample index 0, easy difficulty, canonical Racket returns `[[3,3,3],[3,2,2]]`; the rival returns `[[3,3,3],[2,2,0]]`. The input passes the generator-domain check.

## 2026-10-25 native parametric review

The earlier one-query run-axis prototype has been replaced by a native matched-
input family under `workspace/parametric/`.  `run_axis=horizontal` preserves the
selected canonical Racket program byte-for-byte; `run_axis=vertical` changes only
Step A.  Step A counts maximal runs of colors 3 then 2 along the episode-selected
axis, producing `(n3,n2)`; Step B consumes those counts in the unchanged 2×3
row-major tally with natural six-cell truncation.

The sampler supports 2–6 independently prefix-stable demonstrations and 1–4
prefix-stable queries from a privately shuffled four-query bank.  The first two
demonstrations constructively reject component, occupied-row, occupied-column,
cell-count, swapped-color, and denser/sparser-axis shortcuts in both settings.
The fourth query is a substantive 30×30 boundary-touching case with 151 colored
cells, horizontal counts `[3,3]`, and vertical counts above 60 for both colors.
A bounded audit covered 32 seeds, both settings, every supported count (1,280
episodes/public views), ten distinct count regimes, nine executable rivals, and
26 protected-Racket evaluations with no findings.  Native qualification passed
on seeds 0 and 17 with 3 demonstrations, 4 queries, and 40 protected-Racket
labels.  A source-bound wrong-count witness received reviewer replay and an
independent recheck.  Owner acceptance, canonical approval of the vertical
variant, measured training benefit, and training admission remain pending.
