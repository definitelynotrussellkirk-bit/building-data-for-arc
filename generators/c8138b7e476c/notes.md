# Working notes: c8138b7e476c

## Review `review-7a1552f1e53a1388`

Baseline generator SHA-256: `a8c1b51d1dff2459895177692186a81ccaa0d5a5bbb04ed5693a2c38f84d099d`.
Final generator SHA-256: `aaa837a90551a68c63aa02f9bf7703ce31f9286565939b3130473185b614f3d4`.
Canonical rule hash: `df62a46d5c10` (unchanged).

The retained review `review-b669e671215aed9a:v0001` was used only as a lead.
Fresh baseline measurements reproduced ignored `grid_h`, accepted unknown keys,
off-center separator acceptance, dead texture aliases, missing `RULE_HASH`,
misstated axis ranges, zero canonical-profile support in the small profile-floor
sample, and absence of an executable semantic contract.

The repaired `3.0.0` generator exposes four exact constructive axes, validates
the complete source grammar, weights canonical-linked profiles, and guarantees
that reflection disagrees with the plausible copy-without-reversal shortcut on
every generated input. An independent oracle/rival/witness/lesson hook and 29
portable task tests were added.

Final evidence:

- 29/29 task tests passed.
- 12/12 official battery stages green.
- 600/600 semantic-gate draws were strict and witnessed vertical order.
- 300/300 production lessons and 1,200/1,200 required query rotations were
  unambiguous against the declared rival.
- The post-repair visible-only solve passed 3/3 demonstrations on the final
  generator bytes; prior rule exposure was declared honestly.

Known limit: finite checks against one declared plausible rival do not prove
unique induction against all programs. The distribution intentionally restricts
training support to centered odd-height grids and 2–4 source colors; those limits
are now explicit rather than accidental.
## Current reviewer considerations

Source SHA-256: `aaa837a90551a68c63aa02f9bf7703ce31f9286565939b3130473185b614f3d4`.

# Decisions for `c8138b7e476c`

## D1 — Replace the legacy surface with four exact axes

**Choice.** Keep only `grid_h`, `grid_w`, `cells`, and `n_colors`, with domains that are fully constructive and observable. Unknown keys and invalid values fail loudly.

**Original rationale.** Unknown. The baseline declared broad height/width/cell ranges, palette aliases, metadata-like axes, and degenerate textures, but several were ignored, dead, or outside regular task support.

**Alternatives considered.** Preserve every legacy name as a compatibility alias; retain diagnostic-only textures; silently clamp controls. Aliases would perpetuate ambiguity, negative fixtures do not belong in the ordinary training domain, and clamping makes requested experiments irreproducible.

**Probe.** The official override matrix, boundary tests in `tests/test_generator.py`, and `observe_overrides` verify exact realization in all difficulty bands.

**Failure modes / limits.** Strict rejection can break undocumented callers that relied on permissive behavior. That is intentional contract tightening; the supported surface is now small and explicit.

## D2 — Use canonical-linked profiles plus lawful broad draws

**Choice.** Weight three profiles matching canonical `(height, width, palette-count)` signatures—`(7,8,4)`, `(9,9,4)`, `(9,10,5)`—while retaining broader heights, widths, cell counts, and color counts.

**Original rationale.** The baseline's sampling rationale was undocumented. Its profile-floor run had zero exact canonical hits in 60 draws.

**Alternatives considered.** Emit only canonical shapes; ignore canonical profiles and maximize morphology diversity; hard-code the exact canonical grids. Canonical-only sampling is too narrow, unconstrained broad sampling loses distribution support, and memorized grids add no compositional value.

**Probe.** `test_default_distribution_contains_canonical_profiles` and the official profile-floor report. Final result: 29 exact hits in 60 draws with nonzero support in every band.

**Failure modes / limits.** This is profile support, not proof that frequency is optimal for Qwen3.5-9B. The weighting is a pragmatic curriculum prior and can be recalibrated from downstream learning curves.

## D3 — Guarantee a vertical-order witness structurally

**Choice.** Place one source cell in the top row and another in the row immediately above the separator, while forbidding the top cell's same-column near-separator partner. Fill remaining cells randomly.

**Original rationale.** Unknown. Baseline random placement could generate examples where vertical reversal was not visibly distinguished from copying rows in order.

**Alternatives considered.** Rejection-sample until the two rules differ; depend on one witness per multi-example lesson; add a special texture. Constructive placement is deterministic, cheap, and makes every individual example useful; rejection loops and schedule-dependent witnesses are less robust.

**Probe.** `SEMANTIC_WITNESSES['vertical_order_matters']`, task tests, semantic gate, and the 300-lesson census.

**Failure modes / limits.** The anchor pattern is a mild distribution signature. Column and color assignment remain randomized, and the task law—not anchor location—still determines the output.

## D4 — Validate the actual grammar, not just superficial counts

**Choice.** `self_check` now rejects malformed/ragged/non-ARC grids, multiple or missing full-9 rows, off-center separators, stray 9s, nonzero lower cells, empty source panels, and source colors outside 1..8.

**Original rationale.** Baseline validation focused on a subset of properties and returned success for an off-center separator.

**Alternatives considered.** Leave structural checks to the Racket rule; validate only generated samples; make `self_check` throw on malformed inputs. A public validator should be total and explain invalidity without requiring rule execution.

**Probe.** Focused malformed-grid and off-center tests, official self-check, grammar, and rule-smoke stages.

**Failure modes / limits.** `self_check` deliberately validates task grammar rather than every reviewed distribution axis; `strict_canonical_like` adds the narrower profile and witness requirements.

## D5 — Add an executable oracle, rival, and lesson hook

**Choice.** Declare true vertical reflection, the plausible `copy_top_in_order` competitor, the witness linking them, and a lesson hook that rejects a rival fitting all demonstrations but changing the query.

**Original rationale.** Baseline had no executable semantic contract; the small semantic gate was advisory.

**Alternatives considered.** Rely on prose; enumerate a large generic transformation library; add only an instance-level witness. Prose cannot gate exported lessons, a large generic library adds false positives and cost, and instance witnesses alone do not check actual lesson assembly.

**Probe.** Canonical parity, semantic smoke, synthetic survivor lesson in `checks/qwen9-rival-survival-counterexample.json`, and source-bound 300-lesson/1,200-rotation census.

**Failure modes / limits.** One named rival is not exhaustive program synthesis. Future evidence may justify additional task-specific rivals, but they should be executable and plausible rather than speculative.

## D6 — Keep the Racket authority unchanged

**Choice.** Do not alter the canonical rule. Pin existing rule hash `df62a46d5c10` in the generator.

**Original rationale.** Rule smoke and canonical outputs were already correct; defects were in sampling, validation, and teaching support.

**Alternatives considered.** Rewrite or duplicate the Racket rule; infer a new authority from generator behavior. Neither was justified and both risk authority drift.

**Probe.** Rule smoke, Racket lint, authority sync, all three canonical input/output pairs, and final battery hash binding.

**Failure modes / limits.** Authority sync reports an archival divergent copy, but selected execution parity passes. No archival source was edited in this assignment.

## D7 — Build portable regression tests before implementation

**Choice.** Add task-local tests using `reviewer_support.find_root`, `canonical_pairs`, and the `GENERATOR_UNDER_TEST` override used by the portable task-test harness.

**Original rationale.** No task-local regression suite existed.

**Alternatives considered.** Depend only on the broad battery; write fixed-depth repository paths; test only random samples. The battery did not directly encode all observed defects, fixed parent assumptions break return replay, and deterministic boundary tests give clearer failures.

**Probe.** Initial run produced 21 expected failures and 8 passes; final portable run produced 29/29 passes.

**Failure modes / limits.** Tests cover the repaired public contract and one principal rival, not every random seed. The official distribution and census tools provide complementary sampled evidence.

## D8 — Use prior review only as a lead, then remeasure current bytes

**Choice.** Use `review-b669e671215aed9a:v0001` from `evidence/review_index.json` as a hypothesis source, then reproduce every relied-on defect against baseline hash `a8c1b51d…`.

**Original rationale.** The packet explicitly marks retained reviews as leads rather than measurements of selected source.

**Alternatives considered.** Trust prior prose; ignore it entirely. Trusting it would conflate versions, while ignoring it would waste high-value diagnostic information.

**Probe.** Fresh before battery, focused override/validator probe, and red regression suite.

**Failure modes / limits.** Historical evidence may mention additional ideas not implemented here; only independently reproduced issues are claimed as baseline facts.

## D9 — Treat rotation support as required for this repaired sampler

**Choice.** Run the larger lesson census with `--rotate-query --rotation-policy require`, because every generated instance independently contains the vertical-order witness and downstream assembly can safely rotate any of the four pairs.

**Original rationale.** Baseline had no documented lesson/query policy.

**Alternatives considered.** Report ordered-production only; mark rotations diagnostic. Since the repaired generator makes each pair individually refute the named rival, requiring rotations is cheap and matches the actual support claim.

**Probe.** 300 production lessons, 1,200 unique pairs, and all 1,200 held-out query positions passed with zero declared-rival ambiguity.

**Failure modes / limits.** This certifies the sampled production schedule only against the declared rival. It does not enumerate all seeds or all possible hypotheses.
