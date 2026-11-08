# Current notes: `382eb0e592eb`

## Intended rule

Every adjacent equal nonzero horizontal pair above the bottom row copies its color into the same two columns one row below. Trigger tests read the original input; accumulated writes may overwrite nonzero targets but never create recursive triggers. Overlapping windows in a length-three run copy all three cells. Bottom-row pairs are inert.

Selected authority is unchanged and pinned as `RULE_HASH = 03fbcf596117`. Reviewed generator version is `3.0.0`, SHA-256 `674aca05b5a30e0d7bea944dbfa3e112e9e8b1c767f699860fd10b93caf3e257`.

## Reversed distribution decision

The prior version generated only isolated dominoes on arbitrary 8–12 by 8–14 grids with blank target cells. That choice taught a narrower “isolated domino becomes a 2×2 block” rule and left canonical-fitting shortcuts unchallenged. It was replaced with a deterministic four-slot curriculum over exact public profiles:

1. `canonical_4x5`
2. `semantic_3x6`
3. `canonical_3x6`
4. `semantic_4x5`

Canonical scenes retain simple anchors. Every semantic scene contains a length-three overlapping run, a same-color vertical nontrigger, a nonzero target overwrite, and an inert bottom-row pair. Each normal draw uses zero plus exactly two nonzero colors and stays in a canonical 4×5 or 3×6 shape/profile.

## Controls and lesson policy

`scene_profile` is the only advertised override. It is exact, observable, and strictly validated. Easy, medium, and hard use disjoint nonzero color pools so `difficulty` is not behaviorally dead; this changes appearance, not rule complexity.

A lesson uses three demonstrations and one query. Every cyclic four-pair window contains all four profiles. All four possible query positions are checked against four executable canonical-fitting rivals: `exact_domino_only`, `copy_all_nonzero_down`, `blank_below_only`, and `bottom_pair_upwards`.

## Evidence

- Final battery: 12/12 green, including required rotations and schedule enumeration: `checks/after/checks/382eb0e592eb_after_battery_summary.json`.
- Portable selected-task tests: 32/32 passed: `checks/task-tests-final/result.json`.
- Wider production census: 300 lessons, zero declared-rival ambiguity in production queries or 1,200 rotations, 293 unique inputs: `checks/lesson-census-final.summary.json`.
- Minimal actual-Racket witness: `counterexamples/semantic_3x6_all_rivals.json` and `checks/counterexamples/semantic_3x6_all_rivals-racket.json`.
- Future-review helper: `workspace/qualify.py` (12 windows, 48 rotations at one seed).
- Separate direction prototype: `workspace/parametric/`; it does not alter selected canonical execution.

## Known limits and open findings

Identifiability is finite and relative to the four named rivals; it is not a proof against every possible hypothesis. The support intentionally has only two dimensions and four layout families, so template recognition remains possible. Difficulty colors do not represent genuine cognitive difficulty. The parametric `up` direction is proposal-only. Catalog approval and training admission remain unchanged and maintainer-owned.
## Current reviewer considerations

Source SHA-256: `674aca05b5a30e0d7bea944dbfa3e112e9e8b1c767f699860fd10b93caf3e257`.

# Design decisions for `382eb0e592eb`

## D1 — Pin the existing canonical authority

**Choice.** Keep the selected Racket rule unchanged and declare `RULE_HASH = "03fbcf596117"`.

**Rationale.** The authority already expresses a coherent rule: every adjacent equal nonzero horizontal window copies down, using original-input reads. The defect was primarily that the sampler taught a narrower isolated-domino story.

**Alternatives considered.** Narrow the Racket rule to isolated connected 1×2 components; or change it to a component-based expansion. Both would fit the visible canonical anchors but would discard lawful overlapping-window and overwrite behavior already present in the selected authority.

**Probe/evidence.** `checks/counterexamples/semantic_3x6_all_rivals-racket.json` executes the canonical rule on a lawful semantic witness. Final authority parity is in `checks/after/checks/382eb0e592eb_after_authority_sync.json`.

**Failure mode/limit.** An archival solution remains divergent, but the selected authority is synchronized and execution parity passes. Catalog approval remains outside this review.

## D2 — Reverse the isolated-domino-only sampler

**Prior choice.** Version 2.0.0 generated 8–12 by 8–14 grids containing three to five isolated horizontal dominoes, each with blank cells directly below. The original rationale is not retained beyond the old summary; likely goals were simple generation and obvious labels.

**New choice.** Generate the exact public 4×5 and 3×6 profiles and include both canonical anchors and semantic counterexamples.

**Reason.** The old sampler made four incorrect rules observationally equivalent to the authority. It therefore produced correct labels but weak teaching data.

**Alternatives considered.** Keep large random grids and occasionally inject one edge case; or sample arbitrary lawful grids. The first makes witness coverage probabilistic. The second gives more diversity but makes exact-profile support, observable controls, and lesson identifiability harder to guarantee cheaply.

**Probe/evidence.** The four retained rivals fit all canonical pairs. Semantic profiles refute all four, and the final semantic gate records 4/4 witness and rival claims. See `checks/after/checks/382eb0e592eb_after_semantic_gate.json`.

**Failure mode/limit.** The support is intentionally compact: only two dimensions and four layout families. This is a teaching curriculum, not broad enumeration of all lawful grids.

## D3 — Use a four-profile cyclic curriculum

**Choice.** Schedule `canonical_4x5`, `semantic_3x6`, `canonical_3x6`, `semantic_4x5` cyclically by `sample_index`.

**Rationale.** A standard lesson has three demonstrations and one query. Every four-pair window therefore contains both canonical anchors and both semantic shapes, independent of the start position.

**Alternatives considered.** Independent random profile choice; weighted sampling; or a two-slot canonical/semantic alternation. Independent choice can omit a witness from a short lesson. A two-slot schedule does not guarantee both public dimensions and both semantic dimensions in every four-pair window.

**Probe/evidence.** `workspace/qualify.py` exhausts four starts × three bands × four query positions. It reports 12 windows and 48 unambiguous rotations in `checks/qualification/final.json`. The final battery also ran schedule-period enumeration.

**Failure mode/limit.** Deterministic order can itself become a positional cue for systems that see global sample indices. Query-rotation tests remove within-lesson position dependence, but they do not model every downstream shuffling scheme.

## D4 — Bundle the semantic distinctions in each semantic scene

**Choice.** Each semantic profile contains a length-three run, a vertical same-color nontrigger, a nonzero target overwrite, and an inert bottom-row pair.

**Rationale.** This makes each semantic example independently refute all four named shortcuts, so one held-out semantic query cannot leave a different shortcut unchallenged.

**Alternatives considered.** One witness per profile or one witness per lesson. Those designs offer more combinatorial diversity but need more demonstrations or a more complex scheduler to guarantee all distinctions before every query.

**Probe/evidence.** Focused tests assert every witness fires and every rival disagrees for both semantic profiles across multiple seeds. The retained 3×6 counterexample records the actual Racket answer and all rival predictions.

**Failure mode/limit.** Repeated co-occurrence can encourage a learner to treat the four distinctions as a single scene template. Canonical/semantic shapes and mirrored layout choices reduce but do not eliminate template recognition.

## D5 — Advertise only one exact control

**Choice.** Expose `scene_profile` as the sole axis. It names an exact, observable dimension/layout family and rejects unknown or invalid values.

**Rationale.** The baseline controls described implementation randomness rather than a stable semantic contract. One honest control is preferable to several weak knobs.

**Alternatives considered.** Expose raw row, column, color, pair count, or witness booleans. Those axes would require a larger compatibility matrix and could create unsupported combinations or leak implementation details.

**Probe/evidence.** Override checks accepted 450/450 valid cases, rejected unknown keys, and found no axis-realization mismatch: `checks/after/checks/382eb0e592eb_after_override_results.json`.

**Failure mode/limit.** Reviewers cannot independently request each individual witness; semantic profiles intentionally bundle them.

## D6 — Make difficulty observable through color pools only

**Choice.** Easy uses colors 1–3, medium 4–6, hard 7–9; every draw still selects exactly two nonzero colors.

**Rationale.** The first repair draft accepted `difficulty` but produced identical behavior. Disjoint pools make the band observable without changing the rule, shape, witness coverage, or profile support.

**Alternatives considered.** Vary grid size, witness count, or clutter by band. Those choices could make some bands semantically weaker or fall outside the exact canonical profile floor.

**Probe/evidence.** The focused regression requires distinct outputs for all three bands at the same seed/index while every grid remains strict-canonical-like. Defect-lint then passed with no warnings.

**Failure mode/limit.** Color identity is not genuine reasoning difficulty; this is an interface-honesty fix, not a claim that the bands rank cognitive difficulty.

## D7 — Detect triggers from the original input

**Choice.** The Python mirror and all rivals make pair decisions from the original grid, while writes accumulate in a copy.

**Rationale.** This matches the sequential Racket fold because every condition reads `g`, not the evolving `out`. It permits overlapping windows and overwrites without recursive propagation.

**Alternatives considered.** Read from the evolving output, which would create cascades; or process connected components. Neither matches authority behavior.

**Probe/evidence.** Rule smoke passed 120/120. Fixtures include overlapping runs and targets that are already nonzero.

**Failure mode/limit.** The mirror is still an independent Python implementation; actual Racket output is retained for the minimal counterexample and prototype parity fixtures.

## D8 — Require three demonstrations plus one query and support all rotations

**Choice.** Keep `EXAMPLES_NEEDED = 3`; verify every pair in each four-item schedule window as the possible query.

**Rationale.** Three demonstrations are sufficient under the chosen curriculum, and supporting arbitrary rotations makes downstream lesson assembly safer.

**Alternatives considered.** Two demonstrations, which can omit one semantic profile; or fixed query position only, which permits positional shortcuts.

**Probe/evidence.** Exhaustive 48-rotation qualifier and required-rotation semantic battery both pass. The wider 100-per-band census checks 1,200 held-out-query rotations with zero declared-rival ambiguity.

**Failure mode/limit.** Sufficiency is established only against declared rivals and retained hooks, not every conceivable rule.

## D9 — Keep direction parameterization separate

**Choice.** Prototype one episode-level `direction` parameter with complete `down` and `up` Racket rules, but do not select it in production.

**Rationale.** Direction is small, compositional, and demonstrably inferable, but merging it would expand task identity and alter the canonical rule distribution.

**Alternatives considered.** No prototype; or production randomization between directions. The former misses a useful experiment. The latter would violate the pinned selected authority unless the task were explicitly redefined.

**Probe/evidence.** Ten actual Racket/Python parity cases pass; every fixture distinguishes settings; public files hide parameter source and query answer. See `checks/parametric/direction-run/summary.json`.

**Failure mode/limit.** Five fixtures per direction are not broad coverage. The prototype does not evaluate model inference quality or justify canonical adoption.

## D10 — Build a live-registry qualification tool

**Choice.** Add `workspace/qualify.py`, which imports the selected generator, reads its live rival registries, checks canonical fit, and exhausts schedule starts/query rotations.

**Rationale.** Future agents can add a rival once and rerun a cheap, source-bound gate without copying names into a stale script.

**Alternatives considered.** A prose checklist or a hard-coded standalone script. Both drift as the generator evolves.

**Probe/evidence.** The tool is covered by a portable focused test and produced `checks/qualification/final.json`.

**Failure mode/limit.** It uses one seed and finite declared rivals. The shared Racket battery and larger production census remain necessary.
