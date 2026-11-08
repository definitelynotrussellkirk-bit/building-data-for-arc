# Current notes: dd6724624b9f

## Intended rule

The two nonzero cells at the start of row 0 are controls. `grid[0][0]` is one of six transform codes and `grid[0][1]` is the output color. Clear the controls, crop the sole 4-connected monochrome body, apply:

1. identity
2. left/right reflection
3. up/down reflection
4. clockwise rotation
5. 180° rotation
6. counterclockwise rotation

Then recolor every occupied output cell to the requested color. The selected Racket authority was not changed; generator `3.0.1` is pinned to `RULE_HASH = 8dd08a5ab5cb`.

## Current design

Five exact observable axes are public: canvas height/width, transform code, body-cell count, and color-pair index. Explicit overrides use the full public domains in every band. Odd sample slots use canonical-size anchors; even slots cycle the complete dimension domains. Body size carries difficulty (easy 3–4, medium 5–6, hard 7–8). Transform codes follow a six-slot ordered schedule.

Shapes come from cached complete fixed-polyomino sets through eight cells. Nonidentity candidates must make the canonical branch visible and disagree with the stale `2.1.0` table. Declared rivals cover the stale table, omission of code 6, and failure to recolor.

## Decisions and reversal

A temporary `LESSON_SCHEDULE_PERIOD = 6` declaration was removed. Although every ordered six-demo window covers all codes, arbitrary query rotations can remove the sole example of one code. The exhaustive near-final census passed 18/18 production lessons but found 15/126 ambiguous rotations, and the shared receipt requires blocking rotations for a declared period. The final contract is therefore explicitly ordered-only, with task-local start-window tests and diagnostic rotation reporting.

## Verification and limits

Final source SHA-256: `ba007156605bde9b4a2b797f8e7585b858f979ba2abedce28706c02bb383b188`.

- 41/41 task tests pass.
- 12/12 battery stages are green.
- 55,260/55,260 override draws pass with zero findings.
- 12/12 production lessons are identifiable.
- 9/84 arbitrary query rotations are ambiguous; this is the known ordered-curriculum limit, not hidden.

Independent test support lives in `workspace/reference_probe.py`. Full rationale is in `DECISIONS.md`; retained failures and final receipts are under `checks/`.
## Current reviewer considerations

Source SHA-256: `ba007156605bde9b4a2b797f8e7585b858f979ba2abedce28706c02bb383b188`.

# Decisions for dd6724624b9f

## D1 — Treat the selected Racket rule as authority

**Prior choice:** generator `2.1.0` used a five-code table. Its original rationale is not recorded beyond the stale summary/comments.

**Decision:** pin rule hash `8dd08a5ab5cb` and implement the six authority branches exactly. Do not change Racket source or canonical labels.

**Alternatives rejected:** preserving the five-code table for backward compatibility, or inferring transforms only from the public examples. Both would continue producing mislabeled data and leave code 6 untrained.

**Probe:** the independent transform implementation in `workspace/reference_probe.py` matches every labeled canonical pair and every branch in the task-local test suite.

**Failure mode guarded:** a future table reorder or omitted branch makes `test_rule_pin_and_exact_six_code_table` fail.

## D2 — Replace decorative axes with exact observable controls

**Prior choice:** the baseline declared palette, density, position, and texture axes, many fixed or aliases, while dimensions were narrowed inside difficulty branches.

**Decision:** expose only `grid_h`, `grid_w`, `transform_code`, `body_cells`, and `color_pair`; provide `observe_overrides`; reject unknown keys and invalid scalar types; keep all Cartesian combinations legal in all bands.

**Alternatives rejected:** retaining compatibility aliases, silently clamping values, or declaring band-specific valid ranges. Those choices make exact interventions unfalsifiable or contradict the public `AXES` domain.

**Probe:** the final override checker exhausts 614 cases × 30 seeds × 3 bands = 55,260 draws with zero findings.

**Known limit:** `color_pair` is an index into a documented finite palette rather than two separately controlled colors. This avoids incompatible color/code collisions in ordinary draws while preserving eight exact pairs.

## D3 — Generate from complete fixed-polyomino domains

**Prior choice:** random growth plus a small fallback bank. The rationale appears to have been diversity and crash avoidance, but it did not guarantee semantic visibility.

**Decision:** enumerate all translation-normalized fixed polyominoes for sizes 3–8, filter by canvas fit and semantic witnesses, then sample deterministically through the generator context. Cache pure domains.

**Alternatives rejected:** a larger hand-written bank (still brittle) and rejection sampling random walks (slow and difficult to prove complete).

**Probe:** all generated nonidentity shapes differ under canonical and stale tables; 1,000 formerly expensive worst-case generations complete in roughly one second after caching.

**Failure mode guarded:** symmetric shapes hiding a code, skinny line-only bodies, or code/table pairs that accidentally produce the same output.

## D4 — Use a six-demo ordered curriculum

**Prior choice:** four examples with random codes and a comment claiming at least three distinct transforms were enough.

**Decision:** set `EXAMPLES_NEEDED = 6` and schedule code `sample_index % 6 + 1`, so every ordered six-demo window contains all six branches. `lesson_identifiable` verifies labels and refutes all declared rivals.

**Alternative rejected:** random transform draws. It cannot guarantee code 6 or eliminate the “five codes only” shortcut in each lesson.

**Limitation:** arbitrary query rotations are not guaranteed identifiable because holding out the sole code example removes that branch. Final diagnostics report 9/84 ambiguous rotations; production remains 12/12 identifiable.

## D5 — Reverse the schedule-period declaration

**Prior intermediate choice:** declare `LESSON_SCHEDULE_PERIOD = 6` after proving all six start residues cover all codes.

**Reversal:** remove the declaration. The shared schedule receipt treats a declared period as a claim that all query rotations are blocking-safe, while this curriculum intentionally supports ordered production only.

**Evidence:** `checks/final-v4-schedule-census.json` reports 18/18 ordered lessons identifiable and 15/126 rotations ambiguous; `checks/final-v4-semantic-with-schedule/checks/dd6724624b9f_after_semantic_gate.log` rejects the diagnostic rotation policy.

**Current choice:** retain task-local exhaustive start-window tests and document the ordered-only contract without overclaiming shared period metadata.

## D6 — Interleave canonical anchors with full dimension coverage

**Prior intermediate choices:** first, difficulty-only size bands; then canonical anchors in every ordinary draw. The former triggered axis-span lint; the latter left much of the declared domain reachable only by overrides.

**Decision:** odd slots use band-specific canonical anchors; even slots cycle every height 8–16 and width 9–17 over 18 slots. Explicit overrides remain legal everywhere.

**Alternatives rejected:** shrinking public domains to the canonical envelope, or relying only on overrides for large/small sizes.

**Probe:** `test_even_curriculum_slots_cover_every_declared_grid_dimension`, the profile-floor gate, and the distribution gate all pass.

## D7 — Keep audit targets unchanged

The two assigned audit generators were inspected only. Their current-source defects are reproduced in portable scripts and JSON evidence under `checks/audit/`; no source patch was made to either target.
