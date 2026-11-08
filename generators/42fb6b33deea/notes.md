# Working notes: 42fb6b33deea

## Intended rule

The pinned Racket authority is **count-gated, not geometry-gated**: for every nonzero color appearing exactly four times, fill that color's complete bounding box on a fresh zero canvas. Colors with any other count disappear. `RULE_HASH = b800fc792026` remains unchanged.

## Reversed teaching decision

Prior retained decision `GNOTE-001542` kept generated exact-four groups as literal rectangle corners and rejected exact-four/non-corner recombinations, even though the executable authority accepts them. That made the strongest plausible rival—“fill only when the four cells are the four bounding-box corners”—fit every canonical pair and every generated lesson.

Version 2.3.0 reverses the teaching-only part of that decision. The validator and sampler admit one exact-four/non-corner target (`target_style=count_witness`) while preserving its nontrivial bounding box. The authority did not change. Exact witness `counterexamples/exact_four_noncorner.json` is accepted by `self_check`; the Racket authority fills rows 1–4 and columns 1–6 with color 8, while the geometric-corners rival returns zeros.

## Distribution and lesson assembly

The internal three-role schedule is:

1. two targets, no distractor, `count_witness`;
2. one target, one three-cell distractor, `corners`;
3. two or three targets, three- and five-cell distractors, `count_witness`.

Thus every three consecutive production examples contain all distractor-count roles and two non-corner witnesses. Any one of four consecutive examples may be held out as query while at least one decisive witness remains in the other three demonstrations. Only the first target may be non-corner; other exact-four targets remain ordinary corners for visual clarity.

Role 2 (zero-based role 1) uses one of the exact canonical three-color profiles `(8,11,3)`, `(9,10,3)`, `(9,12,3)`, or `(10,10,3)` in every band unless the caller explicitly overrides grid dimensions. This prevents the generated lesson from drifting entirely away from canonical scale.

## Exact controls and bounded work

- `sample_index`, grid dimensions, and target/distractor counts reject booleans, floats, and numeric strings rather than silently coercing them.
- Unknown override names raise immediately.
- Palette rotation has its own keyed RNG, so changing the layout search cannot silently change a requested palette axis.
- Target rectangles are constructed inside randomized disjoint slabs. Candidate **shapes** are cached and ranked once; no draw shuffles thousands of positioned boxes.
- Distractors use a bounded random probe with an exhaustive deterministic fallback. Focused tests prohibit full-catalog shuffles, preserving the override-stage performance contract.

## Assumptions and limits

- Background is zero; grids are 5–16 by 7–18 in the advertised sampler.
- One to three exact-four target colors are allowed, at most one of them non-corner.
- Target bounding boxes do not overlap, avoiding paint-order ambiguity. Distractor boxes may contact targets; only occupied cells must be disjoint during generation.
- Distractors are limited to three bbox corners or four bbox corners plus one interior cell. This is a curriculum restriction, not a claim that the Racket authority cannot execute other counts or layouts.
- Finite checks refute the declared geometric-corners rival; they do not prove universal rule identifiability against every imaginable program.
- The public schedule period is intentionally not declared as a semantic contract; exhaustive cyclic-start support is retained in focused tests and the enumerated `schedule_profile` values.

## Current evidence

Focused tests cover canonical synchronization, strict overrides, deterministic generation, canonical-scale anchoring, bounded layout work, the retained counterexample, all three cyclic lesson roles, and every held-out query position across four consecutive samples. Final battery, strict semantic gate, and 100-lessons-per-band census receipts are recorded in the review return under `checks/`.
## Current reviewer considerations

Source SHA-256: `f7b18a5c8e7347d5555c1cea11c2a2d5375817be63a7c6ae1489601c98456868`.

# Decisions for 42fb6b33deea

## D1 — Treat the Racket program as literal count-gated authority

**Decision.** Preserve the rule: every nonzero color with exactly four cells fills its complete bbox; all other colors disappear.

**Reason.** The normalized canonical program hash is `b800fc792026`, and the source-bound Racket counterexample receipt confirms that an exact-four non-corner configuration is filled. No canonical or Racket change was needed.

**Rejected alternative.** Reinterpret “four cells” as “four literal rectangle corners.” That alternative fits the canonical pairs but disagrees with the executable authority on the retained witness.

**Evidence.** `checks/counterexample-final/input.json`, `checks/counterexample-final/racket.json`, and `repo/generators/42fb6b33deea/counterexamples/exact_four_noncorner.json`.

## D2 — Reverse the prior corner-only teaching choice

**Prior choice.** Retained note `GNOTE-001542` kept all exact-four generated targets as actual corners. Its original rationale was visual regularity and a narrow canonical-like domain.

**New choice.** Admit one exact-four/non-corner target in two of the three scheduled roles. Construct it by replacing one corner with a non-corner cell while preserving the bbox.

**Reason.** The prior choice taught the geometric-corners rival instead of distinguishing the literal count rule. The replacement construction creates one controlled distinction without changing color count, bbox, label, or authority.

**Rejected alternatives.** Randomly sprinkling four cells was rejected because it can shrink the bbox, create trivial boxes, or make examples visually noisy. Allowing every target to be non-corner was rejected because one decisive target is sufficient and ordinary corners remain useful for readability.

**Failure mode retained.** At most one count witness is allowed per grid; the validator rejects more.

## D3 — Use a deterministic three-role lesson schedule

**Decision.** Schedule `count_witness/no distractor`, `corners/three-cell distractor`, and `count_witness/three-plus-five-cell distractors` by `sample_index mod 3`.

**Reason.** Random witness frequency can produce a three-demonstration lesson containing no decisive example, or place the only witness in the held-out query. Two witnesses per three consecutive production examples make the ordinary lesson decisive; four-consecutive held-out tests leave at least one witness among the remaining three demos.

**Rejected alternative.** A low-probability independent witness toggle was rejected because passing pair-level distribution checks would not guarantee lesson-level teaching support.

**Evidence.** Focused cyclic regressions in `tests/test_generator_42fb6b33deea.py`; strict gate `checks/final-strict-semantic-run/`; 300-lesson census `checks/lesson-census-final.json`.

## D4 — Declare and execute the strongest plausible rival

**Decision.** Implement `four_actual_corners_only` once and expose it via all semantic declaration surfaces. Implement `exact_four_noncorner` as a witness predicate and check lesson identifiability directly.

**Reason.** The rival fits every canonical demonstration and is the closest simple alternative to the intended rule. An executable declaration lets the shared semantic gate and census verify actual outputs rather than matching prose tags.

**Limit.** Refuting one declared rival is not universal identifiability. Undeclared program hypotheses remain outside the finite claim.

## D5 — Anchor canonical scale without erasing diversity

**Decision.** In the ordinary-corners role, choose one of `(8x11)`, `(9x10)`, `(9x12)`, or `(10x10)` with three nonzero colors unless dimensions are explicitly overridden.

**Reason.** The strict profile-floor gate showed that the first 20 draws could miss exact canonical size/palette support. One scheduled anchor per cycle guarantees support in every band while the two witness roles retain broader dimensions.

**Rejected alternative.** Force canonical dimensions on every role. That would unnecessarily collapse spatial diversity.

## D6 — Make controls exact and fail loudly

**Decision.** Reject coercible integer values, negative `sample_index`, and unknown override keys. Add an observable `target_style` axis and isolate palette RNG from layout RNG.

**Reason.** String/float/bool acceptance and swallowed unknown names make the advertised override contract unreliable. RNG isolation prevents a layout optimization from silently changing palette behavior.

**Evidence.** RED receipts `checks/tdd-red-battery-blockers/` and `checks/tdd-red-unknown-override/`; final override stage in `checks/after-final-managed/`.

## D7 — Replace full positioned-box catalog shuffles with bounded construction

**Decision.** Partition one axis into randomized disjoint slabs, sample a cached ranked rectangle shape per slab, and position it locally. Place distractors with 96 random probes followed by deterministic exhaustive fallback.

**Reason.** The former path shuffled thousands of positioned boxes per draw and caused the 47,160-draw override stage to exceed practical controller limits. The new path preserves exact boundaries and deterministic fallback while reducing measured worst-case 3,000-draw time from about 25.0 seconds to about 1.8 seconds.

**Rejected alternatives.** Raising timeouts would hide an algorithmic issue. Truncating the override matrix would weaken the contract. Pure random rejection without fallback could fail lawful dense overrides nondeterministically.

**Trade-off.** Slab construction creates a stronger spatial separation than the authority requires. This is the principal remaining sampler restriction.

## D8 — Keep the public period contract undeclared

**Decision.** Retain the internal period and expose `schedule_profile`, but do not publish `LESSON_SCHEDULE_PERIOD` as a shared semantic contract.

**Reason.** The shared gate treats a public period as a stronger exhaustively supported promise. Focused tests already enumerate all cyclic starts needed by this generator, while the random production census independently checks 300 lessons and all held-out positions.

**Limit.** The census does not prove every seed or undeclared rival; the internal schedule remains an implementation detail.

## D9 — Preserve failed evidence and honest solve provenance

**Decision.** Keep the meaningful RED receipts and both solve episodes. Mark the post-repair solve as earlier-exposed and both private-query verdicts as unknown.

**Reason.** Passing tests without the earlier failures would not establish the regressions. Visible-example success is not private-label evidence.

## D10 — Add a source-bound two-policy parametric family

**Decision.** Preserve the exact canonical program as `fill_policy=all_exact_four` and add `fill_policy=selector_area_gate`. In the latter, Step A finds the unique three-cell selector and computes its bounding-box area; Step B fills an exactly-four color only when its own bounding-box area is at least that input-derived threshold.

**Reason.** The alternate policy remains in the canonical task's count-and-bounding-box vocabulary while adding a genuine input-dependent A→intermediate→B dependency. Inputs are matched across settings, so demonstrations must teach the rule rather than incidental layouts.

**Source binding.** The production generator remains byte-for-byte at SHA-256 `f7b18a5c8e7347d5555c1cea11c2a2d5375817be63a7c6ae1489601c98456868`; the canonical default program is byte-for-byte at SHA-256 `7ab882f12694d89a3350c97a8b168249cf2efc1d25faf9e53d336e338964a2f9` and rule hash `b800fc792026`.

## D11 — Construct before sampling and audit finite rivals

**Decision.** Materialize a deterministic six-demonstration/four-query schedule before truncating to requested counts. Support independent 2–6 demonstration and 1–4 query requests, retain four distinct controller-side queries, and make query four a substantive 30×30 scene. Public projection strips settings, programs, all query answers, and future queries; public IDs hash visible bytes only.

**Learnability check.** The first two demonstrations eliminate the alternate policy and five nearby shortcuts: literal corners only, strict selector threshold, at-most threshold, largest bbox only, and all nonzero bboxes. The protected audit exercised both policies at seeds 0 and 17, all count boundaries, matched inputs, public masking, and eight 30×30 episodes: 16 episodes, 104 labeled pairs, 68 Racket evaluations, zero failures. This is finite rival coverage, not universal identifiability.

## D12 — Freeze a protected causal witness and hand off owner acceptance

**Witness.** In qualified nondefault episode 2/test pair 0, Step A computes selector area `8`. The correct policy paints exactly-four boxes with area at least 8. Replacing it with the canonical skip-A program also paints an area-6 color, changing six final cells. Both labels were freshly executed and replayed in the protected Racket runtime.

**Status.** Native qualification passed two settings × two fresh seeds with three demonstrations and four queries per job (40 Racket labels). Reviewer status is `ready`; exact-source owner acceptance and any training admission remain pending.
