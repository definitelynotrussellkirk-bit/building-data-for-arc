# Working notes: 144582f287b5

## Intended rule

Read the four fixed source cells `(1,1)`, `(1,2)`, `(2,1)`, and `(2,2)` in row-major order. Preserve the input shape, copy those four values to the four output corners in the same order, and set every other output cell to `0`. The selected canonical rule hash is `acb1a0ae5f73`.

## Review repair (assignment review-4d1bbf602e4954b4)

The imported v2 generator ranged over 4–14 rows/columns and broad noisy textures. That changed the task's visible scale (median generated area about 70 versus canonical area 16), made the transformation affect under 10% of cells on 24/60 sampled pairs although every canonical pair changed at least 50%, admitted negative textures as ordinary values, accepted many structural impostors, silently accepted unknown overrides, and had no executable lesson/rival contract. Its active base Racket text was behaviorally equivalent to the canonical program but not source-identical.

Version 3.0.0 narrows the ordinary grammar to 4–8 rows/columns, four pairwise-distinct nonzero source colors, and exactly one of four outside-source layouts: no decoys, corner decoys, a source halo, or edge midpoints. Every declared axis (`grid_h`, `grid_w`, `decoy_pattern`) is exact, observable, exhaustively tested, and unknown keys fail loudly. `self_check` now recognizes this grammar rather than merely accepting rectangular colored grids.

## Lesson schedule and rivals

A deterministic period-4 schedule uses:

1. exact 4×4 canonical/no-decoy anchor;
2. 4×4 corner-decoy contrast, reusing one source color so canonical dimensions and palette size remain represented;
3. a compact larger source-halo witness;
4. a compact larger edge-midpoint witness.

Lessons use three demonstrations and one query. The four profiles jointly refute these canonical-fitting shortcuts: read the geometric center, take the first four nonzero cells, take the nonzero bounding-box corners, or force a 4×4 output. `lesson_identifiable` validates labels and reports any declared rival that fits every demonstration but changes the query. The task tests hold out every position from every cyclic schedule window; the source-bound census additionally checked 300 production lessons and 1,200 rotations, while fixed-seed period enumeration checked all 12 band/start combinations and 48 rotations.

## Reversed choice

The first compact rewrite used only one exact 4×4 profile. The profile-floor gate found 11/60 exact hits and an 18.3% canonical envelope, below the required 25%. The second profile was changed from a wider shape to a 4×4 corner-decoy contrast; this preserves a decisive source-selection witness while raising canonical-scale support. Evidence: `checks/profile-floor-fix/`, `checks/after-final/`, and `checks/schedule-census-final.json`.

## Racket authority

The canonical ledger and rule behavior were not changed. The selected active base authority's `raw_code` and `target_code` were replaced with the exact canonical source text because the prior text was an unsynchronized, behaviorally equivalent beautification. Exact-sync and sampled execution parity now pass.

## Known limits

The generated domain intentionally covers only fixed source offsets, 4–8 dimensions, and four finite decoy layouts; it does not claim arbitrary translations or arbitrary noise. The finite rival census establishes no ambiguity against the four declared plausible shortcuts, not universal uniqueness among all possible programs. Two 4×4 profiles intentionally repeat their dimensions across difficulty bands, while source colors, larger profiles, and outputs remain diverse. External lesson assemblers must preserve the declared three-demo schedule or call `lesson_identifiable`; a canonical-only lesson is deliberately rejected as ambiguous.

Minimal retained counterexamples are in `counterexamples/review-4d1bbf602e4954b4/`. Focused regressions are in `tests/test_generator_144582f287b5.py`.
## Current reviewer considerations

Source SHA-256: `9c8cdb46dd61677b21d7469cc662a25e790e2a18a76450b0548b63efbf5eaa4e`.

# Decisions

## D1 — Preserve the selected canonical rule and current distribution

**Choice.** Keep the fixed-offset rule, v3 grammar, four-profile schedule, lesson contract, RULE_HASH `acb1a0ae5f73`, and generator version `3.0.0` unchanged.

**Reason.** The before battery showed 11/12 green stages; the only reproduced current defect was at the public scalar call boundary. Canonical outputs, valid generation, schedule behavior, and selected Racket authority were already correct.

**Rejected alternative.** A wider distribution rewrite or Racket change would add risk without addressing the observed defect. The exact valid-call comparison in `checks/output-stability.json` supports the narrower repair.

## D2 — Fail closed on call scalars in one shared helper

**Choice.** Require `seed` to be an integer but not `bool`; require `sample_index` to be an integer but not `bool` and at least zero. Call the same helper from `generate` and `schedule_profile`.

**Reason.** Python booleans are integer subclasses, so an `isinstance(value, int)` check alone would preserve the defect. Shared validation prevents generator/scheduler divergence. The focused red run (`checks/tdd-red-call-scalars/result.json`) failed exactly the two new tests; the green run passed 25/25.

**Rejected alternatives.** Coercing values with `int(...)` would silently collapse distinct invalid inputs. Validating only `generate` would leave schedule selection inconsistent. Changing the difficulty contract was unnecessary for the selected task because the current generator already rejects invalid difficulty values through its profile lookup.

## D3 — Keep version `3.0.0`

**Choice.** Do not bump the generator version for this validation-only repair.

**Reason.** The patch changes behavior only for calls that violate the contract. Across 620 valid generation calls and 320 valid schedule calls, final outputs matched baseline source SHA `61a0f8ba...` with zero mismatches.

**Probe reversal.** The first retained comparison script incorrectly passed the override mapping as a single `overrides` keyword; the generator correctly rejected that unknown axis. The corrected probe expands the three axis keywords directly. Both revisions and the traceback are under `checks/output-stability-*`.

**Failure mode and limit.** The finite matrix is broad but not an exhaustive proof over all integer seeds. It is sufficient evidence that the intended valid API path and declared overrides are stable.

## D4 — Reverse the frozen-fixture edit

**Prior choice.** The first TDD red test was inserted into `tests/test_generator_144582f287b5.py`.

**New choice.** Restore that frozen fixture byte-for-byte and move new coverage to `tests/test_call_scalar_validation.py`.

**Reason.** `DUTIES.md` explicitly declares the baseline root test file frozen. Its final SHA-256 is the packet baseline `4d99fd4bead193b7664bd607eb680f6808964661866c58be4e6f92aad25d4637`.

## D5 — Use source rotation as the one parametric rule axis

**Choice.** Prototype `source_rotation_quarter_turns ∈ {0,1,2,3}`, selected once per episode. Rotate the extracted fixed 2×2 source before the existing scatter operation. Keep the prototype under `workspace/parametric/` and outside the selected generator path.

**Reason.** This is a small, interpretable transformation that preserves object roles and the original extract–transform–scatter reasoning. Distinct source colors make every wrong rotation observationally separable. Setting 0 is the exact canonical program, allowing a precise compatibility check.

**Rejected alternatives.** Moving the source block would change the task's fixed-offset selection role. Changing scatter destinations would replace the original relation rather than parameterize it. Permuting colors would risk confusing semantic color roles with the spatial rule. Adding multiple parameters would exceed the bounded evidence available in this review.

**Evidence and limits.** `checks/parametric/corner-rotation/report.json` covers four settings and saved seeds, 16 complete pairs, 64 protected-Racket executions, and 12 wrong-parameter rivals. This does not approve the variants or prove uniqueness outside the finite sampler.

## D6 — Bind strict semantics to the declared schedule census

**Choice.** Retain the declared `LESSON_SCHEDULE_PERIOD=4`, enumerate all fixed-seed start residues across easy/medium/hard, and feed that exact receipt into the final battery.

**Reason.** The first after battery's semantic failure was not a lesson ambiguity; it said the declared schedule period had not been enumerated. `checks/schedule-period-s0.json` materialized all 12 band/start lessons and all 48 rotations without ambiguity. The schedule-bound battery then passed 12/12.

**Rejected alternatives.** Removing the period declaration would hide useful scheduling structure. Treating the unbound warning as a generator defect would conflate missing evidence with bad lessons. Relying only on random lessons would not exhaust all cyclic starts.

## D7 — Retain the geometric-center witness as the strongest shortcut counterexample

**Choice.** Use the lawful 7×7 `source_halo` draw at seed 5521, sample index 2 as the answer to the shortcut question and as a focused regression.

**Reason.** The geometric-center rival fits all canonical 4×4 demonstrations because the fixed source block is central there. On this emitted input, the intended corners are `[9,2,1,8]` and the rival predicts `[8,7,7,0]`. The selected protected Racket authority produced the intended output.

**Rejected alternatives.** `fixed_4x4_output`, first-four-nonzero, and bounding-box-corners are plausible, but geometric-center is the most direct canonical coincidence and the 7×7 halo example separates it cleanly without leaving the generator domain.

## D8 — Report audit defects without editing audit targets

**Choice.** Preserve both audit generators unchanged and return exact call-level reproducers plus strict-lint receipts.

**Reason.** The assignment makes audits findings-only. `6be2608558c4` accepts invalid seed, difficulty, and negative sample-index values; `105b239cb812` accepts invalid seed/difficulty values while correctly rejecting a negative sample index. Their ordinary task/semantic contracts otherwise passed within the checked scope.

## D9 — Do not overclaim lesson or prototype evidence

The period census exhausts declared starts only at seed 0 and three bands. The 300-lesson census samples finite seeds and declared rivals. Query rotations reuse each materialized bundle. Neither result proves identifiability against every possible program, all seeds, translated sources, arbitrary noise, or future lesson assemblers. Prototype variants remain proposed and unapproved.
