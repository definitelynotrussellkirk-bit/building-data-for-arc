# Working notes: d8d37830884c

## Review ef60e89ef8fcf034 (2026-10-20)

Selected baseline SHA-256:
`0d888ce299f656e7355eb1637cdc14bebb361ec032d8c798eca827e495c1cd62`.
Final generator SHA-256:
`4fecf23bd273239b3f322ec9eeba52b6e63a24a691a1e23ebb1302871a553af1`.
Version: `3.0.1`. Canonical rule hash remains `0b5bfbd1622f`; no Racket
authority changed.

The completed before battery was 11/12 green. Its only failure was strict defect
lint: `generate()` accepted 33 invalid public scalar calls across booleans,
floats, strings, and negative `sample_index`. The root cause was a missing call
boundary before context construction. The repair requires an exact-integer
`seed`, an exact nonnegative-integer `sample_index`, and leaves the existing
closed difficulty and exact-override checks intact. Eleven focused validation
cases failed before the repair and pass afterward. A 128-call source-to-source
probe found all valid baseline/current grids byte-identical.

Final verification is 12/12 battery stages green, 73/73 task tests, 15/15
focused validation/parametric tests, and 300/300 three-demo-plus-one-query
lessons with zero production ambiguity. All 1,200 hold-each-pair-out query
rotations also had zero declared-rival ambiguity under diagnostic rotation
policy. Evidence is in `checks/after/`, `checks/task-tests/`, `checks/tdd/`,
`checks/contract-equivalence/`, and `checks/lesson-census.summary.json`.

The strongest canonical-fitting shortcut remains
`gray_only_size_six`. A current-source Racket witness generated at seed 901,
sample index 2, difficulty easy has three non-gray six-cell components; the
rival differs from the canonical authority in 18 cells. See
`checks/question-shortcut/report.json`.

`workspace/parametric/target_size.py` is a separate **proposed prototype**, not
production integration. It selects `target_size` once per episode from
`{5,6,7}`, preserving 6 as the exact canonical program. Every pair contains
objects of sizes 5, 6, and 7 so demonstrations distinguish the settings. At
seeds 900–902, all 3 complete Racket-labelled episodes were identified and all
3 query inputs produced setting-distinct outputs. Evidence is under
`checks/parametric/target-size-900/`.

Known limits remain finite shape/rival coverage and finite validation samples.
The parametric extension covers only three values and is not approved. The
public contract repair does not claim universal valid-call equivalence beyond
the retained 128-call probe.

## Review 05f12ae0dce0712e (2026-10-06)

Pinned baseline SHA-256: `c849bc084ad8cf6f3df66ba0ba7231ff82cdeb1c519e795fcf4619486d99c0eb`. Final generator SHA-256: `0d888ce299f656e7355eb1637cdc14bebb361ec032d8c798eca827e495c1cd62`.

The baseline's placement/palette/texture surface was not recoverable, unknown overrides were accepted, legality varied by difficulty, fallback construction weakened exact counts, and no semantic rival contract existed. Canonical inputs also admit the shortcut “only gray six-cell objects become red.”

Version 3.0.0 uses deterministic direct construction with six honest exact axes, two canonical anchors and two non-gray witnesses per four-slot window, strict malformed-input handling, `observe_overrides`, a rule mirror, and executable witness/rival hooks. See `DECISIONS.md`, task-local tests, `workspace/reference_probe.py`, and `checks/shortcut/counterexample.json`.

The canonical `program_solution` was not behaviorally changed. Two active selected `target_code` fields were synchronized to its exact text; archival `raw_code` remains preserved.

No prior return supplied a patch or actionable note; `evidence/associated_notes.jsonl` was empty. The pinned baseline and before battery were used as the lead.
## Current reviewer considerations

Source SHA-256: `4fecf23bd273239b3f322ec9eeba52b6e63a24a691a1e23ebb1302871a553af1`.

# Decisions for `d8d37830884c`

## D1 — repair the public scalar boundary only

**Decision.** Require `type(seed) is int`; require `type(sample_index) is int`
and `sample_index >= 0`; keep the existing closed difficulty set and override
validation.

**Evidence and rationale.** The completed baseline battery was green in 11 of 12
stages. Its only failure was 33 strict-scalar findings across booleans, floats,
strings, and `sample_index=-1`. That isolates the root cause to request
validation rather than generation or semantics. The focused tests were written
first and failed for the expected reason before implementation.

**Rejected alternatives.** Numeric coercion was rejected because it hides caller
defects. A broader generator rewrite, shared-runtime edit, or Racket change was
rejected because no evidence implicated those layers.

## D2 — record the contract repair as version `3.0.1`

**Decision.** Advance `VERSION` from `3.0.0` to `3.0.1` while preserving valid
outputs.

**Rationale.** Invalid-call behavior is part of the public generator contract and
deserves a patch-version marker. Because this generator's scheduled values and
layout are deterministic from valid arguments, the version change did not alter
the sampled grids in the measured domain.

**Probe and limit.** `checks/contract-equivalence/report.json` compares the exact
selected baseline and final source over 128 valid calls spanning all difficulty
values and representative exact overrides; 128/128 outputs are byte-identical.
This is a finite equivalence probe, not a proof for all integers.

## D3 — preserve rule authority and the existing curriculum

**Decision.** Keep canonical rule hash `0b5bfbd1622f`, the six exact axes, the
four-slot two-anchor/two-witness schedule, and the declared
`gray_only_size_six` rival unchanged.

**Rationale.** Rule smoke, authority sync, distribution, profile floor,
diversity, grammar, semantic gate, and override checks were already green before
the repair. Changing them would add risk without addressing the observed defect.

**Measured outcome.** The final battery is 12/12 green; valid-call equivalence is
128/128; a fresh 300-lesson census found zero ambiguity in production order and
all 1,200 diagnostic query rotations.

## D4 — propose one reasoning-preserving parameter: `target_size`

**Decision.** Add an isolated prototype with bounded settings `{5,6,7}` and
canonical/default setting 6. The parameter is chosen once per episode and is not
encoded in the query input.

**Invariant reasoning.** All settings require same-color 4-connected object
segmentation and exact cardinality classification. Only the cardinality receiving
red (2) changes; every other nonzero component becomes blue (1).

**Why this parameter.** It changes the executed transformation while keeping the
original abstraction intact. Output-color substitution was rejected as more
cosmetic, and unrelated geometry/composition changes were rejected as leaving
the family.

## D5 — make every prototype episode directly distinguish all settings

**Decision.** Every generated pair contains separate objects of sizes 5, 6, and
7, plus a size-3 distractor. Input generation is independent of the hidden
setting. Three demonstrations and one query share the same setting.

**Rationale.** This avoids an episode in which an unobserved target size makes
multiple settings observationally equivalent. It also yields a shared-input
witness where all three exact Racket programs produce different outputs.

**Evidence.** `checks/parametric/target-size-900/report.json` records 3/3
identified episodes, 3/3 separating queries, exact program text/hashes, runtime
status, private complete episodes, and solver-safe public challenges.

**Limit.** The design deliberately makes the small parameter easy to infer and
checks only sizes 5, 6, and 7 on three retained seeds. It remains proposed and
isolated from production.

## D6 — tolerate duplicate canonical rows only when authority bytes agree

**Decision.** The prototype's canonical lookup accepts multiple rows for the task
only when every `program_solution` is identical, and then prefers the primary
row (`content_hash == task_id`, no parent).

**Root cause.** The canonical ledger contains both a primary record and an
augmented child for this task, with identical program bytes. Requiring exactly
one row caused the first green attempt to fail despite no authority conflict.

**Rejected alternative.** Silently taking the first row without checking all
programs was rejected because it could mask a genuine authority disagreement.

## D7 — retain `gray_only_size_six` as the strongest canonical shortcut

**Decision.** Answer the assignment question with the color-specific rival:
only gray(5) six-cell objects become red; all other nonzero components become
blue.

**Why strongest.** Every canonical foreground cell is gray, so the rival fits all
canonical labels while differing from the intended color-invariant rule on a
minimal, plausible feature. The final generator emits non-gray six-cell objects
in two of every four scheduled positions.

**Probe.** The exact current-source witness at
`checks/question-shortcut/report.json` has three color-6 six-cell components;
the selected Racket authority and independent mirror agree, and the rival differs
at 18 coordinates.

## D8 — report ordered and rotated lesson evidence separately

**Decision.** Use three demonstrations plus one query, report production-order
and hold-each-pair-out results separately, and label rotations diagnostic.

**Evidence.** `checks/lesson-census.summary.json` records 300/300 materialized
lessons, zero production ambiguities, and zero of 1,200 rotated-query
ambiguities. The complete 13.3 MB JSON is retained as deterministic gzip to stay
within return limits.

**Limit.** These are finite checks against declared rivals, not proof against all
possible shortcut programs or model behavior.
