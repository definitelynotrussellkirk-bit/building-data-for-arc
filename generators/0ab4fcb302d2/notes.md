# Working notes: 0ab4fcb302d2

## Current review — assignment `review-947387e6c956194f`

### Provenance and authority

This review started from approved generator SHA-256
`03fd288c9a5dff36f863a6b9761e480e842b090443af946c9710c9e91f5d4a2e`
(version 3.2.0). The earlier retained review `review-887d22ece756d563`
was used as a lead for the schedule rationale, strongest rivals, and the prior
duplicate-filter failure; every current claim was remeasured on this packet.
The canonical rule hash remains `39724c7d06e2`; no Racket authority or canonical
example changed.

### Reproduced baseline defect and repair

The current before battery was 11/12 green. `defect_lint` emitted 24 strict-call
warnings because `generate` and `schedule_profile` accepted booleans, floats,
strings, and `None` as seeds and accepted negative/non-plain sample indices.
Focused tests were written first and observed failing in
`checks/parametric/00-tests-red.log`. Version 3.2.1 adds one shared
`_validate_call`: seed must be a plain integer and `sample_index` a nonnegative
plain integer. The generator's lawful input distribution, schedule, axes,
canonical mirror, and Racket rule are otherwise unchanged. The minimal retained
case is `counterexamples/strict-scalar-contract.json`.

### Proposed parametric family

`workspace/parametric/prototype.py` is a separate **proposed/unapproved** authoring
prototype. It selects exactly once per episode:

- `diagonal_mapping` in `{match, opposite}`; and
- `block_size` in `{4, 3}`.

The default `(match, 4)` is byte-for-byte canonical (SHA-256
`10f2062065488ac615c7b7811a1a805e57c04041e558742f79ef69265b207c90`).
The other three sources are guarded transformations of that exact text. Inputs
remain the same mini-code; the first parameter changes the marker-to-output
diagonal relation, and the second changes each expanded block from 4x4/9x9 to
3x3/7x7 while retaining one-cell gutters. All labels and rival predictions are
real-Racket executions. Public episodes omit seed, parameters, rule text, and
query output; private evidence retains them with hashes.

Four retained seeds cover all four settings. Each episode has three
demonstrations and one query; every nonselected setting disagrees on all three
demonstrations and the query. Canonical replay is 3/3 and the shared witness has
four distinct outputs. Evidence: `checks/parametric/episodes-v1/report.json`.
This finite four-fixture matrix is not a production distribution, does not prove
universal identifiability, and does not alter approval or the production API.

### Final measurements

Final generator SHA-256 is
`c5fc561ed3181e490cedee7e7e06c981021d0af7f589b6cc68a732799b97ef0c`.

- After battery: 12/12 green (`checks/after/`).
- Portable selected task tests: 62/62 passed (`checks/task-tests-v2/`). The
  first foreground attempt was interrupted after 61 dots and remains honestly
  retained at `checks/task-tests/`; it is not counted as a pass.
- Parametric focused red/green subset: 18 failures before implementation, then
  18/18 passed (`checks/parametric/00-tests-red.log`,
  `checks/parametric/02-tests-green-attempt.log`).
- Production census: 300/300 lessons, three demonstrations plus one query each,
  1,200 pairs, 275 unique inputs, zero production ambiguities and zero of 1,200
  query-rotation ambiguities against the four declared rivals
  (`checks/lesson-census-v3_2_1.summary.json`).
- Post-repair visible-only solve: one revision, 3/3 visible examples; earlier
  rule exposure declared yes, reference consulted during solve no.

The production schedule was deliberately left unchanged: the large current
census reconfirms the earlier repair, and changing it during a parametric-priority
draw would add risk without a reproduced distribution defect. Finite declared
rivals remain evidence, not proof against arbitrary hypotheses.

## Historical retained notes from the prior review

## Review provenance

Assignment `review-887d22ece756d563` was evaluated from the pinned packet baseline. No prior return was used as evidence or copied as a lead; `evidence/associated_notes.jsonl` was empty. The original generator SHA-256 was `6867a657da561ba45dc647d028bbb94a904f74d388364101290a27bfa71e9c72` (version 2.0.1).

## Baseline defects

The before battery finished with 7 green stages, 1 advisory, and 4 failures:

- `lint`: missing canonical `RULE_HASH`; fake singleton `grid_h`/`grid_w` axes.
- `defect_lint`: aliases and degenerate `texture` values contradicted the stated lawful domain; difficulty bands were behaviorally dead.
- `override`: 2,979 findings across 13,230 draws, including malformed `gap_row` controls, invalid/off-domain textures, and silently accepted unknown keys.
- `authority_sync`: selected base `target_code` was semantically equivalent but not exact-text synchronized with the canonical Racket authority.
- `semantic_gate` was only advisory because no executable rival contract was declared.

The original rule smoke was already correct, so the semantic Racket rule did not need alteration.

## Strongest rival

The strongest plausible canonical-perfect shortcut is **gap parity**: ignore the red marker and use the main output diagonal iff the empty-row index equals the empty-column index. It fits all three canonical pairs. It fails on:

```text
0 0 0
0 3 2
0 3 3
```

Here both gaps are index 0, so the rival predicts main diagonal, while the red marker is the top-right cell of the remaining 2×2 code, so the intended rule predicts anti-diagonal blocks. `workspace/reference_probe.py` checks this with an independent pixel oracle and the task tests compare the oracle to the real Racket rule.

## Repair decisions

The repaired generator exposes only four exact pixel-observable axes:

- `gap_row ∈ {0,1,2}`
- `gap_col ∈ {0,1,2}`
- `marker_corner ∈ {0,1,2,3}` in row-major order within the non-gap 2×2 code
- `block_color ∈ {1,3,4,5,6,7,8,9}`

Unknown keys, wrong types, invalid difficulties, and out-of-range values fail closed. `_parse`, `self_check`, `observe_overrides`, `strict_canonical_like`, and `rule_mirror` share one exact structural contract. Difficulty changes sampling weights only; every band retains the full lawful support.

The declared rivals are `gap_parity`, `inverse_gap_parity`, `always_main`, and `always_anti`. The four schedule phases realize the complete intended-orientation × gap-parity truth table. Every phase uses a different marker corner, which makes a four-pair lesson duplicate-proof under the production sampler. The parity assignment flips with seed parity so each marker corner occurs with both equal and unequal gap indices across seeds.

## Retained failed attempt

Version 3.0.0 passed the small battery but failed the required production lesson census once in 1,200 query rotations. At medium lesson index 41, seed `3163466928`, requested sample 44 duplicated sample 43 and was rejected. The accepted sequence became 41, 42, 43, 45; holding out pair 43 left three main-diagonal demonstrations, so `always_main` survived. The full evidence is `checks/lesson-census.json`; a compact reproducer is `checks/review_analysis/lesson_census_failure_reproducer.json`.

A counterexample-only schedule was rejected because it would teach inverse gap parity. A fixed truth-table-to-corner mapping was also rejected because it would permanently correlate marker corner with gap relation. Version 3.2.0 addresses both failure modes.

## Authority decision

The canonical Racket program and rule hash were not changed. Only `racket_target.target_code` in the selected base authority record was exact-text synchronized to the canonical source; `raw_code` remains archival. Final authority synchronization and 120/120 real-rule smoke applications pass.

## Final evidence and limits

Final generator SHA-256: `03fd288c9a5dff36f863a6b9761e480e842b090443af946c9710c9e91f5d4a2e`.

- Final battery: 12/12 green (`checks/after-final/`).
- Portable focused tests: 44/44 passed (`checks/task-tests-final/`).
- Production census: 300/300 lessons materialized; 0 ordinary ambiguities and 0/1,200 rotated ambiguities; 279 unique inputs (`checks/lesson-census-final.json`).
- Independent probe: 2,000 draws, full declared support in all four bands, no validation or determinism failures, and each declared rival disagreed on exactly 250/500 draws per band (`checks/review_analysis/semantic_probe_v3_2_0.json`).

These finite rivals and sampled/cyclic probes provide strong evidence for the teaching contract, not a proof of unique induction over all conceivable rules.
## Current reviewer considerations

Source SHA-256: `c5fc561ed3181e490cedee7e7e06c981021d0af7f589b6cc68a732799b97ef0c`.

# Decisions for 0ab4fcb302d2

## D1 — Preserve the selected canonical rule and production curriculum

**Choice.** Keep rule hash `39724c7d06e2`, the four exact pixel axes, and the
version-3.2 truth-table schedule. No canonical Racket text, authority record,
output law, or sampling relation changed.

**Rationale and evidence.** The baseline already passed rule smoke, semantic
contract, profile, override, grammar, Racket lint, and authority synchronization.
The current 300-lesson census materialized every requested lesson and found zero
ordinary or query-rotation ambiguities among the four declared rivals. The prior
return `review-887d22ece756d563` was a useful lead, but the current evidence is
source-bound to final SHA-256
`c5fc561ed3181e490cedee7e7e06c981021d0af7f589b6cc68a732799b97ef0c`.

**Alternative rejected.** Changing the schedule or rule merely to make this draw
look larger would risk reopening a previously reproduced duplicate-filter defect
without addressing any current failure.

**Limit.** Four declared rivals and 300 sampled lessons do not prove unique
induction against all programs.

## D2 — Fail closed on keyed scalar arguments

**Choice.** Add a shared `_validate_call` used by both `generate` and
`schedule_profile`; accept only a plain integer seed and a nonnegative plain
integer `sample_index`. Bump the generator from 3.2.0 to 3.2.1.

**Original rationale or prior choice.** Unknown. The baseline delegated these
values to downstream operations and therefore silently accepted Python booleans,
floats/strings in some paths, and negative sample indices.

**Probe.** Two focused tests were written first. The red run recorded 18 expected
failures across the scalar matrix and absent prototype; the green run passed
18/18. The full before battery had 24 `defect_lint` warnings; the after battery
was 12/12 green.

**Alternatives rejected.** Coercion with `int(...)` would make `True`, `1.0`, and
`"1"` collide with valid keys, while modulo-wrapping negative sample indices
would conceal a caller error.

**Failure mode/limit.** Seed sign/range remains intentionally whatever the common
runtime supports; the reproduced gate required exact integer type, while only
sample indices are constrained nonnegative.

## D3 — Use `diagonal_mapping` as the semantic parameter

**Choice.** In the separate prototype, allow `match` (canonical) or `opposite`
for the relation between the red marker's local diagonal and the two output
blocks.

**Rationale.** This preserves the original object roles and core inference:
remove the empty row/column, read the red marker as a symbolic cue, and select an
output diagonal. It creates a meaningful contextual-gating alternative rather
than changing colors cosmetically.

**Alternatives rejected.** Varying the marker color or fill palette would be a
surface permutation, not a rule change. Randomly replacing the marker with an
unrelated cue would abandon the original reasoning pattern.

**Probe and limit.** Every authored fixture distinguishes `match` from
`opposite`, but the finite fixture set is not proof that every lawful input does.

## D4 — Use block size 4/3 as a structural parameter

**Choice.** Allow canonical block size 4 (9x9 output) and alternative block size
3 (7x7 output), preserving the single gutter selected by each input gap.

**Rationale.** The parameter changes the expansion factor while retaining the
same mini-code, spatial correspondence, and two-block construction. The
canonical default remains exact text, not a regenerated approximation.

**Alternatives rejected.** A block size larger than 4 adds cost without a new
reasoning distinction. A block size of 1 or 2 makes the output too small and the
expansion relation less legible. Variable gutter width would confound two
independent concepts in one parameter.

**Failure mode/limit.** Output dimensions reveal block size directly. That is
acceptable for a rule-family episode, but it should not be mistaken for a hard
latent-parameter inference benchmark.

## D5 — Select parameters once per episode and prove the demonstrations refute rivals

**Choice.** Map seeds 0–3 deterministically onto the four parameter settings,
choose once before all four pairs, and use a four-corner fixture truth table.
Each public episode has three labeled demonstrations and one unlabeled query;
private evidence evaluates every allowed setting with the persistent Racket
bridge.

**Rationale.** Episode-fixed parameters preserve a coherent rule. Holding out
each of two main/two anti fixtures leaves both orientations in the three
demonstrations. Size changes and mapping inversion make every nonselected
setting disagree on all three demonstrations and the query.

**Alternatives rejected.** Pair-wise parameter draws would create internally
inconsistent lessons. Python-generated labels were rejected because they would
not prove parity with the proposed Racket source. Random fixture search was
unnecessary for a four-setting bounded matrix and would make evidence less
reproducible.

**Limit.** The four authored fixtures are proposal evidence only, not a proposed
production sampler or training approval.

## D6 — Keep public and private parametric artifacts separate

**Choice.** Public JSON retains only train inputs/outputs and test inputs. Private
JSON retains seed, chosen parameters, exact Racket text and hashes, query output,
and every rival prediction. Evidence writing refuses overwrite and hashes every
member.

**Rationale.** This makes the challenge usable without leaking its hidden rule or
answer while preserving enough source-bound material for audit and replay.

**Failure mode/limit.** Redaction is schema-tested, but a future schema extension
must add its own forbidden-field checks rather than relying on field names alone.

## D7 — Retain interrupted attempts and stop after genuine success

**Choice.** Keep the first interrupted portable task-test directory and report it
as interrupted; count only the completed 62/62 rerun. In the post-repair solve,
stop after the first 3/3 visible pass rather than inventing a negative revision.

**Rationale.** Both choices preserve an honest process record. The solve is
explicitly marked as earlier-exposed and its private-query result remains
unknown.

## D8 — Keep both audit targets findings-only

**Choice.** Do not modify `c2badae666ad` or `6b1fe17a40a7`.

**Evidence.** Source-bound counterexamples are retained under
`checks/audit/<task>/counterexample.json`. The first generator omits a canonical
distractor and permits an all-nonzero-shapes shortcut; the second perfectly
correlates size rank with position rank and permits a position-order shortcut.
Both isolated audit presets also failed for missing semantic contracts and had
no selected tests.

**Rationale.** The assignment explicitly scopes code changes to `0ab4fcb302d2`;
audits are adversarial findings for later owners, not opportunistic cross-task
repairs.

## D9 — Verify the transported patch in a full fresh extraction

**Choice.** Build a candidate return, replay its exact source patch into a full
extraction of the original user ZIP, and rerun the complete selected task-test
stage from that replayed checkout.

**Evidence.** `checks/final-replay/replay.json` records a clean Git-root,
`git apply --check`, application, seven-path inventory, and final generator hash
`c5fc561ed3181e490cedee7e7e06c981021d0af7f589b6cc68a732799b97ef0c`
across all 90,295 extracted files. The first foreground test attempt was
interrupted and retained; `checks/final-replay/task-tests-v2/result.json` is the
completed 62/62 rerun.

**Rationale.** This distinguishes a locally working tree from a portable delta
that applies cleanly to the exact upload and still passes its selected tests.
