# Working notes: 81eddce255be

## Current rule and domain

Count the blue (`1`) cells in row 0. Preserve the unique body object whose four-connected area equals that count; clear the header and the other two objects. Row 1 is a blank separator. The generator emits exactly three body objects with pairwise-distinct colors from `2..9`, pairwise-distinct areas in `1..7`, and one-cell cardinal separation.

Selected Racket authority is unchanged: `RULE_HASH = 70441dae68b0`. Final generator version is `3.0.0`; final source SHA-256 is `e51985885c66a2b47b0c43245ca49e5a06633c41821e6a5d7e56b4c22cc49ed8`.

## Reversed decisions

The imported `2.0.1` sampler advertised controls it did not honor, scattered header cells despite a canonical contiguous-header signature, allowed canonical `K=5/6` examples that its own validator rejected, and accepted marker-free arbitrary grids. It also left the canonical rule hash unpinned. Those choices were replaced by a constructive sampler with four exact controls only: `grid_h` (`10..14`), `grid_w` (`10..14`), `K` (`2..6`), and `target_rank` (`0..2`). Unknown, coercible, and out-of-range values now fail explicitly.

The prior stochastic grow-and-retry placement was replaced rather than patched. Three vertical slots and a connected-shape bank make every legal joint override constructive, deterministic, and validator-clean. The header is now one contiguous run, matching the canonical object signature; difficulty changes nuisance placement only and is visibly live.

## Teaching distribution

Defaults cycle 10x10, 11x11, and 12x12 profiles. A 15-step `K` schedule covers all values 2..6. Over nine consecutive samples, target row-rank and target size-rank cross all nine pairs, so topmost, bottommost, smallest, middle-sized, and largest-object shortcuts cannot proxy for the rule. Body colors and legal shapes are independently keyed nuisance variables.

The declared canonical shortcut is `topmost_object`: preserve the first body component in row-major order. It fits both canonical demonstrations. Generated three-example lessons deliberately refute it, including under every query rotation checked by the source-bound census. Exact witness: seed 19, sample index 5, `K=4`, `target_rank=2`; see `counterexamples/review-fd6ce8c89abe4417-v0001/topmost-shortcut-witness.json`.

## Verification and limits

Final task tests: 53/53 pass. Final inherited battery: 12/12 stages green. Production census: 300/300 lessons materialized, zero declared-rival ambiguities; 1,200/1,200 query rotations checked, zero ambiguous; 1,200 unique inputs. The visible-only post-repair solve passed all three demonstrations on its first revision, with earlier rule exposure declared.

This remains a finite teaching contract, not a proof of unique induction. Generated bodies are limited to connected subsets of a 2x4 box, every scene has exactly three objects, and only the strongest currently identified canonical shortcut is declared. Future audits should probe undeclared color-, shape-, and ordering-based rivals before expanding training admission.
## Current reviewer considerations

Source SHA-256: `e51985885c66a2b47b0c43245ca49e5a06633c41821e6a5d7e56b4c22cc49ed8`.

# Decisions for `81eddce255be`

## D1 — Replace, rather than patch, the stochastic sampler

**Prior choice.** Version `2.0.1` used stochastic blob growth and retry-based placement. It advertised axes whose values were not reliably reflected in returned pixels.

**Decision.** Use a constructive three-slot layout and a precomputed bank of connected shapes of areas 1..7.

**Why.** Construction guarantees termination, exact cardinal separation, pairwise-distinct sizes, and every legal joint override. It also makes failures diagnosable instead of hiding them behind retries.

**Rejected alternative.** Keep the old grow/retry code and add more retry loops. That would not fix ignored controls, weak validation, or proof of joint support.

**Probe.** Every boundary and a representative full joint assignment is exercised in `tests/test_generator.py`; override and grammar gates pass.

## D2 — Advertise only four exact controls

**Decision.** Public axes are `grid_h`, `grid_w`, `K`, and `target_rank`.

**Why.** Each is directly observable from returned pixels and has a clear semantic or distribution purpose. All values are legal in all difficulty bands.

**Rejected alternative.** Preserve palette/texture aliases from the imported sampler. Those axes were either ignored or difficult to make exact without adding irrelevant complexity.

**Failure handling.** Unknown keys, booleans, floats, strings, out-of-range values, negative sample indices, and unsupported difficulties raise explicit errors.

## D3 — Match the canonical header signature

**Prior choice.** Blue markers were scattered across row 0.

**Decision.** Emit one contiguous horizontal run of `K` blue cells.

**Why.** The canonical examples present the header as one object. Scattering it created an avoidable morphology shift and triggered strict defect evidence.

**Rejected alternative.** Allow both scattered and contiguous forms. That widens the induction problem without strengthening the intended rule and makes component-based header interpretations ambiguous.

## D4 — Keep exactly three objects with distinct colors and areas

**Decision.** Every generated scene contains exactly three non-touching body objects, colors from `2..9`, and pairwise-distinct areas.

**Why.** This preserves the canonical task structure and makes the unique area-`K` target mechanically checkable.

**Rejected alternatives.** Variable object count and duplicate distractor areas. Both are plausible future extensions, but they would enlarge the domain and require new rule/teaching evidence rather than a repair-only change.

## D5 — Decouple row-rank from size-rank

**Decision.** Over nine default samples, target row-rank and target size-rank cover all nine pairs.

**Why.** The canonical demonstrations admit “keep the topmost object.” A schedule that merely varies `K` could still leave topmost, smallest, or largest as a proxy.

**Evidence.** Seed 19, sample index 5, `K=4`, `target_rank=2` refutes topmost exactly; the 300-lesson census and 1,200 query rotations report no surviving declared rival.

**Rejected alternative.** Randomize rank independently without a schedule. Random support does not guarantee each three-demonstration lesson teaches the distinction.

## D6 — Preserve canonical-scale support while widening dimensions

**Decision.** Default dimensions cycle `(10,10)`, `(11,11)`, `(12,12)`; exact overrides cover 10..14 independently.

**Why.** This keeps every short lesson close to canonical scale while allowing controlled dimension variation and passing the strict profile floor.

**Rejected alternative.** Uniformly draw 10..14 for every pair. It is diverse but gives weaker guarantees about canonical-profile presence in each lesson.

## D7 — Difficulty changes nuisance placement only

**Decision.** Easy, medium, hard, and unspecified difficulty use different deterministic header offsets while preserving the same four public facts.

**Why.** Difficulty must not silently alter the rule or invalidate overrides, but it must not be a dead parameter either.

**Probe.** Round-two regressions first failed on identical bands, then passed after the offset change (`checks/task-tests-red-round2/`, `checks/task-tests-green-round2/`).

## D8 — Pin authority; do not change the Racket rule

**Decision.** Add `RULE_HASH = 70441dae68b0` and leave canonical data and reference code unchanged.

**Why.** The intended transformation and canonical labels were already correct. The defects were sampling, validation, and teaching support.

**Evidence.** Rule smoke and authority sync pass in the final battery. The exact topmost witness was independently evaluated by `arcpuzzles apply` and matched the Python oracle.

## D9 — Require arbitrary query rotations for the reported lesson contract

**Decision.** Report three demonstrations and require every held-out position to refute the declared rival.

**Why.** The downstream lesson census supports query rotation, and the short deterministic structure makes this affordable to verify.

**Evidence.** 300 production lessons and 1,200 rotations; zero ambiguous, zero scoring errors, 1,200 unique inputs.

**Limitation.** The census covers declared and shared generic rivals only. It is not a proof of unique human or model induction.

## D10 — Curriculum annotation

`contextual_gating` is marked present: the row-0 count gates which body object survives, and the topmost rival changes its prediction on the retained generated witness. `task_defined_symbols` is also present because blue header cells acquire a count-as-selector role from the examples. `multi_rule_interaction` and `sequential_state` are not applicable: this is a single selection-and-filter operation with no intermediate temporal state.
