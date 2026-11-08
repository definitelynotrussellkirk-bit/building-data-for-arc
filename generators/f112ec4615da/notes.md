# Current notes: f112ec4615da

## Intended rule

Split an even input into four equal quadrants. At each local coordinate, treat
zero as transparent and apply the fixed positional precedence
`TR > BL > BR > TL`; the result is the first nonzero value in that order, or
zero when all four cells are zero. The selected Racket semantics and
`RULE_HASH = 8724ec70a45a` were not changed by this review.

## Baseline findings used

The retained audit from `review-1f4b2a09912ae523-v0001` supplied the lead that
the seven canonical pairs admit a color-value shortcut: choose the globally
smallest quadrant color when present, otherwise choose the numerically largest
present value. Its seed-107 lesson retained two demonstrations on which that
rival matched and a query on which it differed at three cells. This return
rechecked the exact query through current-source canonical Racket evidence at
`checks/question-generator-shortcuts/evidence.json`.

The baseline generator (`3.0.0`, SHA-256
`438a4a576a6a5790a9f92dc00bba8835fe27f264c13cbfcb6a2ad2ad6fd68cc1`)
also accepted non-integer/bool seeds and sample indices, accepted negative
sample indices, declared no executable lesson rival contract, and had selected
`target_code` that differed from the canonical program only in whitespace.
The before battery retained these results: 9 green, 1 advisory semantic gate,
and 2 failures (`defect_lint`, `authority_sync`).

## Decisions in version 3.1.0

- Validate `seed` and `sample_index` as exact integers and reject negative
  sample indices before constructing a generation context.
- Declare the canonical-fitting `numeric_color_rank` rival in
  `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_RIVALS`; add the
  `position_over_numeric_color` witness and a query-aware
  `lesson_identifiable` hook.
- Preserve the existing canonical-profile prior and general sampler, but draw
  four distinct colors so the top-right color is never the global minimum.
  Every generated mask already contains an all-four overlap; this makes every
  generated input an authoritative counterexample to the numeric-color rival
  without changing the positional rule.
- Synchronize only the selected base authority `target_code` to the exact
  canonical text. The archival `raw_code` remains byte-identical at SHA-256
  `8724ec70a45a246d517528c6024011d4af96fc926d73cc44e898a690515bace6`.
- Keep the inherited root test fixture unchanged. It is frozen by the packet
  and still uses a fixed `__file__.parents[...]` canonical path; the portable
  aggregate task-test stage therefore stops in preflight. New tests use
  `reviewer_support` and pass independently.

Final generator SHA-256:
`a54140d2680583a29b3f18a4053547de51a1e0fb6c7252fe6689327c9fd16ecd`.

## Evidence

- After battery: 12/12 green, no warning/advisory/failure
  (`checks/after/checks/f112ec4615da_after_battery_summary.json`).
- Semantic gate: witness on 600/600 draws; 60/60 checked rival claims held;
  12/12 three-demo-plus-one-query lessons and 48/48 smoke rotations had no
  declared-rival ambiguity.
- Larger source-bound census: 300/300 lessons, 1,200 labelled pairs,
  1,193 unique inputs, 0 production ambiguities, and 0/1,200 query-rotation
  ambiguities (`checks/lesson-census-final.summary.json`).
- New canonical repair and parametric tests: 15/15 pass
  (`checks/focused-tests-final.log`). Red-before-green logs are retained.
- Required aggregate task-test stage: blocked before pytest by frozen
  `tests/test_generator_f112ec4615da.py:17`; see
  `checks/task-tests-after/result.json`.
- Post-repair visible-only solve: first revision, 3/3 visible examples exact;
  earlier source exposure declared honestly and no reference consulted during
  the solve (`solve/summary.json`).

## Parametric assessment

A separate proposed prototype under `workspace/parametric/` changes only one
small parameter, `priority_order`, with settings `canonical`
(`TR > BL > BR > TL`) and `reverse` (`TL > BR > BL > TR`). The setting is
chosen once per episode; all labels are produced by actual instantiated Racket
programs. The retained run checks 7/7 canonical labels, two episodes, eight
generated labels, eight counterfactual labels, two production queries, and all
eight single-query rotations with zero declared-setting ambiguities. It is a
prototype only, not a selected rule or approved production API.

## Known limits and open findings

The semantic evidence is finite and covers the declared numeric-color rival;
it is not a proof against every possible shortcut. The intentional color
constraint is a teaching intervention and narrows color-role support: the
sampler does not place the global minimum in the top-right role. The canonical
profile prior and all documented size overrides remain supported, but arbitrary
lesson reassembly outside the tested three-demo/one-query policy is unknown.
The only required-check blocker is migration of the immutable inherited test
fixture to `reviewer_support.find_root`, `canonical_path`, and
`canonical_pairs`; that migration belongs to a future packet or maintainer.
## Current reviewer considerations

Source SHA-256: `a54140d2680583a29b3f18a4053547de51a1e0fb6c7252fe6689327c9fd16ecd`.

# Decisions for f112ec4615da — review-4bfe455c92aabee9

## D1 — Preserve the selected positional overlay

**Input choice and prior rationale.** The baseline builds four equal quadrants,
each with one distinct color and zero background, then overlays corresponding
cells. The original source comments and all canonical labels agree on effective
precedence `TR > BL > BR > TL`. The exact original rationale for the broad
6..30 even-dimension support and 0.28 canonical-profile prior is not recorded.

**Decision.** Keep the Racket rule, `RULE_HASH`, dimensions, density bands,
canonical masks, and profile prior unchanged. The task defect was curricular,
not a label or transformation defect.

**Alternatives rejected.** Changing the Racket order would contradict all
seven canonical labels. Shrinking to canonical 10×10 masks would discard useful
size diversity. Replacing the sampler wholesale was unnecessary and would make
before/after attribution weaker.

**Probe and limits.** Canonical rule smoke and execution parity pass in the
12/12 final battery. The rule remains defined only for even grids whose four
quadrants each have one distinct foreground color under this generator's
validator.

## D2 — Make the numeric-color shortcut executable and observable

**Prior choice.** Canonical colors are fixed by position (`TL=4`, `TR=3`,
`BL=9`, `BR=8`). Consequently, a non-positional rule—choose the globally
smallest color if present, otherwise the largest present value—matches all
seven canonical pairs. The baseline had no `CANONICAL_SHORTCUTS`, lesson
competitor, semantic witness, or lesson hook.

**Decision.** Declare one named rival, `numeric_color_rank`, in all three
semantic registries. Add `position_over_numeric_color` and map it to that rival.
Add `lesson_identifiable` that validates demonstration labels and reports a
rival only when it fits every demonstration and changes the query.

**Alternatives.** A prose-only note would not exercise the semantic gate.
Declaring a rival without changing the sampler would make many lessons fail.
Adding many speculative rivals would inflate apparent coverage without evidence.
The selected single rival is the strongest retained, Racket-bound hypothesis.

**Evidence.** It fits 7/7 canonical pairs. The retained seed-107 exact input,
current-source Racket output, and three differing cells are in
`checks/question-generator-shortcuts/evidence.json`. The final semantic gate
checks 60/60 authoritative disagreements; the larger census reports 0/300
production and 0/1,200 rotation ambiguities against the declared rival.

**Limits.** This is finite named-rival evidence, not universal induction.

## D3 — Use palette permutation to teach position rather than numeric value

**Prior choice.** The baseline sampled four distinct colors without preventing
the top-right role from being the global minimum. Its forced five-pattern chain
included an all-four overlap, but that overlap could still agree with the
numeric shortcut.

**Decision.** Keep color sampling broad over 1..9, then swap top-left and
top-right only when top-right is the global minimum. Thus top-right is never the
minimum. Since every general grid and every retained profile has an all-four
overlap, intended output chooses top-right there while the rival chooses the
minimum elsewhere. Every generated input is therefore a direct witness.

**Alternatives.** Fixed role colors would preserve the defect. Rejection
sampling entire lessons would add variable runtime and obscure deterministic
replay. Forcing the global minimum into a fixed *other* role is equivalent but
less direct than the one conditional swap.

**Failure modes and limits.** The intervention introduces a deliberate palette
restriction: the minimum color never occupies top-right. It does not balance all
24 role permutations and could support undeclared statistical shortcuts. The
semantic gate saw the witness on 600/600 draws across all bands, but that finite
sample is not proof against arbitrary color rules.

## D4 — Enforce the public scalar call contract

**Prior choice.** Baseline generation accepted booleans, floats, strings, and
negative sample indices through context coercion. Defect lint emitted 33
warnings.

**Decision.** Validate `seed` and `sample_index` before creating the context:
exact Python integers only; `sample_index >= 0`. Preserve existing difficulty
and override validation.

**Alternatives.** Coercing strings/floats was rejected because it aliases
recipes and makes replay metadata misleading. Accepting bool was rejected
because bool is an int subclass but not a meaningful seed/index type.

**Evidence.** Seven new negative cases fail before the fix and pass after it;
final defect lint is green with no warnings.

## D5 — Synchronize selected authority text without rewriting history

**Prior state.** Canonical program, selected target, and archival raw source were
execution-equivalent, but selected `target_code` differed from canonical only in
whitespace. The baseline authority stage failed exact synchronization.

**Decision.** Use the supported proposal/apply workflow with `--selected-only`.
Set only `racket_target.target_code` to exact canonical text. Preserve
`raw_code` byte-for-byte and do not edit the canonical row.

**Alternatives.** Reformatting canonical source or overwriting archival raw code
would erase provenance. Ignoring the mismatch would leave a required stage red.

**Evidence.** `checks/authority-sync-proposal.json`; final authority stage green;
archival raw SHA-256
`8724ec70a45a246d517528c6024011d4af96fc926d73cc44e898a690515bace6`.

## D6 — Add tests without modifying the frozen fixture

**Prior state.** The inherited `test_generator_f112ec4615da.py` resolves
canonical data using a fixed parent depth. In the portable staged runtime it
looks below the task directory and preflight fails before pytest. The assignment
marks that file frozen.

**Decision.** Leave it unchanged. Add `test_repair_contract.py` and
`test_parametric_priority.py` using `reviewer_support.find_root`,
`canonical_path`, `canonical_pairs`, and `load_selected_generator`. Retain the
aggregate failure as a blocker rather than misreporting it.

**Evidence.** Focused red logs show 11 missing repair behaviors and four missing
prototype behaviors. Final focused run passes 15/15. Required aggregate stage
remains `preflight_failed` at the frozen line 17.

**Limit.** Completion is reported blocked even though the selected repair's new
tests and full battery pass; maintainer or future-packet migration is required.

## D7 — Prototype one bounded parametric extension

**Parameter.** `priority_order ∈ {canonical, reverse}`; original default is
`canonical`. Reverse changes only effective precedence to
`TL > BR > BL > TR`.

**Decision.** Keep it separate under `workspace/parametric/`. Choose the setting
once per episode by seed parity. Generate four inputs independently of the
setting, label three demonstrations and one query with one instantiated Racket
program, and check every query rotation against the alternate setting.

**Alternatives.** Per-cell or per-example priority changes would alter the
reasoning pattern. A free permutation parameter would be larger than needed for
this assignment. Changing quadrant geometry would conflate two mechanisms.

**Evidence.** `checks/parametric/priority-s0/report.json`: both settings, 7/7
canonical labels, 8 generated labels, 8 counterfactual labels, 0/2 production
ambiguities, and 0/8 rotation ambiguities. Exact canonical and reverse program
hashes are retained.

**Limits.** Two seeds and one alternative only; proposed, not selected or
approved.

## D8 — Lesson assembly, solves, audits, and stopping

**Lesson choice.** Retain three demonstrations plus one query. The production
census materializes 100 lessons per band and rotates each of the four labelled
pairs through the query position. This matches the solve episode's three-demo
configuration.

**Evidence.** 300/300 lessons, 1,200 labels, 1,193 unique inputs, 0 production
ambiguities, and 0/1,200 rotation ambiguities. The smaller battery independently
checks 12 lessons and 48 rotations.

**Solves.** The pre-repair blind task and post-repair selected task both passed
3/3 visible examples on revision 1. The post-repair record declares earlier
source exposure and no reference consultation during the solve.

**Audits.** The one permitted audit draw selected `fdb8815ba528` and
`d2b3402dde86`. No audit source was edited. Both findings have accepted-domain,
canonical-Racket reproducers under `checks/audit/`.

**Stopping reason.** The selected source is stable, all semantic and battery
work is complete, and the only required blocker is the immutable portable-path
fixture. Further speculative rivals would not convert finite testing into a
proof and were not used to delay the handoff.

## Current overlapping proposal

Overlapping old-baseline alternative is unselected. Current approved a54140d2 source already repairs scalar/numeric-color semantics and has12/12 reported battery with selected authority formatting fixed; its existing canonical/reverse priority prototype remains current. This proposed6c231b14 source starts from438a4a57 and collides on generator/notes/prototype/tests, reports11/12 due authority text plus frozen fixture blocker, and supplies21 safe palette-role permutations and2-demo priority episodes. Preserve code/evidence for a source-bound rebase that keeps current authority synchronization and prototype; its reported results cannot approve new combined bytes. Existing fixture audit remains unresolved. No current generator/rule/prototype modification or variant approval. Retained at `workspace/proposals/review-b70667c77b48efc8/manifest.json`.
