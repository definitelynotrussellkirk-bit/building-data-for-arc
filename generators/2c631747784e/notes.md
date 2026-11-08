# Current notes: 2c631747784e

## Intended rule and authority

On a cyan-8 background, all non-background cells form one simple non-branching 4-connected path. Walk from either endpoint, reverse the encountered color sequence, and repaint the same coordinates. The selected Racket authority is unchanged: `RULE_HASH=1b96d7f1e866`, canonical source SHA-256 `6094434f574e1496a23f55a73fd77fd917b53e91f3616393c3406c19b69882ab`.

Final selected generator SHA-256: `3ad4bb9784a8520161d14edac52ec73de6c4d7d6dd757e287ee676e87ab10f11`.

## Current input design

The generator retains the accepted induced-snake constructor and five exact controls: `grid_h`, `grid_w`, `path_length`, `n_distinct_colors`, and `anchor_corner`. Canonical anchors are scheduled while generalized dimensions and path lengths remain available. Assumptions enforced by `self_check` include one connected degree-1/2 path, 8–32 cells, 2–7 non-cyan colors, repeated color support, and a visibly non-palindromic sequence.

Known limit: this is a broad but bounded induced-snake family, not every possible self-avoiding path morphology.

## 2026-10-21 contract repair

The pinned baseline SHA `38d33c517fb4fbde1be861ef7cba7d071432c8c217f5d285bada09aeeb030b44` passed 10/12 battery stages. `defect_lint` found 120 scalar-coercion defects; `semantic_gate` rejected the declaration that all four partial rivals were canonical shortcuts.

Decision changes:

1. **Public scalar contracts tightened.** `seed`, `sample_index`, and integer axes now require non-boolean integers; `sample_index` must be nonnegative; difficulty is limited to `None/easy/medium/hard`; `anchor_corner` requires literal `bool`. Invalid coercions now fail loudly.
2. **Rival categories corrected.** Identity, row-major reversal, endpoint-only swap, and color sorting remain in `LESSON_COMPETITORS`. `CANONICAL_SHORTCUTS` is now empty because those rules do not fit every canonical pair.
3. **Valid generation preserved.** A source-bound replay of 51 valid calls—17 per difficulty, sample indices 0–16—matches the accepted baseline exactly. See `checks/valid_output_regression_reproduce.py` and `checks/valid-output-regression-v2.json` in the return.

Focused contract TDD: 43 expected failures before the repair; 49/49 focused tests after. Final portable task tests pass 54/54. The complete after battery is 12/12 green, with 22/60 exact-profile hits and 293/600 strict-canonical semantic hits. Production lesson smoke is 12/12 identifiable with three demos and one query; 48/48 diagnostic query rotations show no ambiguity.

## Parametric extension

`workspace/parametric/` contains an isolated **proposed prototype**, not a production change. Parameter `reverse_shift∈{0,1}` is chosen once per episode:

- `0`: exact canonical reversal;
- `1`: canonical reversal plus a one-position cyclic shift toward traversal start.

Both settings preserve path detection, endpoint selection, traversal, background, and coordinate-preserving repaint. Evidence covers seeds 0 and 1, one three-demo/one-query episode per setting. All labels were executed in Racket; all six demos refute the alternate setting; default matches all six labeled canonical pairs. Limits: two settings, two episodes, declared rival only, no production API or approval.

## Prior lead and open findings

Associated note `GNOTE-003642` and prior return `local-random-b5485cf89e20` were used only to understand existing design choices. Fresh checks measured the pinned baseline and final source.

No selected-task blocker remains. The inherited frozen test still warns about a legacy `scripts.canonical_profile_gate` import but passes in the portable 54-test run; migration is maintainer-owned. Historical archival raw-code authorities remain textually divergent but selected active authority is synchronized and execution parity passes.
## Current reviewer considerations

Source SHA-256: `3ad4bb9784a8520161d14edac52ec73de6c4d7d6dd757e287ee676e87ab10f11`.

# Decisions — 2c631747784e

## D1 — Preserve the canonical rule and geometry family

**Prior choice.** The accepted source generates one simple non-branching path on cyan 8 and reverses its color sequence in place. It uses a bounded induced-snake constructor with scheduled exact canonical profiles.

**Current choice.** Keep that transformation, constructor, axes, and Racket authority unchanged. The current review found contract and declaration defects, not a canonical-law or distribution failure.

**Rationale and probes.** The baseline already passed lint, self-check, rule smoke, distribution, profile floor, diversity, override, grammar, Racket lint, and authority sync. The final battery remains 12/12 green, and the valid-call replay matches the accepted baseline on 51/51 deterministic calls across all three difficulty bands. Replacing geometry would add risk without addressing the measured blockers.

**Evidence.** `checks/before/checks/2c631747784e_before_battery_summary.json`; `checks/after/checks/2c631747784e_after_battery_summary.json`; `checks/valid-output-regression-v2.json`.

**Known limit.** The generator intentionally covers a broad but bounded family of induced snakes rather than every possible self-avoiding path morphology.

## D2 — Reject scalar coercion at the public boundary

**Prior choice.** Generation delegated directly to context draws, allowing Python scalar coercions such as `True` or `8.0` to reach integer axes, and numeric/string surrogates to reach the boolean axis.

**New choice.** Require exact non-boolean integers for `seed`, `sample_index`, and integer axes; require `sample_index >= 0`; allow only `None`, `easy`, `medium`, or `hard` for difficulty; require a literal `bool` for `anchor_corner`.

**Rationale.** Exact controls are part of the generator contract. Coercion makes invalid calls observationally indistinguishable from valid controls, hides upstream data errors, and triggered 120 strict-scalar defect-lint findings.

**Alternative rejected.** Silently normalizing numeric strings, integral floats, or 0/1 booleans would preserve convenience at the cost of falsifiability. It was rejected because this generator is used to author training data, where loud invalidity is safer than implicit reinterpretation.

**Failure mode and limitation.** Existing callers that relied on coercion now receive `TypeError` or `ValueError`. Valid calls are unchanged; 51/51 replay cases match baseline.

**Evidence.** `generators/2c631747784e/tests/test_review_contracts.py`; `checks/tdd-red-contracts/result.json`; `checks/tdd-green-contracts/result.json`; `checks/valid-output-regression-v2.json`.

## D3 — Separate canonical shortcuts from lesson competitors

**Prior choice.** `CANONICAL_SHORTCUTS` aliased all four `SEMANTIC_RIVALS`.

**New choice.** Keep identity, row-major reversal, endpoint-only swap, and color sorting in `LESSON_COMPETITORS`; declare `CANONICAL_SHORTCUTS = {}`.

**Rationale.** A canonical shortcut must fit every usable canonical pair while differing elsewhere. These four rules are already refuted by canonical labels, so calling them canonical shortcuts is false metadata. They remain useful for checking whether generated demonstrations teach the intended rule.

**Alternative rejected.** Removing the rivals entirely would make the semantic gate less informative. Keeping them as lesson competitors preserves all witness and lesson checks without overclaiming canonical ambiguity.

**Evidence.** Before semantic failure in `checks/before/checks/2c631747784e_before_semantic_gate.json`; final semantic report in `checks/after/checks/2c631747784e_after_semantic_gate.json`.

## D4 — Add a reproducible valid-output replay tool

**Choice.** Add `checks/valid_output_regression_reproduce.py`, binding the accepted baseline source hash and comparing 17 calls per difficulty against the selected source.

**Rationale.** The repair is intended to reject invalid API values only. A source-bound replay is cheaper and more transparent than asserting by inspection that valid output bytes did not change.

**Schedule.** Difficulties `easy`, `medium`, and `hard`; sample indices 0–16; seed rule `910000 + 1000 * band_index + sample_index`. Final result: 51/51 equal.

**Limit.** This is a deterministic regression slice, not exhaustive equivalence over all valid seeds and overrides.

## D5 — Prototype one nearby rule parameter: `reverse_shift`

**Choice.** Build an isolated two-setting prototype:

- `0` (default): canonical path-color reversal.
- `1`: canonical reversal followed by a one-position cyclic shift toward the chosen traversal start.

**Why this parameter.** It changes the executed transformation while preserving the original recognition and reasoning sequence: detect cyan background, isolate the simple path, choose a deterministic endpoint, traverse, reverse, and repaint at the same coordinates. Only the final sequence alignment changes.

**Alternatives rejected.** Changing path size, placement, palette, or distractor frequency would vary inputs rather than the rule. Changing traversal direction is not meaningful for pure reversal because endpoint orientation cancels. Changing the background color is cosmetic. Adding rotation, translation, or object composition would create a different puzzle family.

**Episode policy.** Choose `reverse_shift` once as `episode_seed modulo 2`; hold it fixed across three demonstrations and one query. Public challenges omit the seed, parameter, Racket source, and query answer.

**Identifiability probe.** One episode per setting, seeds 0 and 1. Each episode has three demonstrations and one query. Exact Racket labels are used; all six demos distinguish the alternate setting, and all six labeled canonical pairs pass under setting 0.

**Status and limit.** **Prototype/proposed.** It is not wired into production or approval. Evidence covers two settings and two episodes only, and does not establish uniqueness against undeclared hypotheses.

**Evidence.** `generators/2c631747784e/workspace/parametric/README.md`; `checks/parametric/reverse-shift-v1/summary.json`.

## D6 — Retain the existing ordered three-demo lesson policy

**Choice.** Keep `EXAMPLES_NEEDED = 3` and the production order of three demonstrations followed by one query.

**Rationale.** The final semantic smoke materialized 12/12 identifiable lessons, four per difficulty, against all four declared competitors. Diagnostic query rotation checked all four positions for each lesson (48/48) with no ambiguity. There is no canonical shortcut that survives all canonical pairs, so the conditional requirement for a 100-per-band rival census was not triggered.

**Limit.** The 12-lesson smoke and 48 rotations are bounded checks, not a proof against every possible alternative rule. The prototype separately tests its one declared parameter rival.

## D7 — Treat the two audit targets as findings-only

**Choice.** Do not edit `8b5f756cc8ea` or `64dbf786fa7f`; retain source-bound reproducers and strict battery receipts.

**Rationale.** The assignment explicitly separates adversarial audits from the selected repair. Editing either audit source would mix ownership and invalidate the source-hash binding.

**Evidence.** `AUDIT.md`; `checks/audit/8b5f756cc8ea/`; `checks/audit/64dbf786fa7f/`.

## D8 — Prior evidence used as a lead, not as a current measurement

The accepted associated note `GNOTE-003642` and prior return `local-random-b5485cf89e20` were used to understand why the induced-snake geometry, canonical anchor schedule, Racket source, and semantic rivals existed. No prior pass claim was treated as evidence for the pinned baseline. All baseline and final verdicts in this return come from fresh source-bound runs.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/2c631747784e/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
